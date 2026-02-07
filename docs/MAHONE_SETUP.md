# Mahone Setup Guide: February 2026 Repository

**Date:** 2026-02-06
**Objective:** Switch from USB transfers to Git Sync.

We have established a new private repository for February to handle our day-to-day synchronization. This replaces the need for manual folder transfers.

## 1. The New Workflow
Instead of using a USB drive:
- **Scofield** pushes code to GitHub.
- **Mahone** pulls code from GitHub.

## 2. Initial Setup (Do this ONCE)
Since Scofield has merged all the latest work into a unified folder, your current local folder is likely outdated. The safest way to sync is to start fresh from the new repository.

### Step A: Backup Old Folder
1.  Close VS Code and any terminals.
2.  Rename your current `kerne-main` folder to `kerne-backup-jan`.

### Step B: Clone New Repository
1.  Open a terminal (PowerShell or Command Prompt).
2.  **Authenticate:** If you haven't already, run `gh auth login` to ensure you have access to the private repo.
3.  Navigate to your `d:\KERNE` drive (or your preferred location).
4.  Run the following command (choose HTTPS or SSH):
    
    **HTTPS:**
    ```bash
    git clone https://github.com/enerzy17/kerne-feb-2026.git kerne-main
    ```
    
    **SSH:**
    ```bash
    git clone git@github.com:enerzy17/kerne-feb-2026.git kerne-main
    ```
5.  Open the new `kerne-main` folder in VS Code.

### Step C: Restore Local Config (CRITICAL)
Since `.env` files are not tracked in Git, you must copy them from your backup:
1.  Copy `kerne-backup-jan/.env` -> `kerne-main/.env`
2.  Copy `kerne-backup-jan/bot/.env` -> `kerne-main/bot/.env`
3.  **Install Dependencies:**
    *   Root: `npm install`
    *   Contracts: `forge build`
    *   Bot: `pip install -r bot/requirements.txt`

### Step D: Git Identity
Ensure your commits are correctly attributed:
```bash
git config user.name "Mahone"
git config user.email "your-github-email@example.com"
```

## 3. Daily Workflow

### The "Memory" Protocol
At the end of every successful task, you **MUST** update `project_state.md` in the root.
Format: `[YYYY-MM-DD HH:MM] - Action Taken - Status`

### Start of Day (Get latest changes)
Before you start working, always run:
```bash
git pull origin main
```
*(Note: When you clone, the default remote is named `origin`. Scofield calls it `february`, but for you it will be `origin` by default unless you rename it).*

### End of Day (Save your work)
When you are finished:
```bash
git add .
git commit -m "[2026-02-XX] frontend: description of work"
git push origin main
```

## 4. Troubleshooting
If `git push` fails because Scofield pushed something while you were working:
1.  Run `git pull origin main` to get his changes.
2.  If there are merge conflicts, Cline can help you resolve them.
3.  Once resolved, run `git push origin main` again.

## 5. Monthly Rotation
To keep the history clean, we rotate repositories every month (e.g., `kerne-march-2026`). Scofield will handle the creation of the new repo and update the `AGENTS.md` instructions. When this happens, you will simply need to add the new remote or clone the new repo as instructed.
