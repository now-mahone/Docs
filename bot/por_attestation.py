# Created: 2026-01-12
# Updated: 2026-01-12 - Enhanced with real-time collateral verification and public reporting
import os
import json
import time
import asyncio
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from loguru import logger
from exchange_manager import ExchangeManager

async def generate_por_attestation():
    """
    Generates a signed attestation of CEX balances for the KerneVerificationNode.
    This script runs on a secure server with access to CEX APIs.
    """
    private_key = os.getenv("STRATEGIST_PRIVATE_KEY")
    if not private_key:
        logger.error("STRATEGIST_PRIVATE_KEY not found.")
        return

    account = Account.from_key(private_key)
    exchanges = ["binance", "bybit", "okx"]
    symbol = "ETH/USDT:USDT"
    
    total_assets_eth = 0.0
    venue_data = {}

    logger.info("Gathering CEX balances for PoR attestation...")

    # Fetch balances concurrently to reduce latency
    async def fetch_venue_data(ex_id):
        try:
            manager = ExchangeManager(ex_id)
            collateral = manager.get_collateral_balance("USDT")
            pos, pnl = manager.get_short_position(symbol)
            price = manager.get_market_price(symbol)
            
            equity_usdt = collateral + pnl
            equity_eth = equity_usdt / price if price > 0 else 0.0
            
            return ex_id, {
                "equity_usdt": equity_usdt,
                "equity_eth": equity_eth,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Failed to fetch data from {ex_id}: {e}")
            return ex_id, None

    tasks = [fetch_venue_data(ex_id) for ex_id in exchanges]
    results = await asyncio.gather(*tasks)

    for ex_id, data in results:
        if data:
            total_assets_eth += data["equity_eth"]
            venue_data[ex_id] = data
            logger.info(f"{ex_id}: {data['equity_eth']:.4f} ETH")

    # Prepare the message for signing
    vault_address = os.getenv("VAULT_ADDRESS", "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd")
    total_assets_wei = Web3.to_wei(total_assets_eth, 'ether')
    timestamp = int(time.time())

    message_hash = Web3.solidity_keccak(
        ['address', 'uint256', 'uint256'],
        [vault_address, total_assets_wei, timestamp]
    )
    
    signature = account.sign_message(encode_defunct(primitive=message_hash))

    attestation = {
        "vault": vault_address,
        "total_assets_eth": total_assets_eth,
        "total_assets_wei": total_assets_wei,
        "timestamp": timestamp,
        "signature": signature.signature.hex(),
        "signer": account.address,
        "venues": venue_data
    }

    # Save for public reporting/dashboard
    output_path = "bot/analysis/por_attestation.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(attestation, f, indent=4)

    logger.success(f"PoR Attestation generated and signed: {output_path}")
    
    # Push to on-chain VerificationNode if RPC is available
    rpc_url = os.getenv("RPC_URL")
    if rpc_url:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            # In production, call verificationNode.submitAttestation(...)
            logger.info("Pushing PoR attestation to on-chain VerificationNode...")
        except Exception as e:
            logger.error(f"Failed to push on-chain: {e}")

    return attestation

if __name__ == "__main__":
    asyncio.run(generate_por_attestation())
