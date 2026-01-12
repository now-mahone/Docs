# Created: 2026-01-12
import os
import json
import time
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from loguru import logger
from exchange_manager import ExchangeManager

def generate_por_attestation():
    """
    Generates a signed attestation of CEX balances for the KerneVerificationNode.
    This script would run on a secure server with access to CEX APIs.
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

    for ex_id in exchanges:
        try:
            manager = ExchangeManager(ex_id)
            # In a real scenario, we'd fetch the total equity (collateral + pnl)
            collateral = manager.get_collateral_balance("USDT")
            pos, pnl = manager.get_short_position(symbol)
            price = manager.get_market_price(symbol)
            
            equity_usdt = collateral + pnl
            equity_eth = equity_usdt / price if price > 0 else 0.0
            
            total_assets_eth += equity_eth
            venue_data[ex_id] = {
                "equity_usdt": equity_usdt,
                "equity_eth": equity_eth,
                "timestamp": time.time()
            }
            logger.info(f"{ex_id}: {equity_eth:.4f} ETH")
        except Exception as e:
            logger.error(f"Failed to fetch data from {ex_id}: {e}")

    # Prepare the message for signing
    # Format: [vault_address, total_assets_wei, timestamp]
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

    output_path = "bot/analysis/por_attestation.json"
    with open(output_path, "w") as f:
        json.dump(attestation, f, indent=4)

    logger.success(f"PoR Attestation generated and signed: {output_path}")
    logger.info(f"Total Verified Assets: {total_assets_eth:.4f} ETH")
    return attestation

if __name__ == "__main__":
    generate_por_attestation()
