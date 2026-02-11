# Created: 2026-02-10
# Update all references from old vault to new hardened vault
import os

OLD = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"
NEW = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"

files = [
    "bot/capital_router.py",
    "bot/profit_telemetry.py",
    "bot/check_hl_status.py",
    "bot/daily_performance_report.py",
    "deploy_capital.py",
    "_quick_scan.py",
    "_verify_vaults.py",
    "verify_vault_v2.py",
    "_check_all_contracts.py",
    "seed_vault.py",
    "check_vault_assets.py",
    "check_protocol_balances.py",
]

updated = 0
for f in files:
    if not os.path.exists(f):
        print(f"  SKIP (not found): {f}")
        continue
    with open(f, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  UPDATED: {f}")
        updated += 1
    else:
        print(f"  no match: {f}")

print(f"\nDone. Updated {updated} files.")
print(f"Old: {OLD}")
print(f"New: {NEW}")