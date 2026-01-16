# Created: 2026-01-16
import httpx
import asyncio
from typing import Optional, List
from loguru import logger
from web3 import Web3

class MEVProtectedSubmitter:
    """Submit transactions via private channels to avoid frontrunning on Base."""
    
    PRIVATE_ENDPOINTS = [
        "https://rpc.flashbots.net",
        "https://base.llamarpc.com",
    ]
    
    def __init__(self, w3: Web3, private_key: str):
        self.w3 = w3
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
    
    async def submit_private(self, signed_tx_raw: bytes, timeout: float = 30.0) -> Optional[str]:
        """Submit to private mempool endpoints."""
        tx_hex = signed_tx_raw.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
            
        tasks = []
        for endpoint in self.PRIVATE_ENDPOINTS:
            tasks.append(self._send_to_endpoint(endpoint, tx_hex, timeout))
            
        # Also send to public mempool as fallback if needed, or just rely on private
        # For Flash-Arb, private is preferred to avoid sandwiches
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, str) and res.startswith("0x"):
                return res
        
        # Fallback to public if all private failed
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx_raw)
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Public submission fallback failed: {e}")
            return None

    async def _send_to_endpoint(self, endpoint: str, tx_hex: str, timeout: float) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(endpoint, json={
                    "jsonrpc": "2.0",
                    "method": "eth_sendRawTransaction",
                    "params": [tx_hex],
                    "id": 1
                })
                result = resp.json()
                if "result" in result:
                    logger.info(f"Successfully submitted to private endpoint: {endpoint}")
                    return result["result"]
                elif "error" in result:
                    logger.debug(f"Private endpoint {endpoint} returned error: {result['error']}")
        except Exception as e:
            logger.debug(f"Private endpoint {endpoint} failed: {e}")
        return None
    
    def build_with_priority(self, tx_dict: dict, priority_gwei: float = 0.1) -> dict:
        """Add priority fee for faster inclusion."""
        latest_block = self.w3.eth.get_block('latest')
        base_fee = latest_block.get('baseFeePerGas', self.w3.to_wei(0.01, 'gwei'))
        
        priority_fee = self.w3.to_wei(priority_gwei, 'gwei')
        tx_dict['maxPriorityFeePerGas'] = priority_fee
        tx_dict['maxFeePerGas'] = base_fee * 2 + priority_fee # 2x base fee buffer
        tx_dict['type'] = 2 # EIP-1559
        return tx_dict
