# Created: 2026-01-13
# Updated: 2026-01-14 - Full UniswapX Priority Order integration
import asyncio
import aiohttp
from loguru import logger
from eth_account import Account
from web3 import Web3
import os
import json

# Priority Order Reactor addresses per chain
PRIORITY_ORDER_REACTORS = {
    8453: "0x000000001Ec5656dcdB24D90DFa42742738De729",   # Base
    130: "0x00000006021a6Bce796be7ba509BBBA71e956e37",    # Unichain
}

# Dutch V2 Reactor addresses (for reference)
DUTCH_V2_REACTORS = {
    1: "0x6000da47483062A0D734Ba3dc7576Ce6A0B645C4",      # Mainnet
    42161: "0x1bd1aAdc9E230626C44a139d7E70d842749351eb",  # Arbitrum
}

# Permit2 address (universal across chains)
PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"

# Minimal ABI for PriorityOrderReactor.execute()
PRIORITY_REACTOR_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "bytes", "name": "order", "type": "bytes"},
                    {"internalType": "bytes", "name": "sig", "type": "bytes"}
                ],
                "internalType": "struct SignedOrder",
                "name": "order",
                "type": "tuple"
            },
            {"internalType": "bytes", "name": "fillContract", "type": "address"},
            {"internalType": "bytes", "name": "fillData", "type": "bytes"}
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "bytes", "name": "order", "type": "bytes"},
                    {"internalType": "bytes", "name": "sig", "type": "bytes"}
                ],
                "internalType": "struct SignedOrder[]",
                "name": "orders",
                "type": "tuple[]"
            },
            {"internalType": "bytes", "name": "fillContract", "type": "address"},
            {"internalType": "bytes", "name": "fillData", "type": "bytes"}
        ],
        "name": "executeBatch",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]


