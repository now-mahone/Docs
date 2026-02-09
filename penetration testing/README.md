# Created: 2026-02-09
# Kerne Protocol — Penetration Testing

## Overview

This directory contains the security penetration testing infrastructure for Kerne Protocol. We use **Shannon** (https://github.com/KeygraphHQ/shannon), a fully autonomous AI pentester that performs white-box security testing by analyzing source code and executing real exploits against running applications.

Shannon delivers actual exploits, not just alerts. It autonomously hunts for attack vectors in the codebase, then uses its built-in browser to execute real attacks (injection, auth bypass, XSS, SSRF) to prove vulnerabilities are exploitable.

---

## Directory Structure

```
penetration testing/
├── README.md                          # This file
├── shannon/                           # Shannon AI Pentester (cloned repo)
│   ├── configs/
│   │   ├── kerne-frontend.yaml        # Kerne frontend pentest config
│   │   └── example-config.yaml        # Shannon example config
│   ├── repos/                         # Target repos go here (created at runtime)
│   └── ...                            # Shannon core files
└── reports/                           # Pentest reports output directory
```

---

## Prerequisites

1. **Docker Desktop** — Must be installed and running
   - Download: https://docs.docker.com/desktop/install/windows-install/
   - Ensure WSL2 backend is enabled

2. **OpenRouter API Key** — Required for Shannon's AI engine (Gemini 3 Flash)
   - Get from: https://openrouter.ai/keys
   - Model: `google/gemini-3-flash-preview` (configured in `router-config.json`)
   - Cost: Significantly cheaper than Claude (~$2-5 per full run)
   - Alternative: Anthropic API key also supported (see Shannon docs)

---

## Quick Start

### Step 1: Set Up Credentials

```bash
cd "penetration testing/shannon"

# Create .env file with your OpenRouter API key (for Gemini 3 Flash)
echo OPENROUTER_API_KEY=your-openrouter-key-here > .env
```

> Get your OpenRouter key at https://openrouter.ai/keys
> The router is pre-configured to use `google/gemini-3-flash-preview` in `configs/router-config.json`

### Step 2: Prepare the Kerne Repository for Scanning

Shannon expects target repos in its `./repos/` directory. Copy the Kerne source code there:

```bash
# From the kerne-main root directory:
mkdir -p "penetration testing/shannon/repos/kerne-protocol"

# Copy frontend source (primary web attack surface)
xcopy /E /I frontend "penetration testing\shannon\repos\kerne-protocol\frontend"

# Copy smart contract source (for code-aware analysis)
xcopy /E /I src "penetration testing\shannon\repos\kerne-protocol\src"

# Copy API routes and bot (server-side attack surface)
xcopy /E /I bot "penetration testing\shannon\repos\kerne-protocol\bot"

# Copy SDK
xcopy /E /I sdk "penetration testing\shannon\repos\kerne-protocol\sdk"
```

### Step 3: Start the Local Frontend (Target)

Shannon needs a running application to test against. Start the Kerne frontend locally:

```bash
# In a separate terminal:
cd frontend
npm run dev
# Frontend will be available at http://localhost:3000
```

### Step 4: Run the Pentest

```bash
cd "penetration testing/shannon"

# Run against local frontend with Kerne config (Gemini 3 Flash via Router Mode)
./shannon start URL=http://host.docker.internal:3000 REPO=kerne-protocol CONFIG=./configs/kerne-frontend.yaml OUTPUT=../reports ROUTER=true
```

Or use the one-click Windows script from the `penetration testing/` directory:
```bash
cd "penetration testing"
run_pentest.bat frontend
```

> **Note:** Use `host.docker.internal` instead of `localhost` because Shannon runs inside Docker containers.

### Step 5: Monitor Progress

```bash
# View real-time logs
./shannon logs

# Open Temporal Web UI for detailed monitoring
start http://localhost:8233
```

### Step 6: Stop Shannon

```bash
# Stop containers (preserves data)
./shannon stop

# Full cleanup
./shannon stop CLEAN=true
```

---

## Test Targets

### 1. Frontend (Primary Target)
- **URL:** `http://host.docker.internal:3000` (local) or `https://kerne.ai` (production — STAGING ONLY)
- **Config:** `configs/kerne-frontend.yaml`
- **Attack Surface:**
  - Next.js API routes (`/api/stats`, `/api/apy`)
  - Terminal page (user input handling)
  - Wallet connection flow
  - Documentation redirect
  - Server-side rendering injection vectors

### 2. Smart Contracts (Code Analysis Only)
- Shannon performs white-box source code analysis on Solidity contracts
- Located in `repos/kerne-protocol/src/`
- Identifies potential reentrancy, access control, and logic flaws
- Note: Shannon cannot execute on-chain exploits — use Foundry fuzzing for that

### 3. Bot/API (Future Target)
- The hedging engine API endpoints
- Exchange connector authentication flows
- Webhook/callback handlers

---

## Vulnerability Categories Tested

| Category | Description | Kerne Relevance |
|----------|-------------|-----------------|
| **Injection** | SQL/NoSQL/Command injection | API routes, data fetching |
| **XSS** | Cross-site scripting | Terminal page, user inputs |
| **SSRF** | Server-side request forgery | API routes fetching external data |
| **Broken Auth** | Authentication/authorization bypass | Wallet-gated features, admin routes |

---

## Important Warnings

> ⚠️ **NEVER run Shannon against production (kerne.ai) without explicit authorization.**
> Shannon executes real exploits that can mutate data and trigger unintended side effects.

> ⚠️ **Always test against local development or staging environments.**

> ⚠️ **Windows Defender may flag Shannon's exploit reports as malware.**
> These are false positives. Add an exclusion for the `penetration testing` directory.

---

## Cost Estimates

| Run Type | Duration | Estimated Cost (Gemini 3 Flash) |
|----------|----------|--------------------------------|
| Full pentest (all categories) | 1-1.5 hours | ~$2-5 USD |
| Single category (e.g., XSS only) | 20-30 min | ~$0.50-1 USD |

> **Note:** Costs are dramatically lower with Gemini 3 Flash vs Claude 4.5 Sonnet (~$50). Shannon marks Router Mode as **EXPERIMENTAL**, but Gemini 3 Flash has proven capable for security analysis tasks.

---

## Report Archive

All pentest reports are saved to the `reports/` directory with timestamps. Reports include:
- Executive summary of findings
- Detailed vulnerability descriptions
- Reproducible proof-of-concept exploits (copy-paste ready)
- Severity ratings (Critical/High/Medium/Low)
- Remediation recommendations

---

## Integration with Kerne Security Pipeline

Shannon complements the existing Kerne security infrastructure:

1. **Foundry Fuzzing** (`forge test`) — Smart contract invariant testing
2. **Shannon** — Web application penetration testing
3. **Sentinel Monitor** (`bot/sentinel_monitor.py`) — Runtime anomaly detection
4. **Circuit Breakers** — Automated on-chain risk management

Together, these form a defense-in-depth security posture covering:
- Static analysis (Solidity compilation + linting)
- Dynamic testing (Foundry fuzzing + Shannon exploitation)
- Runtime monitoring (Sentinel + circuit breakers)
- Incident response (Panic module + insurance fund)