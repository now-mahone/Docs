import os

files_to_read = [
    "KERNE_GENESIS_NEW.md",
    "AGENTS.md",
    "docs/INVESTOR_READINESS_CHECKLIST.md",
    "docs/research/MONTE_CARLO_V4_RISK_REPORT.md",
    "docs/ABRUZZI_ACTION_PLAN.md",
    "docs/marketing/IMMEDIATE_EXECUTION_PLAN.md",
    "docs/investor/EXECUTIVE_SUMMARY.md",
    "docs/investor/SEED_INVESTOR_TARGETS.md",
    "docs/research/KERNE_PHILANTHROPY_INITIATIVE.md",
    "docs/research/ORACLE_UPGRADE_SUMMARY.md",
    "docs/research/RISK_MITIGATION_SPEC.md",
    "docs/runbooks/aggregator_submissions.md",
    "docs/runbooks/basis_trading_activation.md",
    "docs/runbooks/ZIN_SEEDING_STRATEGY.md",
    "bot/autonomous_outreach.py",
    "bot/engine.py",
    "bot/main.py",
    "bot/capital_router.py",
    "bot/basis_yield_monitor.py",
    "bot/sentinel_monitor.py",
    "bot/omni_orchestrator.py",
    "bot/oracle_updater.py",
    "bot/profit_telemetry.py",
    "bot/reporting_service.py",
    "bot/sovereign_vault.py",
    "bot/mev_protection.py",
    "bot/liquidity_manager.py",
    "bot/flash_arb_scanner.py",
    "bot/event_listener.py",
    "bot/daily_report.py",
    "bot/canary.py",
    "bot/alert_manager.py",
    "bot/arb_executor.py",
    "bot/apy_calculator.py",
    "bot/chain_manager.py",
    "bot/check_hl_status.py",
    "bot/credits_manager.py",
    "bot/daily_performance_report.py",
    "bot/daily_profit_report.py",
    "bot/email_manager.py",
    "bot/exchange_manager.py",
    "bot/gas_estimator.py",
    "bot/kerne_live_report.py",
    "bot/kerne_monte_carlo_v4.py",
    "bot/lead_scanner_v3.py",
    "bot/messenger.py",
    "bot/metrics.py",
    "bot/panic.py",
    "bot/por_attestation.py",
    "bot/por_automated.py",
    "bot/por_scheduler.py",
    "bot/router.py",
    "bot/telemetry_scheduler.py",
    "bot/test_exchange.py",
    "bot/verify_live.py",
    "src/KerneVault.sol",
    "src/KerneVaultFactory.sol",
    "src/KerneInsuranceFund.sol",
    "src/KerneIntentExecutorV2.sol",
    "src/KerneArbExecutor.sol",
    "src/KUSDPSM.sol"
]

count = 0
for f in files_to_read:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            print(f"--- {f} ---")
            print(content[:300])
            print("...\n")
            count += 1
        if count >= 55:
            break
print(f"Total files read: {count}")