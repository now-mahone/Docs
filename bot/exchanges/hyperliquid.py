import os
from typing import Tuple
from loguru import logger
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import eth_account
from exchanges.base import BaseExchange

class HyperliquidExchange(BaseExchange):
    def __init__(self, use_testnet: bool = False):
        self.private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY") or os.getenv("STRATEGIST_PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("Missing Hyperliquid Private Key")

        self.account = eth_account.Account.from_key(self.private_key)
        self.address = self.account.address
        self.base_url = constants.TESTNET_API_URL if use_testnet else constants.MAINNET_API_URL
        self.info = Info(self.base_url, skip_ws=True)
        self.exchange = Exchange(self.account, self.base_url)
        logger.info(f"HyperliquidExchange initialized: {self.address}")

    def get_market_price(self, symbol: str) -> float:
        try:
            all_mids = self.info.all_mids()
            price = all_mids.get(symbol)
            return float(price) if price else 0.0
        except Exception as e:
            logger.error(f"HL Error market price: {e}")
            return 0.0

    def get_position(self, symbol: str) -> Tuple[float, float]:
        try:
            user_state = self.info.user_state(self.address)
            positions = user_state.get("assetPositions", [])
            for pos_wrapper in positions:
                pos = pos_wrapper["position"]
                if pos["coin"] == symbol:
                    szi = float(pos["szi"])
                    upnl = float(pos["unrealizedPnl"])
                    return abs(szi), upnl
            return 0.0, 0.0
        except Exception as e:
            logger.error(f"HL Error position: {e}")
            return 0.0, 0.0

    def get_collateral_balance(self) -> float:
        try:
            user_state = self.info.user_state(self.address)
            return float(user_state.get("withdrawable", 0.0))
        except Exception as e:
            logger.error(f"HL Error balance: {e}")
            return 0.0

    def get_total_equity(self) -> float:
        try:
            user_state = self.info.user_state(self.address)
            margin_summary = user_state.get("marginSummary", {})
            # Total equity = accountValue in HL
            return float(margin_summary.get("accountValue", 0.0))
        except Exception as e:
            logger.error(f"HL Error equity: {e}")
            return 0.0

    def execute_order(self, symbol: str, size: float, side: str) -> bool:
        try:
            is_buy = side.lower() == 'buy'
            price = self.get_market_price(symbol)
            px = price * 1.05 if is_buy else price * 0.95
            
            order_result = self.exchange.market_open(
                name=symbol,
                is_buy=is_buy,
                sz=size,
                px=px,
                slippage=0.05
            )
            return order_result["status"] == "ok"
        except Exception as e:
            logger.error(f"HL Error execute: {e}")
            return False

    def get_funding_rate(self, symbol: str) -> float:
        try:
            meta = self.info.meta_and_asset_ctxs()
            universe = meta[0]["universe"]
            asset_ctxs = meta[1]
            for i, asset in enumerate(universe):
                if asset["name"] == symbol:
                    return float(asset_ctxs[i]["funding"])
            return 0.0
        except Exception as e:
            logger.error(f"HL Error funding: {e}")
            return 0.0

    def get_liquidation_price(self, symbol: str) -> float:
        try:
            user_state = self.info.user_state(self.address)
            positions = user_state.get("assetPositions", [])
            for pos_wrapper in positions:
                pos = pos_wrapper["position"]
                if pos["coin"] == symbol:
                    liq_px = pos.get("liquidationPx")
                    return float(liq_px) if liq_px else 0.0
            return 0.0
        except Exception as e:
            logger.error(f"HL Error liquidation price: {e}")
            return 0.0
