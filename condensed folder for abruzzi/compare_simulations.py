import json

# Compare 1st and 2nd simulation (both 10,000 runs)
files = [
    ('monte_carlo_results_20260217_121102.json', '1st Run (Previous)'),
    ('monte_carlo_results_20260217_115537.json', '2nd Run (Latest)')
]

for filename, label in files:
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        summary = data['analysis']
        survivor = summary.get('survivor_stats', {})
        
        survival_rate = summary['survival_rate'] * 100 if summary['survival_rate'] < 1 else summary['survival_rate']
        
        print("=" * 60)
        print(f"MONTE CARLO SIMULATION - {label}")
        print("=" * 60)
        print(f"Simulations: {summary['total_simulations']:,}")
        print(f"Survived: {summary['survival_count']:,}")
        print(f"Failed: {summary['failure_count']:,}")
        print(f"Survival Rate: {survival_rate:.2f}%")
        print(f"Mean Final TVL: ${survivor.get('mean_final_tvl', 0)/1e6:.2f}M")
        print(f"Median Final TVL: ${survivor.get('median_final_tvl', 0)/1e6:.2f}M")
        print(f"Mean Yield: ${survivor.get('mean_yield', 0)/1e6:.2f}M")
        print(f"Mean Min CR: {survivor.get('mean_min_cr', 0):.2f}")
        print(f"Mean Max Drawdown: {survivor.get('mean_max_drawdown', 0):.2f}%")
        print(f"VaR 95: ${summary.get('var_95', 0)/1e6:.2f}M")
        print(f"VaR 99: ${summary.get('var_99', 0)/1e6:.2f}M")
        
        print("\nFailure Breakdown:")
        for reason, count in summary.get('failure_reasons', {}).items():
            pct = (count / summary['failure_count'] * 100) if summary['failure_count'] > 0 else 0
            print(f"  {reason}: {count} ({pct:.1f}%)")
        print()
        
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")