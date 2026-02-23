# Created: 2026-01-13
import asyncio
import json
import os
from loguru import logger
from bot.solver.intent_listener import IntentListener

class SolverSimulator:
    """
    Simulates the solver's performance against historical or mock data.
    """
    def __init__(self):
        self.listener = IntentListener()
        self.mock_orders_path = "bot/solver/mock_orders.json"
        self._create_mock_data()

    def _create_mock_data(self):
        mock_orders = [
            {
                "uid": "mock_1",
                "buyToken": "0xc1cba3fc4d133901b3e238628f5514533683e0bf", # wstETH
                "sellToken": "0x4200000000000000000000000000000000000006", # WETH
                "buyAmount": "1000000000000000000", # 1 ETH
                "sellAmount": "1045000000000000000"
            },
            {
                "uid": "mock_2",
                "buyToken": "0x2ae3f1ec7f1f5012cfeab2295b6240137331713f", # cbETH
                "sellToken": "0x4200000000000000000000000000000000000006",
                "buyAmount": "5000000000000000000", # 5 ETH
                "sellAmount": "5225000000000000000"
            }
        ]
        with open(self.mock_orders_path, "w") as f:
            json.dump(mock_orders, f, indent=4)

    async def run_simulation(self):
        logger.info("Starting Solver Simulation...")
        with open(self.mock_orders_path, "r") as f:
            orders = json.load(f)
            
        for order in orders:
            logger.info(f"Simulating order: {order['uid']}")
            await self.listener.process_order(order, "Simulation")
            
        logger.success("Simulation complete. Check bot/solver/profit_log.csv for results.")

if __name__ == "__main__":
    sim = SolverSimulator()
    asyncio.run(sim.run_simulation())
