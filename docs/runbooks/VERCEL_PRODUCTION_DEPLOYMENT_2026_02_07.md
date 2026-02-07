// Created: 2026-02-07
# Vercel Production Deployment: kerne.ai → kerne-feb-2026

## Objective
Swap the `kerne.ai` production domain from the outdated Vercel project to the new February repository (`enerzy17/kerne-feb-2026`).

## Pre-requisites
- [x] Staging validated at `m-vercel.vercel.app`
- [x] Repository synchronized: commit `9ee9d019` on `enerzy17/kerne-feb-2026`
- [x] Vault address updated: `0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC`

## Method: Reconnect Existing Project

### Step 1: Log in to Vercel
Go to https://vercel.com/login and sign in with the account that owns the `kerne.ai` domain.

### Step 2: Identify the kerne.ai Project
- Go to https://vercel.com/dashboard
- Find the project with `kerne.ai` as its domain (may be named `kerne-protocol`, `kerne-vercel`, or similar)
- Click into the project

### Step 3: Update Connected Repository
1. Go to **Settings** → **Git**
2. Under "Connected Git Repository", click **Disconnect**
3. Click **Connect Git Repository**
4. Select **GitHub** → `enerzy17/kerne-feb-2026`
5. Confirm the connection

### Step 4: Verify Build Settings
1. Go to **Settings** → **General**
2. Set **Root Directory** to: `frontend`
3. Set **Framework Preset** to: `Next.js`
4. **Build Command**: `npm run build` (default)
5. **Output Directory**: `.next` (default)
6. **Install Command**: `npm install` (default)
7. Click **Save**

### Step 5: Trigger Deployment
1. Go to the **Deployments** tab
2. Click **Redeploy** on the latest deployment, OR
3. Push any commit to `enerzy17/kerne-feb-2026` main branch to trigger auto-deploy

### Step 6: Verify Domain
1. Go to **Settings** → **Domains**
2. Confirm `kerne.ai` and `www.kerne.ai` are listed
3. Verify DNS status shows ✅ (green checkmark)

### Step 7: Smoke Test
- Visit https://kerne.ai in an incognito window
- Verify the new February frontend loads (check for updated design, new vault address references)
- Test navigation: Home, Terminal, About, Transparency, Institutional pages

## Alternative Method: Domain Transfer (if different Vercel accounts)

If `kerne.ai` is on Scofield's Vercel and `m-vercel` is on Mahone's Vercel:

### On Scofield's Vercel:
1. Go to the old project → Settings → Domains
2. Remove `kerne.ai` and `www.kerne.ai`

### On Mahone's Vercel (m-vercel project):
1. Go to the m-vercel project → Settings → Domains
2. Add `kerne.ai`
3. Add `www.kerne.ai` (redirect to `kerne.ai`)
4. Vercel will show DNS configuration if needed
5. Since Vercel manages DNS, propagation should be near-instant

## DNS Configuration (if applicable)
If `kerne.ai` DNS is managed externally (not Vercel):
- A Record: `76.76.21.21`
- CNAME: `cname.vercel-dns.com`

## Rollback Plan
If the new deployment has issues:
- Revert the Git connection back to the old repository
- OR redeploy from the old project's deployment history

## Status
- [ ] Deployment executed
- [ ] kerne.ai verified live with new frontend
- [ ] project_state.md updated