# Created: 2026-01-15
"""
Flash Arbitrage Scanner Bot
===========================
Zero-capital arbitrage bot that uses Kerne's internal flash loans to capture
price spreads between Aerodrome and Uniswap V3 on Base.

Architecture:
    1. Continuously scans DEX prices for configured token pairs
    2. Detects profitable opportunities (after gas costs)
    3. Executes via KerneFlashArbBot smart contract
    4. Routes 80% of profits to Treasury, 20% to Insurance Fund

Revenue Model:
    - Risk-free profit extraction from market inefficiencies
    - No capital required (uses internal flash loans)
    - Creates immediate, high-velocity revenue stream
"""

import os
import json
import time
import asyncio
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from enum import IntEnum

from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv
from loguru import logger

try:
    from bot.alerts import send_discord_alert
except ImportError:
    try:
        from alerts import send_discord_alert
    except ImportError:
        def send_discord_alert(msg, level="INFO"):
            logger.info(f"[ALERT-{level}] {msg}")


# =============================================================================
# CONFIGURATION
# =============================================================================

class DEX(IntEnum):
    AERODROME = 0
    UNISWAP_V3 = 1


@dataclass
class TokenPair:
    """Configuration for a token pair to monitor for arbitrage."""
    name: str
    token_a: str
    token_b: str
    decimal_a: int = 18
    decimal_b: int = 18
    aero_stable: bool = False
    uni_fee: int = 3000  # 0.3% = 3000
    min_profit_usd: float = 5.0
    max_trade_size: float = 100.0  # In token_a terms
    enabled: bool = True


@dataclass
class ArbOpportunity:
    """Represents a detected arbitrage opportunity."""
    pair: TokenPair
    buy_dex: DEX
    sell_dex: DEX
    amount_in: int
    expected_profit: int
    profit_usd: float
    buy_price: float
    sell_price: float
    spread_bps: float
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return (
            f"{self.pair.name} | Buy on {self.buy_dex.name} @ {self.buy_price:.6f} → "
            f"Sell on {self.sell_dex.name} @ {self.sell_price:.6f} | "
            f"Spread: {self.spread_bps:.2f} bps | Profit: ${self.profit_usd:.2f}"
        )


# Default token pairs to monitor on Base
DEFAULT_PAIRS = [
    TokenPair(
        name="WETH/USDC",
        token_a="0x4200000000000000000000000000000000000006",  # WETH on Base
        token_b="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        decimal_a=18,
        decimal_b=6,
        aero_stable=False,
        uni_fee=500,  # 0.05% pool
        min_profit_usd=10.0,
        max_trade_size=10.0,
    ),
    TokenPair(
        name="USDC/USDbC",
        token_a="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Native USDC
        token_b="0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",  # Bridged USDbC
        decimal_a=6,
        decimal_b=6,
        aero_stable=True,
        uni_fee=100,  # 0.01% stable pool
        min_profit_usd=2.0,
        max_trade_size=50000.0,
    ),
    TokenPair(
        name="cbETH/WETH",
        token_a="0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",  # cbETH
        token_b="0x4200000000000000000000000000000000000006",  # WETH
        decimal_a=18,
        decimal_b=18,
        aero_stable=False,
        uni_fee=500,
        min_profit_usd=5.0,
        max_trade_size=5.0,
    ),
]


# =============================================================================
# FLASH ARB SCANNER
# =============================================================================

