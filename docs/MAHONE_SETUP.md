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
2.  Navigate to your `z:` drive (or wherever you keep your projects).
3.  Run the following command:
    ```bash
    git clone https://github.com/enerzy17/kerne-feb-2026.git kerne-main
    ```
4.  Open the new `kerne-main` folder in VS Code.

## 3. Daily Workflow

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