import os
import json
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
try:
    from bot.alerts import send_discord_alert
except ImportError:
    from alerts import send_discord_alert

# Created: 2025-12-28

class ChainManager:
    """
    Handles interactions with the Base blockchain and the KerneVault contract.
    Supports multi-chain TVL aggregation (Base, Arbitrum, Optimism).
    """
    def __init__(self):
        load_dotenv()
        
        self.rpc_url = os.getenv("RPC_URL")
        self.arb_rpc_url = os.getenv("ARB_RPC_URL")
        self.opt_rpc_url = os.getenv("OPT_RPC_URL")
        
        self.private_key = os.getenv("PRIVATE_KEY")
        self.vault_address = os.getenv("VAULT_ADDRESS")
        
        if not self.rpc_url or not self.private_key or not self.vault_address:
            logger.error("Missing environment variables for ChainManager.")
            raise ValueError("Missing RPC_URL, PRIVATE_KEY, or VAULT_ADDRESS")

        self.w3 = self._connect_with_retry(self.rpc_url, "Base")
        
        # Multi-chain RPCs
        self.arb_w3 = self._connect_with_retry(self.arb_rpc_url, "Arbitrum") if self.arb_rpc_url else None
        self.opt_w3 = self._connect_with_retry(self.opt_rpc_url, "Optimism") if self.opt_rpc_url else None

        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Load ABI from Foundry output
        abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneVault.sol", "KerneVault.json")
        if not os.path.exists(abi_path):
            abi_path = os.path.join(os.path.dirname(__file__), "out", "KerneVault.sol", "KerneVault.json")
        
        with open(abi_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
            self.abi = artifact["abi"]

        self.vault = self.w3.eth.contract(address=self.vault_address, abi=self.abi)

        # Load Yield Oracle ABI
        oracle_address = os.getenv("YIELD_ORACLE_ADDRESS")
        if oracle_address:
            oracle_abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneYieldOracle.sol", "KerneYieldOracle.json")
            if not os.path.exists(oracle_abi_path):
                oracle_abi_path = os.path.join(os.path.dirname(__file__), "out", "KerneYieldOracle.sol", "KerneYieldOracle.json")
            
            with open(oracle_abi_path, "r", encoding="utf-8") as f:
                oracle_artifact = json.load(f)
                self.oracle_abi = oracle_artifact["abi"]
            self.oracle = self.w3.eth.contract(address=oracle_address, abi=self.oracle_abi)
        else:
            self.oracle = None

        # Load kUSDMinter ABI
        minter_address = os.getenv("KUSD_MINTER_ADDRESS")
        if minter_address:
            minter_abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "kUSDMinter.sol", "kUSDMinter.json")
            if not os.path.exists(minter_abi_path):
                minter_abi_path = os.path.join(os.path.dirname(__file__), "out", "kUSDMinter.sol", "kUSDMinter.json")
            
            with open(minter_abi_path, "r", encoding="utf-8") as f:
                minter_artifact = json.load(f)
                self.minter_abi = minter_artifact["abi"]
            self.minter = self.w3.eth.contract(address=minter_address, abi=self.minter_abi)
        else:
            self.minter = None

        logger.info(f"ChainManager initialized. Connected to {self.rpc_url}. Vault: {self.vault_address}")

    def get_total_kusd_debt(self) -> float:
        """
        Returns the total kUSD debt across all positions in the minter.
        """
        if not self.minter:
            return 0.0
        try:
            total_debt_wei = self.minter.functions.totalDebt().call()
            return float(self.w3.from_wei(total_debt_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error getting kUSD debt: {e}")
            return 0.0

    def get_vault_assets(self) -> float:
        """
        Calls totalAssets() on the vault and returns the value in ETH.
        """
        try:
            total_assets_wei = self.vault.functions.totalAssets().call()
            return float(self.w3.from_wei(total_assets_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error calling totalAssets: {e}")
            raise

    def get_on_chain_assets(self) -> float:
        """
        Returns the actual on-chain balance of the underlying asset in the vault.
        """
        try:
            asset_address = self.vault.functions.asset().call()
            asset_abi = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
            asset_contract = self.w3.eth.contract(address=asset_address, abi=asset_abi)
            balance_wei = asset_contract.functions.balanceOf(self.vault_address).call()
            return float(self.w3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error getting on-chain assets: {e}")
            return 0.0

    def update_hedging_reserve(self, amount_eth: float) -> str:
        """
        Updates the hedging reserve in the KerneVault contract for institutional facade.
        """
        try:
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.vault.functions.updateHedgingReserve(amount_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Hedging reserve updated: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error updating hedging reserve: {e}")
            raise

    def update_yield_oracle(self) -> str:
        """
        Triggers the updateYield function on the KerneYieldOracle contract.
        """
        if not self.oracle:
            return ""
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.oracle.functions.updateYield(self.vault_address).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.success(f"Yield oracle updated: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error updating yield oracle: {e}")
            raise

    def update_offchain_value(self, amount_eth: float) -> str:
        """
        Updates the off-chain asset value in the KerneVault contract.
        """
        try:
            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance_eth = float(self.w3.from_wei(balance_wei, 'ether'))
            if balance_eth < 0.005:
                msg = f"LOW GAS: Bot wallet needs refill. Current balance: {balance_eth:.4f} ETH"
                logger.critical(msg)
                send_discord_alert(msg, level="CRITICAL")

            try:
                prev_offchain_wei = self.vault.functions.offChainAssets().call()
                prev_offchain_eth = float(self.w3.from_wei(prev_offchain_wei, 'ether'))
                
                if prev_offchain_eth > 0:
                    deviation = abs(amount_eth - prev_offchain_eth) / prev_offchain_eth
                    if deviation > 0.05:
                        msg = f"WARNING: High deviation in off-chain report. Prev: {prev_offchain_eth}, New: {amount_eth} ({deviation*100:.2f}%)"
                        logger.warning(msg)
                        send_discord_alert(msg, level="WARNING")
            except Exception as e:
                logger.error(f"Failed to perform deviation check: {e}")

            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.vault.functions.updateOffChainAssets(amount_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Off-chain assets updated: {tx_hash.hex()}")
            else:
                logger.error(f"Transaction failed: {tx_hash.hex()}")
                
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error updating off-chain value: {e}")
            raise

    def capture_founder_wealth(self, gross_yield_eth: float) -> str:
        """
        Triggers the captureFounderWealth function on the KerneVault contract.
        """
        try:
            if gross_yield_eth <= 0:
                return ""

            gross_yield_wei = self.w3.to_wei(gross_yield_eth, 'ether')
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.vault.functions.captureFounderWealth(gross_yield_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Founder wealth captured: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error capturing founder wealth: {e}")
            raise

    def _connect_with_retry(self, url: str, name: str, retries: int = 3) -> Web3:
        """
        Connects to an RPC URL with retry logic and failover support.
        """
        # Support for comma-separated fallback RPCs in environment variables
        urls = [u.strip() for u in url.split(",")] if url else []
        
        for current_url in urls:
            for i in range(retries):
                try:
                    w3 = Web3(Web3.HTTPProvider(current_url, request_kwargs={'timeout': 10}))
                    if w3.is_connected():
                        logger.info(f"Connected to {name} RPC: {current_url}")
                        return w3
                except Exception as e:
                    logger.warning(f"Retry {i+1}/{retries} for {name} RPC ({current_url}) failed: {e}")
            
            logger.error(f"Failed to connect to {name} RPC at {current_url}. Trying next fallback...")
        
        logger.critical(f"ALL RPC FALLBACKS FAILED FOR {name}!")
        send_discord_alert(f"CRITICAL: All RPC fallbacks failed for {name}!", level="CRITICAL")
        return None

    def get_multi_chain_tvl(self) -> dict:
        """
        Aggregates TVL across all connected chains.
        """
        tvl_data = {"Base": self.get_vault_assets()}
        
        # In a real multi-chain setup, we'd have vault addresses for each chain
        # For now, we simulate or use placeholders if addresses aren't in env
        if self.arb_w3:
            # Placeholder for Arbitrum vault assets
            tvl_data["Arbitrum"] = 0.0 
        if self.opt_w3:
            # Placeholder for Optimism vault assets
            tvl_data["Optimism"] = 0.0
            
        return tvl_data

    def draw_from_insurance_fund(self, amount_eth: float) -> str:
        """
        Triggers the claim function on the KerneInsuranceFund contract.
        """
        try:
            if amount_eth <= 0:
                return ""

            insurance_fund_address = self.vault.functions.insuranceFund().call()
            if insurance_fund_address == "0x0000000000000000000000000000000000000000":
                logger.error("Insurance fund address not set in vault.")
                return ""

            # Load Insurance Fund ABI
            if_abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneInsuranceFund.sol", "KerneInsuranceFund.json")
            if not os.path.exists(if_abi_path):
                if_abi_path = os.path.join(os.path.dirname(__file__), "out", "KerneInsuranceFund.sol", "KerneInsuranceFund.json")
            
            with open(if_abi_path, "r", encoding="utf-8") as f:
                if_artifact = json.load(f)
                if_abi = if_artifact["abi"]

            if_contract = self.w3.eth.contract(address=insurance_fund_address, abi=if_abi)

            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Claim funds back to the vault
            tx = if_contract.functions.claim(self.vault_address, amount_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Insurance fund drawn: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error drawing from insurance fund: {e}")
            raise

    def bridge_kusd(self, amount_eth: float, dst_chain_id: int) -> str:
        """
        Bridges kUSD to another chain using the KerneOFT contract (LayerZero V1).
        """
        try:
            oft_address = os.getenv("KUSD_OFT_ADDRESS")
            if not oft_address:
                logger.error("KUSD_OFT_ADDRESS not set.")
                return ""

            # Load OFT ABI
            oft_abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneOFT.sol", "KerneOFT.json")
            if not os.path.exists(oft_abi_path):
                oft_abi_path = os.path.join(os.path.dirname(__file__), "out", "KerneOFT.sol", "KerneOFT.json")
            
            with open(oft_abi_path, "r", encoding="utf-8") as f:
                oft_artifact = json.load(f)
                oft_abi = oft_artifact["abi"]

            oft_contract = self.w3.eth.contract(address=oft_address, abi=oft_abi)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # LZ V1 sendFrom
            # function sendFrom(address _from, uint16 _dstChainId, bytes32 _toAddress, uint _amount, address payable _refundAddress, address _zroPaymentAddress, bytes memory _adapterParams) public payable
            to_bytes32 = self.w3.to_bytes(hexstr=self.account.address).rjust(32, b'\0')
            
            # Estimate fees
            fees = oft_contract.functions.estimateSendFee(dst_chain_id, to_bytes32, amount_wei, False, b"").call()
            native_fee = fees[0]

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = oft_contract.functions.sendFrom(
                self.account.address,
                dst_chain_id,
                to_bytes32,
                amount_wei,
                self.account.address, # refundAddress
                "0x0000000000000000000000000000000000000000", # zroPaymentAddress
                b"" # adapterParams
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'value': native_fee,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"kUSD bridged to chain {dst_chain_id}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error bridging kUSD: {e}")
            raise
