# Created: 2026-02-05
"""
Kerne Capital Router — Autonomous Capital Operations System
============================================================
Automates all capital movement so Scofield never has to manually bridge,
swap, or allocate tokens. Supports multi-chain scanning, Li.Fi bridging,
same-chain swaps, Hyperliquid deposits/withdrawals, and strategic allocation.

Usage:
    python bot/capital_router.py scan                          # Show all balances everywhere
    python bot/capital_router.py bridge 100 USDC POLYGON -> BASE   # Bridge tokens
    python bot/capital_router.py swap 50 USDC -> WETH BASE         # Swap on same chain
    python bot/capital_router.py deposit-hl 200                    # Deposit USDC to Hyperliquid
    python bot/capital_router.py withdraw-hl 50                    # Withdraw from Hyperliquid
    python bot/capital_router.py collect BASE                      # Collect all USDC to one chain
    python bot/capital_router.py allocate                          # Auto-allocate per strategy
    python bot/capital_router.py allocate --dry-run                # Preview allocation moves

Add --dry-run to any command to simulate without executing.
"""

import os
import sys
import json
import time
import argparse
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

# Ensure bot module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("capital_router")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    # Add success method for compatibility
    logger.success = logger.info

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ChainConfig:
    name: str
    chain_id: int
    rpc_url: str
    explorer: str
    native_symbol: str = "ETH"
    usdc_address: str = ""
    weth_address: str = ""
    wsteth_address: str = ""

@dataclass
class WalletConfig:
    name: str
    address: str
    is_hot: bool = True  # Can we sign transactions from this wallet?

CHAINS: Dict[str, ChainConfig] = {
    "BASE": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url=os.getenv("BASE_RPC_URL", os.getenv("RPC_URL", "https://mainnet.base.org")),
        explorer="https://basescan.org",
        usdc_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        weth_address="0x4200000000000000000000000000000000000006",
        wsteth_address="0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
    ),
    "ARBITRUM": ChainConfig(
        name="Arbitrum",
        chain_id=42161,
        rpc_url=os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        explorer="https://arbiscan.io",
        usdc_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        weth_address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        wsteth_address="0x5979D7b546E38E414F7E9822514be443A4800529",
    ),
    "OPTIMISM": ChainConfig(
        name="Optimism",
        chain_id=10,
        rpc_url=os.getenv("OPT_RPC_URL", "https://optimism.llamarpc.com"),
        explorer="https://optimistic.etherscan.io",
        usdc_address="0x0b2C639c533413bc44a77d5ec4f02fC03b0c8C33",
        weth_address="0x4200000000000000000000000000000000000006",
        wsteth_address="0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb",
    ),
    "POLYGON": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url=os.getenv("POLYGON_RPC_URL", "https://polygon.llamarpc.com"),
        explorer="https://polygonscan.com",
        native_symbol="MATIC",
        usdc_address="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # Native USDC
        weth_address="0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    ),
    "ETHEREUM": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url=os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
        explorer="https://etherscan.io",
        usdc_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        weth_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    ),
}

# Bridged USDC.e addresses (checked separately in scanner)
USDC_E_ADDRESSES = {
    "POLYGON": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e (bridged)
    "ARBITRUM": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC.e (bridged)
}

# All wallets to scan
WALLETS: List[WalletConfig] = [
    WalletConfig(
        name="Hot Wallet (Deployer)",
        address="0x57D400cED462a01Ed51a5De038F204Df49690A99",
        is_hot=True,
    ),
    WalletConfig(
        name="Trezor Burner",
        address="0x14f0fd37A6c42bFe4afDD9DEe6C4Eb7d25073946",
        is_hot=False,
    ),
    WalletConfig(
        name="Gnosis Safe (ETH)",
        address="0xa29528c5ae6969053CA4560a3608Fb9531D868E5",
        is_hot=False,
    ),
]

# Protocol contracts to scan (Base)
PROTOCOL_CONTRACTS_BASE = {
    "KerneVault": "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC",
    "ZIN Pool (Base)": "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7",
    "Treasury": "0xB656440287f8A1112558D3df915b23326e9b89ec",
    "Insurance Fund": "0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9",
}

# Protocol contracts to scan (Arbitrum)
PROTOCOL_CONTRACTS_ARB = {
    "KerneVault (Arb)": "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF",
    "ZIN Pool (Arb)": "0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD",
}

# Hyperliquid configuration
HL_BRIDGE_ADDRESS = "0x2Df1c51E09a42Ad01097321978c7035100396630"
HL_API_URL = "https://api.hyperliquid.xyz"

# ERC20 minimal ABI
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
]

# Target allocation strategy (percentages of total capital)
DEFAULT_ALLOCATION = {
    "hyperliquid": 0.55,       # 55% to Hyperliquid for basis trading
    "zin_base": 0.15,          # 15% to Base ZIN Pool
    "zin_arbitrum": 0.10,      # 10% to Arbitrum ZIN Pool
    "gas_base": 0.08,          # 8% gas reserve on Base
    "gas_arbitrum": 0.06,      # 6% gas reserve on Arbitrum
    "gas_optimism": 0.06,      # 6% gas reserve on Optimism
}

