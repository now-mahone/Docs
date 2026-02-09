# Kerne Protocol Documentation Repository Setup

This repository contains the official documentation for Kerne Protocol, built with Docsify.

## Repository Information
- **Organization:** kerne-protocol
- **Repository Name:** docs
- **Visibility:** Public
- **GitHub Pages URL:** https://kerne-protocol.github.io/docs
- **Custom Domain:** docs.kerne.ai (optional)

## Setup Instructions

### 1. Create the Repository on GitHub

1. Go to https://github.com/organizations/kerne-protocol/repositories/new
2. **Repository name:** `docs`
3. **Description:** "Official documentation for Kerne Protocol"
4. **Visibility:** **Public** (required for free GitHub Pages)
5. Click **"Create repository"**

### 2. Initialize and Push This Directory

From the root of your main Kerne project (`d:/KERNE/kerne-feb`), run:

```bash
cd "gitbook (docs)"
git init
git add -A
git commit -m "Initial documentation commit"
git branch -M main
git remote add origin https://github.com/kerne-protocol/docs.git
git push -u origin main
```

### 3. Enable GitHub Pages

1. Go to https://github.com/kerne-protocol/docs/settings/pages
2. Under **"Build and deployment"**:
   - **Source:** Select **"GitHub Actions"**
3. Click **"Save"**

The GitHub Actions workflow (`.github/workflows/deploy.yml`) will automatically deploy the documentation.

### 4. Verify Deployment

After the workflow runs (check the Actions tab), your documentation will be live at:
- **https://kerne-protocol.github.io/docs**

### 5. Optional: Configure Custom Domain

If you want to use `docs.kerne.ai`:

1. Add a CNAME record in your DNS provider:
   - **Type:** CNAME
   - **Name:** docs
   - **Value:** kerne-protocol.github.io
   - **TTL:** 3600 (or your provider's default)

2. In GitHub repository settings (Settings → Pages):
   - Under **"Custom domain"**, enter: `docs.kerne.ai`
   - Click **"Save"**
   - Wait for DNS check to complete (green checkmark)

## Updating Documentation

Once set up, any changes pushed to the `main` branch will automatically deploy via GitHub Actions.

From your main project directory:
```bash
cd "gitbook (docs)"
# Make your changes to .md files
git add -A
git commit -m "Update documentation"
git push origin main
```

The site will rebuild automatically within 1-2 minutes.

## Documentation Structure

- `index.html` - Docsify entry point
- `README.md` - Homepage content
- `_sidebar.md` - Navigation sidebar
- `SUMMARY.md` - Table of contents
- `/mechanisms` - Protocol mechanisms
- `/security` - Security documentation  
- `/strategy` - Strategy guides
- `/tokenomics` - Token economics

## Troubleshooting

**Workflow fails:** Check the Actions tab for error details
**404 errors:** Ensure GitHub Pages is enabled with "GitHub Actions" as source
**DNS issues:** DNS propagation can take up to 48 hours
**Build errors:** Validate markdown syntax and file paths