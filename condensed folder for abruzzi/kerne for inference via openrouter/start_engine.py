# Created: 2026-02-12
# Kerne Inference Profit Engine - Startup Script

"""
Kerne Inference Profit Engine - One-Command Startup
====================================================

This script initializes and runs the complete inference profit engine.

Usage:
    python start_engine.py --mode [local|production|simulate]
    
Modes:
    local       - Run locally with simulated GPU (for testing)
    production  - Run with real GPU provisioning
    simulate    - Run simulation mode to test profitability
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

def setup_environment():
    """Setup environment variables and dependencies"""
    
    print("=" * 60)
    print("KERNE INFERENCE PROFIT ENGINE - ENVIRONMENT SETUP")
    print("=" * 60)
    
    # Check for required environment variables
    required_vars = ["HF_TOKEN"]
    optional_vars = [
        "RUNPOD_API_KEY", 
        "VAST_API_KEY", 
        "LAMBDA_API_KEY",
        "OPENROUTER_API_KEY"
    ]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {missing_required}")
        print("Set them with: export HF_TOKEN=your_token")
        return False
    
    print("\n✅ Required environment variables present")
    
    # Check optional variables
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        print(f"⚠️  Optional variables not set: {missing_optional}")
        print("Some GPU providers may not be available.")
    else:
        print("✅ All GPU provider API keys configured")
    
    # Check Python dependencies
    print("\nChecking Python dependencies...")
    try:
        import vllm
        print("✅ vLLM installed")
    except ImportError:
        print("❌ vLLM not installed. Run: pip install vllm")
        return False
    
    try:
        import transformers
        print("✅ transformers installed")
    except ImportError:
        print("❌ transformers not installed. Run: pip install transformers")
        return False
    
    try:
        import huggingface_hub
        print("✅ huggingface_hub installed")
    except ImportError:
        print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
        return False
    
    return True


def load_config(config_path: str = "config.json"):
    """Load configuration file"""
    
    if not Path(config_path).exists():
        print(f"❌ Config file not found: {config_path}")
        print("Using default configuration...")
        return None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"✅ Configuration loaded from {config_path}")
    return config


# ============================================================================
# LOCAL MODE (Testing)
# ============================================================================

def run_local_mode(config):
    """Run in local mode with simulated GPU"""
    
    print("\n" + "=" * 60)
    print("RUNNING IN LOCAL MODE (Simulated GPU)")
    print("=" * 60)
    
    from profit_engine import (
        InferenceOrchestrator, 
        ModelRegistry, 
        GPUManager
    )
    
    orchestrator = InferenceOrchestrator()
    
    print("\n📊 Available Models (by profitability priority):")
    models = ModelRegistry.get_all_models()
    for name, model in models.items():
        print(f"  {model.priority}. {name} ({model.parameters}) - ${model.cost_per_hour:.2f}/hr")
    
    print("\n🚀 Starting orchestrator...")
    orchestrator.running = True
    orchestrator.start_time = datetime.now()
    
    # Simulate 10 minutes of demand
    print("\n📈 Simulating 10 minutes of traffic...")
    orchestrator.simulate_demand(duration_minutes=10)
    
    # Show results
    print(orchestrator.profit_tracker.get_report())
    
    print("\n✅ Local mode complete!")


# ============================================================================
# SIMULATION MODE
# ============================================================================

def run_simulation_mode(config, duration_minutes: int = 60):
    """Run full simulation to estimate profitability"""
    
    print("\n" + "=" * 60)
    print("RUNNING IN SIMULATION MODE")
    print("=" * 60)
    
    from profit_engine import InferenceOrchestrator
    
    orchestrator = InferenceOrchestrator()
    
    print(f"\n📊 Simulating {duration_minutes} minutes of operation...")
    print("This will estimate potential daily profit.\n")
    
    orchestrator.running = True
    orchestrator.start_time = datetime.now()
    
    # Run simulation
    orchestrator.simulate_demand(duration_minutes=duration_minutes)
    
    # Calculate projected daily profit
    hours_elapsed = duration_minutes / 60
    hourly_profit = orchestrator.profit_tracker.daily_stats["profit"] / hours_elapsed
    daily_profit_projection = hourly_profit * 24
    
    print("\n" + "=" * 60)
    print("PROFITABILITY SIMULATION RESULTS")
    print("=" * 60)
    print(orchestrator.profit_tracker.get_report())
    print(f"\n📈 PROJECTIONS:")
    print(f"  Hourly Profit: ${hourly_profit:.2f}")
    print(f"  Projected Daily Profit: ${daily_profit_projection:.2f}")
    print(f"  Projected Monthly Profit: ${daily_profit_projection * 30:.2f}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if daily_profit_projection >= 100:
        print("  ✅ Excellent! This configuration is highly profitable.")
        print("  Recommendation: Deploy to production immediately.")
    elif daily_profit_projection >= 50:
        print("  ✅ Good. This configuration is profitable.")
        print("  Recommendation: Deploy and optimize pricing.")
    elif daily_profit_projection >= 20:
        print("  ⚠️  Marginal profit. Consider:")
        print("  - Lower cost GPU providers")
        print("  - Higher pricing during peak hours")
    else:
        print("  ❌ Not profitable with current configuration.")
        print("  Recommendation: Focus on small models only.")
    
    return daily_profit_projection


# ============================================================================
# PRODUCTION MODE
# ============================================================================

def run_production_mode(config):
    """Run in production mode with real GPU provisioning"""
    
    print("\n" + "=" * 60)
    print("RUNNING IN PRODUCTION MODE")
    print("=" * 60)
    
    print("\n⚠️  PRODUCTION MODE WILL:")
    print("  1. Provision real GPU instances (charges apply)")
    print("  2. Download models to GPU instances")
    print("  3. Start vLLM servers")
    print("  4. Register with OpenRouter")
    print("  5. Begin serving real requests")
    
    confirm = input("\nProceed with production deployment? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return
    
    from profit_engine import InferenceOrchestrator
    
    orchestrator = InferenceOrchestrator()
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        orchestrator.stop()


# ============================================================================
# QUICK DEPLOY (One-command setup)
# ============================================================================

def quick_deploy():
    """Quick deploy - minimal setup for immediate profit"""
    
    print("\n" + "=" * 60)
    print("QUICK DEPLOY - FASTEST PATH TO PROFIT")
    print("=" * 60)
    
    print("""
