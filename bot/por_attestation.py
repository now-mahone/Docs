import os
import json
import time
from web3 import Web3
from eth_account.messages import encode_defunct
from dotenv import load_dotenv
from loguru import logger

# Created: 2026-01-12

class PoRAttestationBot:
    """
    Automated Proof of Reserve (PoR) Attestation Bot.
    Signs off-chain reserve data and publishes it for institutional transparency.
    """
    def __init__(self):
        load_dotenv()
        self.rpc_url = os.getenv("RPC_URL")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.vault_address = os.getenv("VAULT_ADDRESS")
        self.verification_node_address = os.getenv("VERIFICATION_NODE_ADDRESS")
        
        if not all([self.rpc_url, self.private_key, self.vault_address]):
            logger.error("Missing environment variables for PoRAttestationBot.")
            raise ValueError("Missing RPC_URL, PRIVATE_KEY, or VAULT_ADDRESS")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Load VerificationNode ABI
        abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneVerificationNode.sol", "KerneVerificationNode.json")
        if os.path.exists(abi_path):
            with open(abi_path, "r") as f:
                self.abi = json.load(f)["abi"]
        else:
            # Fallback or mock ABI for testing
            self.abi = []
            
        if self.verification_node_address:
            self.node = self.w3.eth.contract(address=self.verification_node_address, abi=self.abi)
        else:
            self.node = None

    def sign_attestation(self, total_assets_eth: float, timestamp: int):
        """
        Signs the reserve data using the bot's private key.
        """
        message_hash = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256'],
            [self.vault_address, self.w3.to_wei(total_assets_eth, 'ether'), timestamp]
        )
        encoded_message = encode_defunct(hexstr=message_hash.hex())
        signed_message = self.w3.eth.account.sign_message(encoded_message, private_key=self.private_key)
        return signed_message.signature.hex()

    def publish_attestation(self, total_assets_eth: float):
        """
        Publishes the signed attestation to the on-chain VerificationNode.
        """
        if not self.node:
            logger.warning("VerificationNode address not set. Skipping on-chain publication.")
            return None

        timestamp = int(time.time())
        signature = self.sign_attestation(total_assets_eth, timestamp)
        
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.node.functions.submitAttestation(
                self.vault_address,
                self.w3.to_wei(total_assets_eth, 'ether'),
                timestamp,
                signature
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.success(f"PoR Attestation published: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to publish PoR attestation: {e}")
            return None

    def run_cycle(self, current_assets_eth: float):
        """
        Runs a single attestation cycle.
        """
        logger.info(f"Starting PoR Attestation cycle for {current_assets_eth} ETH...")
        return self.publish_attestation(current_assets_eth)

if __name__ == "__main__":
    # Example usage
    bot = PoRAttestationBot()
    bot.run_cycle(126.5)
