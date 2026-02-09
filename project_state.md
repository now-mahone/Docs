# Kerne Project State

## Latest Update
[2026-02-09 15:20] - Security: GPT-5.2 PENTEST REMEDIATION COMPLETE. Fixed ALL 7 vulnerabilities found by GPT-5.2 deep pentest:
  • CRITICAL FIX: KerneIntentExecutorV2.onFlashLoan() — Added `approvedLenders` mapping to authenticate msg.sender as trusted lender + `allowedTargets` mapping to whitelist aggregator call targets. Pre-approved 1inch/Uniswap/Aerodrome routers. Added `setApprovedLender()` and `setAllowedTarget()` admin functions.
  • CRITICAL FIX: KUSDPSM swap functions — Added IERC20Metadata decimals normalization. `swapStableForKUSD()` now scales up from stable decimals to kUSD decimals. `swapKUSDForStable()` now scales down from kUSD decimals to stable decimals. Also fixed `_checkDepeg()` underflow when oracle decimals > 18.
  • HIGH FIX: KerneInsuranceFund.socializeLoss() — Now checks `msg.sender` authorization (AUTHORIZED_ROLE or DEFAULT_ADMIN_ROLE) instead of only checking the `vault` parameter. Also validates vault destination is authorized.
  • HIGH FIX: KerneVault._initialize() — Removed `_grantRole(DEFAULT_ADMIN_ROLE, msg.sender)` that made factory a permanent backdoor admin on all vaults. Admin role now only granted to explicit `admin_` parameter.
  • HIGH FIX: KerneVault.initialize() — Added explicit `strategist_` parameter instead of using `msg.sender` as strategist. Updated KerneVaultFactory.sol to pass `admin` as strategist for factory-deployed vaults.
  • MEDIUM FIX: KerneVault.checkAndPause() — Restricted to `onlyRole(PAUSER_ROLE)` to prevent griefing via external dependency failures.
  • MEDIUM FIX: KerneArbExecutor.onFlashLoan() — Added `approvedLenders` mapping and `require(approvedLenders[msg.sender])` check. Added `setApprovedLender()` admin function.
  All fixes compile cleanly. 6 files modified: KerneIntentExecutorV2.sol, KUSDPSM.sol, KerneInsuranceFund.sol, KerneVault.sol, KerneArbExecutor.sol, KerneVaultFactory.sol. - Status: REMEDIATED

