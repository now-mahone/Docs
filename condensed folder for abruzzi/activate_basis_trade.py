# Created: 2026-02-07
"""
Kerne Protocol — Basis Trade Activation Script
Opens the first delta-neutral position:
  - LONG: 0.057025 WETH in KerneVault (already deposited)
  - SHORT: ~0.057 ETH-PERP on Hyperliquid (this script opens it)

This creates a delta-neutral position that earns funding rate income.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add bot directory to path
sys.path.insert(0, os.path.join(os.getcwd(), 'bot'))

from loguru import logger
from exchanges.hyperliquid import HyperliquidExchange

# ============================================================
# CONFIGURATION
# ============================================================
VAULT_WETH = 0.057025  # WETH held in KerneVault on Base
# Hyperliquid minimum order size for ETH is 0.001
# We'll short slightly less than vault WETH to account for any rounding
SHORT_SIZE = 0.057  # ETH to short (rounded down from 0.057025)

def main():
    load_dotenv('bot/.env')
    
    logger.info("=" * 60)
    logger.info("  KERNE BASIS TRADE ACTIVATION")
    logger.info("=" * 60)
    
    # 1. Connect to Hyperliquid
    logger.info("Connecting to Hyperliquid...")
    hl = HyperliquidExchange(use_testnet=False)
    
    status = hl.get_api_status()
    if status["status"] != "connected":
        logger.error(f"Failed to connect: {status}")
        return False
    
    logger.success(f"Connected: {status['address']}")
    logger.info(f"Mainnet: {status['is_mainnet']}")
    
    # 2. Check current state
    equity = hl.get_total_equity()
    withdrawable = hl.get_collateral_balance()
    eth_price = hl.get_market_price("ETH")
    funding_rate = hl.get_funding_rate("ETH")
    current_pos, current_upnl = hl.get_position("ETH")
    
    logger.info(f"Account Equity: ${equity:.2f}")
    logger.info(f"Withdrawable:   ${withdrawable:.2f}")
    logger.info(f"ETH Price:      ${eth_price:.2f}")
    logger.info(f"Funding Rate:   {funding_rate*100:.4f}% (per 8h)")
    logger.info(f"Annual Funding: {funding_rate*3*365*100:.2f}%")
    logger.info(f"Current Pos:    {current_pos} ETH short, uPnL: ${current_upnl:.2f}")
    
    # 3. Pre-flight checks
    logger.info("-" * 60)
    logger.info("PRE-FLIGHT CHECKS")
    logger.info("-" * 60)
    
    # Check if position already exists
    if current_pos > 0.001:
        logger.warning(f"Position already exists: {current_pos} ETH short")
        logger.warning("Skipping — already hedged. Use bot/engine.py for rebalancing.")
        return False
    
    # Check minimum equity
    notional_value = SHORT_SIZE * eth_price
    required_leverage = notional_value / equity if equity > 0 else 999
    
    logger.info(f"Vault WETH:      {VAULT_WETH} WETH (${VAULT_WETH * eth_price:.2f})")
    logger.info(f"Short Size:      {SHORT_SIZE} ETH (${notional_value:.2f})")
    logger.info(f"Required Margin: ${equity:.2f} at {required_leverage:.1f}x leverage")
    
    if equity < 10:
        logger.error(f"Insufficient equity: ${equity:.2f} (need at least $10)")
        return False
    
    if required_leverage > 10:
        logger.error(f"Leverage too high: {required_leverage:.1f}x (max 10x for safety)")
        return False
    
    if eth_price < 100 or eth_price > 100000:
        logger.error(f"ETH price looks wrong: ${eth_price}")
        return False
    
    # Calculate funding income projection
    annual_funding_pct = funding_rate * 3 * 365  # 3 funding periods per day * 365 days
    daily_funding_usd = notional_value * (funding_rate * 3)
    monthly_funding_usd = daily_funding_usd * 30
    annual_funding_usd = notional_value * annual_funding_pct
    
    logger.info("-" * 60)
    logger.info("PROJECTED INCOME (if funding rate persists)")
    logger.info("-" * 60)
    logger.info(f"Daily:   ${daily_funding_usd:.4f}")
    logger.info(f"Monthly: ${monthly_funding_usd:.4f}")
    logger.info(f"Annual:  ${annual_funding_usd:.2f} ({annual_funding_pct*100:.2f}% APY)")
    
    # Liquidation estimate (approximate for short position)
    # For a short, liquidation happens when price goes UP
    # Rough estimate: liq_price ≈ entry * (1 + 1/leverage * 0.9)
    # where 0.9 accounts for maintenance margin
    if required_leverage > 0:
        liq_price_estimate = eth_price * (1 + (1 / required_leverage) * 0.85)
        distance_pct = ((liq_price_estimate - eth_price) / eth_price) * 100
        logger.info(f"Est. Liquidation: ~${liq_price_estimate:.0f} ({distance_pct:.1f}% above current)")
    
    logger.info("=" * 60)
    logger.info("  EXECUTING SHORT: {} ETH @ ~${:.2f}".format(SHORT_SIZE, eth_price))
    logger.info("=" * 60)
    
    # 4. Execute the short
    # Use market_open with 5% slippage tolerance for immediate fill
    price = eth_price
    px = price * 0.95  # Limit price 5% below market for a short (worst acceptable fill)
    
    try:
        order_result = hl.exchange.market_open(
            name="ETH",
            is_buy=False,  # SHORT
            sz=SHORT_SIZE,
            px=px,
            slippage=0.05  # 5% slippage tolerance
        )
        
        logger.info(f"Order Result: {order_result}")
        
        if order_result.get("status") == "ok":
            logger.success("✅ SHORT ORDER EXECUTED SUCCESSFULLY")
            
            # Extract fill details
            response = order_result.get("response", {})
            if response.get("type") == "order":
                data = response.get("data", {})
                statuses = data.get("statuses", [])
                for s in statuses:
                    if "filled" in s:
                        fill = s["filled"]
                        logger.success(f"  Filled: {fill.get('totalSz', '?')} ETH @ ${fill.get('avgPx', '?')}")
                    elif "resting" in s:
                        logger.info(f"  Resting (limit): {s['resting']}")
                    elif "error" in s:
                        logger.error(f"  Order Error: {s['error']}")
                        return False
        else:
            logger.error(f"Order failed: {order_result}")
            return False
            
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return False
    
    # 5. Verify the position
    logger.info("Waiting 3 seconds for settlement...")
    time.sleep(3)
    
    new_pos, new_upnl = hl.get_position("ETH")
    new_equity = hl.get_total_equity()
    liq_price = hl.get_liquidation_price("ETH")
    
    logger.info("=" * 60)
    logger.info("  POST-TRADE VERIFICATION")
    logger.info("=" * 60)
    logger.info(f"Position Size:   {new_pos} ETH short")
    logger.info(f"Unrealized PnL:  ${new_upnl:.4f}")
    logger.info(f"Account Equity:  ${new_equity:.2f}")
    logger.info(f"Liquidation Px:  ${liq_price:.2f}" if liq_price > 0 else "Liquidation Px:  N/A")
    
    if new_pos > 0.001:
        logger.success("=" * 60)
        logger.success("  🎯 DELTA-NEUTRAL POSITION ESTABLISHED")
        logger.success(f"  LONG:  {VAULT_WETH} WETH in KerneVault")
        logger.success(f"  SHORT: {new_pos} ETH-PERP on Hyperliquid")
        logger.success(f"  Funding income accruing every 8 hours")
        logger.success("=" * 60)
        return True
    else:
        logger.error("Position not detected after execution!")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Basis trade activated. Funding rate income now accruing.")
    else:
        print("\n❌ Basis trade activation failed. Review logs above.")