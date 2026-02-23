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


def _sanitize_exc(e: Exception) -> str:
    """
    SECURITY (KRN-24-003): Returns a sanitized string representation of an exception.
    Strips raw private key hex patterns (0x + 64 hex chars) to prevent accidental
    leakage of the bot's private key into log files / log aggregation services.
    """
    import re as _re
    msg = str(e)
    # Redact any 64-character hex string (bare or 0x-prefixed) - typical private key format
    msg = _re.sub(r'0x[0-9a-fA-F]{64}', '0x[REDACTED]', msg)
    msg = _re.sub(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])', '[REDACTED]', msg)
    return msg


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
        
        # Load ABIs
        self.abi = self._load_abi("KerneVault")
        self.reg_abi = self._load_abi("KerneVaultRegistry")
        self.oracle_abi = self._load_abi("KerneYieldOracle")
        self.minter_abi = self._load_abi("kUSDMinter")
        self.treasury_abi = self._load_abi("KerneTreasury")

        self.vault = self.w3.eth.contract(address=self.vault_address, abi=self.abi)

        # Multi-vault configuration
        self.vaults = [
            {"address": self.vault_address, "chain": "Base", "w3": self.w3}
        ]
        
        arb_vault = os.getenv("ARB_VAULT_ADDRESS")
        if arb_vault and self.arb_w3:
            self.vaults.append({"address": arb_vault, "chain": "Arbitrum", "w3": self.arb_w3})
            
        opt_vault = os.getenv("OPT_VAULT_ADDRESS")
        if opt_vault and self.opt_w3:
            self.vaults.append({"address": opt_vault, "chain": "Optimism", "w3": self.opt_w3})

        # Contracts
        registry_address = os.getenv("VAULT_REGISTRY_ADDRESS")
        self.registry = self.w3.eth.contract(address=registry_address, abi=self.reg_abi) if registry_address else None

        oracle_address = os.getenv("YIELD_ORACLE_ADDRESS")
        self.oracle = self.w3.eth.contract(address=oracle_address, abi=self.oracle_abi) if oracle_address else None

        minter_address = os.getenv("KUSD_MINTER_ADDRESS")
        self.minter = self.w3.eth.contract(address=minter_address, abi=self.minter_abi) if minter_address else None

        treasury_address = os.getenv("TREASURY_ADDRESS")
        self.treasury = self.w3.eth.contract(address=treasury_address, abi=self.treasury_abi) if treasury_address else None

        logger.info(f"ChainManager initialized. Registered {len(self.vaults)} vaults.")

    def _load_abi(self, name: str) -> list:
        abi_path = os.path.join(os.path.dirname(__file__), "..", "out", f"{name}.sol", f"{name}.json")
        if not os.path.exists(abi_path):
            abi_path = os.path.join(os.path.dirname(__file__), "out", f"{name}.sol", f"{name}.json")
        
        if os.path.exists(abi_path):
            with open(abi_path, "r", encoding="utf-8") as f:
                artifact = json.load(f)
                return artifact["abi"]
        return []

    def get_vault_contract(self, vault_address: str, chain_name: str = "Base"):
        w3 = self.w3
        if chain_name == "Arbitrum": w3 = self.arb_w3
        elif chain_name == "Optimism": w3 = self.opt_w3
        
        return w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=self.abi)

    def set_active_vault(self, vault_address: str, chain_name: str = "Base"):
        """
        Sets the active vault for contract interactions.
        """
        self.vault_address = vault_address
        w3 = self.w3
        if chain_name == "Arbitrum": w3 = self.arb_w3
        elif chain_name == "Optimism": w3 = self.opt_w3
        
        self.w3 = w3 
        self.vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=self.abi)
        logger.info(f"Active vault set to {vault_address} on {chain_name}")

    def get_vault_assets(self, vault_address: str = None, chain_name: str = "Base") -> float:
        """
        Calls totalAssets() on the specified vault and returns the value in ETH.
        """
        try:
            addr = vault_address or self.vault_address
            w3 = self.w3
            if chain_name == "Arbitrum": w3 = self.arb_w3
            elif chain_name == "Optimism": w3 = self.opt_w3
            
            if not w3: return 0.0
            
            vault = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=self.abi)
            total_assets_wei = vault.functions.totalAssets().call()
            return float(w3.from_wei(total_assets_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error calling totalAssets on {chain_name}: {_sanitize_exc(e)}")
            return 0.0


    def get_vault_tvl(self) -> float:
        """
        Alias for get_vault_assets for consistency across services.
        """
        return self.get_vault_assets()

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
            logger.error(f"Error getting on-chain assets: {_sanitize_exc(e)}")
            return 0.0

    def get_lst_eth_ratio(self) -> float:
        """
        Returns the LST/ETH ratio for the vault's underlying asset.
        Defaults to 1.0 if price feeds are unavailable.
        """
        try:
            asset_address = self.vault.functions.asset().call()
            if not asset_address:
                return 1.0

            # Chainlink-style feed lookup via env, fallback to 1.0
            feed_address = os.getenv("LST_ETH_FEED")
            if not feed_address:
                return 1.0

            feed_abi = [
                {"inputs":[],"name":"latestAnswer","outputs":[{"name":"","type":"int256"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
            ]
            feed = self.w3.eth.contract(address=Web3.to_checksum_address(feed_address), abi=feed_abi)
            answer = feed.functions.latestAnswer().call()
            decimals = feed.functions.decimals().call()
            ratio = float(answer) / (10 ** decimals)
            if ratio <= 0:
                return 1.0
            return ratio
        except Exception as e:
            logger.warning(f"Error getting LST/ETH ratio: {_sanitize_exc(e)}")
            return 1.0

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
            logger.error(f"Error updating hedging reserve: {_sanitize_exc(e)}")
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
            logger.error(f"Error updating yield oracle: {_sanitize_exc(e)}")
            raise

    def register_vault_in_registry(self, vault_address: str, asset_address: str, metadata: str = "") -> str:
        """
        Registers a vault in the KerneVaultRegistry.
        """
        if not self.registry:
            return ""
        try:
            # Check if already registered
            is_reg = self.registry.functions.isRegistered(vault_address).call()
            if is_reg:
                return "ALREADY_REGISTERED"

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.registry.functions.registerVault(vault_address, asset_address, metadata).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.success(f"Vault registered in registry: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error registering vault: {_sanitize_exc(e)}")
            raise

    def update_l1_assets(self, amount_wei: int) -> str:
        """
        Updates the L1 asset value in the KerneVault contract for Sovereign Vault hedging.
        """
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.vault.functions.updateL1Assets(amount_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"L1 assets updated: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error updating L1 assets: {_sanitize_exc(e)}")
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
                    if deviation > 0.20:
                        msg = f"CRITICAL: Extreme deviation in off-chain report. Prev: {prev_offchain_eth}, New: {amount_eth} ({deviation*100:.2f}%). BLOCKING UPDATE."
                        logger.critical(msg)
                        send_discord_alert(msg, level="CRITICAL")
                        return "DEVIATION_BLOCKED"
                    elif deviation > 0.05:
                        msg = f"WARNING: High deviation in off-chain report. Prev: {prev_offchain_eth}, New: {amount_eth} ({deviation*100:.2f}%)"
                        logger.warning(msg)
                        send_discord_alert(msg, level="WARNING")

            except Exception as e:
                logger.error(f"Failed to perform deviation check: {_sanitize_exc(e)}")

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
            logger.error(f"Error updating off-chain value: {_sanitize_exc(e)}")
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
            logger.error(f"Error capturing founder wealth: {_sanitize_exc(e)}")
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
                    logger.warning(f"Retry {i+1}/{retries} for {name} RPC ({current_url}) failed: {_sanitize_exc(e)}")
            
            logger.error(f"Failed to connect to {name} RPC at {current_url}. Trying next fallback...")
        
        logger.critical(f"ALL RPC FALLBACKS FAILED FOR {name}!")
        send_discord_alert(f"CRITICAL: All RPC fallbacks failed for {name}!", level="CRITICAL")
        return None

    def get_multi_chain_tvl(self) -> dict:
        """
        Aggregates TVL across all connected chains using the registered vaults.
        """
        tvl_data = {}
        for v in self.vaults:
            tvl = self.get_vault_assets(v["address"], v["chain"])
            tvl_data[v["chain"]] = tvl
            
        return tvl_data

    def get_pending_withdrawals(self, vault_address: str = None, chain_name: str = "Base") -> float:
        """
        Fetches all WithdrawalRequested events and calculates the total pending assets.
        """
        try:
            addr = vault_address or self.vault_address
            w3 = self.w3
            if chain_name == "Arbitrum": w3 = self.arb_w3
            elif chain_name == "Optimism": w3 = self.opt_w3
            
            if not w3: return 0.0
            
            vault = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=self.abi)
            
            # Fetch events from the last 30 days (approx blocks)
            current_block = w3.eth.block_number
            from_block = max(0, current_block - (30 * 24 * 60 * 5)) # 5 blocks per min approx
            
            events = vault.events.WithdrawalRequested.get_logs(fromBlock=from_block)
            
            total_pending_wei = 0
            for event in events:
                # Check if already claimed (this requires a contract call per request or a more complex event filter)
                # For now, we fetch the request status from the contract
                request_id = event.args.requestId
                user = event.args.user
                request_data = vault.functions.withdrawalRequests(user, request_id).call()
                
                # request_data: [assets, shares, unlockTimestamp, claimed]
                if not request_data[3]: # if not claimed
                    total_pending_wei += request_data[0]
            
            return float(w3.from_wei(total_pending_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error fetching pending withdrawals on {chain_name}: {_sanitize_exc(e)}")
            return 0.0


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
            logger.error(f"Error drawing from insurance fund: {_sanitize_exc(e)}")
            raise

    # ═══════════════════════════════════════════════════════════════════════════════
    # TREASURY BUYBACK FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_treasury_balance(self, token_address: str) -> float:
        """
        Returns the balance of a specific token in the Treasury contract.
        """
        try:
            if not self.treasury:
                logger.warning("Treasury contract not initialized")
                return 0.0
            
            treasury_address = os.getenv("TREASURY_ADDRESS")
            if not treasury_address:
                return 0.0
            
            erc20_abi = [
                {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
            ]
            token = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            balance = token.functions.balanceOf(treasury_address).call()
            decimals = token.functions.decimals().call()
            return float(balance) / (10 ** decimals)
        except Exception as e:
            logger.error(f"Error getting treasury balance: {_sanitize_exc(e)}")
            return 0.0

    def get_buyback_stats(self) -> dict:
        """
        Returns buyback statistics from the Treasury contract.
        """
        try:
            if not self.treasury:
                return {"total_kerne_bought": 0, "total_spent": 0}
            
            stats = self.treasury.functions.getBuybackStats().call()
            return {
                "total_kerne_bought": float(self.w3.from_wei(stats[0], 'ether')),
                "total_spent": float(self.w3.from_wei(stats[1], 'ether'))
            }
        except Exception as e:
            logger.error(f"Error getting buyback stats: {_sanitize_exc(e)}")
            return {"total_kerne_bought": 0, "total_spent": 0}

    def preview_buyback(self, token_address: str, amount: float) -> dict:
        """
        Previews expected KERNE output for a given input amount.
        Returns expected output and minimum with slippage.
        """
        try:
            if not self.treasury:
                return {"expected": 0, "minimum": 0, "error": "Treasury not initialized"}
            
            # Determine decimals
            erc20_abi = [{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]
            token = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            decimals = token.functions.decimals().call()
            amount_wei = int(amount * (10 ** decimals))
            
            result = self.treasury.functions.previewBuyback(token_address, amount_wei).call()
            return {
                "expected": float(self.w3.from_wei(result[0], 'ether')),
                "minimum": float(self.w3.from_wei(result[1], 'ether')),
                "error": None
            }
        except Exception as e:
            logger.error(f"Error previewing buyback: {_sanitize_exc(e)}")
            return {"expected": 0, "minimum": 0, "error": str(e)}

    def is_buyback_token_approved(self, token_address: str) -> bool:
        """
        Checks if a token is approved for buybacks.
        """
        try:
            if not self.treasury:
                return False
            return self.treasury.functions.isApprovedToken(token_address).call()
        except Exception as e:
            logger.error(f"Error checking approved token: {_sanitize_exc(e)}")
            return False

    def execute_treasury_distribute(self, token_address: str) -> str:
        """
        Distributes accumulated fees in Treasury (80% founder, 20% buyback pool).
        """
        try:
            if not self.treasury:
                logger.error("Treasury contract not initialized")
                return ""
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.treasury.functions.distribute(token_address).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price,
                'gas': 200000
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Treasury distribution executed: {tx_hash.hex()}")
            else:
                logger.error(f"Treasury distribution failed: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error executing treasury distribute: {_sanitize_exc(e)}")
            return ""

    def execute_buyback(self, token_address: str, amount: float, min_kerne_out: float = 0) -> str:
        """
        Executes a KERNE buyback using the Treasury contract via Aerodrome.
        
        Args:
            token_address: Input token to swap (WETH, USDC, etc.)
            amount: Amount of input token to swap
            min_kerne_out: Minimum KERNE to receive (0 = use calculated slippage)
        
        Returns:
            Transaction hash on success, empty string on failure
        """
        try:
            if not self.treasury:
                logger.error("Treasury contract not initialized")
                return ""
            
            # Determine token decimals
            erc20_abi = [{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]
            token = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            decimals = token.functions.decimals().call()
            amount_wei = int(amount * (10 ** decimals))
            min_out_wei = int(min_kerne_out * (10 ** 18)) if min_kerne_out > 0 else 0
            
            # Preview first for logging
            preview = self.preview_buyback(token_address, amount)
            logger.info(f"Buyback preview: {amount} tokens → ~{preview['expected']:.4f} KERNE (min: {preview['minimum']:.4f})")
            
            if preview['expected'] == 0:
                logger.warning("Preview returned 0 output - pool may have no liquidity")
                return ""
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.treasury.functions.executeBuyback(
                token_address,
                amount_wei,
                min_out_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price,
                'gas': 400000  # Higher gas for DEX swap
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"🔥 KERNE buyback executed: {tx_hash.hex()}")
                send_discord_alert(f"🔥 KERNE Buyback: {amount} tokens swapped for ~{preview['expected']:.4f} KERNE", level="SUCCESS")
            else:
                logger.error(f"Buyback transaction failed: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error executing buyback: {_sanitize_exc(e)}")
            return ""

    def execute_distribute_and_buyback(self, token_address: str, min_kerne_out: float = 0) -> str:
        """
        Distributes fees AND executes buyback in one transaction (gas efficient).
        
        Args:
            token_address: Token to distribute and swap
            min_kerne_out: Minimum KERNE to receive (0 = use calculated slippage)
        
        Returns:
            Transaction hash on success, empty string on failure
        """
        try:
            if not self.treasury:
                logger.error("Treasury contract not initialized")
                return ""
            
            min_out_wei = int(min_kerne_out * (10 ** 18)) if min_kerne_out > 0 else 0
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.treasury.functions.distributeAndBuyback(
                token_address,
                min_out_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price,
                'gas': 500000  # Higher gas for distribute + DEX swap
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"🔥 Distribute + Buyback executed: {tx_hash.hex()}")
                send_discord_alert(f"🔥 Treasury Distribute + KERNE Buyback executed", level="SUCCESS")
            else:
                logger.error(f"Distribute+Buyback transaction failed: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error executing distribute+buyback: {_sanitize_exc(e)}")
            return ""

    def approve_buyback_token(self, token_address: str, approved: bool = True) -> str:
        """
        Approves or revokes a token for buyback swaps (owner only).
        """
        try:
            if not self.treasury:
                logger.error("Treasury contract not initialized")
                return ""
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.treasury.functions.setApprovedBuybackToken(
                token_address,
                approved
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price,
                'gas': 100000
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                action = "approved" if approved else "revoked"
                logger.success(f"Token {action} for buyback: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error approving buyback token: {_sanitize_exc(e)}")
            return ""

    def set_routing_hop(self, token_address: str, hop_address: str) -> str:
        """
        Sets an intermediate routing hop for deeper liquidity (e.g., USDC → WETH → KERNE).
        """
        try:
            if not self.treasury:
                logger.error("Treasury contract not initialized")
                return ""
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.treasury.functions.setRoutingHop(
                token_address,
                hop_address
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price,
                'gas': 100000
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"Routing hop set: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error setting routing hop: {_sanitize_exc(e)}")
            return ""

    def transfer_erc20(self, token_address: str, to_address: str, amount: float, chain_name: str = "Arbitrum") -> str:
        """
        Generic ERC20 transfer for autonomous rebalancing.
        """
        try:
            w3 = self.arb_w3 if chain_name == "Arbitrum" else self.w3
            if not w3:
                logger.error(f"RPC for {chain_name} not available.")
                return ""

            erc20_abi = [
                {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}
            ]
            token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc20_abi)
            decimals = token.functions.decimals().call()
            amount_raw = int(amount * (10 ** decimals))

            nonce = w3.eth.get_transaction_count(self.account.address)
            tx = token.functions.transfer(Web3.to_checksum_address(to_address), amount_raw).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': w3.eth.gas_price
            })

            signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.success(f"ERC20 Transfer successful on {chain_name}: {tx_hash.hex()}")
                return tx_hash.hex()
            return ""
        except Exception as e:
            logger.error(f"ERC20 Transfer failed: {_sanitize_exc(e)}")
            return ""

    def bridge_kusd_v2(self, amount_eth: float, dst_eid: int) -> str:
        """
        Bridges kUSD to another chain using the KerneOFTV2 contract (LayerZero V2).
        """
        try:
            oft_address = os.getenv("KUSD_OFT_V2_ADDRESS")
            if not oft_address:
                logger.error("KUSD_OFT_V2_ADDRESS not set.")
                return ""

            # Load OFT V2 ABI
            oft_abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneOFTV2.sol", "KerneOFTV2.json")
            if not os.path.exists(oft_abi_path):
                oft_abi_path = os.path.join(os.path.dirname(__file__), "out", "KerneOFTV2.sol", "KerneOFTV2.json")
            
            with open(oft_abi_path, "r", encoding="utf-8") as f:
                oft_artifact = json.load(f)
                oft_abi = oft_artifact["abi"]

            oft_contract = self.w3.eth.contract(address=oft_address, abi=oft_abi)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # LZ V2 send
            # function send(SendParam calldata _sendParam, MessagingFee calldata _fee, address _refundAddress) external payable returns (MessagingReceipt memory msgReceipt, OFTReceipt memory oftReceipt)
            to_bytes32 = self.w3.to_bytes(hexstr=self.account.address).rjust(32, b'\0')
            
            send_param = (
                dst_eid,
                to_bytes32,
                amount_wei,
                amount_wei, # minAmount
                b"", # extraOptions
                b"", # composeMsg
                b""  # oftCmd
            )

            # Estimate fees
            fees = oft_contract.functions.quoteSend(send_param, False).call()
            native_fee = fees[0]

            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = oft_contract.functions.send(
                send_param,
                (native_fee, 0), # MessagingFee
                self.account.address # refundAddress
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
                logger.success(f"kUSD V2 bridged to EID {dst_eid}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error bridging kUSD V2: {_sanitize_exc(e)}")
            raise
