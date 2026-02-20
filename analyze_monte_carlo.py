import json

# Read the most recent Monte Carlo results
with open('monte_carlo_results_20260217_115537.json', 'r') as f:
    data = json.load(f)

summary = data['analysis']

print("=" * 60)
print("MONTE CARLO SIMULATION RESULTS (2nd Run)")
print("=" * 60)
print(f"\nSimulations: {summary['total_simulations']:,}")
print(f"Survived: {summary['survival_count']:,}")
print(f"Failed: {summary['failure_count']:,}")
# Survival rate is stored as decimal (0.9906), convert to percentage
survival_rate = summary['survival_rate'] * 100 if summary['survival_rate'] < 1 else summary['survival_rate']
print(f"Survival Rate: {survival_rate:.2f}%")

# Survivor stats
survivor = summary.get('survivor_stats', {})
print(f"\n--- SURVIVOR STATISTICS ---")
print(f"Mean Final TVL: ${survivor.get('mean_final_tvl', 0)/1e6:.2f}M")
print(f"Mean Yield Generated: ${survivor.get('mean_yield_generated', 0)/1e6:.2f}M")
print(f"Mean APY: {survivor.get('mean_apy', 0):.2f}%")
print(f"Mean Max Drawdown: {survivor.get('mean_max_drawdown', 0):.2f}%")

# Print all survivor stats keys to see what's available
print(f"\nSurvivor stats keys: {list(survivor.keys())}")

print("\n" + "=" * 60)
print("FAILURE BREAKDOWN")
print("=" * 60)
failure_reasons = summary.get('failure_reasons', {})
total_failures = summary['failure_count']
for reason, count in failure_reasons.items():
    pct = (count / total_failures * 100) if total_failures > 0 else 0
    print(f"{reason}: {count} ({pct:.1f}%)")

print("\n" + "=" * 60)
print("RISK METRICS")
print("=" * 60)
print(f"VaR 95: ${summary.get('var_95', 0)/1e6:.2f}M")
print(f"VaR 99: ${summary.get('var_99', 0)/1e6:.2f}M")

# Failure stats
failure_stats = summary.get('failure_stats', {})
if failure_stats:
    print(f"\n--- FAILURE STATISTICS ---")
    print(f"Mean Failure Day: {failure_stats.get('mean_failure_day', 'N/A'):.1f}")
    print(f"Mean TVL at Failure: ${failure_stats.get('mean_tvl_at_failure', 0)/1e6:.2f}M")
    print(f"Failure stats keys: {list(failure_stats.keys())}")