This will deploy:
  - 1x RTX 4090 on RunPod ($0.34/hr)
  - Llama 3.1 8B model
  - Basic monitoring

Expected profit: $30-60/day at 40-60% utilization
""")
    
    # Check prerequisites
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        hf_token = input("Enter your HuggingFace token: ").strip()
        os.environ["HF_TOKEN"] = hf_token
    
    print("\n📋 Deployment Steps:")
    print("1. Provisioning RTX 4090 on RunPod...")
    print("   → Go to https://runpod.io and create RTX 4090 instance")
    print("   → Select 'PyTorch' template")
    print("   → Note the instance IP address")
    
    instance_ip = input("\nEnter your RunPod instance IP: ").strip()
    
    print("\n2. Connecting to instance...")
    print(f"   ssh root@{instance_ip}")
    
    print("\n3. Running deployment script on instance...")
    print("   Copy and paste these commands:")
    print("-" * 40)
    
    deploy_commands = f"""
# Install vLLM
pip install vllm huggingface_hub

# Authenticate with HuggingFace
huggingface-cli login --token {hf_token}

# Start Llama 3.1 8B server
python -m vllm.entrypoints.openai.api_server \\
    --model meta-llama/Llama-3.1-8B-Instruct \\
    --host 0.0.0.0 --port 8000 \\
    --dtype auto --max-model-len 8192 \\
    --gpu-memory-utilization 0.9
"""
    print(deploy_commands)
    print("-" * 40)
    
    print("\n4. Configure OpenRouter:")
    print("   → Go to https://openrouter.ai/providers")
    print(f"   → Add endpoint: http://{instance_ip}:8000/v1")
    print("   → Set model: meta-llama/llama-3.1-8b-instruct")
    print("   → Set pricing: Prompt $0.12/M, Completion $0.25/M")
    
    print("\n✅ Quick deploy setup complete!")
    print("📊 Monitor your profit with: python monitor.py")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kerne Inference Profit Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_engine.py --mode simulate --duration 30
    python start_engine.py --mode local
    python start_engine.py --mode production
    python start_engine.py --quick-deploy
"""
    )
    
    parser.add_argument(
        "--mode", 
        choices=["local", "production", "simulate"],
        default="simulate",
        help="Operating mode"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in minutes for simulation mode"
    )
    
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--quick-deploy",
        action="store_true",
        help="Run quick deploy wizard"
    )
    
    args = parser.parse_args()
    
    # Quick deploy mode
    if args.quick_deploy:
        quick_deploy()
        return
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Load config
    config = load_config(args.config)
    
    # Run in selected mode
    if args.mode == "local":
        run_local_mode(config)
    elif args.mode == "simulate":
        run_simulation_mode(config, args.duration)
    elif args.mode == "production":
        run_production_mode(config)


if __name__ == "__main__":
    main()