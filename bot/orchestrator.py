import os
import subprocess
import json
from loguru import logger
from typing import Dict

# Created: 2026-01-09

class BotOrchestrator:
    """
    Manages isolated HedgingEngine instances for white-label vaults.
    Uses Docker to spin up dedicated containers for each partner.
    """
    def __init__(self, config_path: str = "bot/orchestrator_config.json"):
        self.config_path = config_path
        self.active_instances: Dict[str, str] = {} # vault_address -> container_id
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.active_instances = json.load(f)

    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.active_instances, f)

    def deploy_instance(self, vault_address: str, partner_config: dict):
        """
        Deploys a new Docker container for a specific vault.
        """
        if vault_address in self.active_instances:
            logger.warning(f"Instance already exists for vault {vault_address}")
            return self.active_instances[vault_address]

        logger.info(f"Deploying isolated hedging instance for vault: {vault_address}")

        # Create environment variables for the container
        env_vars = {
            "VAULT_ADDRESS": vault_address,
            "EXCHANGE_API_KEY": partner_config.get("api_key"),
            "EXCHANGE_SECRET": partner_config.get("secret"),
            "EXCHANGE_PASSPHRASE": partner_config.get("passphrase"),
            "STRATEGIST_PRIVATE_KEY": partner_config.get("private_key"),
            "RPC_URL": partner_config.get("rpc_url", "https://mainnet.base.org"),
            "RISK_THRESHOLD": str(partner_config.get("threshold", 0.5))
        }

        # Construct Docker run command
        # Assuming a pre-built 'kerne-hedging-engine' image
        cmd = [
            "docker", "run", "-d",
            "--name", f"kerne-vault-{vault_address[:8]}",
            "--restart", "unless-stopped"
        ]
        
        for k, v in env_vars.items():
            cmd.extend(["-e", f"{k}={v}"])
        
        cmd.append("kerne-hedging-engine")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()
            self.active_instances[vault_address] = container_id
            self._save_config()
            logger.success(f"Deployed container {container_id} for vault {vault_address}")
            return container_id
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy container: {e.stderr}")
            raise

    def stop_instance(self, vault_address: str):
        if vault_address not in self.active_instances:
            return

        container_id = self.active_instances[vault_address]
        logger.info(f"Stopping instance {container_id} for vault {vault_address}")

        try:
            subprocess.run(["docker", "stop", container_id], check=True)
            subprocess.run(["docker", "rm", container_id], check=True)
            del self.active_instances[vault_address]
            self._save_config()
            logger.success(f"Stopped and removed instance for vault {vault_address}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop container: {e}")

    def get_status(self, vault_address: str):
        if vault_address not in self.active_instances:
            return "NOT_DEPLOYED"
        
        container_id = self.active_instances[vault_address]
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_id],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().upper()
        except subprocess.CalledProcessError:
            return "ERROR"

if __name__ == "__main__":
    orchestrator = BotOrchestrator()
    # Example usage:
    # orchestrator.deploy_instance("0x123...", {"api_key": "...", "secret": "..."})
