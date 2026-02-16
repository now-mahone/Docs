# Created: 2026-02-12
# Kerne OpenRouter Inference Provider - Profit Monitor

import time
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import subprocess

# Try to import psutil, fallback if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not installed. Some metrics unavailable.")


@dataclass
class InferenceMetrics:
    """Track inference provider metrics"""
    start_time: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_errors: int = 0
    
    # Pricing (per million tokens)
    prompt_rate: float = 0.15  # $/M tokens
    completion_rate: float = 0.30  # $/M tokens
    
    # GPU costs
    hourly_gpu_cost: float = 0.34  # RTX 4090 on RunPod
    
    def calculate_revenue(self) -> float:
        """Calculate total revenue in USD"""
        prompt_revenue = (self.total_prompt_tokens / 1_000_000) * self.prompt_rate
        completion_revenue = (self.total_completion_tokens / 1_000_000) * self.completion_rate
        return prompt_revenue + completion_revenue
    
    def calculate_costs(self) -> float:
        """Calculate total GPU costs in USD"""
        hours_elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
        return hours_elapsed * self.hourly_gpu_cost
    
    def calculate_profit(self) -> float:
        """Calculate net profit in USD"""
        return self.calculate_revenue() - self.calculate_costs()
    
    def get_utilization(self) -> float:
        """Estimate utilization percentage based on tokens processed"""
        # Rough estimate: RTX 4090 can do ~100 tokens/sec
        # At 50% utilization = 4.32M tokens/hour
        hours_elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
        if hours_elapsed == 0:
            return 0.0
        tokens_per_hour = (self.total_prompt_tokens + self.total_completion_tokens) / hours_elapsed
        max_tokens_per_hour = 4_320_000  # 100 tokens/sec * 3600 * 12 (prompt + completion)
        return min(100.0, (tokens_per_hour / max_tokens_per_hour) * 100)