class UniswapXProvider:
    """
    Handles fetching, analyzing, and executing UniswapX orders.
    Supports Priority Orders (Base/Unichain) and Dutch V2 (Mainnet/Arbitrum).
    
    As a filler, we:
    1. Monitor the UniswapX orderbook for open orders
    2. Calculate if we can profitably fill an order
    3. Execute fills on-chain via the appropriate reactor
    
    For Priority Orders (Base), fillers compete via priority gas auctions.
    The filler with the highest priorityFee wins the order.
    """
    
    def __init__(self, private_key=None, rpc_url=None, chain_id=8453):
        self.private_key = private_key or os.getenv("STRATEGIST_PRIVATE_KEY")
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "").split(',')[0]
        self.chain_id = chain_id
        
        # Initialize Web3
        if self.rpc_url:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        else:
            self.w3 = None
            logger.warning("UniswapX Provider: No RPC URL configured")
        
        # Initialize account
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            logger.info(f"UniswapX Provider initialized for {self.account.address} on chain {chain_id}")
        else:
            self.account = None
            logger.warning("UniswapX Provider: No private key configured")
        
        # Get reactor address for this chain
        self.reactor_address = self._get_reactor_address()
        if self.reactor_address and self.w3:
            self.reactor = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.reactor_address),
                abi=PRIORITY_REACTOR_ABI
            )
        else:
            self.reactor = None
    
    def _get_reactor_address(self) -> str:
        """Get the appropriate reactor address for the current chain."""
        if self.chain_id in PRIORITY_ORDER_REACTORS:
            return PRIORITY_ORDER_REACTORS[self.chain_id]
        elif self.chain_id in DUTCH_V2_REACTORS:
            return DUTCH_V2_REACTORS[self.chain_id]
        else:
            logger.warning(f"UniswapX: No reactor configured for chain {self.chain_id}")
            return None
    
    def calculate_priority_fee(self, profit_usd: float, desired_margin_pct: float = 0.10) -> int:
        """
        Calculate the priority fee to bid for a Priority Order.
        
        For Priority Orders, fillers bid by setting priorityFee on their transaction.
        Higher priorityFee = better price for the user = more likely to win.
        
        The formula converts basis points improvement to milli-basis-points (mps):
        priorityFee (wei) = improvement_bps * 1000
        
        Args:
            profit_usd: Expected profit from filling this order
            desired_margin_pct: Percentage of profit to keep (default 10%)
        
        Returns:
            Priority fee in wei to set on the fill transaction
        """
        # Calculate how much we're willing to give to the user (in bps)
        # If profit is $100 and we want 10% margin, we give $90 to user
        improvement_usd = profit_usd * (1 - desired_margin_pct)
        
        # Convert to basis points (assuming $1000 order size as baseline)
        # This is a simplification - in production, use actual order size
        improvement_bps = (improvement_usd / 1000) * 10000
        
        # Convert bps to milli-bps (mps) for priority fee
        # 1 wei of priorityFee = 1 mps of improvement
        priority_fee_wei = int(improvement_bps * 1000)
        
        # Ensure minimum priority fee
        min_priority_fee = 1000  # 1 bps minimum
        return max(priority_fee_wei, min_priority_fee)
    
    async def execute_priority_order(
        self,
        encoded_order: str,
        signature: str,
        fill_contract: str,
        fill_data: bytes,
        priority_fee_wei: int
    ) -> dict:
        """
        Execute a Priority Order by submitting a fill transaction.
        
        For Priority Orders on Base, the filler with the highest priorityFee wins.
        
        Args:
            encoded_order: The encoded order bytes from the API
            signature: The swapper's signature
            fill_contract: Contract to use for filling (e.g., swap aggregator)
            fill_data: Calldata for the fill contract
            priority_fee_wei: Priority fee to bid (in wei)
        
        Returns:
            Transaction result dict
        """
        if not self.reactor or not self.account or not self.w3:
            logger.error("UniswapX: Provider not fully initialized")
            return {"success": False, "error": "Provider not initialized"}
        
        try:
            # Build the signed order tuple
            signed_order = {
                "order": bytes.fromhex(encoded_order[2:]) if encoded_order.startswith("0x") else bytes.fromhex(encoded_order),
                "sig": bytes.fromhex(signature[2:]) if signature.startswith("0x") else bytes.fromhex(signature)
            }
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
            
            tx = self.reactor.functions.execute(
                signed_order,
                Web3.to_checksum_address(fill_contract),
                fill_data
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 500000,  # Estimate, should be calculated
                'maxFeePerGas': base_fee + priority_fee_wei,
                'maxPriorityFeePerGas': priority_fee_wei,
                'chainId': self.chain_id
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.success(f"UniswapX: Fill transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt (with timeout)
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                if receipt['status'] == 1:
                    logger.success(f"UniswapX: Order filled successfully! Gas used: {receipt['gasUsed']}")
                    return {
                        "success": True,
                        "tx_hash": tx_hash.hex(),
                        "gas_used": receipt['gasUsed'],
                        "block_number": receipt['blockNumber']
                    }
                else:
                    logger.error(f"UniswapX: Fill transaction reverted")
                    return {"success": False, "error": "Transaction reverted", "tx_hash": tx_hash.hex()}
            except Exception as e:
                # Transaction might still succeed, return the hash
                logger.warning(f"UniswapX: Timeout waiting for receipt: {e}")
                return {"success": None, "tx_hash": tx_hash.hex(), "status": "pending"}
                
        except Exception as e:
            logger.error(f"UniswapX: Error executing order: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_order_fillable(self, order_hash: str) -> bool:
        """
        Check if an order is still fillable (not expired, not filled, etc.)
        
        In production, use the UniswapXOrderQuoter contract for accurate validation.
        """
        # For now, return True - actual validation would query the reactor
        # or use the UniswapX SDK's OrderQuoter
        return True
    
    def estimate_fill_profit(
        self,
        input_token: str,
        input_amount: int,
        output_token: str,
        output_amount: int,
        current_market_price: float
    ) -> float:
        """
        Estimate profit from filling an order.
        
        Args:
            input_token: Token the swapper is selling
            input_amount: Amount of input token (in wei)
            output_token: Token the swapper wants to buy
            output_amount: Minimum amount of output token (in wei)
            current_market_price: Current market rate (output per input)
        
        Returns:
            Estimated profit in USD
        """
        # Convert amounts from wei
        input_amount_normalized = input_amount / 1e18
        output_amount_normalized = output_amount / 1e18
        
        # Calculate what we can get on the market
        market_output = input_amount_normalized * current_market_price
        
        # Profit is the difference between market output and required output
        # (minus gas costs, which we estimate separately)
        profit = market_output - output_amount_normalized
        
        # Convert to USD (simplified - assumes ETH-denominated)
        eth_price = 3500  # Should fetch real price
        profit_usd = profit * eth_price
        
        return max(0, profit_usd)
    
    async def get_fill_data_for_aggregator(
        self,
        input_token: str,
        output_token: str,
        amount: int,
        aggregator: str = "1inch"
    ) -> tuple:
        """
        Get fill contract and calldata from a DEX aggregator.
        
        This prepares the data needed to actually execute the swap
        that fulfills the user's order.
        """
        # This would integrate with 1inch, Uniswap Router, etc.
        # For now, return placeholder
        fill_contract = "0x1111111254EEB25477B68fb85Ed929f73A960582"  # 1inch router
        fill_data = b""  # Would be actual swap calldata
        
        return fill_contract, fill_data


if __name__ == "__main__":
    # Test initialization
    provider = UniswapXProvider()
    
    # Test priority fee calculation
    fee = provider.calculate_priority_fee(profit_usd=100, desired_margin_pct=0.10)
    print(f"Priority fee for $100 profit: {fee} wei ({fee / 1000} bps)")
