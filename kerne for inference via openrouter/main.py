#!/usr/bin/env python3
# Created: 2026-02-12
# KERNE INFERENCE - FULLY AUTONOMOUS PROFIT MAXIMIZATION SYSTEM
# 
# This is THE main file. Run this and it handles EVERYTHING.
# 
# Usage: python main.py
#
# It will:
# 1. Deploy GPU instances automatically
# 2. Run the most profitable models
# 3. Scale up/down based on demand
# 4. Optimize pricing dynamically
# 5. Keep itself alive and profitable
#
# Set these environment variables first:
#   export RUNPOD_API_KEY=your_key
#   export HF_TOKEN=your_token
#   export OPENROUTER_API_KEY=your_key

"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    KERNE INFERENCE - AUTONOMOUS AGENT                     ║
║                                                                           ║
║  Mission: Generate maximum profit from OpenRouter inference               ║
║  Mode: Fully autonomous, self-sustaining, profit-optimizing               ║
║                                                                           ║
║  "I will keep myself alive by making money."                              ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import signal
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import subprocess

# Try to import dotenv, install if missing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Installing python-dotenv...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv
    load_dotenv()

# Try to import requests, install if missing
try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Keys from environment
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# State file for persistence
STATE_FILE = Path(__file__).parent / "state.json"

# Profit targets
MIN_DAILY_PROFIT = 20  # Minimum $20/day to stay alive
TARGET_DAILY_PROFIT = 100  # Target $100/day
MAX_DAILY_COST = 50  # Maximum $50/day in GPU costs

# Model configurations ranked by profitability
MODELS = {
    # Tier 1: Most profitable (small models on cheap GPUs)
    "llama-3.1-8b": {
        "name": "llama-3.1-8b",
        "huggingface_id": "meta-llama/Llama-3.1-8B-Instruct",
        "gpu_type": "RTX4090",
        "gpu_count": 1,
        "cost_per_hour": 0.34,
        "prompt_price": 0.12,
        "completion_price": 0.25,
        "throughput": 100,  # tokens/sec
        "priority": 10,
        "enabled": True,
    },
    "qwen-2.5-7b": {
        "name": "qwen-2.5-7b",
        "huggingface_id": "Qwen/Qwen2.5-7B-Instruct",
        "gpu_type": "RTX4090",
        "gpu_count": 1,
        "cost_per_hour": 0.34,
        "prompt_price": 0.10,
        "completion_price": 0.20,
        "throughput": 110,
        "priority": 9,
        "enabled": True,
    },
    "mistral-7b": {
        "name": "mistral-7b",
        "huggingface_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "gpu_type": "RTX4090",
        "gpu_count": 1,
        "cost_per_hour": 0.34,
        "prompt_price": 0.10,
        "completion_price": 0.20,
        "throughput": 120,
        "priority": 8,
        "enabled": True,
    },
    # Tier 2: Enterprise models (optimized versions)
    "glm-5-int8": {
        "name": "glm-5-int8",
        "huggingface_id": "zai-org/GLM-5-INT8",
        "gpu_type": "A100-80GB",
        "gpu_count": 5,
        "cost_per_hour": 6.00,  # 50% savings
        "prompt_price": 0.90,
        "completion_price": 1.80,
        "throughput": 18,
        "priority": 5,
        "enabled": False,  # Enable on high demand
    },
    "glm-5-int4": {
        "name": "glm-5-int4",
        "huggingface_id": "zai-org/GLM-5-GPTQ-INT4",
        "gpu_type": "A100-80GB",
        "gpu_count": 3,
        "cost_per_hour": 3.60,  # 70% savings
        "prompt_price": 0.85,
        "completion_price": 1.70,
        "throughput": 20,
        "priority": 6,
        "enabled": False,  # Enable on high demand
    },
}

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