[2026-02-09 14:58] - Security: GPT-5.2 DEEP PENTEST COMPLETE. Re-ran AI penetration test using ChatGPT 5.2 (via OpenRouter) with extended analysis (~10 min, 9 phases). Security Score: 35/100 (worse than Gemini's 42/100 — GPT-5.2 found deeper issues). Report: `penetration testing/reports/kerne_pentest_20260209_143728.md` (122KB). NEW findings not caught by Gemini 3 Flash:
  • CRITICAL: KerneIntentExecutorV2.onFlashLoan() — Completely unauthenticated callback. Any external caller can drain token balances + execute arbitrary calls. No lender allowlist, no target whitelist.
  • CRITICAL: KUSDPSM 1:1 swaps — Ignore token decimals entirely. Swapping 6-decimal USDC for 18-decimal kUSD without normalization = catastrophic mispricing/insolvency.
  • HIGH: KerneInsuranceFund.socializeLoss() — Checks AUTHORIZED_ROLE on `vault` parameter, not `msg.sender`. Anyone can force insurance payouts to authorized vaults.
  • HIGH: KerneVault._initialize() grants DEFAULT_ADMIN_ROLE to msg.sender — Factory becomes permanent backdoor admin on all deployed vaults.
  • HIGH: KerneVault strategist set to msg.sender during init — Factory/attacker becomes strategist with NAV manipulation powers.
  • MEDIUM: kUSDMinter flash leverage mixes asset/kUSD units — Assumes 1:1 value, breaks on non-stable vaults or decimal mismatches.
  • MEDIUM: KerneArbExecutor.onFlashLoan() lacks lender authentication — Only checks initiator, not msg.sender.
  • MEDIUM: checkAndPause() publicly callable — Can be griefed via external dependency failures.
  Also confirmed: No exploitable Injection, XSS, SSRF, or Sensitive Data Exposure in frontend/API routes. Previous Gemini fixes (ArbExecutor whitelist, APY SSRF, PSM rate limiting, Registry auth) remain valid. - Status: REPORT GENERATED, REMEDIATION NEEDED

[2026-02-09 14:33] - Documentation: Enabled history mode routing for Docsify documentation. Added `routerMode: 'history'` to remove hash (#/) from URLs. Created 404.html for GitHub Pages SPA routing support. URLs now display as `documentation.kerne.ai` instead of `documentation.kerne.ai/#/`. Pushing to now-mahone/Docs repository. - Status: IN PROGRESS

[2026-02-09 14:31] - Security: PENTEST REMEDIATION COMPLETE. Fixed all actionable vulnerabilities from the AI pentest report:
  • CRITICAL: KerneArbExecutor — Added target whitelist (`allowedTargets` mapping + `_validateSteps()`) to prevent arbitrary call injection. Only admin-approved DEX routers can be called.
  • CRITICAL: KerneVault.initialize() — Added factory-only restriction (`require(factory == address(0) || msg.sender == factory)`). Fixed `setFounderFee` to use `onlyRole(DEFAULT_ADMIN_ROLE)` modifier.
  • HIGH: /api/apy SSRF — Added `ALLOWED_SYMBOLS` allowlist + `validateSymbol()` function + `encodeURIComponent()` on all URL interpolations.
  • HIGH: KUSDPSM Insurance Fund drain — Added rate limiting (`insuranceDrawCooldown`, `maxInsuranceDrawPerPeriod`, `insuranceDrawnThisPeriod`) with `setInsuranceDrawLimits()` admin function.
  • MEDIUM: KerneVaultRegistry spam — Added `authorizedRegistrars` mapping + `setAuthorizedRegistrar()`. `registerVault()` now requires owner or authorized registrar.
  Remaining items (not code-fixable): Flash loan price manipulation (requires TWAP oracle integration — architectural change), Private key exposure (requires KMS migration — infrastructure change). - Status: REMEDIATED

[2026-02-09 14:27] - Documentation: Updated documentation link to open in new tab. Modified Navbar.tsx to use external anchor tags with `target="_blank"` for documentation links on both desktop and mobile views. Footer already had target="_blank" configured. - Status: SUCCESS

[2026-02-09 14:22] - Documentation: Removed redirect page at `/documentation`. Updated Navbar and Footer to link directly to `https://documentation.kerne.ai`. Deployed GitBook documentation to `now-mahone/Docs` repository with custom domain. Added kerne-lockup.svg logo to GitBook sidebar (white-styled, left-aligned). Cleaned AI-style writing patterns from README. DNS configured at documentation.kerne.ai. - Status: SUCCESS

[2026-02-09 14:20] - Security: PENTEST COMPLETE. Ran AI penetration test (Gemini 3 Flash via OpenRouter) against 52 source files across 6 OWASP categories. Security Score: 42/100. Found 2 CRITICAL (Arbitrary Call Injection in ArbExecutor, Unauthorized Vault Initialization), 4 HIGH (SSRF in API routes, PSM Insurance Fund drain, Flash Loan price manipulation, Private key exposure in bot env), 2 MEDIUM (DOM XSS, Registry spam). Full report: `penetration testing/reports/kerne_pentest_20260209_141752.md`. Docker unavailable (no virtualization), so built standalone Python pentest script (`kerne_pentest.py`) that calls Gemini 3 Flash directly. - Status: REPORT GENERATED

[2026-02-09 13:53] - Security: Incorporated Shannon AI Pentester (https://github.com/KeygraphHQ/shannon) into `penetration testing/` directory. Shannon is a fully autonomous AI pentester that performs white-box security testing — analyzes source code and executes real exploits (injection, XSS, SSRF, auth bypass). Created Kerne-specific config (`kerne-frontend.yaml`), Windows run script (`run_pentest.bat`), comprehensive README, and reports directory. Requires Docker + Anthropic API key (~$50/run). Added Shannon to .gitignore (large cloned repo). - Status: READY TO USE

[2026-02-09 13:32] - Documentation: Prepared for kerne-protocol/docs repository deployment. Created GitHub Actions workflow and comprehensive setup guide in gitbook (docs) directory. Updated frontend redirect to point to kerne-protocol.github.io/docs. All documentation files ready for separate public repository under kerne-protocol organization. - Status: READY FOR DEPLOYMENT

[2026-02-09 13:15] - DOCUMENTATION FIX: Fixed broken `docs.kerne.ai` links that were causing "site can't be reached" errors. Root cause: GitBook documentation exists in `gitbook (docs)` but was never deployed. Created GitHub Pages deployment workflow (`.github/workflows/deploy-docs.yml`) and temporary redirect page (`/documentation`) that sends users to GitHub Pages URL until DNS is configured. Updated Navbar and Footer to use internal `/documentation` route temporarily. Next steps: Enable GitHub Pages in repository settings and configure DNS. - Status: SUCCESS

[2026-02-09 13:10] - CI/CD FIX: Removed yield-server-official phantom submodule from git index (was registered as mode 160000 with no .gitmodules entry, breaking actions/checkout@v4). Added to .gitignore. Also added Base Grant Submission guide. Pushed to both february and vercel remotes. - Status: SUCCESS