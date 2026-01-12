import os
import subprocess
import json
import asyncio
from loguru import logger
from typing import Dict

# Created: 2026-01-09
# Updated: 2026-01-12 - Refactored for asynchronous execution to reduce hedging latency

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

    async def deploy_instance(self, vault_address: str, partner_config: dict):
        """
        Deploys a new Docker container for a specific vault asynchronously.
        """
        if vault_address in self.active_instances:
            status = await self.get_status(vault_address)
            if status == "RUNNING":
                logger.warning(f"Instance already running for vault {vault_address}")
                return self.active_instances[vault_address]
            else:
                logger.info(f"Instance for {vault_address} exists but is {status}. Restarting...")
                await self.stop_instance(vault_address)

        logger.info(f"Deploying isolated hedging instance for vault: {vault_address}")

        # Create environment variables for the container
        env_vars = {
            "VAULT_ADDRESS": vault_address,
            "EXCHANGE_API_KEY": partner_config.get("api_key"),
            "EXCHANGE_SECRET": partner_config.get("secret"),
            "EXCHANGE_PASSPHRASE": partner_config.get("passphrase"),
            "STRATEGIST_PRIVATE_KEY": partner_config.get("private_key"),
            "RPC_URL": partner_config.get("rpc_url", "https://mainnet.base.org"),
            "RISK_THRESHOLD": str(partner_config.get("threshold", 0.5)),
            "LOG_LEVEL": "INFO"
        }

        # Construct Docker run command
        container_name = f"kerne-vault-{vault_address[:8]}"
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--restart", "unless-stopped",
            "--health-cmd", "python -c 'import os; exit(0 if os.path.exists(\"/tmp/heartbeat\") else 1)'",
            "--health-interval", "30s",
            "--health-timeout", "10s",
            "--health-retries", "3"
        ]
        
        for k, v in env_vars.items():
            if v: # Only add if value exists
                cmd.extend(["-e", f"{k}={v}"])
        
        cmd.append("kerne-hedging-engine")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Failed to deploy container for {vault_address}: {error_msg}")
                if "already in use" in error_msg:
                    logger.info(f"Container name {container_name} conflict. Attempting to remove and retry...")
                    await asyncio.create_subprocess_exec("docker", "rm", "-f", container_name)
                    return await self.deploy_instance(vault_address, partner_config)
                raise Exception(f"Docker error: {error_msg}")

            container_id = stdout.decode().strip()
            self.active_instances[vault_address] = container_id
            self._save_config()
            logger.success(f"Deployed container {container_id} ({container_name}) for vault {vault_address}")
            return container_id
        except Exception as e:
            logger.error(f"Orchestrator deployment failed: {e}")
            raise

    async def stop_instance(self, vault_address: str):
        if vault_address not in self.active_instances:
            return

        container_id = self.active_instances[vault_address]
        logger.info(f"Stopping instance {container_id} for vault {vault_address}")

        try:
            await asyncio.create_subprocess_exec("docker", "stop", container_id)
            await asyncio.create_subprocess_exec("docker", "rm", container_id)
            del self.active_instances[vault_address]
            self._save_config()
            logger.success(f"Stopped and removed instance for vault {vault_address}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")

    async def get_status(self, vault_address: str):
        if vault_address not in self.active_instances:
            return "NOT_DEPLOYED"
        
        container_id = self.active_instances[vault_address]
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "inspect", "-f", "{{.State.Status}}", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode().strip().upper()
        except Exception:
            return "ERROR"

if __name__ == "__main__":
    orchestrator = BotOrchestrator()
    # Example usage:
    # asyncio.run(orchestrator.deploy_instance("0x123...", {"api_key": "...", "secret": "..."}))
