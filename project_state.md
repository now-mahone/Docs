## 2026-02-19 20:04 - Optimized 32x32 Risk Heatmap with Logarithmic Scaling
**Status**: ✅ Complete
**Action**: Optimized the Risk Heatmap visualization to improve color variance and data readability using logarithmic scaling and a refined temperature gradient.
**Changes Made**:
1. **Logarithmic Scaling**: Applied a log transform (`log1p`) to the scenario densities in `generate_heatmap.py`. This boosts the visibility of lower-density outcomes, creating a much richer color variance across the 32x32 grid.
2. **Refined Temperature Scale**: Implemented a smooth 6-color interpolation logic (Blue -> Cyan -> Green -> Yellow -> Orange -> Red) to represent the risk distribution more intuitively.
3. **High-Resolution Grid**: Maintained the 32x32 resolution (1,024 data points) for maximum granularity of the Monte Carlo v4 results.
4. **Data Fidelity**: Re-processed the 10,000 simulation scenarios to ensure the heatmap accurately reflects the relationship between Max Drawdown (0-15%) and APY (10-35%) with the new scaling logic.

## 2026-02-19 19:53 - High-Fidelity 32x32 Risk Heatmap
**Status**: ✅ Complete
**Action**: Upgraded the Risk Heatmap to a 32x32 resolution with a refined temperature gradient for institutional-grade data visualization.

## 2026-02-19 19:44 - Enhanced 2D Histogram Risk Heatmap
**Status**: ✅ Complete
**Action**: Upgraded the Risk Heatmap to a high-fidelity 25x25 2D histogram with a 7-color temperature gradient.

## 2026-02-19 19:28 - Implemented 2D Histogram Risk Heatmap
**Status**: ✅ Complete
**Action**: Replaced the static 10x10 heatmap with a data-driven 20x20 2D histogram based on the actual Monte Carlo v4 simulation results.

## 2026-02-19 19:18 - Standardized Monte Carlo Bento Box UI
**Status**: ✅ Complete
**Action**: Standardized the Monte Carlo Risk Simulation section to use the "gradient metric cards on black section card" pattern for site-wide consistency.
**Changes Made**:
1. **Container Logic**: Wrapped the Monte Carlo grid in a `bg-[#000000]` container with standard padding and spacing.
2. **Gradient Cards**: Updated all cards (Methodology, Metrics, and Heatmap) to use the `bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]` style.
3. **Visual Consistency**: Aligned the Monte Carlo section's internal architecture with the "Institutional Reliability" and "Bento Box" sections found elsewhere on the site.

## 2026-02-19 18:15 - Standardized Monte Carlo Scenario Cards
**Status**: ✅ Complete
**Action**: Standardized the Monte Carlo scenario breakdown cards to match the site-wide metric card style and added a fourth risk vector.
**Changes Made**:
1. **Style Alignment**: Converted the large scenario cards into the standard 4-column grid format used for metrics, ensuring section-wide visual consistency.
2. **Fourth Risk Vector**: Added "LST Depeg Events" (0.00% failure rate) to the breakdown, completing the 4-card row.
3. **Data Fidelity**: Updated failure rates to reflect v4 simulation results (Oracle: 0.00%, Exploit: 0.22%, Cascade: 0.05%, Depeg: 0.00%).
4. **Visual Cleanup**: Removed large icons and long paragraphs in favor of the clean "Label > Value > Status" architecture.

**Files Modified**: `frontend/src/app/transparency/page.tsx`
**Deployed to**: m-vercel remote

## 2026-02-19 18:05 - Updated Monte Carlo Simulation Metrics
**Status**: ✅ Complete
**Action**: Updated the Monte Carlo Risk Simulation metric cards on the transparency page with higher-fidelity results and improved risk reporting.
**Changes Made**:
1. **Survival Rate**: Updated to 99.73% (9,973/10,000 scenarios).
2. **Mean Yield**: Updated to 21.78% APY.
3. **Metric Swap**: Replaced "Mean Final TVL" with "Max Drawdown" (2.62%) to better reflect downside risk.
4. **VaR Update**: Switched from VaR 95 to VaR 99% ($86.77M) with a clearer description of capital preservation (86.77c per dollar).

**Files Modified**: `frontend/src/app/transparency/page.tsx`
**Deployed to**: m-vercel remote