class InferenceMonitor:
    """Monitor inference server and track profits"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.metrics = InferenceMetrics()
        self.config = self._load_config(config_path)
        self.log_file = self.config.get("log_file", "inference_metrics.json")
        
        # Load existing metrics if available
        self._load_metrics()
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from file"""
        default_config = {
            "log_file": "inference_metrics.json",
            "prompt_rate": 0.15,
            "completion_rate": 0.30,
            "hourly_gpu_cost": 0.34,
            "vllm_port": 8000,
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_metrics(self):
        """Load metrics from previous session"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.metrics.total_requests = data.get("total_requests", 0)
                    self.metrics.total_prompt_tokens = data.get("total_prompt_tokens", 0)
                    self.metrics.total_completion_tokens = data.get("total_completion_tokens", 0)
                    self.metrics.total_errors = data.get("total_errors", 0)
                    if "start_time" in data:
                        self.metrics.start_time = datetime.fromisoformat(data["start_time"])
            except Exception as e:
                print(f"Could not load metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file"""
        data = {
            "start_time": self.metrics.start_time.isoformat(),
            "total_requests": self.metrics.total_requests,
            "total_prompt_tokens": self.metrics.total_prompt_tokens,
            "total_completion_tokens": self.metrics.total_completion_tokens,
            "total_errors": self.metrics.total_errors,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_request(self, prompt_tokens: int, completion_tokens: int):
        """Record a completed inference request"""
        self.metrics.total_requests += 1
        self.metrics.total_prompt_tokens += prompt_tokens
        self.metrics.total_completion_tokens += completion_tokens
        self.save_metrics()
    
    def record_error(self):
        """Record an error"""
        self.metrics.total_errors += 1
        self.save_metrics()
    
    def get_gpu_info(self) -> dict:
        """Get GPU information using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                return {
                    "gpu_name": parts[0],
                    "memory_used_gb": float(parts[1]) / 1024,
                    "memory_total_gb": float(parts[2]) / 1024,
                    "gpu_utilization": float(parts[3]),
                }
        except Exception as e:
            print(f"Could not get GPU info: {e}")
        return {}
    
    def check_server_health(self, port: int = 8000) -> bool:
        """Check if vLLM server is healthy"""
        try:
            import urllib.request
            url = f"http://localhost:{port}/health"
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def get_status_report(self) -> str:
        """Generate a status report"""
        gpu_info = self.get_gpu_info()
        server_healthy = self.check_server_health(self.config.get("vllm_port", 8000))
        
        hours_elapsed = (datetime.now() - self.metrics.start_time).total_seconds() / 3600
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          KERNE INFERENCE PROVIDER STATUS                     ║
╠══════════════════════════════════════════════════════════════╣
║ Uptime: {hours_elapsed:.2f} hours
║ Server Status: {'✅ HEALTHY' if server_healthy else '❌ UNHEALTHY'}
╠══════════════════════════════════════════════════════════════╣
║ TOKENS                                                       ║
║   Prompt Tokens:     {self.metrics.total_prompt_tokens:>12,}                    
║   Completion Tokens: {self.metrics.total_completion_tokens:>12,}                    
║   Total Tokens:      {self.metrics.total_prompt_tokens + self.metrics.total_completion_tokens:>12,}                    
║   Total Requests:    {self.metrics.total_requests:>12,}                    
║   Errors:            {self.metrics.total_errors:>12,}                    
╠══════════════════════════════════════════════════════════════╣
║ FINANCIALS                                                   ║
║   Revenue:           ${self.metrics.calculate_revenue():>10.2f}                    
║   GPU Costs:         ${self.metrics.calculate_costs():>10.2f}                    
║   ─────────────────────────────                              ║
║   NET PROFIT:        ${self.metrics.calculate_profit():>10.2f}                    
╠══════════════════════════════════════════════════════════════╣
║ PERFORMANCE                                                  ║
║   Est. Utilization:  {self.metrics.get_utilization():>10.1f}%                    
║   Tokens/Hour:       {(self.metrics.total_prompt_tokens + self.metrics.total_completion_tokens) / max(0.01, hours_elapsed):>12,.0f}                    
║   Hourly Revenue:    ${self.metrics.calculate_revenue() / max(0.01, hours_elapsed):>10.2f}                    
║   Hourly Profit:     ${self.metrics.calculate_profit() / max(0.01, hours_elapsed):>10.2f}                    
╚══════════════════════════════════════════════════════════════╝
"""
        
        if gpu_info:
            report += f"""
GPU INFO:
  GPU: {gpu_info.get('gpu_name', 'Unknown')}
  Memory: {gpu_info.get('memory_used_gb', 0):.1f}GB / {gpu_info.get('memory_total_gb', 0):.1f}GB
  GPU Utilization: {gpu_info.get('gpu_utilization', 0):.1f}%
"""
        
        return report
    
    def get_daily_projection(self) -> str:
        """Project daily earnings based on current performance"""
        hours_elapsed = (datetime.now() - self.metrics.start_time).total_seconds() / 3600
        
        if hours_elapsed < 0.1:
            return "Not enough data for projection (need at least 6 minutes of data)"
        
        hourly_profit = self.metrics.calculate_profit() / hours_elapsed
        daily_profit = hourly_profit * 24
        
        return f"""
DAILY PROJECTION (based on {hours_elapsed:.1f} hours of data):
  Projected Daily Revenue:  ${self.metrics.calculate_revenue() / hours_elapsed * 24:.2f}
  Projected Daily Cost:     ${self.metrics.hourly_gpu_cost * 24:.2f}
  Projected Daily Profit:   ${daily_profit:.2f}
  Monthly Profit (30 days): ${daily_profit * 30:.2f}
"""


def main():
    """Main monitoring loop"""
    print("Kerne Inference Monitor Starting...")
    print("=" * 50)
    
    monitor = InferenceMonitor()
    
    # Print initial status
    print(monitor.get_status_report())
    
    # Interactive mode
    print("\nCommands: [s]tatus, [p]rojection, [r]eset, [q]uit")
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 's' or cmd == 'status':
                print(monitor.get_status_report())
            elif cmd == 'p' or cmd == 'projection':
                print(monitor.get_daily_projection())
            elif cmd == 'r' or cmd == 'reset':
                monitor.metrics = InferenceMetrics()
                monitor.save_metrics()
                print("Metrics reset!")
            elif cmd == 'q' or cmd == 'quit':
                break
            else:
                print("Unknown command. Use: s, p, r, q")
    except KeyboardInterrupt:
        print("\nExiting...")
    
    print("\nFinal Status:")
    print(monitor.get_status_report())


if __name__ == "__main__":
    main()