# Kerne Project State

## Latest Update
[2026-02-10 20:40] - Frontend: Fixed layout shift in hero APY animation by adding invisible placeholder (`opacity-0`) while data loads. Prevents content jumping during page load by maintaining the space before animation begins. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 20:35] - Frontend: Refined hero APY typed animation with slower, more deliberate timing (stagger 0.08s, duration 0.1s). Removed placeholder text so nothing displays until the animation begins, creating a cleaner reveal effect. `TypedText` component now accepts custom timing parameters for flexibility. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 20:30] - Frontend: Replaced hero APY count-up animation with character-by-character typed animation. Created `TypedText.tsx` component that preserves the CSS mesh gradient while displaying the APY value with typewriter effect. No more "starting from 0" logic - APY displays directly at its live value with typing animation. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 14:59] - Frontend: Increased `TypedHeading` animation speed (stagger 0.02s, duration 0.03s) for a snappier feel. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 14:48] - Frontend: Fixed layout shift in `TypedHeading` typewriter animation by removing `display: none`. Characters now maintain their space with `opacity: 0` before animating, preventing content jumping on mobile. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 14:08] - Frontend: Implemented Palantir-style character typewriter animations for all H2 headings across the site. Created reusable `TypedHeading` Framer Motion component and applied it to all major pages (Home, About, Transparency, Institutional) and global shared components (KerneExplained, BacktestedPerformance, KerneLive, FAQ). Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 13:46] - Frontend: Updated site titles and Open Graph metadata. Main title now "Kerne - The future of onchain yield" with description "Building the most capital efficient delta neutral infrastructure in DeFi." Added title template "%s - Kerne" for automatic page title formatting. Individual pages (About, Terminal, Transparency, Institutional) are client components and will display templated titles. Deployed to m-vercel. - Status: SUCCESS

[2026-02-10 13:34] - Frontend: Fixed Open Graph metadata domain - Changed from kerne.finance to kerne.ai and added metadataBase for proper URL resolution. Image URLs now use relative paths (/og-image.png) which resolve to https://kerne.ai/og-image.png. Deployed to m-vercel. NOTE: Social platforms cache OG images - may require cache clearing. - Status: SUCCESS

[2026-02-10 13:25] - Frontend: Added Open Graph/Twitter preview image (og-image.png) for social media link sharing. Copied KWL.png from root to frontend/public/og-image.png and updated layout.tsx metadata to use new image for Open Graph and Twitter cards (1200x630). Deployed to m-vercel. - Status: SUCCESS

[2026-02-09 18:13] - Frontend: Added favicon.svg to kerne.ai website. Copied kerne-favicon.svg from root to frontend/public/favicon.svg and updated layout.tsx metadata with icons configuration. Deployed to m-vercel remote for kerne.ai website. - Status: SUCCESS

[2026-02-09 15:02] - Terminal: Updated footer documentation link from `docs.kerne.ai` to `documentation.kerne.ai` to match the correct domain. All documentation links across the website now point to the unified documentation.kerne.ai domain. - Status: SUCCESS

[2026-02-09 14:42] - Frontend: Removed password gate (AccessGate component) from website. Deleted `AccessGate.tsx` component and `/access` page. Updated `layout.tsx` to remove authentication wrapper. Terminal and all pages now publicly accessible without access code. - Status: SUCCESS

[2026-02-09 14:33] - Documentation: Enabled history mode routing for Docsify documentation. Added `routerMode: 'history'` to remove hash (#/) from URLs. Created 404.html for GitHub Pages SPA routing support. URLs now display as `documentation.kerne.ai` instead of `documentation.kerne.ai/#/`. Currently deploying to now-mahone/Docs repository. - Status: IN PROGRESS

[2026-02-09 14:27] - Documentation: Updated documentation link to open in new tab. Modified Navbar.tsx to use external anchor tags with `target="_blank"` for documentation links on both desktop and mobile views. Footer already had target="_blank" configured. - Status: SUCCESS

[2026-02-09 14:22] - Documentation: Removed redirect page at `/documentation`. Updated Navbar and Footer to link directly to `https://documentation.kerne.ai`. Deployed GitBook documentation to `now-mahone/Docs` repository with custom domain. Added kerne-lockup.svg logo to GitBook sidebar (white-styled, left-aligned). Cleaned AI-style writing patterns from README. DNS configured at documentation.kerne.ai. - Status: SUCCESS

[2026-02-09 13:32] - Documentation: Prepared for kerne-protocol/docs repository deployment. Created GitHub Actions workflow and comprehensive setup guide in gitbook (docs) directory. Updated frontend redirect to point to kerne-protocol.github.io/docs. All documentation files ready for separate public repository under kerne-protocol organization. - Status: READY FOR DEPLOYMENT

[2026-02-09 13:15] - DOCUMENTATION FIX: Fixed broken `docs.kerne.ai` links that were causing "site can't be reached" errors. Root cause: GitBook documentation exists in `gitbook (docs)` but was never deployed. Created GitHub Pages deployment workflow (`.github/workflows/deploy-docs.yml`) and temporary redirect page (`/documentation`) that sends users to GitHub Pages URL until DNS is configured. Updated Navbar and Footer to use internal `/documentation` route temporarily. Next steps: Enable GitHub Pages in repository settings and configure DNS. - Status: SUCCESS

[2026-02-09 13:10] - CI/CD FIX: Removed yield-server-official phantom submodule from git index (was registered as mode 160000 with no .gitmodules entry, breaking actions/checkout@v4). Added to .gitignore. Also added Base Grant Submission guide. Pushed to both february and vercel remotes. - Status: SUCCESS

[Rest of file content remains exactly the same...]