# CAD to ETH Privacy Blueprint (The "LTC Tunnel")

**Created:** 2026-02-02
**Author:** Kerne Architect
**Target:** Scofield
**Objective:** Transfer 5,000 - 10,000 CAD from BMO to ETH.
**Constraints:** Maximize Privacy, Minimize Fees (Target 99% Retention).

---

## 1. Executive Summary

**The Trilemma:** You cannot have *Zero KYC*, *Zero Fees*, and *High Liquidity* simultaneously.
- **Bisq (No KYC):** High fees (4-8% premium). Violates retention goal.
- **Direct Exchange (Kraken/Newton):** Low fees (<1%), but Full KYC. Violates privacy goal.

**The Solution:** **The "LTC Tunnel" Strategy.**
We utilize a low-fee Canadian on-ramp for the initial fiat-to-crypto conversion (accepting the initial KYC hit), then immediately "wash" the trail using a dual-swap through Monero (XMR) via non-custodial aggregators.

**Projected Metrics:**
- **Capital Retention:** ~98.2% - 98.8% (Cost: ~1.2% - 1.8%)
- **Privacy Level:** High (On-chain link broken via XMR).
- **Time:** ~1-2 Hours.

---

## 2. The Blueprint (Step-by-Step)

### Phase 1: The Acquisition (Low Fee On-Ramp)
*Objective: Convert CAD to Crypto with minimal spread.*

1.  **Platform:** Use **Newton** or **Kraken**.
    *   *Why:* Lowest spreads in Canada for CAD pairs.
    *   *Note:* BMO will see a transfer to this entity. This is unavoidable for <2% fees.
2.  **Action:**
    *   Send CAD via **Interac e-Transfer** (Free).
    *   Buy **Litecoin (LTC)**.
    *   *Why LTC?* Lower transfer fees than BTC/ETH and faster confirmations.
3.  **Withdrawal:**
    *   Withdraw LTC to a self-custody wallet (e.g., **Exodus** or **Cake Wallet**).
    *   *Do NOT* send directly to the swap service. Always withdraw to your own wallet first.

### Phase 2: The "Wash" (The Monero Tunnel)
*Objective: Break the on-chain link between your identity and the final ETH.*

1.  **Tool:** **Cake Wallet** (Mobile) or **Trocador.app** (Desktop/Tor).
    *   *Trocador* is an aggregator of non-KYC exchanges.
2.  **Step A (LTC -> XMR):**
    *   In Cake Wallet/Trocador, swap **LTC** for **Monero (XMR)**.
    *   *Privacy:* The exchange sees LTC coming in and XMR going out, but XMR is untraceable on-chain.
3.  **Step B (The Hop):**
    *   Move the XMR to a **new** sub-address within your Monero wallet.
    *   *Crucial:* Never swap back immediately from the same address. Move it once internally (churn).

### Phase 3: The Destination (XMR -> ETH)
*Objective: Acquire ETH with no history.*

1.  **Step C (XMR -> ETH):**
    *   Use **Trocador** or **Houdini Swap** to swap your **XMR** for **Ethereum (ETH)**.
    *   **Destination:** Input a **FRESH** Ethereum address (generated on a hardware wallet like Trezor/Ledger or a fresh MetaMask).
    *   *Warning:* Do NOT send this ETH to an address that has ever interacted with your KYC'd exchanges (Coinbase, Newton, etc.).

---

## 3. Fee Breakdown (Estimated)

| Step | Action | Fee/Spread | Retention |
| :--- | :--- | :--- | :--- |
| 1 | BMO -> Newton (Interac) | $0.00 | 100% |
| 2 | CAD -> LTC (Newton Spread) | ~0.70% | 99.30% |
| 3 | LTC Network Fee | ~$0.01 | 99.30% |
| 4 | LTC -> XMR (Swap Spread) | ~0.50% | 98.80% |
| 5 | XMR Network Fee | ~$0.01 | 98.80% |
| 6 | XMR -> ETH (Swap Spread) | ~0.50% | 98.30% |
| **Total** | **Final ETH Received** | **~1.7% Cost** | **~98.3%** |

*Note: To achieve strictly >99% retention, you would need to skip the XMR privacy hop (LTC -> ETH direct swap), but this leaves a probabilistic link that sophisticated chain analysis could potentially de-anonymize.*

---

## 4. Operational Security (OpSec) Checklist

- [ ] **VPN:** Always active (Mulvad or ProtonVPN) when accessing Trocador/Exchanges.
- [ ] **Browser:** Use Brave or Tor Browser for the swap services.
- [ ] **Wallets:**
    -   Intermediate: Cake Wallet (Mobile) or Exodus.
    -   Final: Hardware Wallet (Ledger/Trezor) - **Brand New Seed Phrase recommended**.
- [ ] **BMO:** Do not mention "Crypto" in any bank notes.

## 5. Emergency Hatch (If 100% Privacy is paramount over Fees)
If you absolutely cannot have BMO know you bought crypto:
1.  Withdraw Cash.
2.  Use a **Bitcoin ATM** (HoneyBadger/Localcoin).
3.  **Cost:** 10% - 20% fees. (Not recommended due to capital loss).
4.  **Alternative:** Buy a prepaid Visa with Cash -> Buy Crypto on non-KYC platform (High failure rate, high fees).

**Recommendation:** Stick to the **LTC Tunnel**. The government knowing you *bought* $10k of crypto is not illegal. The privacy comes from them not knowing *where it went* or *what you did with it* afterwards.