# Li.Fi API
LIFI_API_URL = "https://li.quest/v1"


# ============================================================================
# BALANCE SCANNER
# ============================================================================

class BalanceScanner:
    """Scans all wallets and contracts across all chains."""

    def __init__(self):
        self._w3_cache: Dict[str, Web3] = {}
        self._price_cache: Dict[str, float] = {}

    def _get_w3(self, chain_key: str) -> Optional[Web3]:
        if chain_key in self._w3_cache:
            return self._w3_cache[chain_key]
        cfg = CHAINS.get(chain_key)
        if not cfg:
            return None

        # RPC URLs may be comma-separated; try each one
        raw_rpc = cfg.rpc_url
        if not raw_rpc:
            return None
            
        rpc_urls = [u.strip() for u in raw_rpc.split(",") if u.strip() and u.strip().startswith("http")]
        
        for rpc_url in rpc_urls:
            try:
                # Ensure we don't have trailing commas or malformed URLs
                clean_url = rpc_url.strip().split()[0] 
                w3 = Web3(Web3.HTTPProvider(clean_url, request_kwargs={"timeout": 10}))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                # Quick check: try getting chain ID instead of is_connected (faster)
                w3.eth.chain_id
                self._w3_cache[chain_key] = w3
                return w3
            except Exception as e:
                continue

        logger.warning(f"All RPCs failed for {cfg.name}")
        return None

    def get_eth_price(self) -> float:
        """Fetch current ETH price from CoinGecko (free, no key)."""
        if "ETH" in self._price_cache:
            return self._price_cache["ETH"]
        try:
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"},
                timeout=5,
            )
            price = resp.json()["ethereum"]["usd"]
            self._price_cache["ETH"] = price
            return price
        except Exception:
            fallback = float(os.getenv("ETH_PRICE_USD", "2700"))
            self._price_cache["ETH"] = fallback
            return fallback

    def get_matic_price(self) -> float:
        """Fetch current MATIC/POL price."""
        if "MATIC" in self._price_cache:
            return self._price_cache["MATIC"]
        try:
            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "matic-network", "vs_currencies": "usd"},
                timeout=5,
            )
            price = resp.json()["matic-network"]["usd"]
            self._price_cache["MATIC"] = price
            return price
        except Exception:
            self._price_cache["MATIC"] = 0.35
            return 0.35

    def _get_token_balance(self, w3: Web3, token_addr: str, wallet_addr: str) -> float:
        """Get ERC20 token balance."""
        if not token_addr:
            return 0.0
        try:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI
            )
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_addr)
            ).call()
            decimals = contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception:
            return 0.0

    def _get_native_balance(self, w3: Web3, wallet_addr: str) -> float:
        """Get native token balance (ETH/MATIC)."""
        try:
            balance = w3.eth.get_balance(Web3.to_checksum_address(wallet_addr))
            return float(w3.from_wei(balance, "ether"))
        except Exception:
            return 0.0

    def scan_wallet_on_chain(self, wallet_addr: str, chain_key: str) -> Dict[str, float]:
        """Scan a single wallet on a single chain. Returns {token: amount}."""
        w3 = self._get_w3(chain_key)
        if not w3:
            return {}
        cfg = CHAINS[chain_key]
        result = {}

        native = self._get_native_balance(w3, wallet_addr)
        if native > 0.000001:
            result[cfg.native_symbol] = native

        usdc = self._get_token_balance(w3, cfg.usdc_address, wallet_addr)
        if usdc > 0.001:
            result["USDC"] = usdc

        weth = self._get_token_balance(w3, cfg.weth_address, wallet_addr)
        if weth > 0.000001:
            result["WETH"] = weth

        if cfg.wsteth_address:
            wsteth = self._get_token_balance(w3, cfg.wsteth_address, wallet_addr)
            if wsteth > 0.000001:
                result["wstETH"] = wsteth

        # Check USDC.e (bridged) if applicable
        usdc_e_addr = USDC_E_ADDRESSES.get(chain_key)
        if usdc_e_addr:
            usdc_e = self._get_token_balance(w3, usdc_e_addr, wallet_addr)
            if usdc_e > 0.001:
                result["USDC.e"] = usdc_e

        return result

    def get_hyperliquid_balance(self, wallet_addr: str) -> float:
        """Check Hyperliquid account equity via API."""
        try:
            resp = requests.post(
                f"{HL_API_URL}/info",
                json={"type": "clearinghouseState", "user": wallet_addr},
                timeout=10,
            )
            data = resp.json()
            if "marginSummary" in data:
                return float(data["marginSummary"]["accountValue"])
            return 0.0
        except Exception as e:
            logger.warning(f"Hyperliquid API error: {e}")
            return 0.0

    def full_scan(self) -> dict:
        """
        Scan everything. Returns structured data:
        {
            "wallets": { "wallet_name": { "chain": { "token": amount } } },
            "contracts": { "contract_name": { "token": amount } },
            "hyperliquid": float,
            "total_usd": float,
            "eth_price": float,
        }
        """
        eth_price = self.get_eth_price()
        matic_price = self.get_matic_price()
        total_usd = 0.0

        # Scan wallets
        wallet_data = {}
        for w in WALLETS:
            wallet_data[w.name] = {}
            for chain_key in CHAINS:
                balances = self.scan_wallet_on_chain(w.address, chain_key)
                if balances:
                    wallet_data[w.name][chain_key] = balances
                    # Accumulate USD
                    for token, amt in balances.items():
                        if token in ("ETH", "WETH", "wstETH"):
                            total_usd += amt * eth_price
                        elif token in ("USDC", "USDC.e"):
                            total_usd += amt
                        elif token == "MATIC":
                            total_usd += amt * matic_price

        # Scan protocol contracts (Base)
        contract_data = {}
        for name, addr in PROTOCOL_CONTRACTS_BASE.items():
            balances = self.scan_wallet_on_chain(addr, "BASE")
            if balances:
                contract_data[name] = balances
                for token, amt in balances.items():
                    if token in ("ETH", "WETH", "wstETH"):
                        total_usd += amt * eth_price
                    elif token in ("USDC", "USDC.e"):
                        total_usd += amt

        # Scan protocol contracts (Arbitrum)
        for name, addr in PROTOCOL_CONTRACTS_ARB.items():
            balances = self.scan_wallet_on_chain(addr, "ARBITRUM")
            if balances:
                contract_data[name] = balances
                for token, amt in balances.items():
                    if token in ("ETH", "WETH", "wstETH"):
                        total_usd += amt * eth_price
                    elif token in ("USDC", "USDC.e"):
                        total_usd += amt

        # Hyperliquid
        hl_balance = self.get_hyperliquid_balance(WALLETS[0].address)
        total_usd += hl_balance

        return {
            "wallets": wallet_data,
            "contracts": contract_data,
            "hyperliquid": hl_balance,
            "total_usd": total_usd,
            "eth_price": eth_price,
        }

    def print_scan(self, data: dict):
        """Pretty-print the scan results."""
        eth_price = data["eth_price"]
        print("\n" + "=" * 70)
        print("  KERNE CAPITAL ROUTER — FULL BALANCE SCAN")
        print(f"  ETH Price: ${eth_price:,.2f}")
        print("=" * 70)

        # Wallets
        for wallet_name, chains in data["wallets"].items():
            if not chains:
                continue
            print(f"\n  💼 {wallet_name}")
            for chain_key, tokens in chains.items():
                chain_name = CHAINS[chain_key].name
                parts = []
                for token, amt in tokens.items():
                    if token in ("USDC", "USDC.e"):
                        parts.append(f"{amt:,.2f} {token}")
                    elif token in ("ETH", "WETH", "wstETH"):
                        usd = amt * eth_price
                        parts.append(f"{amt:.6f} {token} (${usd:,.2f})")
                    elif token == "MATIC":
                        parts.append(f"{amt:.4f} MATIC")
                    else:
                        parts.append(f"{amt:.6f} {token}")
                print(f"     {chain_name:12s} │ {' | '.join(parts)}")

        # Protocol contracts
        if data["contracts"]:
            print(f"\n  📦 Protocol Contracts")
            for name, tokens in data["contracts"].items():
                parts = []
                for token, amt in tokens.items():
                    if token in ("USDC", "USDC.e"):
                        parts.append(f"{amt:,.2f} {token}")
                    elif token in ("ETH", "WETH", "wstETH"):
                        usd = amt * eth_price
                        parts.append(f"{amt:.6f} {token} (${usd:,.2f})")
                    else:
                        parts.append(f"{amt:.6f} {token}")
                print(f"     {name:22s} │ {' | '.join(parts)}")

        # Hyperliquid
        print(f"\n  🔮 Hyperliquid")
        print(f"     Account Equity      │ ${data['hyperliquid']:,.2f}")

        # Total
        print(f"\n{'=' * 70}")
        print(f"  💰 TOTAL CAPITAL: ${data['total_usd']:,.2f}")
        print(f"{'=' * 70}\n")