## 2026-02-19 11:25 - Refactored Monte Carlo Section Layout
**Status**: ✅ Complete
**Action**: Refactored the Monte Carlo Risk Simulation section on the transparency page for better layout, spacing, and content clarity.
**Changes Made**:
1. **Spacing Standardization**: Updated the card container to use `space-y-4`, matching the spacing of the Bento Box section above.
2. **Methodology Card Refactor**: Converted the Simulation Methodology card into a clean header and paragraph format, removing the complex 4-column grid and extra elements.
3. **Card Reordering**: Moved the Simulation Methodology card to the top of the grid for better narrative flow.
4. **TVL Neutrality**: Removed all mentions of the initial $100M TVL to emphasize that the protocol's risk resilience is independent of specific TVL thresholds.
5. **Visual Consistency**: Maintained the `bg-gradient-to-b from-[#ffffff] to-[#d4dce1]` for the section background.

**Files Modified**: `frontend/src/app/transparency/page.tsx`
**Deployed to**: m-vercel remote

## 2026-02-19 19:55 - MC V4 RISK REPORT PUBLISHED + REPO CLEANUP
**Status**: ✅ Complete
**Action**: Created investor and website-ready risk report at docs/research/MONTE_CARLO_V4_RISK_REPORT.md with all verified v4 data (99.73% survival, 21.78% APY, VaR 99% $86.77M, 9-layer protection breakdown).
**Changes Made**:
1. **Report Creation**: Published `docs/research/MONTE_CARLO_V4_RISK_REPORT.md`.
2. **Cleanup**: Deleted stale Monte Carlo JSON results and superseded simulation scripts.
3. **Canonical Files**: Established `bot/kerne_monte_carlo_v4.py` and `bot/montecarlosimulation4feb19.json` as the primary references.

## 2026-02-18 13:05 - Standardized Transparency Page Background Gradients
**Status**: ✅ Complete
**Action**: Standardized the background logic for the Risk Management Framework section on the transparency page to match the site-wide design language.
**Changes Made**:
1. **Gradient Alignment**: Replaced the static `bg-[#f8fafc]` and top border with the standard `bg-gradient-to-b from-[#ffffff] to-[#d4dce1]` used in other sections.
2. **Visual Consistency**: Ensured the Risk Management section now flows seamlessly with the Hero and Yield Calculator sections found on the homepage and transparency page.
3. **Cleanup**: Removed the redundant `border-t border-[#e2e8f0]` to maintain the clean, modular section aesthetic.

**Files Modified**: `frontend/src/app/transparency/page.tsx`
**Deployed to**: m-vercel remote

## 2026-02-18 13:00 - Refactored Transparency Page Section Logic
**Status**: ✅ Complete
**Action**: Refactored the transparency page to use standard modular section logic, separating the Monte Carlo simulation and Risk Management Framework into distinct blocks.
**Changes Made**:
1. **Section Separation**: Isolated the "Monte Carlo Risk Simulation" and "Risk Management Framework" into independent sections with standard padding (`pt-32 pb-32`).
2. **Visual Distinction**: Applied a subtle background color (`bg-[#f8fafc]`) and top border to the Risk Management section to clearly differentiate it from the white Monte Carlo section.
3. **Design Consistency**: Aligned the page structure with the homepage and about page, removing the cascading gradients that previously merged sections together.

**Files Modified**: `frontend/src/app/transparency/page.tsx`
**Deployed to**: m-vercel remote

## 2026-02-17 16:26 - Rebranded "The Narrative Cartel" to "The Narrative Collective"
**Status**: ✅ Complete
**Action**: Rebranded all mentions of "The Narrative Cartel" to "The Narrative Collective" in the documentation for a more professional tone.
**Changes Made**:
1. **File Renaming**: Renamed `gitbook (docs)/strategy/narrative-cartel.md` to `narrative-collective.md`.
2. **Content Update**: Replaced "The Narrative Cartel" with "The Narrative Collective" in `_sidebar.md`, `SUMMARY.md`, `strategy/README.md`, and the renamed `narrative-collective.md`.

**Files Modified**: `gitbook (docs)/_sidebar.md`, `gitbook (docs)/SUMMARY.md`, `gitbook (docs)/strategy/README.md`, `gitbook (docs)/strategy/narrative-collective.md`
**Deployed to**: m-vercel remote

## Project Overview
Kerne is a delta-neutral synthetic dollar protocol, leveraging LST collateral and hedging to provide institutional grade yield and capital efficiency.