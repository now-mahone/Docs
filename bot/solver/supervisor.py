# Created: 2026-01-13
import asyncio
import subprocess
import sys
from loguru import logger
import time

class SolverSupervisor:
    """
    Monitors and manages the lifecycle of all solver components.
    Ensures 100% uptime for the extraction engine.
    """
    def __init__(self):
        self.processes = {
            "listener": "bot/solver/intent_listener.py",
            "sentinel": "bot/solver/sentinel_v2.py",
            "analytics": "bot/solver/analytics_api.py"
        }
        self.running_processes = {}

    def start_process(self, name, path):
        logger.info(f"Supervisor: Starting {name} ({path})...")
        try:
            proc = subprocess.Popen([sys.executable, path])
            self.running_processes[name] = proc
            return True
        except Exception as e:
            logger.error(f"Supervisor: Failed to start {name}: {e}")
            return False

    def check_health(self):
        for name, proc in list(self.running_processes.items()):
            if proc.poll() is not None: # Process has exited
                logger.warning(f"Supervisor: {name} has stopped! Restarting...")
                self.start_process(name, self.processes[name])

    async def run_loop(self):
        logger.info("Kerne Solver Supervisor active.")
        # Initial start
        for name, path in self.processes.items():
            self.start_process(name, path)
            
        while True:
            self.check_health()
            await asyncio.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    supervisor = SolverSupervisor()
    asyncio.run(supervisor.run_loop())
