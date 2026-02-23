# Preface for Next Cline Session

**Copy and paste this into your next chat to provide context:**

---

## Previous Session Context (Feb 7, 2026)

We just completed updating the **Backtested Performance chart** on kerne.ai homepage. Here's what you need to know:

### What We Built
- **Chart Type:** Real-time ETH historical price chart with delta-neutral comparison
- **Data Source:** CoinGecko API for 1-year rolling window (365 daily data points)
- **Display:** X-axis labels every 2 months, 45° angles, daily granularity
- **Fallback:** Graceful degradation to hardcoded monthly data if API fails
- **Files:** `frontend/src/app/api/eth-history/route.ts` + `frontend/src/components/BacktestedPerformance.tsx`

### Git Repositories & Workflow
We work with **TWO remotes** that must stay in sync:

1. **origin** (Primary Dev)
   - URL: `https://github.com/enerzy17/kerne-feb-2026.git`
   - Owner: Scofield (enerzy17)

2. **m-vercel** (Deployment)
   - URL: `https://github.com/now-mahone/m-vercel.git`  
   - Owner: Mahone (now-mahone)
   - Requires `--force` push due to divergent history

**Standard commit workflow:**
```bash
git add -A
git commit -m "[2026-02-07] area: description"
git push origin main
git push m-vercel main --force
```

### Environment
- **OS:** Windows 11
- **Shell:** cmd.exe (NOT bash - use Windows commands)
- **Working Dir:** `d:\KERNE\kerne-feb`
- **Frontend:** Next.js 16, React 18, TypeScript, Tailwind CSS 4
- **Charts:** Recharts library
- **API:** Next.js Edge Runtime

### Important Notes
1. **TypeScript Errors:** IDE shows `JSX.IntrinsicElements` errors - these are non-blocking and resolve on server run
2. **Git Remotes:** ALWAYS push to both `origin` and `m-vercel`
3. **Windows Environment:** Use Windows-native commands (e.g., `type` not `cat`, backslashes in paths)
4. **Latest Commit:** 4cdde6d1 - "Changed chart to rolling 1-year window with daily data"

### Current State
- Chart fetches real ETH prices from CoinGecko (1 year rolling)
- Displays 365 daily data points with 2-month x-axis intervals
- All changes committed and pushed to both repositories
- Vercel deployment will auto-update from m-vercel push

---

**Full documentation:** See `docs/runbooks/CLINE_HANDOFF_2026_02_07_PART_2.md`