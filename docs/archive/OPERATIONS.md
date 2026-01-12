# KERNE MASTER OPERATIONS MANUAL

**Date:** 2025-12-29
**Status:** PRODUCTION READY

---

## 1. System Architecture Overview
Kerne consists of three primary layers:
1.  **Smart Contracts (Base):** `KerneVault.sol` (ERC-4626) handles user deposits, withdrawals, and share accounting.
2.  **Hedging Engine (Python):** An autonomous bot that manages delta-neutral short positions on CEXs (Binance/Bybit).
3.  **Frontend (Next.js):** An institutional-grade interface for users to interact with the vault and view transparency metrics.

## 2. Bot Operations & Maintenance

### 2.1. Bot Refill Procedure
The bot requires ETH for gas to report `offChainAssets` to the vault.
-   **Threshold:** If bot balance < 0.005 ETH, an alert is triggered.
-   **Action:** Send 0.05 ETH to the bot wallet address (found in `bot/.env` as `PRIVATE_KEY`'s public address).

### 2.2. Restarting the Engine
If the bot crashes or requires an update:
```bash
cd bot
docker-compose down
docker-compose up -d --build
```

## 3. Emergency Procedures (Runbooks)

### 3.0. CI/CD & Permission Loops (Lessons Learned)
- **Issue:** AccessControl errors during automated deployments/tests.
- **Cause:** Factory contracts attempting post-deployment calls on clones without having the required roles (e.g., `DEFAULT_ADMIN_ROLE`).
- **Solution:** Refactor `initialize()` functions to accept all configuration parameters (fees, whitelists, etc.) in a single atomic transaction. This removes the need for the factory to have elevated permissions after the clone is created.

### 3.1. Emergency Pause
In case of a smart contract exploit or extreme market volatility:
-   **Command:** Use the `Panic` script or call `pause()` via the Multisig on Basescan.
-   **Effect:** Disables `deposit`, `withdraw`, `mint`, and `redeem`.

### 3.2. Depeg Event (wstETH/ETH < 0.98)
-   **Action:** Unwind the strategy. Close CEX shorts and swap wstETH for ETH.
-   **Reference:** See `docs/runbooks/DEPEG_EVENT.md`.

### 3.3. Exchange Halt / Insolvency
-   **Action:** Migrate hedge to on-chain venues (GMX/Synthetix).
-   **Reference:** See `docs/runbooks/EXCHANGE_HALT.md`.

## 4. White-Label Deployment
To deploy a new partner vault:
1.  Run `script/Deploy.s.sol` with the partner's specific parameters.
2.  Initialize a new `bot` instance with the new `VAULT_ADDRESS`.
3.  Configure the partner's frontend environment variables.

## 5. Key Contacts & Resources
-   **Team:**
    -   **Scofield (INTP):** Lead Architect / Founder
    -   **Mahone (ISFP):** Core Contributor
-   **Multisig Address:** [See docs/smart_contract_arch.md]
-   **Bot Wallet:** [See bot/.env]
-   **Alerts Channel:** Discord Webhook [See bot/.env]

---

## 6. Genesis Sequence (The Launch)
To launch the protocol with the Seed TVL strategy:

1.  **Deploy Contracts:**
    ```bash
    forge script script/Deploy.s.sol --rpc-url $RPC_URL --broadcast --verify
    ```
2.  **Initial Seed Deposit:**
    -   Deposit 1 ETH into the Vault via the Terminal.
3.  **Initialize Bot (Genesis Mode):**
    ```bash
    cd bot
    python main.py --seed-only
    ```
    *This sets the `offChainAssets` to the target seed amount ($375k).*
4.  **Mint kUSD & Seed Liquidity:**
    -   Use the Terminal to lock kLP and mint kUSD.
    -   Provide kUSD/USDC liquidity on Aerodrome.
5.  **Start Production Bot:**
    ```bash
    docker-compose up -d --build
    ```

---
**Kerne Protocol: Autonomous. Delta-Neutral. Yield-Bearing.**
