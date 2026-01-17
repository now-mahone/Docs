# bot/solver/lst_capture_engine.py
import os
import asyncio
from loguru import logger
from web3 import Web3
from dotenv import load_dotenv

# Created: 2026-01-16

class LSTCaptureEngine:
    """
    Kerne LST-Solver & Shadow-Yield Engine.
    Tracks LST rebase rates and captures yield gaps via the KerneLSTSolver contract.
    """
    def __init__(self, chain_manager):
        self.cm = chain_manager
        self.w3 = chain_manager.w3
        
        # Contract Addresses
        self.hook_address = os.getenv("LST_HOOK_ADDRESS")
        self.solver_address = os.getenv("LST_SOLVER_ADDRESS")
        
        # ABIs (Minimal)
        self.hook_abi = [
            {"inputs":[{"name":"vault","type":"address"},{"name":"amount","type":"uint256"}],"name":"updateShadowYield","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"name":"vault","type":"address"}],"name":"getVerifiedAssets","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
        ]
        self.solver_abi = [
            {"inputs":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},{"name":"amount","type":"uint256"},{"name":"data","type":"bytes"}],"name":"executeLSTSwap","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
        ]
        
        if self.hook_address:
            self.hook = self.w3.eth.contract(address=self.hook_address, abi=self.hook_abi)
        if self.solver_address:
            self.solver = self.w3.eth.contract(address=self.solver_address, abi=self.solver_abi)
            
        # LST Registry (Base Mainnet)
        self.lst_tokens = {
            "wstETH": "0xc1CBa3fC4D133901B3E238628F5514533683e0BF",
            "cbETH": "0x2Ae3F1Ec7F1F5012CFEab2295B6240137331713F"
        }
        
        self.shadow_yield_cache = {}

    async def fetch_lst_rates(self):
        """
        Fetches current rebase/APR rates for LSTs.
        In production, this would call Lido/Coinbase APIs or on-chain rate providers.
        """
        # Mocking rates: wstETH ~3.8%, cbETH ~3.2%
        return {
            "wstETH": 0.038,
            "cbETH": 0.032
        }

    async def update_shadow_yield(self):
        """
        Calculates and reports accrued shadow yield to the KerneLSTHook.
        Shadow yield = Sum(Vault_LST_Balance * Daily_Rate * Days_Since_Last_Report)
        """
        if not self.hook_address:
            return
            
        rates = await self.fetch_lst_rates()
        total_shadow_yield = 0
        
        for name, addr in self.lst_tokens.items():
            # Get vault balance of this LST
            balance = self._get_erc20_balance(addr, self.cm.vault_address)
            # Calculate 1 day of yield
            daily_yield = balance * (rates[name] / 365)
            total_shadow_yield += daily_yield
            
        logger.info(f"LST Engine: Calculated total shadow yield: {total_shadow_yield / 1e18:.6f} ETH")
        
        # Update on-chain
        try:
            nonce = self.w3.eth.get_transaction_count(self.cm.account.address)
            tx = self.hook.functions.updateShadowYield(
                self.cm.vault_address, 
                int(total_shadow_yield)
            ).build_transaction({
                'from': self.cm.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.cm.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.success(f"LST Engine: Shadow yield updated: {tx_hash.hex()}")
        except Exception as e:
            logger.error(f"LST Engine: Failed to update shadow yield: {e}")

    async def scan_and_capture_gaps(self):
        """
        Scans for price gaps between LST secondary market and its backing.
        Triggers KerneLSTSolver if a profitable gap is found.
        """
        if not self.solver_address:
            return
            
        # Example: wstETH/WETH gap on Aerodrome
        # In production, this would use the PricingEngine to find real gaps
        logger.info("LST Engine: Scanning for LST gaps...")
        
        # Mock profitable gap found
        # tokenIn = WETH, tokenOut = wstETH
        # amount = 10 ETH
        # routerType = 0 (Aerodrome)
        # ...
        
        # await self.execute_solver_swap(...)

    async def execute_solver_swap(self, token_in, token_out, amount, swap_data):
        """
        Calls executeLSTSwap on the KerneLSTSolver contract.
        """
        try:
            nonce = self.w3.eth.get_transaction_count(self.cm.account.address)
            tx = self.solver.functions.executeLSTSwap(
                token_in,
                token_out,
                amount,
                swap_data
            ).build_transaction({
                'from': self.cm.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.cm.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.success(f"LST Engine: Solver swap executed: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"LST Engine: Solver swap failed: {e}")
            return None

    def _get_erc20_balance(self, token_address, account_address):
        abi = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = self.w3.eth.contract(address=token_address, abi=abi)
        return contract.functions.balanceOf(account_address).call()

    async def run_loop(self):
        logger.info("Kerne LST Capture Engine active.")
        while True:
            await self.update_shadow_yield()
            await self.scan_and_capture_gaps()
            await asyncio.sleep(3600) # Run every hour

if __name__ == "__main__":
    from bot.chain_manager import ChainManager
    cm = ChainManager()
    engine = LSTCaptureEngine(cm)
    asyncio.run(engine.run_loop())
