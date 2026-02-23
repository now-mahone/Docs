from loguru import logger
from typing import Dict, List

class SmartRouter:
    """
    Smart Order Router for Kerne V2.
    Calculates optimal order distribution across multiple CEXs 
    to minimize slippage and maximize capital efficiency.
    """
    def __init__(self, exchange_manager):
        self.em = exchange_manager

    def calculate_distribution(self, symbol: str, amount_eth: float, side: str) -> Dict[str, float]:
        """
        Determines how much of the total amount_eth should be routed to each exchange.
        Uses order book depth analysis.
        """
        logger.info(f"🔍 Routing {amount_eth} {symbol} ({side}) across exchanges...")
        books = self.em.get_order_book(symbol)
        distribution = {}
        
        depths = {}
        total_depth = 0
        
        for name, book in books.items():
            side_key = 'asks' if side.lower() == 'buy' else 'bids'
            levels = book.get(side_key, [])
            
            if not levels:
                continue
            
            # Calculate depth within 1% of best price
            best_px = levels[0][0]
            depth = 0
            for px, sz in levels:
                if abs(px - best_px) / best_px <= 0.01:
                    depth += sz
                else:
                    break
            
            depths[name] = depth
            total_depth += depth
            
        if total_depth == 0:
            logger.warning("No depth found on any exchange. Falling back to equal distribution.")
            active_ex = list(self.em.exchanges.keys())
            return {name: amount_eth / len(active_ex) for name in active_ex}
            
        for name, depth in depths.items():
            share = (depth / total_depth) * amount_eth
            distribution[name] = share
            logger.info(f"📍 Route: {name} -> {share:.4f} ETH ({ (depth/total_depth)*100:.1f}%)")
            
        return distribution
