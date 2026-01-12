# Created: 2026-01-12
# Updated: 2026-01-12 - Institutional Deep Hardening: Multi-venue equity verification and cryptographic attestation
import os
import json
import time
import asyncio
import hmac
import hashlib
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from loguru import logger
from exchange_manager import ExchangeManager

class PoRManager:
    """
    Institutional Proof of Reserve Manager.
    Handles multi-venue equity verification and cryptographic signing.
    """
    def __init__(self):
        self.private_key = os.getenv("STRATEGIST_PRIVATE_KEY")
        self.vault_address = os.getenv("VAULT_ADDRESS", "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd")
        self.exchanges = ["binance", "bybit", "okx"]
        self.symbol = "ETH/USDT:USDT"

    async def fetch_venue_equity(self, ex_id: str) -> Dict:
        """
        Fetches total equity (collateral + unrealized PnL) from a venue.
        """
        try:
            manager = ExchangeManager(ex_id)
            # Concurrent fetching of balance and positions
            collateral = manager.get_collateral_balance("USDT")
            pos, pnl = manager.get_short_position(self.symbol)
            price = manager.get_market_price(self.symbol)
            
            equity_usdt = collateral + pnl
            equity_eth = equity_usdt / price if price > 0 else 0.0
            
            return {
                "venue": ex_id,
                "equity_usdt": equity_usdt,
                "equity_eth": equity_eth,
                "timestamp": time.time(),
                "status": "VERIFIED"
            }
        except Exception as e:
            logger.error(f"PoR fetch failed for {ex_id}: {e}")
            return {"venue": ex_id, "status": "FAILED", "error": str(e)}

    async def generate_attestation(self):
        """
        Generates a signed multi-venue attestation.
        """
        if not self.private_key:
            logger.error("STRATEGIST_PRIVATE_KEY not found.")
            return

        logger.info("Initiating multi-venue PoR attestation...")
        tasks = [self.fetch_venue_equity(ex_id) for ex_id in self.exchanges]
        results = await asyncio.gather(*tasks)
        
        total_eth = sum(r.get("equity_eth", 0) for r in results if r["status"] == "VERIFIED")
        total_wei = Web3.to_wei(total_eth, 'ether')
        timestamp = int(time.time())

        # Cryptographic Message: [vault, total_assets, timestamp, venue_hash]
        venue_json = json.dumps(results, sort_keys=True)
        venue_hash = hashlib.sha256(venue_json.encode()).digest()
        
        message_hash = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256', 'bytes32'],
            [self.vault_address, total_wei, timestamp, venue_hash]
        )
        
        account = Account.from_key(self.private_key)
        signature = account.sign_message(encode_defunct(primitive=message_hash))

        attestation = {
            "vault": self.vault_address,
            "total_assets_eth": total_eth,
            "total_assets_wei": total_wei,
            "timestamp": timestamp,
            "venue_hash": venue_hash.hex(),
            "signature": signature.signature.hex(),
            "signer": account.address,
            "venues": results
        }

        output_path = "bot/analysis/por_attestation_v2.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(attestation, f, indent=4)

        logger.success(f"Institutional PoR Attestation generated: {total_eth:.4f} ETH")
        return attestation

if __name__ == "__main__":
    manager = PoRManager()
    asyncio.run(manager.generate_attestation())
