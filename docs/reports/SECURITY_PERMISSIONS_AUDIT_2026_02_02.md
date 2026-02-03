# Kerne Protocol: Security & Permissions Audit
**Date:** 2026-02-02
**Status:** FINAL
**Objective:** Define the "Trezor Moat" and verify that no single point of failure (bot or hacker) can drain the protocol's core wealth.

## 1. The Hierarchy of Power

| Entity | Role | Access Level | Key Storage |
| :--- | :--- | :--- | :--- |
| **Scofield (Owner)** | `DEFAULT_ADMIN_ROLE` | **Absolute.** Can change any parameter, withdraw all funds, and revoke bot access. | Trezor (Cold) |
| **Kerne Bot** | `STRATEGIST_ROLE` | **Operational.** Can only update reports, execute hedges, and fulfill ZIN intents. | Server .env (Hot) |
| **Sentinel** | `PAUSER_ROLE` | **Defensive.** Can only pause the protocol. Cannot move funds. | Server .env (Hot) |

## 2. Asset Isolation (The "Trezor Moat")

### A. Core Wealth (Trezor/Multisig)
*   **Location:** Main Ethereum/Base wallets.
*   **Bot Access:** **WATCH-ONLY.**
*   **Hacker Risk:** ZERO. Even if the bot server is compromised, the hacker cannot sign transactions for these funds.
*   **Movement:** Requires physical interaction with Scofield's Trezor.

### B. Operational Capital (Hot Wallet)
*   **Location:** Bot's execution wallet (`0x57D4...0A99`).
*   **Bot Access:** Full (for gas and ZIN liquidity).
*   **Hacker Risk:** MODERATE. A hacker could steal the gas and small ZIN liquidity.
*   **Defense:** We keep < 5% of total TVL in this wallet.

### C. Exchange Reserve (Hyperliquid/Binance)
*   **Location:** Exchange sub-accounts.
*   **Bot Access:** API-based trading and whitelisted withdrawals.
*   **Hacker Risk:** LOW.
*   **Defense:** 
    1. **IP Whitelisting:** API keys only work from the bot's server IP.
    2. **Withdrawal Whitelisting:** The exchange is configured to ONLY allow withdrawals to Scofield's verified on-chain addresses. A hacker cannot send funds to their own wallet.

## 3. Smart Contract Circuit Breakers

The following logic is hardcoded into `KerneVault.sol` and `ChainManager.py`:

1.  **Deviation Block:** Any report of off-chain assets that changes by >20% in a single cycle is automatically rejected by the contract.
2.  **Rate Limiting:** Withdrawals from the vault are subject to a 24-hour buffer if they exceed the `withdrawalBuffer` threshold.
3.  **Emergency Pause:** Scofield can pause the entire protocol from his phone/Trezor at any time, instantly killing the bot's ability to trade.

## 4. Conclusion
The system is designed for **Sovereign Automation**. The bot has the "Hands" to work and make money, but Scofield keeps the "Brain" (Admin keys) and the "Heart" (Core Wealth) behind a physical hardware barrier.

**Verdict:** IMPLEMENTATION RECOMMENDED. The security architecture successfully isolates the bot's operational risks from the protocol's core wealth.