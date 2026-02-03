# Created: 2026-01-15
import os
import sys
import json
import time
import argparse
import requests
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger

# Add the current directory to sys.path to allow importing from 'bot'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bot.chain_manager import ChainManager
    from bot.alerts import send_discord_alert
except ImportError:
    from chain_manager import ChainManager
    from alerts import send_discord_alert

class OmniOrchestrator:
    """
    The "God Mode" Omnichain Command Center.
    Uses Li.Fi API to bridge and swap anything to anywhere.
    """
    LIFI_API_URL = "https://li.quest/v1"
    
    CHAIN_MAP = {
        "ETH": 1,
        "MAINNET": 1,
        "OPTIMISM": 10,
        "OPT": 10,
        "BSC": 56,
        "POLYGON": 137,
        "BASE": 8453,
        "ARBITRUM": 42161,
        "ARB": 42161,
        "AVALANCHE": 43114,
        "AVAX": 43114,
        "LINEA": 59144,
        "BLAST": 81457
    }

    TOKEN_MAP = {
        "ETH": "0x0000000000000000000000000000000000000000",
        "WETH": "0x4200000000000000000000000000000000000006", # Default to Base WETH, will resolve dynamically
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", # Base USDC
        "KERNE": os.getenv("KERNE_TOKEN_ADDRESS", "0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340")
    }

    def __init__(self):
        load_dotenv()
        self.chain_manager = ChainManager()
        self.private_key = os.getenv("PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("PRIVATE_KEY not found in environment")
        
        self.wallet_address = self.chain_manager.account.address
        logger.info(f"OmniOrchestrator initialized for wallet: {self.wallet_address}")

    def resolve_token(self, symbol: str, chain_id: int) -> str:
        """Resolves a token symbol to an address on a specific chain using Li.Fi."""
        symbol = symbol.upper()
        if symbol == "ETH":
            return "0x0000000000000000000000000000000000000000"
        
        # Try local map first for Kerne or specific overrides
        if symbol == "KERNE" and chain_id == 8453:
            return self.TOKEN_MAP["KERNE"]

        logger.info(f"Resolving {symbol} on chain {chain_id} via Li.Fi...")
        try:
            params = {"chain": chain_id, "symbol": symbol}
            response = requests.get(f"{self.LIFI_API_URL}/token", params=params)
            response.raise_for_status()
            data = response.json()
            return data["address"]
        except Exception as e:
            logger.error(f"Failed to resolve token {symbol} on chain {chain_id}: {e}")
            # Fallback to some common addresses if Li.Fi fails
            if symbol == "USDC":
                if chain_id == 8453: return "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
                if chain_id == 42161: return "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
                if chain_id == 10: return "0x0b2C639c533413bc44a77d5ec4f02fC03b0c8C33"
            raise

    def get_quote(self, from_chain: int, to_chain: int, from_token: str, to_token: str, amount: str):
        """Fetches a bridge/swap quote from Li.Fi."""
        params = {
            "fromChain": from_chain,
            "toChain": to_chain,
            "fromToken": from_token,
            "toToken": to_token,
            "fromAmount": amount,
            "fromAddress": self.wallet_address,
            "slippage": 0.005 # 0.5%
        }
        
        logger.info(f"Fetching Li.Fi quote: {from_chain}:{from_token} -> {to_chain}:{to_token} Amount: {amount}")
        response = requests.get(f"{self.LIFI_API_URL}/quote", params=params)
        if response.status_code != 200:
            logger.error(f"Quote failed: {response.text}")
            response.raise_for_status()
        
        return response.json()

    def parse_command(self, cmd: str):
        """
        Parses command like '0.1 ETH BASE -> ARBITRUM'
        Returns (amount, from_token, from_chain, to_token, to_chain)
        """
        try:
            # Format: [AMOUNT] [TOKEN] [FROM_CHAIN] -> [TO_CHAIN]
            # OR: [AMOUNT] [FROM_TOKEN] [FROM_CHAIN] -> [TO_TOKEN] [TO_CHAIN]
            parts = cmd.upper().replace("->", " -> ").split()
            
            amount = parts[0]
            from_token = parts[1]
            from_chain_name = parts[2]
            
            # Find arrow
            arrow_idx = -1
            for i, p in enumerate(parts):
                if p == "->":
                    arrow_idx = i
                    break
            
            if arrow_idx == -1:
                raise ValueError("Command must contain '->'")
            
            # Destination logic
            if len(parts) > arrow_idx + 2:
                # Specified both token and chain
                to_token = parts[arrow_idx + 1]
                to_chain_name = parts[arrow_idx + 2]
            else:
                # Only chain specified, assume same token
                to_token = from_token
                to_chain_name = parts[arrow_idx + 1]

            from_chain = self.CHAIN_MAP.get(from_chain_name)
            to_chain = self.CHAIN_MAP.get(to_chain_name)
            
            if not from_chain or not to_chain:
                raise ValueError(f"Unknown chain: {from_chain_name} or {to_chain_name}")

            return amount, from_token, from_chain, to_token, to_chain
        except Exception as e:
            logger.error(f"Failed to parse command '{cmd}': {e}")
            raise

    def execute_transaction(self, tx_data: dict, chain_id: int):
        """Signs and sends a transaction on a specific chain."""
        # Get RPC for the specific chain
        rpc = self.get_rpc_for_chain(chain_id)
        w3 = Web3(Web3.HTTPProvider(rpc))
        
        nonce = w3.eth.get_transaction_count(self.wallet_address)
        
        def to_int(val):
            if isinstance(val, str) and val.startswith('0x'):
                return int(val, 16)
            return int(val)

        tx = {
            'from': self.wallet_address,
            'to': tx_data['to'],
            'data': tx_data['data'],
            'value': to_int(tx_data.get('value', 0)),
            'nonce': nonce,
            'gas': int(to_int(tx_data.get('gasLimit', 500000)) * 1.2), # 20% buffer
            'chainId': chain_id
        }
        
        # Use gas price or EIP-1559 if available
        try:
            fee_history = w3.eth.fee_history(1, 'latest')
            base_fee = fee_history['baseFeePerGas'][-1]
            priority_fee = w3.to_wei(0.001, 'gwei') # Lower priority fee for L2s
            tx['maxPriorityFeePerGas'] = priority_fee
            tx['maxFeePerGas'] = int(base_fee * 1.5) + priority_fee
        except:
            tx['gasPrice'] = w3.eth.gas_price

        logger.info(f"Signing transaction on chain {chain_id}...")
        signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.success(f"Transaction sent! Hash: {tx_hash.hex()}")
        return tx_hash.hex()

    def get_rpc_for_chain(self, chain_id: int) -> str:
        """Returns an RPC URL for the given chain ID."""
        if chain_id == 8453: return os.getenv("RPC_URL").split(',')[0]
        if chain_id == 42161: return os.getenv("ARB_RPC_URL")
        if chain_id == 10: return os.getenv("OPT_RPC_URL")
        
        # Fallback to public RPCs if not in .env
        public_rpcs = {
            1: "https://eth.llamarpc.com",
            10: "https://optimism.llamarpc.com",
            56: "https://binance.llamarpc.com",
            137: "https://polygon.llamarpc.com",
            8453: "https://base.llamarpc.com",
            42161: "https://arbitrum.llamarpc.com"
        }
        return public_rpcs.get(chain_id)

    def run_command(self, cmd: str, dry_run: bool = False):
        """Full flow: parse -> resolve -> quote -> execute."""
        logger.info(f"--- Omnichain Execution Started: '{cmd}' ---")
        
        amount_str, from_token_sym, from_chain, to_token_sym, to_chain = self.parse_command(cmd)
        
        from_token_addr = self.resolve_token(from_token_sym, from_chain)
        to_token_addr = self.resolve_token(to_token_sym, to_chain)
        
        # Get decimals for amount conversion
        w3_from = Web3(Web3.HTTPProvider(self.get_rpc_for_chain(from_chain)))
        if from_token_addr == "0x0000000000000000000000000000000000000000":
            decimals = 18
        else:
            erc20_abi = [{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]
            token_contract = w3_from.eth.contract(address=from_token_addr, abi=erc20_abi)
            decimals = token_contract.functions.decimals().call()
        
        amount_raw = str(int(float(amount_str) * (10 ** decimals)))
        
        quote = self.get_quote(from_chain, to_chain, from_token_addr, to_token_addr, amount_raw)
        
        try:
            tool = quote.get('tool', 'unknown')
            action = quote.get('action', {})
            estimate = quote.get('estimate', {})
            
            from_chain_res = action.get('fromChain', from_chain)
            to_chain_res = action.get('toChain', to_chain)
            
            logger.info(f"Route Found: {tool} via {from_chain_res} -> {to_chain_res}")
            
            to_amount = estimate.get('toAmount', '0')
            to_token_data = action.get('toToken', {})
            to_decimals = to_token_data.get('decimals', 18)
            logger.info(f"Estimated Output: {float(to_amount) / (10**to_decimals):.6f} {to_token_sym}")
            
            gas_costs = estimate.get('gasCosts', [])
            gas_usd = gas_costs[0].get('amountUsd', '0') if gas_costs else '0'
            logger.info(f"Estimated Gas: ${gas_usd}")
        except Exception as e:
            logger.error(f"Error parsing quote data: {e}")
            logger.debug(f"Full Quote Structure: {json.dumps(quote, indent=2)}")
            raise
        
        if dry_run:
            logger.info("DRY RUN: Transaction would be executed now.")
            return
        
        # 1. Check Approval
        if from_token_addr != "0x0000000000000000000000000000000000000000":
            approval_address = quote['transactionRequest']['to']
            # Simple approval check could be added here, but Li.Fi quote usually includes it in steps if needed.
            # However, /quote often assumes you have approved or provides the tx for the swap itself.
            # We'll check allowance manually.
            erc20_abi = [
                {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
            ]
            token_contract = w3_from.eth.contract(address=from_token_addr, abi=erc20_abi)
            allowance = token_contract.functions.allowance(self.wallet_address, approval_address).call()
            
            if allowance < int(amount_raw):
                logger.info(f"Insufficient allowance. Approving {from_token_sym}...")
                nonce = w3_from.eth.get_transaction_count(self.wallet_address)
                approve_tx = token_contract.functions.approve(approval_address, 2**256 - 1).build_transaction({
                    'from': self.wallet_address,
                    'nonce': nonce,
                    'gasPrice': w3_from.eth.gas_price
                })
                signed_approve = w3_from.eth.account.sign_transaction(approve_tx, self.private_key)
                app_hash = w3_from.eth.send_raw_transaction(signed_approve.raw_transaction)
                logger.info(f"Approval sent: {app_hash.hex()}. Waiting for confirmation...")
                w3_from.eth.wait_for_transaction_receipt(app_hash)
                logger.success("Approval confirmed.")

        # 2. Execute Swap/Bridge
        tx_hash = self.execute_transaction(quote['transactionRequest'], from_chain)
        
        send_discord_alert(f"🚀 **Omnichain Transfer Initiated**\nCommand: `{cmd}`\nHash: {tx_hash}\nTool: {quote['tool']}", level="INFO")
        
        return tx_hash

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Omnichain Orchestrator CLI")
    parser.add_argument("--cmd", type=str, required=True, help="Command like '0.1 ETH BASE -> ARBITRUM'")
    parser.add_argument("--dry-run", action="store_true", help="Estimate only, do not execute")
    
    args = parser.parse_args()
    
    orchestrator = OmniOrchestrator()
    try:
        orchestrator.run_command(args.cmd, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)