# ============================================================================
# BRIDGE ENGINE (Li.Fi)
# ============================================================================

class BridgeEngine:
    """Handles cross-chain bridging via Li.Fi API."""

    CHAIN_ID_MAP = {k: v.chain_id for k, v in CHAINS.items()}

    def __init__(self, private_key: str, wallet_address: str):
        self.private_key = private_key
        self.wallet_address = wallet_address

    def _get_w3(self, chain_key: str) -> Web3:
        cfg = CHAINS[chain_key]
        # Handle comma-separated RPCs
        rpc_urls = [u.strip() for u in cfg.rpc_url.split(",") if u.strip() and u.strip().startswith("http")]
        for rpc_url in rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                w3.eth.chain_id
                return w3
            except Exception:
                continue
        raise ConnectionError(f"All RPCs failed for {chain_key}")

    def resolve_token_address(self, symbol: str, chain_key: str) -> str:
        """Resolve token symbol to address on a given chain."""
        symbol = symbol.upper()
        cfg = CHAINS[chain_key]

        # Handle native tokens and aliases
        if symbol in ("ETH", "MATIC", "POL") and (symbol == cfg.native_symbol or (symbol in ("MATIC", "POL") and cfg.native_symbol in ("MATIC", "POL"))):
            return "0x0000000000000000000000000000000000000000"
        if symbol == "ETH" and cfg.native_symbol == "MATIC":
            # ETH on Polygon is WETH
            return cfg.weth_address
        if symbol == "USDC":
            return cfg.usdc_address
        if symbol == "WETH":
            return cfg.weth_address
        if symbol == "WSTETH":
            return cfg.wsteth_address

        # Fallback: query Li.Fi
        try:
            resp = requests.get(
                f"{LIFI_API_URL}/token",
                params={"chain": cfg.chain_id, "symbol": symbol},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["address"]
        except Exception as e:
            logger.error(f"Cannot resolve {symbol} on {chain_key}: {e}")
            raise ValueError(f"Unknown token {symbol} on {chain_key}")

    def get_token_decimals(self, token_addr: str, chain_key: str) -> int:
        if token_addr == "0x0000000000000000000000000000000000000000":
            return 18
        w3 = self._get_w3(chain_key)
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        return contract.functions.decimals().call()

    def get_quote(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> dict:
        """Get a Li.Fi quote for bridging/swapping."""
        from_chain_id = CHAINS[from_chain].chain_id
        to_chain_id = CHAINS[to_chain].chain_id
        from_addr = self.resolve_token_address(from_token, from_chain)
        to_addr = self.resolve_token_address(to_token, to_chain)

        decimals = self.get_token_decimals(from_addr, from_chain)
        amount_raw = str(int(amount * (10 ** decimals)))

        params = {
            "fromChain": from_chain_id,
            "toChain": to_chain_id,
            "fromToken": from_addr,
            "toToken": to_addr,
            "fromAmount": amount_raw,
            "fromAddress": self.wallet_address,
            "slippage": 0.005,
        }

        logger.info(f"Fetching Li.Fi quote: {amount} {from_token} on {from_chain} → {to_token} on {to_chain}")
        resp = requests.get(f"{LIFI_API_URL}/quote", params=params, timeout=30)
        if resp.status_code != 200:
            logger.error(f"Li.Fi quote failed ({resp.status_code}): {resp.text[:500]}")
            resp.raise_for_status()

        quote = resp.json()

        # Parse and display estimate
        estimate = quote.get("estimate", {})
        to_amount_raw = estimate.get("toAmount", "0")
        to_token_data = quote.get("action", {}).get("toToken", {})
        to_decimals = to_token_data.get("decimals", 18)
        to_amount = float(to_amount_raw) / (10 ** to_decimals)

        gas_costs = estimate.get("gasCosts", [])
        gas_usd = float(gas_costs[0].get("amountUSD", "0")) if gas_costs else 0

        logger.info(f"  Route: {quote.get('tool', '?')} | Output: {to_amount:.6f} {to_token} | Gas: ${gas_usd:.4f}")

        return quote

    def _ensure_approval(self, token_addr: str, spender: str, amount_raw: int, chain_key: str):
        """Approve token spending if needed."""
        if token_addr == "0x0000000000000000000000000000000000000000":
            return
        w3 = self._get_w3(chain_key)
        contract = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        allowance = contract.functions.allowance(
            Web3.to_checksum_address(self.wallet_address),
            Web3.to_checksum_address(spender),
        ).call()

        if allowance >= amount_raw:
            return

        logger.info(f"Approving token {token_addr} for spender {spender}...")
        nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))
        approve_tx = contract.functions.approve(
            Web3.to_checksum_address(spender), 2**256 - 1
        ).build_transaction({
            "from": self.wallet_address,
            "nonce": nonce,
            "chainId": CHAINS[chain_key].chain_id,
        })

        # Gas pricing
        try:
            if chain_key == "POLYGON":
                # Polygon requires very high priority fee (500 Gwei tested working 2026-02-05)
                approve_tx["maxPriorityFeePerGas"] = w3.to_wei(500, "gwei")
                approve_tx["maxFeePerGas"] = w3.to_wei(1000, "gwei")
            else:
                fee_history = w3.eth.fee_history(1, "latest")
                base_fee = fee_history["baseFeePerGas"][-1]
                approve_tx["maxPriorityFeePerGas"] = w3.to_wei(0.001, "gwei")
                approve_tx["maxFeePerGas"] = int(base_fee * 1.5) + approve_tx["maxPriorityFeePerGas"]
        except Exception:
            approve_tx["gasPrice"] = w3.eth.gas_price

        signed = w3.eth.account.sign_transaction(approve_tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        logger.info(f"Approval TX: {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        logger.success("Approval confirmed.")

    def execute_quote(self, quote: dict, from_chain: str) -> str:
        """Execute a Li.Fi quote transaction."""
        chain_id = CHAINS[from_chain].chain_id
        w3 = self._get_w3(from_chain)
        tx_request = quote["transactionRequest"]

        # Handle approval
        from_token = quote.get("action", {}).get("fromToken", {}).get("address", "")
        if from_token and from_token != "0x0000000000000000000000000000000000000000":
            amount_raw = int(quote["action"]["fromAmount"])
            self._ensure_approval(from_token, tx_request["to"], amount_raw, from_chain)

        def to_int(val):
            if isinstance(val, str) and val.startswith("0x"):
                return int(val, 16)
            return int(val)

        nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))

        tx = {
            "from": self.wallet_address,
            "to": Web3.to_checksum_address(tx_request["to"]),
            "data": tx_request["data"],
            "value": to_int(tx_request.get("value", 0)),
            "nonce": nonce,
            "chainId": chain_id,
        }

        # Gas estimation
        gas_limit = to_int(tx_request.get("gasLimit", 500000))
        tx["gas"] = int(gas_limit * 1.2)

        try:
            if from_chain == "POLYGON":
                # Polygon requires very high priority fee (500 Gwei tested working 2026-02-05)
                tx["maxPriorityFeePerGas"] = w3.to_wei(500, "gwei")
                tx["maxFeePerGas"] = w3.to_wei(1000, "gwei")
            else:
                fee_history = w3.eth.fee_history(1, "latest")
                base_fee = fee_history["baseFeePerGas"][-1]
                tx["maxPriorityFeePerGas"] = w3.to_wei(0.001, "gwei")
                tx["maxFeePerGas"] = int(base_fee * 1.5) + tx["maxPriorityFeePerGas"]
        except Exception:
            tx["gasPrice"] = w3.eth.gas_price

        logger.info(f"Signing and sending transaction on {from_chain} (chain {chain_id})...")
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        hash_hex = tx_hash.hex()
        logger.success(f"Transaction sent: {hash_hex}")
        logger.info(f"Explorer: {CHAINS[from_chain].explorer}/tx/{hash_hex}")

        return hash_hex

    def bridge(
        self,
        amount: float,
        from_token: str,
        from_chain: str,
        to_token: str,
        to_chain: str,
        dry_run: bool = False,
    ) -> Optional[str]:
        """High-level bridge: quote + execute."""
        quote = self.get_quote(from_chain, to_chain, from_token, to_token, amount)

        if dry_run:
            logger.info("DRY RUN — transaction would be executed now. No funds moved.")
            return None

        return self.execute_quote(quote, from_chain)

    def swap(
        self,
        amount: float,
        from_token: str,
        to_token: str,
        chain: str,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Same-chain swap via Li.Fi."""
        return self.bridge(amount, from_token, chain, to_token, chain, dry_run)


# ============================================================================
# HYPERLIQUID OPERATIONS
# ============================================================================

class HyperliquidOps:
    """Deposit/withdraw USDC to/from Hyperliquid via Arbitrum bridge."""

    def __init__(self, private_key: str, wallet_address: str):
        self.private_key = private_key
        self.wallet_address = wallet_address

    def deposit(self, amount_usdc: float, dry_run: bool = False) -> Optional[str]:
        """
        Deposit USDC to Hyperliquid.
        Requires USDC on Arbitrum. Sends to the HL bridge contract.
        """
        cfg = CHAINS["ARBITRUM"]
        w3 = Web3(Web3.HTTPProvider(cfg.rpc_url, request_kwargs={"timeout": 15}))

        usdc_contract = w3.eth.contract(
            address=Web3.to_checksum_address(cfg.usdc_address), abi=ERC20_ABI
        )

        amount_raw = int(amount_usdc * 1e6)

        # Check balance
        balance = usdc_contract.functions.balanceOf(
            Web3.to_checksum_address(self.wallet_address)
        ).call()

        logger.info(f"Arbitrum USDC balance: {balance / 1e6:.2f}")
        if balance < amount_raw:
            logger.error(f"Insufficient USDC on Arbitrum. Have {balance / 1e6:.2f}, need {amount_usdc}")
            return None

        if dry_run:
            logger.info(f"DRY RUN — Would deposit {amount_usdc} USDC to Hyperliquid.")
            return None

        # Approve
        allowance = usdc_contract.functions.allowance(
            Web3.to_checksum_address(self.wallet_address),
            Web3.to_checksum_address(HL_BRIDGE_ADDRESS),
        ).call()

        if allowance < amount_raw:
            logger.info("Approving USDC for Hyperliquid bridge...")
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))
            approve_tx = usdc_contract.functions.approve(
                Web3.to_checksum_address(HL_BRIDGE_ADDRESS), 2**256 - 1
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "chainId": cfg.chain_id,
                "gasPrice": w3.eth.gas_price,
            })
            signed = w3.eth.account.sign_transaction(approve_tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            logger.success("USDC approved for HL bridge.")

        # Transfer USDC to bridge address
        nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))
        transfer_tx = usdc_contract.functions.transfer(
            Web3.to_checksum_address(HL_BRIDGE_ADDRESS), amount_raw
        ).build_transaction({
            "from": self.wallet_address,
            "nonce": nonce,
            "chainId": cfg.chain_id,
            "gasPrice": w3.eth.gas_price,
        })
        signed = w3.eth.account.sign_transaction(transfer_tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        hash_hex = tx_hash.hex()
        logger.success(f"Hyperliquid deposit TX: {hash_hex}")
        logger.info(f"Explorer: {cfg.explorer}/tx/{hash_hex}")
        return hash_hex

    def withdraw(self, amount_usdc: float, dry_run: bool = False) -> bool:
        """
        Withdraw USDC from Hyperliquid to Arbitrum.
        Uses HL API (requires signed action).
        """
        if dry_run:
            logger.info(f"DRY RUN — Would withdraw {amount_usdc} USDC from Hyperliquid.")
            return True

        try:
            # Hyperliquid uses a special signed withdrawal via their SDK
            # For now, log instructions since withdrawals require the HL Python SDK
            logger.warning(
                f"Hyperliquid withdrawal of ${amount_usdc} requires the HL SDK. "
                f"Use the Hyperliquid UI or run: "
                f"python -c \"from hyperliquid.exchange import Exchange; ...\""
            )
            logger.info("Alternatively, use the Hyperliquid web UI to withdraw.")
            return False
        except Exception as e:
            logger.error(f"HL withdrawal failed: {e}")
            return False


# ============================================================================
# CAPITAL ALLOCATOR
# ============================================================================

class CapitalAllocator:
    """
    Automatically allocates capital according to the target strategy.
    Given the current state of all balances, computes the moves needed
    to reach the target allocation and executes them.
    """

    def __init__(self, scanner: BalanceScanner, bridge: BridgeEngine, hl_ops: HyperliquidOps):
        self.scanner = scanner
        self.bridge = bridge
        self.hl_ops = hl_ops

    def compute_moves(self, scan_data: dict, allocation: dict = None) -> List[dict]:
        """
        Compute the list of moves needed to reach target allocation.
        Returns a list of move dicts.
        """
        if allocation is None:
            allocation = DEFAULT_ALLOCATION

        total_usd = scan_data["total_usd"]
        if total_usd < 1.0:
            logger.warning("Total capital < $1. Nothing to allocate.")
            return []

        moves = []

        # Calculate target amounts
        targets = {k: total_usd * v for k, v in allocation.items()}

        # Current amounts by destination
        current = {
            "hyperliquid": scan_data["hyperliquid"],
            "zin_base": 0.0,
            "zin_arbitrum": 0.0,
            "gas_base": 0.0,
            "gas_arbitrum": 0.0,
            "gas_optimism": 0.0,
        }

        # Parse ZIN pool balances
        for name, tokens in scan_data["contracts"].items():
            if "ZIN Pool (Base)" in name:
                current["zin_base"] = tokens.get("USDC", 0) + tokens.get("WETH", 0) * scan_data["eth_price"]
            elif "ZIN Pool (Arb)" in name:
                current["zin_arbitrum"] = tokens.get("USDC", 0) + tokens.get("WETH", 0) * scan_data["eth_price"]

        # Parse gas balances from hot wallet
        hot_wallet_data = scan_data["wallets"].get("Hot Wallet (Deployer)", {})
        for chain_key, tokens in hot_wallet_data.items():
            eth_val = tokens.get("ETH", 0) * scan_data["eth_price"]
            if chain_key == "BASE":
                current["gas_base"] = eth_val
            elif chain_key == "ARBITRUM":
                current["gas_arbitrum"] = eth_val
            elif chain_key == "OPTIMISM":
                current["gas_optimism"] = eth_val

        # Identify surplus capital (USDC sitting in wallets not yet allocated)
        surplus_usdc = {}
        for wallet_name, chains in scan_data["wallets"].items():
            for chain_key, tokens in chains.items():
                usdc = tokens.get("USDC", 0)
                if usdc > 0.50:  # Ignore dust
                    key = f"{wallet_name}:{chain_key}"
                    surplus_usdc[key] = {
                        "amount": usdc,
                        "chain": chain_key,
                        "wallet": wallet_name,
                    }

        # Calculate deficits
        deficits = {}
        for dest, target in targets.items():
            deficit = target - current[dest]
            if deficit > 1.0:  # Only if > $1 deficit
                deficits[dest] = deficit

        logger.info(f"\n--- Allocation Analysis ---")
        logger.info(f"Total Capital: ${total_usd:,.2f}")
        for dest, target in targets.items():
            cur = current[dest]
            status = "✅" if abs(cur - target) < 2 else "⚠️"
            logger.info(f"  {dest:20s}: ${cur:>8.2f} / ${target:>8.2f} target {status}")

        if surplus_usdc:
            logger.info(f"\nSurplus USDC (unallocated):")
            for key, info in surplus_usdc.items():
                logger.info(f"  {key}: ${info['amount']:,.2f}")

        if not deficits:
            logger.info("\n✅ All allocations are within target. No moves needed.")
            return []

        # Generate moves — prioritize filling from nearest surplus
        for dest, deficit_amount in sorted(deficits.items(), key=lambda x: -x[1]):
            if deficit_amount < 1.0:
                continue

            # Determine destination chain
            if dest == "hyperliquid":
                dest_chain = "ARBITRUM"  # HL deposits go via Arbitrum
            elif "base" in dest:
                dest_chain = "BASE"
            elif "arbitrum" in dest:
                dest_chain = "ARBITRUM"
            elif "optimism" in dest:
                dest_chain = "OPTIMISM"
            else:
                continue

            # Find best surplus source
            best_source = None
            best_amount = 0
            for key, info in surplus_usdc.items():
                if info["amount"] > best_amount:
                    best_source = key
                    best_amount = info["amount"]

            if not best_source or best_amount < 1.0:
                logger.warning(f"No surplus USDC available to fill {dest} (deficit: ${deficit_amount:.2f})")
                continue

            source_info = surplus_usdc[best_source]
            move_amount = min(deficit_amount, source_info["amount"])

            # Determine if we need gas (ETH) or USDC
            token = "ETH" if "gas" in dest else "USDC"

            move = {
                "type": "bridge" if source_info["chain"] != dest_chain else "local",
                "from_chain": source_info["chain"],
                "to_chain": dest_chain,
                "from_token": "USDC",
                "to_token": token,
                "amount": round(move_amount, 2),
                "destination": dest,
                "description": f"Move ${move_amount:.2f} USDC from {source_info['chain']} → {dest_chain} as {token} for {dest}",
            }

            # If destination is Hyperliquid, add extra step
            if dest == "hyperliquid":
                move["extra_step"] = "deposit-hl"

            moves.append(move)

            # Reduce surplus
            surplus_usdc[best_source]["amount"] -= move_amount
            if surplus_usdc[best_source]["amount"] < 1.0:
                del surplus_usdc[best_source]

        return moves

    def execute_moves(self, moves: List[dict], dry_run: bool = False):
        """Execute the computed moves."""
        if not moves:
            logger.info("No moves to execute.")
            return

        print(f"\n{'=' * 60}")
        print(f"  ALLOCATION PLAN — {len(moves)} moves")
        print(f"{'=' * 60}")
        for i, move in enumerate(moves, 1):
            print(f"  {i}. {move['description']}")
            if move.get("extra_step") == "deposit-hl":
                print(f"     └─ Then deposit to Hyperliquid")
        print(f"{'=' * 60}\n")

        if dry_run:
            logger.info("DRY RUN — No transactions will be executed.")
            return

        for i, move in enumerate(moves, 1):
            logger.info(f"\n--- Executing Move {i}/{len(moves)} ---")
            logger.info(move["description"])

            try:
                if move["from_chain"] == move["to_chain"] and move["from_token"] == move["to_token"]:
                    logger.info("Same chain, same token — no bridge needed.")
                elif move["from_token"] != move["to_token"] or move["from_chain"] != move["to_chain"]:
                    tx = self.bridge.bridge(
                        amount=move["amount"],
                        from_token=move["from_token"],
                        from_chain=move["from_chain"],
                        to_token=move["to_token"],
                        to_chain=move["to_chain"],
                        dry_run=False,
                    )
                    if tx:
                        logger.success(f"Bridge TX: {tx}")
                        # Wait for bridge to process
                        logger.info("Waiting 30s for bridge to settle...")
                        time.sleep(30)

                # Extra step: deposit to HL
                if move.get("extra_step") == "deposit-hl":
                    self.hl_ops.deposit(move["amount"], dry_run=False)

            except Exception as e:
                logger.error(f"Move {i} failed: {e}")
                logger.info("Continuing with remaining moves...")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kerne Capital Router — Autonomous Capital Operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot/capital_router.py scan
  python bot/capital_router.py bridge 367 USDC POLYGON -> BASE
  python bot/capital_router.py bridge 100 USDC BASE -> ARBITRUM
  python bot/capital_router.py swap 50 USDC -> WETH BASE
  python bot/capital_router.py swap 0.01 ETH -> USDC BASE
  python bot/capital_router.py deposit-hl 200
  python bot/capital_router.py withdraw-hl 50
  python bot/capital_router.py collect BASE
  python bot/capital_router.py allocate
  python bot/capital_router.py allocate --dry-run
        """,
    )

    parser.add_argument("command", choices=[
        "scan", "bridge", "swap", "deposit-hl", "withdraw-hl", "collect", "allocate"
    ], help="Operation to perform")

    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Preview operations without executing")

    parsed = parser.parse_args()

    # Load private key
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key and parsed.command not in ("scan",):
        logger.error("PRIVATE_KEY not found in bot/.env — required for transactions.")
        sys.exit(1)

    # Derive wallet address from private key
    wallet_address = None
    if private_key:
        from eth_account import Account
        wallet_address = Account.from_key(private_key).address

    scanner = BalanceScanner()

    # ---- SCAN ----
    if parsed.command == "scan":
        data = scanner.full_scan()
        scanner.print_scan(data)
        return

    bridge = BridgeEngine(private_key, wallet_address)
    hl_ops = HyperliquidOps(private_key, wallet_address)

    # ---- BRIDGE ----
    if parsed.command == "bridge":
        # Format: bridge 367 USDC POLYGON -> BASE
        # Or: bridge 367 USDC POLYGON -> WETH BASE
        args_str = " ".join(parsed.args)
        parts = args_str.upper().replace("->", " -> ").split()

        if len(parts) < 4 or "->" not in parts:
            logger.error("Usage: bridge [AMOUNT] [TOKEN] [FROM_CHAIN] -> [TO_CHAIN]")
            logger.error("   or: bridge [AMOUNT] [TOKEN] [FROM_CHAIN] -> [TO_TOKEN] [TO_CHAIN]")
            sys.exit(1)

        amount = float(parts[0])
        from_token = parts[1]
        from_chain = parts[2]
        arrow_idx = parts.index("->")

        if len(parts) > arrow_idx + 2:
            to_token = parts[arrow_idx + 1]
            to_chain = parts[arrow_idx + 2]
        else:
            to_token = from_token
            to_chain = parts[arrow_idx + 1]

        bridge.bridge(amount, from_token, from_chain, to_token, to_chain, dry_run=parsed.dry_run)

    # ---- SWAP ----
    elif parsed.command == "swap":
        # Format: swap 50 USDC -> WETH BASE
        args_str = " ".join(parsed.args)
        parts = args_str.upper().replace("->", " -> ").split()

        if len(parts) < 5 or "->" not in parts:
            logger.error("Usage: swap [AMOUNT] [FROM_TOKEN] -> [TO_TOKEN] [CHAIN]")
            sys.exit(1)

        amount = float(parts[0])
        from_token = parts[1]
        arrow_idx = parts.index("->")
        to_token = parts[arrow_idx + 1]
        chain = parts[arrow_idx + 2]

        bridge.swap(amount, from_token, to_token, chain, dry_run=parsed.dry_run)

    # ---- DEPOSIT-HL ----
    elif parsed.command == "deposit-hl":
        if not parsed.args:
            logger.error("Usage: deposit-hl [AMOUNT_USDC]")
            sys.exit(1)
        amount = float(parsed.args[0])
        hl_ops.deposit(amount, dry_run=parsed.dry_run)

    # ---- WITHDRAW-HL ----
    elif parsed.command == "withdraw-hl":
        if not parsed.args:
            logger.error("Usage: withdraw-hl [AMOUNT_USDC]")
            sys.exit(1)
        amount = float(parsed.args[0])
        hl_ops.withdraw(amount, dry_run=parsed.dry_run)

    # ---- COLLECT ----
    elif parsed.command == "collect":
        # Collect all scattered USDC to one destination chain
        dest_chain = parsed.args[0].upper() if parsed.args else "BASE"
        logger.info(f"Collecting all scattered USDC to {dest_chain}...")

        data = scanner.full_scan()
        scanner.print_scan(data)

        moves = []
        for wallet_name, chains in data["wallets"].items():
            for chain_key, tokens in chains.items():
                usdc = tokens.get("USDC", 0)
                if usdc > 0.50 and chain_key != dest_chain:
                    moves.append({
                        "amount": round(usdc, 2),
                        "from_chain": chain_key,
                        "to_chain": dest_chain,
                        "source": wallet_name,
                    })

        if not moves:
            logger.info(f"No USDC to collect — everything is already on {dest_chain}.")
            return

        print(f"\n  Collection Plan:")
        for m in moves:
            print(f"    {m['amount']:.2f} USDC from {m['from_chain']} ({m['source']}) → {dest_chain}")

        if parsed.dry_run:
            logger.info("DRY RUN — No transactions executed.")
            return

        # Only execute from hot wallet (we can't sign from Trezor/burner programmatically)
        for m in moves:
            if "Hot Wallet" in m["source"]:
                bridge.bridge(
                    m["amount"], "USDC", m["from_chain"], "USDC", dest_chain, dry_run=False
                )
            else:
                logger.warning(
                    f"Cannot auto-bridge from {m['source']} (not a hot wallet). "
                    f"Manually send {m['amount']:.2f} USDC from {m['from_chain']} to {dest_chain}."
                )

    # ---- ALLOCATE ----
    elif parsed.command == "allocate":
        logger.info("Running full balance scan...")
        data = scanner.full_scan()
        scanner.print_scan(data)

        allocator = CapitalAllocator(scanner, bridge, hl_ops)
        moves = allocator.compute_moves(data)
        allocator.execute_moves(moves, dry_run=parsed.dry_run)


if __name__ == "__main__":
    main()