class FlashArbScanner:
    """
    Scans Aerodrome and Uniswap V3 for arbitrage opportunities
    and executes them via KerneFlashArbBot contract.
    """

    # Base Mainnet Addresses
    AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"
    UNISWAP_V3_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"
    UNISWAP_V3_QUOTER = "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a"
    
    def __init__(self, pairs: List[TokenPair] = None):
        load_dotenv()
        
        self.rpc_url = os.getenv("RPC_URL")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.arb_bot_address = os.getenv("FLASH_ARB_BOT_ADDRESS")
        self.psm_address = os.getenv("PSM_ADDRESS")
        self.vault_address = os.getenv("VAULT_ADDRESS")
        
        if not self.rpc_url or not self.private_key:
            raise ValueError("Missing RPC_URL or PRIVATE_KEY")
        
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to RPC")
        
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.pairs = pairs or DEFAULT_PAIRS
        
        # Load contract ABIs
        self._load_contracts()
        
        # Stats tracking
        self.opportunities_found = 0
        self.arbs_executed = 0
        self.total_profit_usd = 0.0
        self.start_time = time.time()
        
        # Rate limiting
        self.last_scan_time = 0
        self.min_scan_interval = 0.5  # seconds
        
        # Gas price monitoring
        self.max_gas_price_gwei = float(os.getenv("MAX_GAS_PRICE_GWEI", "50"))
        
        logger.info(f"FlashArbScanner initialized. Monitoring {len(self.pairs)} pairs.")
        logger.info(f"Bot address: {self.arb_bot_address}")
        logger.info(f"Executor wallet: {self.account.address}")

    def _load_contracts(self):
        """Load contract ABIs and create contract instances."""
        base_path = os.path.dirname(__file__)
        
        # Load Aerodrome Router ABI (simplified)
        self.aerodrome_abi = [
            {
                "inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                          {"components": [{"internalType": "address", "name": "from", "type": "address"},
                                         {"internalType": "address", "name": "to", "type": "address"},
                                         {"internalType": "bool", "name": "stable", "type": "bool"},
                                         {"internalType": "address", "name": "factory", "type": "address"}],
                           "internalType": "struct IRouter.Route[]", "name": "routes", "type": "tuple[]"}],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "defaultFactory",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Load Uniswap V3 Quoter ABI (simplified)
        self.quoter_abi = [
            {
                "inputs": [{"internalType": "address", "name": "tokenIn", "type": "address"},
                          {"internalType": "address", "name": "tokenOut", "type": "address"},
                          {"internalType": "uint24", "name": "fee", "type": "uint24"},
                          {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                          {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}],
                "name": "quoteExactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Create contract instances
        self.aerodrome_router = self.w3.eth.contract(
            address=self.AERODROME_ROUTER,
            abi=self.aerodrome_abi
        )
        
        self.uniswap_quoter = self.w3.eth.contract(
            address=self.UNISWAP_V3_QUOTER,
            abi=self.quoter_abi
        )
        
        # Load FlashArbBot if address is set
        if self.arb_bot_address:
            arb_abi_path = os.path.join(base_path, "..", "out", "KerneFlashArbBot.sol", "KerneFlashArbBot.json")
            if os.path.exists(arb_abi_path):
                with open(arb_abi_path, "r") as f:
                    arb_artifact = json.load(f)
                self.arb_bot = self.w3.eth.contract(
                    address=self.arb_bot_address,
                    abi=arb_artifact["abi"]
                )
            else:
                logger.warning(f"FlashArbBot ABI not found at {arb_abi_path}")
                self.arb_bot = None
        else:
            self.arb_bot = None
            logger.warning("FLASH_ARB_BOT_ADDRESS not set - dry run mode")
        
        # Get Aerodrome factory
        try:
            self.aero_factory = self.aerodrome_router.functions.defaultFactory().call()
        except Exception:
            self.aero_factory = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"  # Default

    def get_aerodrome_quote(
        self, 
        token_in: str, 
        token_out: str, 
        amount_in: int, 
        stable: bool = False
    ) -> int:
        """Get quote from Aerodrome."""
        try:
            routes = [(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
                stable,
                self.aero_factory
            )]
            
            amounts = self.aerodrome_router.functions.getAmountsOut(
                amount_in,
                routes
            ).call()
            
            return amounts[-1]
        except Exception as e:
            logger.debug(f"Aerodrome quote failed: {e}")
            return 0

    def get_uniswap_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        fee: int = 3000
    ) -> int:
        """Get quote from Uniswap V3."""
        try:
            # Use eth_call to simulate (quoter is not view, but we can simulate)
            amount_out = self.uniswap_quoter.functions.quoteExactInputSingle(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
                fee,
                amount_in,
                0  # sqrtPriceLimitX96
            ).call()
            
            return amount_out
        except Exception as e:
            logger.debug(f"Uniswap quote failed: {e}")
            return 0

    def calculate_spread(
        self,
        pair: TokenPair,
        amount: int
    ) -> Optional[ArbOpportunity]:
        """
        Calculate price spread between Aerodrome and Uniswap V3.
        Returns ArbOpportunity if profitable, None otherwise.
        """
        # Get quotes from both DEXs (A → B)
        aero_out = self.get_aerodrome_quote(
            pair.token_a, pair.token_b, amount, pair.aero_stable
        )
        uni_out = self.get_uniswap_quote(
            pair.token_a, pair.token_b, amount, pair.uni_fee
        )
        
        if aero_out == 0 or uni_out == 0:
            return None
        
        # Calculate prices (token_b per token_a)
        aero_price = aero_out / amount
        uni_price = uni_out / amount
        
        # Determine direction
        if uni_price > aero_price:
            # Buy on Aerodrome, sell on Uniswap
            buy_dex = DEX.AERODROME
            sell_dex = DEX.UNISWAP_V3
            buy_price = aero_price
            sell_price = uni_price
            
            # Calculate round-trip profit
            # Buy token_b on Aerodrome
            token_b_received = aero_out
            # Sell token_b back to token_a on Uniswap
            uni_return = self.get_uniswap_quote(
                pair.token_b, pair.token_a, token_b_received, pair.uni_fee
            )
            expected_profit = uni_return - amount if uni_return > amount else 0
            
        else:
            # Buy on Uniswap, sell on Aerodrome
            buy_dex = DEX.UNISWAP_V3
            sell_dex = DEX.AERODROME
            buy_price = uni_price
            sell_price = aero_price
            
            # Calculate round-trip profit
            token_b_received = uni_out
            aero_return = self.get_aerodrome_quote(
                pair.token_b, pair.token_a, token_b_received, pair.aero_stable
            )
            expected_profit = aero_return - amount if aero_return > amount else 0
        
        if expected_profit <= 0:
            return None
        
        # Calculate spread in basis points
        spread_bps = abs(sell_price - buy_price) / buy_price * 10000
        
        # Estimate profit in USD (assuming token_a is ETH-like or stable)
        # This is a simplification - in production you'd use price feeds
        token_a_price_usd = 3000.0 if pair.decimal_a == 18 else 1.0
        profit_usd = (expected_profit / (10 ** pair.decimal_a)) * token_a_price_usd
        
        # Check minimum profit threshold
        if profit_usd < pair.min_profit_usd:
            return None
        
        return ArbOpportunity(
            pair=pair,
            buy_dex=buy_dex,
            sell_dex=sell_dex,
            amount_in=amount,
            expected_profit=expected_profit,
            profit_usd=profit_usd,
            buy_price=buy_price,
            sell_price=sell_price,
            spread_bps=spread_bps
        )

    def scan_pairs(self) -> List[ArbOpportunity]:
        """Scan all configured pairs for arbitrage opportunities."""
        opportunities = []
        
        for pair in self.pairs:
            if not pair.enabled:
                continue
            
            # Calculate amount in wei
            amount = int(pair.max_trade_size * (10 ** pair.decimal_a))
            
            try:
                opp = self.calculate_spread(pair, amount)
                if opp:
                    opportunities.append(opp)
                    self.opportunities_found += 1
                    logger.info(f"🎯 Opportunity: {opp}")
            except Exception as e:
                logger.debug(f"Error scanning {pair.name}: {e}")
        
        return opportunities

    def estimate_gas_cost(self) -> Tuple[int, float]:
        """Estimate gas cost for arbitrage execution."""
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = gas_price / 1e9
            
            # Estimate gas for flash loan + 2 swaps
            estimated_gas = 350000
            gas_cost_wei = gas_price * estimated_gas
            gas_cost_eth = gas_cost_wei / 1e18
            gas_cost_usd = gas_cost_eth * 3000  # Assuming ETH = $3000
            
            return gas_price_gwei, gas_cost_usd
        except Exception:
            return 50.0, 5.0  # Default estimates

    def is_profitable_after_gas(self, opp: ArbOpportunity) -> bool:
        """Check if opportunity is profitable after gas costs."""
        gas_price_gwei, gas_cost_usd = self.estimate_gas_cost()
        
        # Check gas price limit
        if gas_price_gwei > self.max_gas_price_gwei:
            logger.debug(f"Gas too high: {gas_price_gwei:.2f} gwei > {self.max_gas_price_gwei}")
            return False
        
        # Check profit minus gas
        net_profit = opp.profit_usd - gas_cost_usd
        if net_profit <= 0:
            logger.debug(f"Not profitable after gas: ${opp.profit_usd:.2f} - ${gas_cost_usd:.2f} = ${net_profit:.2f}")
            return False
        
        logger.info(f"Net profit after gas: ${net_profit:.2f}")
        return True

    def execute_arbitrage(self, opp: ArbOpportunity) -> Optional[str]:
        """Execute arbitrage via KerneFlashArbBot contract."""
        if not self.arb_bot:
            logger.warning("FlashArbBot not configured - skipping execution")
            return None
        
        try:
            # Build swap params
            swaps = []
            
            # First swap: Buy on cheaper DEX
            if opp.buy_dex == DEX.AERODROME:
                swaps.append((
                    int(DEX.AERODROME),  # dex
                    opp.pair.token_a,     # tokenIn
                    opp.pair.token_b,     # tokenOut
                    opp.amount_in,        # amountIn
                    1,                    # minAmountOut
                    opp.pair.aero_stable, # stable
                    0,                    # fee (not used for Aerodrome)
                    b""                   # extraData
                ))
            else:
                swaps.append((
                    int(DEX.UNISWAP_V3),
                    opp.pair.token_a,
                    opp.pair.token_b,
                    opp.amount_in,
                    1,
                    False,
                    opp.pair.uni_fee,
                    b""
                ))
            
            # Second swap: Sell on more expensive DEX
            if opp.sell_dex == DEX.AERODROME:
                swaps.append((
                    int(DEX.AERODROME),
                    opp.pair.token_b,
                    opp.pair.token_a,
                    0,  # Use full balance
                    opp.amount_in,  # Must return at least borrowed amount
                    opp.pair.aero_stable,
                    0,
                    b""
                ))
            else:
                swaps.append((
                    int(DEX.UNISWAP_V3),
                    opp.pair.token_b,
                    opp.pair.token_a,
                    0,
                    opp.amount_in,
                    False,
                    opp.pair.uni_fee,
                    b""
                ))
            
            # Build arb params tuple
            lender = self.psm_address if self.psm_address else self.vault_address
            arb_params = (
                lender,
                opp.pair.token_a,
                opp.amount_in,
                swaps
            )
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price
            
            tx = self.arb_bot.functions.executeArbitrage(arb_params).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"📤 Arb tx sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                self.arbs_executed += 1
                self.total_profit_usd += opp.profit_usd
                
                logger.success(f"✅ Arb executed successfully! Profit: ${opp.profit_usd:.2f}")
                send_discord_alert(
                    f"💰 Flash Arb Profit: ${opp.profit_usd:.2f} on {opp.pair.name}",
                    level="SUCCESS"
                )
                return tx_hash.hex()
            else:
                logger.error(f"❌ Arb tx failed: {tx_hash.hex()}")
                return None
                
        except Exception as e:
            logger.error(f"Arb execution failed: {e}")
            return None

    async def run_scanner_loop(self, interval: float = 1.0):
        """Main scanning loop."""
        logger.info("🚀 Starting Flash Arb Scanner...")
        logger.info(f"Scan interval: {interval}s | Max gas price: {self.max_gas_price_gwei} gwei")
        
        while True:
            try:
                # Rate limit
                now = time.time()
                if now - self.last_scan_time < self.min_scan_interval:
                    await asyncio.sleep(self.min_scan_interval)
                    continue
                
                self.last_scan_time = now
                
                # Scan for opportunities
                opportunities = self.scan_pairs()
                
                # Execute profitable ones
                for opp in opportunities:
                    if self.is_profitable_after_gas(opp):
                        self.execute_arbitrage(opp)
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(5)
        
        self.print_stats()

    def print_stats(self):
        """Print scanner statistics."""
        runtime = time.time() - self.start_time
        hours = runtime / 3600
        
        logger.info("=" * 50)
        logger.info("📊 Flash Arb Scanner Statistics")
        logger.info("=" * 50)
        logger.info(f"Runtime: {hours:.2f} hours")
        logger.info(f"Opportunities found: {self.opportunities_found}")
        logger.info(f"Arbs executed: {self.arbs_executed}")
        logger.info(f"Total profit: ${self.total_profit_usd:.2f}")
        if hours > 0:
            logger.info(f"Profit/hour: ${self.total_profit_usd / hours:.2f}")
        logger.info("=" * 50)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kerne Flash Arbitrage Scanner")
    parser.add_argument("--interval", type=float, default=1.0, help="Scan interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute, just scan")
    parser.add_argument("--max-gas", type=float, default=50.0, help="Max gas price in gwei")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.add("flash_arb_{time}.log", rotation="100 MB", level="DEBUG")
    else:
        logger.add("flash_arb_{time}.log", rotation="100 MB", level="INFO")
    
    # Initialize scanner
    scanner = FlashArbScanner()
    scanner.max_gas_price_gwei = args.max_gas
    
    if args.dry_run:
        scanner.arb_bot = None
        logger.info("🔍 DRY RUN MODE - Scanning only, no execution")
    
    # Run scanner
    asyncio.run(scanner.run_scanner_loop(args.interval))


if __name__ == "__main__":
    main()
