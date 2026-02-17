# Created: 2026-02-12
# Kerne Autonomous Inference Profit Engine
# A fully dynamic system that maximizes profit from OpenRouter inference

"""
KERNE INFERENCE PROFIT ENGINE
=============================
An autonomous system that:
1. Monitors OpenRouter demand in real-time
2. Dynamically scales GPU resources up/down
3. Automatically selects optimal models based on profitability
4. Adjusts pricing based on market conditions
5. Routes requests for maximum throughput
6. Generates daily profit reports
"""

import os
import json
import time
import requests
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import threading
import queue

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for a single model"""
    name: str
    huggingface_id: str
    parameters: str  # e.g., "8B", "70B", "750B"
    vram_required_gb: int
    gpu_count: int
    cost_per_hour: float
    prompt_rate: float  # $ per million tokens
    completion_rate: float
    throughput_tokens_per_sec: int
    is_enterprise: bool = False
    priority: int = 1  # Higher = more profitable
    current_utilization: float = 0.0
    enabled: bool = True


@dataclass
class GPUConfig:
    """GPU instance configuration"""
    provider: str
    gpu_type: str  # "RTX4090", "A100", "H100"
    gpu_count: int
    vram_per_gpu: int
    cost_per_hour: float
    instance_id: Optional[str] = None
    status: str = "idle"  # "idle", "starting", "running", "stopping"
    models_loaded: List[str] = field(default_factory=list)
    total_revenue: float = 0.0
    total_cost: float = 0.0


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistry:
    """Registry of all available models with profitability rankings"""
    
    # Tier 1: Small models (RTX 4090 class)
    SMALL_MODELS = {
        "llama-3.1-8b": ModelConfig(
            name="llama-3.1-8b",
            huggingface_id="meta-llama/Llama-3.1-8B-Instruct",
            parameters="8B",
            vram_required_gb=16,
            gpu_count=1,
            cost_per_hour=0.34,
            prompt_rate=0.12,
            completion_rate=0.25,
            throughput_tokens_per_sec=100,
            is_enterprise=False,
            priority=10,  # Highest priority - best profit/hour
        ),
        "qwen-2.5-7b": ModelConfig(
            name="qwen-2.5-7b",
            huggingface_id="Qwen/Qwen2.5-7B-Instruct",
            parameters="7B",
            vram_required_gb=14,
            gpu_count=1,
            cost_per_hour=0.34,
            prompt_rate=0.10,
            completion_rate=0.20,
            throughput_tokens_per_sec=110,
            is_enterprise=False,
            priority=9,
        ),
        "mistral-7b": ModelConfig(
            name="mistral-7b",
            huggingface_id="mistralai/Mistral-7B-Instruct-v0.3",
            parameters="7B",
            vram_required_gb=14,
            gpu_count=1,
            cost_per_hour=0.34,
            prompt_rate=0.10,
            completion_rate=0.20,
            throughput_tokens_per_sec=120,
            is_enterprise=False,
            priority=8,
        ),
        "phi-4": ModelConfig(
            name="phi-4",
            huggingface_id="microsoft/Phi-4",
            parameters="14B",
            vram_required_gb=28,
            gpu_count=1,
            cost_per_hour=0.34,
            prompt_rate=0.08,
            completion_rate=0.18,
            throughput_tokens_per_sec=90,
            is_enterprise=False,
            priority=7,
        ),
    }
    
    # Tier 2: Medium models (A100 class)
    MEDIUM_MODELS = {
        "qwen-2.5-72b": ModelConfig(
            name="qwen-2.5-72b",
            huggingface_id="Qwen/Qwen2.5-72B-Instruct",
            parameters="72B",
            vram_required_gb=160,
            gpu_count=2,
            cost_per_hour=1.78,  # 2x A100
            prompt_rate=0.60,
            completion_rate=1.20,
            throughput_tokens_per_sec=40,
            is_enterprise=True,
            priority=6,
        ),
        "llama-3.1-70b": ModelConfig(
            name="llama-3.1-70b",
            huggingface_id="meta-llama/Llama-3.1-70B-Instruct",
            parameters="70B",
            vram_required_gb=160,
            gpu_count=2,
            cost_per_hour=1.78,
            prompt_rate=0.50,
            completion_rate=1.00,
            throughput_tokens_per_sec=35,
            is_enterprise=True,
            priority=5,
        ),
    }
    
    # Tier 3: Enterprise models (8x A100/H100)
    ENTERPRISE_MODELS = {
        "glm-5": ModelConfig(
            name="glm-5",
            huggingface_id="zai-org/GLM-5",
            parameters="750B",
            vram_required_gb=800,
            gpu_count=8,
            cost_per_hour=12.00,  # 8x A100
            prompt_rate=1.00,
            completion_rate=2.00,
            throughput_tokens_per_sec=15,
            is_enterprise=True,
            priority=3,  # Lower priority due to high cost
        ),
        # OPTIMIZED VERSIONS - 50-75% cost reduction!
        "glm-5-int8": ModelConfig(
            name="glm-5-int8",
            huggingface_id="zai-org/GLM-5-INT8",
            parameters="750B (INT8)",
            vram_required_gb=375,
            gpu_count=5,
            cost_per_hour=6.00,  # 5x A100 - 50% SAVINGS
            prompt_rate=0.90,
            completion_rate=1.80,
            throughput_tokens_per_sec=18,  # Slightly faster
            is_enterprise=True,
            priority=5,  # Higher priority - more profitable!
        ),
        "glm-5-int4": ModelConfig(
            name="glm-5-int4",
            huggingface_id="zai-org/GLM-5-GPTQ-INT4",
            parameters="750B (INT4)",
            vram_required_gb=188,
            gpu_count=3,
            cost_per_hour=3.60,  # 3x A100 - 70% SAVINGS
            prompt_rate=0.85,
            completion_rate=1.70,
            throughput_tokens_per_sec=20,
            is_enterprise=True,
            priority=6,  # Highest priority for enterprise - most profitable!
        ),
        "llama-3.1-405b": ModelConfig(
            name="llama-3.1-405b",
            huggingface_id="meta-llama/Llama-3.1-405B-Instruct",
            parameters="405B",
            vram_required_gb=800,
            gpu_count=8,
            cost_per_hour=12.00,
            prompt_rate=1.50,
            completion_rate=3.00,
            throughput_tokens_per_sec=20,
            is_enterprise=True,
            priority=4,
        ),
    }
    
    @classmethod
    def get_all_models(cls) -> Dict[str, ModelConfig]:
        """Get all models sorted by priority (profitability)"""
        all_models = {}
        all_models.update(cls.SMALL_MODELS)
        all_models.update(cls.MEDIUM_MODELS)
        all_models.update(cls.ENTERPRISE_MODELS)
        return dict(sorted(all_models.items(), key=lambda x: -x[1].priority))
    
    @classmethod
    def get_models_for_gpu(cls, gpu_type: str, gpu_count: int) -> List[ModelConfig]:
        """Get models that fit on a specific GPU configuration"""
        all_models = cls.get_all_models()
        suitable = []
        for model in all_models.values():
            if model.gpu_count <= gpu_count:
                suitable.append(model)
        return suitable


# ============================================================================
# GPU MANAGER
# ============================================================================

class GPUManager:
    """Manages GPU instances across multiple providers"""
    
    # GPU offerings by provider
    GPU_OFFERINGS = {
        "runpod": {
            "RTX4090": {"vram": 24, "cost": 0.34, "max_gpus": 1},
            "RTX3090": {"vram": 24, "cost": 0.19, "max_gpus": 1},
            "A100-40GB": {"vram": 40, "cost": 0.89, "max_gpus": 1},
            "A100-80GB": {"vram": 80, "cost": 1.20, "max_gpus": 8},
            "H100-80GB": {"vram": 80, "cost": 2.50, "max_gpus": 8},
        },
        "vast": {
            "RTX4090": {"vram": 24, "cost": 0.30, "max_gpus": 1},
            "RTX3090": {"vram": 24, "cost": 0.15, "max_gpus": 1},
            "A100-80GB": {"vram": 80, "cost": 1.00, "max_gpus": 8},
        },
        "lambda": {
            "A100-40GB": {"vram": 40, "cost": 0.50, "max_gpus": 1},
            "A100-80GB": {"vram": 80, "cost": 0.80, "max_gpus": 8},
            "H100-80GB": {"vram": 80, "cost": 1.50, "max_gpus": 8},
            "GH200": {"vram": 96, "cost": 2.50, "max_gpus": 8},
        },
    }
    
    def __init__(self):
        self.active_instances: Dict[str, GPUConfig] = {}
        self.instance_counter = 0
        
    def get_cheapest_gpu_for_model(self, model: ModelConfig) -> Tuple[str, str, float]:
        """Find the cheapest GPU configuration for a model"""
        best_provider = None
        best_gpu = None
        best_cost = float('inf')
        
        vram_needed = model.vram_required_gb
        gpus_needed = model.gpu_count
        
        for provider, gpus in self.GPU_OFFERINGS.items():
            for gpu_type, config in gpus.items():
                if config["max_gpus"] >= gpus_needed:
                    total_vram = config["vram"] * gpus_needed
                    if total_vram >= vram_needed:
                        total_cost = config["cost"] * gpus_needed
                        if total_cost < best_cost:
                            best_cost = total_cost
                            best_provider = provider
                            best_gpu = gpu_type
        
        return best_provider, best_gpu, best_cost
    
    def provision_instance(self, model: ModelConfig) -> Optional[GPUConfig]:
        """Provision a GPU instance for a model"""
        provider, gpu_type, cost = self.get_cheapest_gpu_for_model(model)
        
        if not provider:
            print(f"No suitable GPU found for model {model.name}")
            return None
        
        self.instance_counter += 1
        instance_id = f"kerne-{provider}-{self.instance_counter}"
        
        gpu_config = GPUConfig(
            provider=provider,
            gpu_type=gpu_type,
            gpu_count=model.gpu_count,
            vram_per_gpu=self.GPU_OFFERINGS[provider][gpu_type]["vram"],
            cost_per_hour=cost,
            instance_id=instance_id,
            status="starting",
            models_loaded=[model.name],
        )
        
        self.active_instances[instance_id] = gpu_config
        
        print(f"Provisioning {model.gpu_count}x {gpu_type} on {provider} for {model.name}")
        print(f"Instance ID: {instance_id}, Cost: ${cost:.2f}/hr")
        
        # In production, this would call the provider API
        # For now, we simulate the provisioning
        gpu_config.status = "running"
        
        return gpu_config
    
    def deprovision_instance(self, instance_id: str):
        """Stop and remove a GPU instance"""
        if instance_id in self.active_instances:
            instance = self.active_instances[instance_id]
            instance.status = "stopping"
            print(f"Deprovisioning instance {instance_id}")
            print(f"Final stats - Revenue: ${instance.total_revenue:.2f}, Cost: ${instance.total_cost:.2f}")
            del self.active_instances[instance_id]
    
    def get_active_cost_per_hour(self) -> float:
        """Get total cost per hour of all active instances"""
        return sum(inst.cost_per_hour for inst in self.active_instances.values() 
                   if inst.status == "running")


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """Dynamic pricing based on market conditions"""
    
    # Market rate ranges (from OpenRouter data)
    MARKET_RATES = {
        "llama-3.1-8b": {"prompt": (0.10, 0.20), "completion": (0.20, 0.40)},
        "qwen-2.5-7b": {"prompt": (0.08, 0.15), "completion": (0.15, 0.30)},
        "mistral-7b": {"prompt": (0.08, 0.15), "completion": (0.15, 0.30)},
        "phi-4": {"prompt": (0.06, 0.12), "completion": (0.12, 0.25)},
        "qwen-2.5-72b": {"prompt": (0.50, 0.80), "completion": (1.00, 1.60)},
        "llama-3.1-70b": {"prompt": (0.40, 0.70), "completion": (0.80, 1.40)},
        "glm-5": {"prompt": (0.80, 1.50), "completion": (1.50, 3.00)},
        "llama-3.1-405b": {"prompt": (1.00, 2.00), "completion": (2.00, 4.00)},
    }
    
    def __init__(self):
        self.current_prices: Dict[str, Dict[str, float]] = {}
        self.competition_factor: Dict[str, float] = {}  # Lower = more competition
        self.demand_factor: Dict[str, float] = {}  # Higher = more demand
        
    def calculate_optimal_price(self, model: ModelConfig, 
                                 current_utilization: float,
                                 competitor_prices: Optional[List[float]] = None) -> Tuple[float, float]:
        """Calculate optimal pricing to maximize profit"""
        
        market = self.MARKET_RATES.get(model.name, 
                                       {"prompt": (0.10, 0.30), "completion": (0.20, 0.60)})
        
        # Base price: slightly below market average to attract traffic
        base_prompt = (market["prompt"][0] + market["prompt"][1]) / 2 * 0.9
        base_completion = (market["completion"][0] + market["completion"][1]) / 2 * 0.9
        
        # Adjust based on utilization
        if current_utilization < 0.3:
            # Low utilization - lower prices to attract traffic
            prompt_price = base_prompt * 0.85
            completion_price = base_completion * 0.85
        elif current_utilization > 0.7:
            # High utilization - raise prices (we're in demand)
            prompt_price = base_prompt * 1.15
            completion_price = base_completion * 1.15
        else:
            # Normal utilization - market rate
            prompt_price = base_prompt
            completion_price = base_completion
        
        # Ensure we stay within market bounds
        prompt_price = max(market["prompt"][0], min(market["prompt"][1], prompt_price))
        completion_price = max(market["completion"][0], min(market["completion"][1], completion_price))
        
        return prompt_price, completion_price
    
    def update_prices(self, models: Dict[str, ModelConfig]):
        """Update all model prices based on current conditions"""
        for name, model in models.items():
            prompt, completion = self.calculate_optimal_price(
                model, model.current_utilization
            )
            self.current_prices[name] = {
                "prompt": prompt,
                "completion": completion,
            }


# ============================================================================
# DEMAND MONITOR
# ============================================================================

class DemandMonitor:
    """Monitors OpenRouter demand and traffic patterns"""
    
    def __init__(self):
        self.request_history: List[Dict] = []
        self.model_demand: Dict[str, float] = {}  # requests per minute
        self.peak_hours: List[int] = [9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22]  # UTC
        self.current_demand_level = "medium"  # low, medium, high
        
    def record_request(self, model: str, tokens: int, timestamp: datetime = None):
        """Record an incoming request"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.request_history.append({
            "model": model,
            "tokens": tokens,
            "timestamp": timestamp,
        })
        
        # Update demand metrics
        self._update_demand_metrics()
    
    def _update_demand_metrics(self):
        """Calculate demand metrics from recent history"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        recent_requests = [r for r in self.request_history 
                          if r["timestamp"] > one_hour_ago]
        
        # Calculate requests per minute per model
        self.model_demand = {}
        for req in recent_requests:
            model = req["model"]
            if model not in self.model_demand:
                self.model_demand[model] = 0
            self.model_demand[model] += 1
        
        # Normalize to per-minute
        for model in self.model_demand:
            self.model_demand[model] /= 60
        
        # Determine overall demand level
        current_hour = now.hour
        if current_hour in self.peak_hours:
            self.current_demand_level = "high"
        elif 0 <= current_hour < 6:
            self.current_demand_level = "low"
        else:
            self.current_demand_level = "medium"
    
    def get_recommended_scaling(self) -> Dict[str, int]:
        """Get recommended number of instances per model"""
        recommendations = {}
        
        for model, demand in self.model_demand.items():
            # Scale based on demand level
            if self.current_demand_level == "high":
                scale_factor = 1.5
            elif self.current_demand_level == "low":
                scale_factor = 0.5
            else:
                scale_factor = 1.0
            
            # Base recommendation: 1 instance per 100 requests/minute
            base_instances = demand / 100
            recommended = max(1, int(base_instances * scale_factor))
            recommendations[model] = recommended
        
        return recommendations
    
    def predict_demand_next_hour(self) -> Dict[str, float]:
        """Predict demand for the next hour"""
        predictions = {}
        
        for model, current_demand in self.model_demand.items():
            # Simple prediction based on time of day
            next_hour = (datetime.now().hour + 1) % 24
            
            if next_hour in self.peak_hours:
                predictions[model] = current_demand * 1.3
            elif 0 <= next_hour < 6:
                predictions[model] = current_demand * 0.5
            else:
                predictions[model] = current_demand
        
        return predictions


# ============================================================================
# AUTO SCALER
# ============================================================================

class AutoScaler:
    """Automatically scales GPU resources based on demand"""
    
    def __init__(self, gpu_manager: GPUManager, demand_monitor: DemandMonitor):
        self.gpu_manager = gpu_manager
        self.demand_monitor = demand_monitor
        self.scaling_cooldown = 300  # 5 minutes between scaling actions
        self.last_scale_time = datetime.now() - timedelta(seconds=self.scaling_cooldown)
        self.min_instances = 1
        self.max_instances = 10
        self.target_utilization = 0.6  # 60%
        
    def evaluate_scaling(self, models: Dict[str, ModelConfig]) -> List[str]:
        """Evaluate whether to scale up or down"""
        actions = []
        
        # Check cooldown
        if (datetime.now() - self.last_scale_time).seconds < self.scaling_cooldown:
            return actions
        
        recommendations = self.demand_monitor.get_recommended_scaling()
        current_instances = len(self.gpu_manager.active_instances)
        
        for model_name, recommended_count in recommendations.items():
            model = models.get(model_name)
            if not model:
                continue
            
            current_model_instances = sum(
                1 for inst in self.gpu_manager.active_instances.values()
                if model_name in inst.models_loaded
            )
            
            if recommended_count > current_model_instances and current_instances < self.max_instances:
                # Scale up
                actions.append(f"SCALE_UP:{model_name}")
                self.gpu_manager.provision_instance(model)
                self.last_scale_time = datetime.now()
                
            elif recommended_count < current_model_instances and current_instances > self.min_instances:
                # Scale down
                for inst_id, inst in list(self.gpu_manager.active_instances.items()):
                    if model_name in inst.models_loaded:
                        actions.append(f"SCALE_DOWN:{model_name}:{inst_id}")
                        self.gpu_manager.deprovision_instance(inst_id)
                        self.last_scale_time = datetime.now()
                        break
        
        return actions


# ============================================================================
# PROFIT TRACKER
# ============================================================================

class ProfitTracker:
    """Tracks revenue, costs, and profit"""
    
    def __init__(self):
        self.daily_stats = {
            "revenue": 0.0,
            "cost": 0.0,
            "profit": 0.0,
            "tokens_processed": 0,
            "requests_handled": 0,
            "date": datetime.now().date(),
        }
        self.hourly_stats: List[Dict] = []
        self.model_stats: Dict[str, Dict] = {}
        
    def record_transaction(self, model: str, prompt_tokens: int, 
                          completion_tokens: int, prompt_rate: float,
                          completion_rate: float):
        """Record a completed inference transaction"""
        revenue = (prompt_tokens / 1_000_000 * prompt_rate + 
                   completion_tokens / 1_000_000 * completion_rate)
        
        # Update daily stats
        self.daily_stats["revenue"] += revenue
        self.daily_stats["tokens_processed"] += prompt_tokens + completion_tokens
        self.daily_stats["requests_handled"] += 1
        self.daily_stats["profit"] = self.daily_stats["revenue"] - self.daily_stats["cost"]
        
        # Update model stats
        if model not in self.model_stats:
            self.model_stats[model] = {
                "revenue": 0.0,
                "tokens": 0,
                "requests": 0,
            }
        self.model_stats[model]["revenue"] += revenue
        self.model_stats[model]["tokens"] += prompt_tokens + completion_tokens
        self.model_stats[model]["requests"] += 1
    
    def update_costs(self, cost_per_hour: float, hours_elapsed: float):
        """Update cost tracking"""
        self.daily_stats["cost"] = cost_per_hour * hours_elapsed
        self.daily_stats["profit"] = self.daily_stats["revenue"] - self.daily_stats["cost"]
    
    def get_report(self) -> str:
        """Generate a profit report"""
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║              KERNE INFERENCE PROFIT REPORT                   ║
║                    {datetime.now().strftime("%Y-%m-%d %H:%M")}                        ║
╠══════════════════════════════════════════════════════════════╣
║ DAILY SUMMARY                                                ║
║   Revenue:          ${self.daily_stats['revenue']:>10.2f}                      ║
║   Cost:             ${self.daily_stats['cost']:>10.2f}                      ║
║   ─────────────────────────────                              ║
║   NET PROFIT:       ${self.daily_stats['profit']:>10.2f}                      ║
║                                                              ║
║   Tokens Processed: {self.daily_stats['tokens_processed']:>12,}                    ║
║   Requests Handled: {self.daily_stats['requests_handled']:>12,}                    ║
╠══════════════════════════════════════════════════════════════╣
║ BY MODEL                                                     ║"""
        
        for model, stats in self.model_stats.items():
            report += f"""
║   {model:<20}                                        ║
║     Revenue: ${stats['revenue']:>8.2f}  Tokens: {stats['tokens']:>10,}          ║"""
        
        report += """
╚══════════════════════════════════════════════════════════════╝"""
        
        return report
    
    def save_to_file(self, filepath: str):
        """Save stats to JSON file"""
        data = {
            "daily": self.daily_stats,
            "models": self.model_stats,
            "timestamp": datetime.now().isoformat(),
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset_daily(self):
        """Reset daily stats (run at midnight)"""
        self.hourly_stats.append(self.daily_stats.copy())
        self.daily_stats = {
            "revenue": 0.0,
            "cost": 0.0,
            "profit": 0.0,
            "tokens_processed": 0,
            "requests_handled": 0,
            "date": datetime.now().date(),
        }


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class InferenceOrchestrator:
    """Main orchestrator that coordinates all components"""
    
    def __init__(self):
        self.models = ModelRegistry.get_all_models()
        self.gpu_manager = GPUManager()
        self.pricing_engine = PricingEngine()
        self.demand_monitor = DemandMonitor()
        self.auto_scaler = AutoScaler(self.gpu_manager, self.demand_monitor)
        self.profit_tracker = ProfitTracker()
        
        self.running = False
        self.start_time: Optional[datetime] = None
        
    def start(self):
        """Start the inference profit engine"""
        print("=" * 60)
        print("KERNE INFERENCE PROFIT ENGINE STARTING")
        print("=" * 60)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Deploy initial models (highest priority small models)
        initial_models = [
            self.models["llama-3.1-8b"],
            self.models["qwen-2.5-7b"],
        ]
        
        for model in initial_models:
            self.gpu_manager.provision_instance(model)
        
        print(f"\nInitial deployment: {len(self.gpu_manager.active_instances)} instances")
        print(f"Estimated hourly cost: ${self.gpu_manager.get_active_cost_per_hour():.2f}")
        
        # Main loop
        self._run_loop()
    
    def _run_loop(self):
        """Main operational loop"""
        while self.running:
            # Update costs
            hours_elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
            self.profit_tracker.update_costs(
                self.gpu_manager.get_active_cost_per_hour(),
                hours_elapsed
            )
            
            # Update pricing
            self.pricing_engine.update_prices(self.models)
            
            # Check scaling
            scaling_actions = self.auto_scaler.evaluate_scaling(self.models)
            if scaling_actions:
                print(f"Scaling actions: {scaling_actions}")
            
            # Print periodic report
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                print(self.profit_tracker.get_report())
            
            time.sleep(10)  # Check every 10 seconds
    
    def stop(self):
        """Stop the engine and generate final report"""
        self.running = False
        
        print("\n" + "=" * 60)
        print("KERNE INFERENCE PROFIT ENGINE STOPPING")
        print("=" * 60)
        
        # Generate final report
        print(self.profit_tracker.get_report())
        
        # Save stats
        self.profit_tracker.save_to_file("inference_stats.json")
        
        # Deprovision all instances
        for instance_id in list(self.gpu_manager.active_instances.keys()):
            self.gpu_manager.deprovision_instance(instance_id)
    
    def simulate_demand(self, duration_minutes: int = 60):
        """Simulate demand for testing"""
        print(f"\nSimulating {duration_minutes} minutes of demand...")
        
        for minute in range(duration_minutes):
            # Simulate varying request patterns
            import random
            
            for model_name in ["llama-3.1-8b", "qwen-2.5-7b"]:
                # Higher demand during peak hours
                current_hour = datetime.now().hour
                if current_hour in self.demand_monitor.peak_hours:
                    request_count = random.randint(50, 200)
                else:
                    request_count = random.randint(10, 50)
                
                for _ in range(request_count):
                    prompt_tokens = random.randint(100, 2000)
                    completion_tokens = random.randint(50, 1000)
                    
                    # Record demand
                    self.demand_monitor.record_request(model_name, prompt_tokens + completion_tokens)
                    
                    # Record transaction
                    prices = self.pricing_engine.current_prices.get(model_name, 
                                                                    {"prompt": 0.12, "completion": 0.25})
                    self.profit_tracker.record_transaction(
                        model_name, prompt_tokens, completion_tokens,
                        prices["prompt"], prices["completion"]
                    )
            
            # Update model utilization
            for model in self.models.values():
                model.current_utilization = random.uniform(0.2, 0.8)
            
            time.sleep(0.1)  # Speed up simulation
        
        print("Simulation complete.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    orchestrator = InferenceOrchestrator()
    
    try:
        # Start the engine
        orchestrator.start()
        
        # For demo, simulate demand instead of waiting for real requests
        # In production, remove this and let real requests flow
        orchestrator.simulate_demand(duration_minutes=5)
        
        # Keep running until interrupted
        while orchestrator.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        orchestrator.stop()


if __name__ == "__main__":
    main()