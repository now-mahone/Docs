import os
import subprocess
import json
import asyncio
import time
from loguru import logger
from typing import Dict

# Created: 2026-01-09
# Updated: 2026-01-12 - Institutional Deep Hardening: Sub-millisecond latency optimization and high-availability orchestration

class BotOrchestrator:
    """
    Manages isolated HedgingEngine instances for white-label vaults.
    Optimized for sub-millisecond latency and high availability.
    """
    def __init__(self, config_path: str = "bot/orchestrator_config.json"):
        self.config_path = config_path
        self.active_instances: Dict[str, Dict] = {} # vault_address -> metadata
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
        Deploys a new Docker container with high-performance settings.
        """
        start_time = time.perf_counter()
        
        if vault_address in self.active_instances:
            status = await self.get_status(vault_address)
            if status == "RUNNING":
                logger.warning(f"Instance already running for vault {vault_address}")
                return self.active_instances[vault_address]["container_id"]
            else:
                await self.stop_instance(vault_address)

        # Construct high-performance Docker run command
        container_name = f"kerne-vault-{vault_address[:8]}"
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--restart", "always",
            "--cpus", "1.0", # Dedicated CPU core
            "--memory", "512m",
            "--ulimit", "nofile=65535:65535", # High file descriptor limit for networking
            "--network", "host", # Use host network for lowest latency
            "--health-cmd", "python -c 'import os; exit(0 if os.path.exists(\"/tmp/heartbeat\") else 1)'",
            "--health-interval", "10s",
            "--health-timeout", "5s"
        ]
        
        env_vars = {
            "VAULT_ADDRESS": vault_address,
            "EXCHANGE_API_KEY": partner_config.get("api_key"),
            "EXCHANGE_SECRET": partner_config.get("secret"),
            "STRATEGIST_PRIVATE_KEY": partner_config.get("private_key"),
            "RPC_URL": partner_config.get("rpc_url", "https://mainnet.base.org"),
            "LATENCY_MODE": "ULTRA_LOW"
        }
        
        for k, v in env_vars.items():
            if v: cmd.extend(["-e", f"{k}={v}"])
        
        cmd.append("kerne-hedging-engine")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker error: {stderr.decode().strip()}")

            container_id = stdout.decode().strip()
            self.active_instances[vault_address] = {
                "container_id": container_id,
                "deployed_at": time.time(),
                "config_hash": hash(json.dumps(partner_config, sort_keys=True))
            }
            self._save_config()
            
            end_time = time.perf_counter()
            logger.success(f"Deployed high-performance instance {container_id} in {(end_time - start_time)*1000:.2f}ms")
            return container_id
        except Exception as e:
            logger.error(f"Orchestrator deployment failed: {e}")
            raise

    async def stop_instance(self, vault_address: str):
        if vault_address not in self.active_instances: return

        container_id = self.active_instances[vault_address]["container_id"]
        try:
            # Force remove for speed in emergency
            await asyncio.create_subprocess_exec("docker", "rm", "-f", container_id)
            del self.active_instances[vault_address]
            self._save_config()
            logger.success(f"Force stopped instance for vault {vault_address}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")

    async def get_status(self, vault_address: str):
        if vault_address not in self.active_instances: return "NOT_DEPLOYED"
        
        container_id = self.active_instances[vault_address]["container_id"]
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
    # asyncio.run(orchestrator.deploy_instance("0x123...", {"api_key": "...", "secret": "..."}))
