import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import os

def calculate_apy(leverage, funding_rate_annual, staking_yield, spread_cost=0.001, perf_fee=0.10, insurance_fee=0.10):
    """
    The 'Huge Equation' for Kerne APY.
    
    APY = (1 + (Net_Daily_Yield / 365))^365 - 1
    
    Net_Daily_Yield = (Gross_Yield * (1 - Fees))
    Gross_Yield = (Leverage * Funding) + Staking - Spread
    """
    # Gross Annual Yield
    gross_yield = (leverage * funding_rate_annual) + staking_yield - spread_cost
    
    # Net Annual Yield (after fees)
    net_yield = gross_yield * (1 - perf_fee - insurance_fee)
    
    # Compounded APY (assuming daily compounding for simplicity in this visualization, 
    # though the protocol compounds per block/hour)
    apy = (1 + net_yield / 365) ** 365 - 1
    return apy

def main():
    # Load backtest data for context
    try:
        with open('bot/analysis/backtest_results_18m.json', 'r') as f:
            data = json.load(f)
            avg_funding_period = data['funding_stats']['avg_funding_rate']
            # Convert 8-hour funding to annual
            avg_funding_annual = avg_funding_period * 3 * 365
            print(f"Historical Avg Annual Funding: {avg_funding_annual:.2%}")
    except FileNotFoundError:
        avg_funding_annual = 0.10 # Default 10% if file missing

    # Generate Grid
    leverage_range = np.linspace(1, 10, 50)
    funding_range = np.linspace(0.0, 0.50, 50) # 0% to 50% annual funding
    
    L, F = np.meshgrid(leverage_range, funding_range)
    
    # Staking yield constant at 3.5%
    S = 0.035
    
    # Calculate Z (APY)
    Z = calculate_apy(L, F, S)
    
    # Plotting
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(L, F, Z, cmap='viridis', edgecolor='none', alpha=0.8)
    
    ax.set_xlabel('Leverage (x)')
    ax.set_ylabel('Annual Funding Rate')
    ax.set_zlabel('Net APY')
    ax.set_title('Kerne Protocol: APY Surface\n(Leverage vs. Funding Sensitivity)')
    
    # Add color bar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    
    # Save plot
    output_path = 'docs/reports/apy_3d_surface.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"3D Graph saved to {output_path}")
    
    # Output the Equation
    equation = (
        "$$"
        "APY(L, F, S) = \\left(1 + \\frac{(L \\cdot F_{annual} + S_{annual} - C_{spread}) \\cdot (1 - P_{fee} - I_{ins})}{365}\\right)^{365} - 1"
        "$$"
    )
    print("\nTHE HUGE EQUATION:")
    print(equation)
    
    # Calculate specific point for current config (3x, historical funding)
    current_apy = calculate_apy(3.0, avg_funding_annual, 0.035)
    print(f"\nBacktested 18m APY (3x Leverage): {current_apy:.2%}")

if __name__ == "__main__":
    main()