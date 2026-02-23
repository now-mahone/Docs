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

    def _get_sz_decimals(self, symbol: str) -> int:
        """Get the size decimals for a symbol from Hyperliquid meta."""
        try:
            meta = self.info.meta_and_asset_ctxs()
            universe = meta[0]["universe"]
            for asset in universe:
                if asset["name"] == symbol:
                    return int(asset.get("szDecimals", 4))
            return 4  # Default to 4 decimals
        except Exception:
            return 4

    def execute_order(self, symbol: str, size: float, side: str) -> bool:
        try:
            is_buy = side.lower() == 'buy'
            price = self.get_market_price(symbol)
            px = price * 1.05 if is_buy else price * 0.95

            # Round size to Hyperliquid's required precision to avoid float_to_wire errors
            sz_decimals = self._get_sz_decimals(symbol)
            rounded_size = round(size, sz_decimals)

            if rounded_size <= 0:
                logger.warning(f"HL: Rounded size is 0 for {symbol} (original: {size}, decimals: {sz_decimals})")
                return False

            logger.info(f"HL: Executing {side} {rounded_size} {symbol} @ ~${px:.2f} (sz_decimals={sz_decimals})")

            order_result = self.exchange.market_open(
                name=symbol,
                is_buy=is_buy,
                sz=rounded_size,
                px=px,
                slippage=0.05
            )

            if order_result["status"] == "ok":
                logger.success(f"HL: Order filled - {side} {rounded_size} {symbol}")
                return True
            else:
                logger.error(f"HL: Order failed - {order_result}")
                return False
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

    def get_order_book(self, symbol: str) -> dict:
        try:
            l2_snapshot = self.info.l2_snapshot(symbol)
            levels = l2_snapshot.get("levels", [[], []])
            return {
                "bids": [[float(l["px"]), float(l["sz"])] for l in levels[0]],
                "asks": [[float(l["px"]), float(l["sz"])] for l in levels[1]]
            }
        except Exception as e:
            logger.error(f"HL Error order book: {e}")
            return {"bids": [], "asks": []}

    def withdraw_to_onchain(self, amount_usd: float, destination_address: str = None) -> bool:
        """
        Withdraws USDC from Hyperliquid to an on-chain address (Arbitrum).
        """
        try:
            dest = destination_address or self.address
            logger.info(f"Withdrawing {amount_usd} USDC from Hyperliquid to {dest}")
            
            # Hyperliquid API uses integer for USDC (6 decimals)
            amount_raw = int(amount_usd * 1e6)
            
            response = self.exchange.withdraw_from_bridge(
                amount=amount_raw,
                destination=dest
            )
            
            if response["status"] == "ok":
                logger.success(f"Withdrawal initiated: {response}")
                return True
            else:
                logger.error(f"Withdrawal failed: {response}")
                return False
        except Exception as e:
            logger.error(f"HL Error withdrawal: {e}")
            return False

    def deposit_from_onchain(self, amount_usd: float) -> bool:
        """
        Note: Deposits usually require an on-chain transaction to the HL Bridge.
        This method provides the instructions/parameters for the bot's ChainManager to execute.
        """
        # Hyperliquid Bridge on Arbitrum: 0x2Df1c51E09a42Ad01097321978c7035100396630
        # This is handled by the SovereignVault calling ChainManager.
        logger.info(f"Deposit of {amount_usd} USDC requested. Must be executed via ChainManager on Arbitrum.")
        return True

    def get_api_status(self) -> dict:
        """
        Verifies the API connection and returns account status.
        """
        try:
            user_state = self.info.user_state(self.address)
            return {
                "status": "connected",
                "address": self.address,
                "margin_summary": user_state.get("marginSummary", {}),
                "is_mainnet": self.base_url == constants.MAINNET_API_URL
            }
        except Exception as e:
            logger.error(f"HL API Status Error: {e}")
            return {"status": "error", "message": str(e)}