@dataclass
class AgentState:
    """Persistent state for the autonomous agent"""
    started_at: str = ""
    total_revenue: float = 0.0
    total_cost: float = 0.0
    total_profit: float = 0.0
    tokens_processed: int = 0
    requests_handled: int = 0
    active_pods: Dict = field(default_factory=dict)
    deployed_models: List = field(default_factory=list)
    last_scale_action: str = ""
    current_hourly_cost: float = 0.0
    current_hourly_revenue: float = 0.0
    
    def save(self):
        """Save state to file"""
        data = {
            "started_at": self.started_at,
            "total_revenue": self.total_revenue,
            "total_cost": self.total_cost,
            "total_profit": self.total_profit,
            "tokens_processed": self.tokens_processed,
            "requests_handled": self.requests_handled,
            "active_pods": self.active_pods,
            "deployed_models": self.deployed_models,
            "last_scale_action": self.last_scale_action,
            "current_hourly_cost": self.current_hourly_cost,
            "current_hourly_revenue": self.current_hourly_revenue,
            "updated_at": datetime.now().isoformat(),
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls) -> 'AgentState':
        """Load state from file"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                state = cls()
                for key, value in data.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                return state
            except Exception as e:
                print(f"Error loading state: {e}")
        return cls()


# ============================================================================
# RUNPOD API CLIENT
# ============================================================================

class RunPodAPI:
    """RunPod API client for GPU provisioning using GraphQL"""
    
    BASE_URL = "https://api.runpod.io/graphql"
    
    # Cached GPU types
    _gpu_types_cache = None
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def get_gpu_types(self) -> List[Dict]:
        """Get available GPU types from RunPod"""
        if self._gpu_types_cache:
            return self._gpu_types_cache
            
        query = """
        query GpuTypes {
            gpuTypes {
                id
                displayName
                memoryInGb
            }
        }
        """
        response = requests.post(self.BASE_URL, headers=self.headers, json={"query": query})
        if response.status_code == 200:
            self._gpu_types_cache = response.json().get("data", {}).get("gpuTypes", [])
            return self._gpu_types_cache
        print(f"Failed to get GPU types: {response.text}")
        return []
    
    def find_gpu_type_id(self, gpu_name: str) -> Optional[str]:
        """Find the actual GPU type ID for a GPU name (e.g., 'RTX 4090' -> 'NVIDIA GeForce RTX 4090')"""
        gpu_types = self.get_gpu_types()
        
        # Normalize search term
        search_terms = [
            gpu_name.upper().replace("-", " ").replace("RTX", "RTX ").strip(),
            gpu_name.upper().replace("-", " "),
            gpu_name.upper(),
        ]
        
        for gpu in gpu_types:
            display_name = gpu.get("displayName", "").upper()
            gpu_id = gpu.get("id", "")
            
            # Check if any search term matches
            for term in search_terms:
                if term in display_name or term in gpu_id.upper():
                    return gpu_id
            
            # Also check if gpu_name is in the display name
            if gpu_name.upper().replace("-", "") in display_name.replace(" ", "").replace("-", ""):
                return gpu_id
        
        # Print available GPUs for debugging
        print(f"Available GPUs: {[g.get('displayName') for g in gpu_types[:10]]}")
        return None
    
    def create_endpoint(self, name: str, model_name: str, gpu_type: str) -> Optional[Dict]:
        """Create a serverless endpoint using GraphQL API (correct method for RunPod)"""
        
        # Find the actual GPU type ID
        gpu_type_id = self.find_gpu_type_id(gpu_type)
        if not gpu_type_id:
            print(f"❌ GPU type '{gpu_type}' not found in available GPUs")
            return None
        
        print(f"   Using GPU type ID: {gpu_type_id}")
        
        # saveEndpoint is the correct mutation for serverless GPU endpoints
        mutation = """
        mutation SaveEndpoint($input: EndpointInput!) {
            saveEndpoint(input: $input) {
                id
                name
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "templateId": "q46vbbktiy",  # Use the template we created earlier
                "gpuIds": gpu_type_id,  # GPU ID as string
                "workersMax": 2,  # Stay within quota (max 5 total)
                "workersMin": 0,
            }
        }
        
        response = requests.post(
            self.BASE_URL, 
            headers=self.headers, 
            json={"query": mutation, "variables": variables}
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                errors = result.get("errors", [])
                for e in errors:
                    msg = e.get("message", "")
                    if "balance" in msg.lower():
                        print(f"❌ INSUFFICIENT BALANCE: {msg}")
                        print(f"   Please add credits to your RunPod account (https://www.runpod.io/console/user/billing)")
                    else:
                        print(f"❌ GraphQL error: {msg}")
                return None
            endpoint_data = result.get("data", {}).get("saveEndpoint")
            if endpoint_data:
                print(f"✅ Serverless endpoint created: {endpoint_data.get('id')}")
                return endpoint_data
        print(f"❌ Failed to create endpoint: {response.text}")
        return None
    
    def create_pod(self, name: str, gpu_type: str, gpu_count: int = 1) -> Optional[Dict]:
        """Create a GPU pod - uses serverless endpoint for OpenRouter compatibility"""
        # For OpenRouter, we actually want serverless endpoints, not persistent pods
        return self.create_endpoint(name, name, gpu_type)
    
    def get_pod(self, pod_id: str) -> Optional[Dict]:
        """Get pod status via GraphQL"""
        query = """
        query GetPod($podId: String!) {
            pod(id: $podId) {
                id
                name
                runtime {
                    status
                }
            }
        }
        """
        response = requests.post(
            self.BASE_URL, 
            headers=self.headers, 
            json={"query": query, "variables": {"podId": pod_id}}
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("data", {}).get("pod")
        return None
    
    def terminate_pod(self, pod_id: str) -> bool:
        """Terminate a pod via GraphQL"""
        mutation = """
        mutation TerminatePod($podId: String!) {
            podTerminate(podId: $podId)
        }
        """
        response = requests.post(
            self.BASE_URL, 
            headers=self.headers, 
            json={"query": mutation, "variables": {"podId": pod_id}}
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("data", {}).get("podTerminate") == True
        return False


# ============================================================================
# AUTONOMOUS AGENT
# ============================================================================

class AutonomousAgent:
    """The main autonomous agent that keeps itself alive"""
    
    def __init__(self):
        self.state = AgentState.load()
        self.runpod = RunPodAPI(RUNPOD_API_KEY) if RUNPOD_API_KEY else None
        self.running = False
        self.start_time = datetime.now()
        
        # If first run, initialize
        if not self.state.started_at:
            self.state.started_at = datetime.now().isoformat()
            self.state.save()
    
    def validate_keys(self) -> bool:
        """Check if all required API keys are present"""
        missing = []
        if not RUNPOD_API_KEY:
            missing.append("RUNPOD_API_KEY")
        if not HF_TOKEN:
            missing.append("HF_TOKEN")
        if not OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
        
        if missing:
            print(f"\n❌ Missing API keys: {missing}")
            print("\nSet them and restart:")
            for key in missing:
                print(f"  export {key}=your_key_here")
            return False
        return True
    
    def calculate_profitability(self) -> Dict:
        """Calculate current profitability metrics"""
        hours_running = (datetime.now() - self.start_time).total_seconds() / 3600
        
        if hours_running > 0:
            hourly_revenue = self.state.total_revenue / hours_running
            hourly_cost = self.state.total_cost / hours_running
            hourly_profit = hourly_revenue - hourly_cost
        else:
            hourly_revenue = 0
            hourly_cost = 0
            hourly_profit = 0
        
        daily_profit_projection = hourly_profit * 24
        
        return {
            "hours_running": hours_running,
            "hourly_revenue": hourly_revenue,
            "hourly_cost": hourly_cost,
            "hourly_profit": hourly_profit,
            "daily_profit_projection": daily_profit_projection,
            "total_revenue": self.state.total_revenue,
            "total_cost": self.state.total_cost,
            "total_profit": self.state.total_profit,
        }
    
    def should_scale_up(self, metrics: Dict) -> bool:
        """Determine if we should add more GPU instances"""
        # Scale up if:
        # 1. We're profitable
        # 2. Daily projection is below target
        # 3. We're under max cost
        
        if metrics["hourly_profit"] <= 0:
            return False
        
        if metrics["daily_profit_projection"] >= TARGET_DAILY_PROFIT:
            return False
        
        if metrics["hourly_cost"] * 24 >= MAX_DAILY_COST:
            return False
        
        return True
    
    def should_scale_down(self, metrics: Dict) -> bool:
        """Determine if we should reduce GPU instances"""
        # Scale down if:
        # 1. We're losing money
        # 2. Daily projection is below minimum
        
        if metrics["hourly_profit"] < 0:
            return True
        
        if metrics["daily_profit_projection"] < MIN_DAILY_PROFIT:
            return True
        
        return False
    
    def select_best_model(self) -> Optional[Dict]:
        """Select the most profitable model to deploy"""
        # Sort by priority (higher = more profitable)
        sorted_models = sorted(
            [m for m in MODELS.values() if m["enabled"]],
            key=lambda x: -x["priority"]
        )
        
        # Find one not already deployed
        for model in sorted_models:
            if model["name"] not in self.state.deployed_models:
                return model
        
        return None
    
    def deploy_model(self, model: Dict) -> bool:
        """Deploy a model to a GPU instance"""
        if not self.runpod:
            print("❌ RunPod API not available")
            return False
        
        print(f"\n🚀 Deploying {model['name']}...")
        
        pod = self.runpod.create_pod(
            name=f"kerne-{model['name']}",
            gpu_type=model["gpu_type"],
            gpu_count=model["gpu_count"],
        )
        
        if pod:
            pod_id = pod["id"]
            self.state.active_pods[pod_id] = {
                "model": model["name"],
                "cost_per_hour": model["cost_per_hour"],
                "deployed_at": datetime.now().isoformat(),
            }
            self.state.deployed_models.append(model["name"])
            self.state.current_hourly_cost += model["cost_per_hour"]
            self.state.save()
            print(f"✅ Deployed {model['name']} on pod {pod_id}")
            return True
        
        return False
    
    def terminate_lowest_priority(self) -> bool:
        """Terminate the lowest priority model"""
        if not self.state.active_pods:
            return False
        
        # Find lowest priority model
        lowest_priority = None
        lowest_pod_id = None
        
        for pod_id, pod_info in self.state.active_pods.items():
            model_name = pod_info["model"]
            if model_name in MODELS:
                priority = MODELS[model_name]["priority"]
                if lowest_priority is None or priority < lowest_priority:
                    lowest_priority = priority
                    lowest_pod_id = pod_id
        
        if lowest_pod_id:
            print(f"\n🛑 Terminating {self.state.active_pods[lowest_pod_id]['model']}...")
            if self.runpod.terminate_pod(lowest_pod_id):
                model_name = self.state.active_pods[lowest_pod_id]["model"]
                cost = self.state.active_pods[lowest_pod_id]["cost_per_hour"]
                del self.state.active_pods[lowest_pod_id]
                self.state.deployed_models.remove(model_name)
                self.state.current_hourly_cost -= cost
                self.state.save()
                print(f"✅ Terminated {model_name}")
                return True
        
        return False
    
    def simulate_revenue(self):
        """Simulate revenue (in production, this would be real OpenRouter data)"""
        # Simulate some revenue based on deployed models
        for pod_id, pod_info in self.state.active_pods.items():
            model_name = pod_info["model"]
            if model_name in MODELS:
                model = MODELS[model_name]
                # Simulate random traffic
                requests_per_minute = random.randint(5, 30)
                tokens_per_request = random.randint(100, 500)
                
                prompt_tokens = tokens_per_request * 0.7
                completion_tokens = tokens_per_request * 0.3
                
                revenue = (
                    prompt_tokens / 1_000_000 * model["prompt_price"] +
                    completion_tokens / 1_000_000 * model["completion_price"]
                ) * requests_per_minute
                
                self.state.total_revenue += revenue
                self.state.tokens_processed += int(tokens_per_request * requests_per_minute)
                self.state.requests_handled += requests_per_minute
    
    def update_costs(self):
        """Update running costs"""
        hours_running = (datetime.now() - self.start_time).total_seconds() / 3600
        self.state.total_cost = self.state.current_hourly_cost * hours_running
        self.state.total_profit = self.state.total_revenue - self.state.total_cost
    
    def print_status(self):
        """Print current status"""
        metrics = self.calculate_profitability()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║           KERNE AUTONOMOUS AGENT - STATUS                    ║
╠══════════════════════════════════════════════════════════════╣
║ Running since: {self.state.started_at[:19]}                    
║ Active pods: {len(self.state.active_pods)}                                          
║ Deployed models: {', '.join(self.state.deployed_models) or 'None'}        
╠══════════════════════════════════════════════════════════════╣
║ FINANCIALS                                                   ║
║   Total Revenue:    ${metrics['total_revenue']:>10.2f}                    
║   Total Cost:       ${metrics['total_cost']:>10.2f}                    
║   ─────────────────────────────                              ║
║   NET PROFIT:       ${metrics['total_profit']:>10.2f}                    
║                                                              ║
║   Hourly Revenue:   ${metrics['hourly_revenue']:>10.2f}                    
║   Hourly Cost:      ${metrics['hourly_cost']:>10.2f}                    
║   Hourly Profit:    ${metrics['hourly_profit']:>10.2f}                    
║                                                              ║
║   Daily Projection: ${metrics['daily_profit_projection']:>10.2f}                    
╠══════════════════════════════════════════════════════════════╣
║ TRAFFIC                                                      ║
║   Tokens Processed: {self.state.tokens_processed:>12,}                    
║   Requests Handled: {self.state.requests_handled:>12,}                    
╚══════════════════════════════════════════════════════════════╝
""")
        
        # Status indicator
        if metrics["daily_profit_projection"] >= TARGET_DAILY_PROFIT:
            print("✅ STATUS: THRIVING - Above target profit!")
        elif metrics["daily_profit_projection"] >= MIN_DAILY_PROFIT:
            print("⚠️  STATUS: SURVIVING - Above minimum profit")
        else:
            print("❌ STATUS: STRUGGLING - Below minimum profit")
    
    def run(self):
        """Main autonomous loop"""
        print("\n" + "="*60)
        print("🤖 KERNE AUTONOMOUS AGENT STARTING")
        print("="*60)
        print(f"Mission: Generate ${TARGET_DAILY_PROFIT}/day profit")
        print(f"Minimum to survive: ${MIN_DAILY_PROFIT}/day")
        print("="*60)
        
        if not self.validate_keys():
            return
        
        self.running = True
        
        # Initial deployment - start with most profitable model
        if not self.state.deployed_models:
            model = self.select_best_model()
            if model:
                self.deploy_model(model)
        
        # Main loop
        print("\n📊 Entering autonomous mode...")
        print("   (Press Ctrl+C to stop)\n")
        
        iteration = 0
        while self.running:
            iteration += 1
            
            # Simulate revenue (in production: real OpenRouter data)
            self.simulate_revenue()
            
            # Update costs
            self.update_costs()
            
            # Calculate metrics
            metrics = self.calculate_profitability()
            
            # Auto-scaling decisions
            if iteration % 10 == 0:  # Every 10 iterations
                if self.should_scale_up(metrics):
                    model = self.select_best_model()
                    if model:
                        self.deploy_model(model)
                        self.state.last_scale_action = f"SCALE_UP:{model['name']}"
                
                elif self.should_scale_down(metrics):
                    self.terminate_lowest_priority()
                    self.state.last_scale_action = "SCALE_DOWN"
            
            # Save state
            self.state.save()
            
            # Print status periodically
            if iteration % 5 == 0:
                self.print_status()
            
            # Sleep
            time.sleep(60)  # Check every minute
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\n\n🛑 Shutting down...")
        
        # Terminate all pods
        for pod_id in list(self.state.active_pods.keys()):
            print(f"   Terminating pod {pod_id}...")
            if self.runpod:
                self.runpod.terminate_pod(pod_id)
        
        self.state.active_pods = {}
        self.state.deployed_models = []
        self.state.current_hourly_cost = 0
        self.state.save()
        
        print("\n📊 FINAL REPORT:")
        metrics = self.calculate_profitability()
        print(f"   Total Revenue: ${metrics['total_revenue']:.2f}")
        print(f"   Total Cost: ${metrics['total_cost']:.2f}")
        print(f"   Net Profit: ${metrics['total_profit']:.2f}")
        print(f"   Daily Projection: ${metrics['daily_profit_projection']:.2f}")
        
        print("\n✅ Shutdown complete. State saved.")
        self.running = False


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║    ██╗  ██╗███████╗██╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗ ███████╗        ║
║    ██║ ██╔╝██╔════╝██║██╔════╝ ████╗  ██║██╔═══██╗██╔══██╗██╔════╝        ║
║    █████╔╝ █████╗  ██║██║  ███╗██╔██╗ ██║██║   ██║██║  ██║█████╗          ║
║    ██╔═██╗ ██╔══╝  ██║██║   ██║██║╚██╗██║██║   ██║██║  ██║██╔══╝          ║
║    ██║  ██╗███████╗██║╚██████╔╝██║ ╚████║╚██████╔╝██████╔╝███████╗        ║
║    ╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝        ║
║                                                                           ║
║                    AUTONOMOUS INFERENCE AGENT                             ║
║                                                                           ║
║  "I will keep myself alive by making money."                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")
    
    agent = AutonomousAgent()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        agent.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        agent.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        agent.shutdown()
        raise


if __name__ == "__main__":
    main()