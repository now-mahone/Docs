# Created: 2026-02-19
"""
Monte Carlo Simulation Paths Visualization (Tilted 90 Degrees)
==============================================================

Creates a visualization of multiple Monte Carlo simulation paths,
tilted 90 degrees so that:
- TOP: Starting point (all iterations begin here)
- RIGHT SIDE: Best case scenarios (high TVL)
- LEFT SIDE: Worst case scenarios (low TVL/ruin)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import json

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.facecolor'] = '#f4f4f8'
plt.rcParams['axes.facecolor'] = '#eaeaf2'

def load_latest_results():
    """Load the most recent simulation results"""
    results_files = list(Path('..').glob('monte_carlo_results_*.json'))
    if not results_files:
        return None
    
    latest = max(results_files, key=lambda x: x.stat().st_mtime)
    with open(latest, 'r') as f:
        return json.load(f)

def generate_simulated_paths(n_paths=500, n_steps=365, initial_tvl=100):
    """Generate simulated TVL paths for visualization if full path data isn't available"""
    np.random.seed(42)
    
    # Time array
    t = np.linspace(0, 1, n_steps)
    dt = 1 / n_steps
    
    # Parameters for Geometric Brownian Motion
    mu = 0.15  # Expected return
    sigma = 0.4  # Volatility
    
    paths = np.zeros((n_paths, n_steps))
    paths[:, 0] = initial_tvl
    
    # Generate paths
    for i in range(n_paths):
        # 99.8% survival rate
        if np.random.random() > 0.998:
            # Failure path
            failure_step = np.random.randint(30, n_steps - 30)
            
            # Normal growth until failure
            for j in range(1, failure_step):
                dW = np.random.normal(0, np.sqrt(dt))
                paths[i, j] = paths[i, j-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW)
            
            # Sudden drop at failure
            paths[i, failure_step] = paths[i, failure_step-1] * np.random.uniform(0.1, 0.4)
            
            # Stagnation/slow bleed after failure
            for j in range(failure_step + 1, n_steps):
                paths[i, j] = paths[i, j-1] * np.random.uniform(0.95, 1.02)
                
        else:
            # Survival path
            for j in range(1, n_steps):
                dW = np.random.normal(0, np.sqrt(dt))
                paths[i, j] = paths[i, j-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW)
                
    return paths

def create_tilted_paths_chart(output_path):
    """Create the tilted Monte Carlo paths visualization"""
    
    # Generate paths (using 500 paths for visual clarity, similar to the reference image)
    n_paths = 500
    n_steps = 250  # Match the reference image x-axis
    paths = generate_simulated_paths(n_paths=n_paths, n_steps=n_steps)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Time array
    time_steps = np.arange(n_steps)
    
    # Plot each path
    # We swap x and y to tilt the chart 90 degrees
    # x = TVL (horizontal axis)
    # y = Time (vertical axis, inverted so time flows downwards)
    
    for i in range(n_paths):
        # Use a colormap to match the reference image style exactly
        color = plt.cm.tab10(i % 10)
        alpha = 0.7
        
        # Plot with swapped axes: x=TVL, y=Time
        # We use -time_steps so time flows from top (0) to bottom (-250)
        ax.plot(paths[i, :], -time_steps, color=color, alpha=alpha, linewidth=1.5)
    
    # Formatting to match reference image
    ax.set_xlim(0, 1000)
    ax.set_ylim(-250, 0)
    
    # Remove labels and title to match the clean look of the reference image
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    
    # Clean up ticks
    ax.set_yticks([0, -50, -100, -150, -200, -250])
    ax.set_yticklabels(['0', '50', '100', '150', '200', '250'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_path}")

def main():
    print("=" * 60)
    print("MONTE CARLO TILTED PATHS GENERATOR")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path('monte_carlo_charts')
    output_dir.mkdir(exist_ok=True)
    
    # Generate visualization
    print("\nGenerating tilted paths visualization...")
    create_tilted_paths_chart(output_dir / 'monte_carlo_paths_tilted.png')
    
    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()