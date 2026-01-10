# Kerne Backup & Deployment Blueprint

## 1. Vercel Deployment Process

### First-Time Setup (For Mr. Mahone)
Git remotes are local to your machine. If you just cloned the repo, you need to add the Vercel remote manually:
```bash
git remote add vercel https://github.com/enerzy17/kerne-protocol.git
```

### How to Deploy
The frontend is linked to the `vercel` remote. To push changes to Vercel:

1. **Ensure you are on the main branch:**
   ```bash
   git checkout main
   ```
2. **Push to the vercel remote:**
   ```bash
   git push vercel main
   ```
*Note: Vercel will automatically detect the push and start the deployment build.*

### CRITICAL: Vercel Project Settings
Because the Kerne repository is a monorepo, you **MUST** configure the following in the Vercel Dashboard:
1. **Root Directory:** Set this to `frontend`.
2. **Framework Preset:** Next.js.
3. **Build Command:** `npm run build` (default).
4. **Output Directory:** `.next` (default).

If the Root Directory is not set to `frontend`, the deployment will fail or show an empty page.

---

## 2. The "Triple-Lock" Backup Strategy

### Lock 1: Feature Branching (Prevention)
Never work directly on `main` for complex features.
- Create a branch: `git checkout -b feature/mahone-frontend-update`
- Merge to `main` only when tested.

### Lock 2: Private Repo Sync (Redundancy)
The `private` remote is our primary vault.
- **Scofield/Mahone Rule:** Always `git push private main` at the end of a session.
- This ensures that even if one machine dies, the other can pull the latest state.

### Lock 3: Manual Snapshots (The "Nuclear" Option)
In case of a "fatal fuck up" where Git history itself is corrupted or confusing:
- We will maintain a `backups/` directory (ignored by git to save space, or kept locally).
- **Action:** Run the backup command before any major architectural shift.

---

## 3. Emergency Recovery Procedure
If the code is "unfixable":
1. **Git Revert:** `git reset --hard HEAD~1` (Goes back one commit).
2. **Branch Restore:** Delete the broken branch and pull from `private main`.
3. **Manual Restore:** Replace the `src` or `frontend` folder with the latest manual snapshot.

## 4. Automated Backup Command
You can run this in the terminal to create a timestamped zip of the entire project (excluding node_modules and heavy libs):
```bash
powershell -Command "Compress-Archive -Path frontend, src, bot, script, test, project_state.md -DestinationPath 'backups/kerne_backup_$(Get-Date -Format yyyyMMdd_HHmm).zip'"
```
