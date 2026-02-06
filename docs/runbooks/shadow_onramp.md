# Runbook: Shadow On-Ramp (Capital Efficient & Private)

**Objective:** Transfer $2,000 from BMO (Fiat) to Kerne Treasury (Base Network) with maximum capital efficiency and on-chain privacy.
**Author:** Kerne Architect
**Date:** 2026-02-04

---

## 1. The Strategy: "The Polygon Tunnel"

To balance **Capital Efficiency** (low fees) with **Privacy** (breaking the on-chain link), we utilize a hybrid approach. We use a compliant, high-speed Canadian stablecoin rail for the fiat leg, and a privacy-preserving cross-chain swap for the crypto leg.

**The Route:**
`BMO (CAD)` -> `PayTrie (USDC on Polygon)` -> `Houdini Swap (Privacy Layer)` -> `Kerne Wallet (USDC on Base)`

### Why this route?
1.  **BMO -> PayTrie:** Interac e-Transfer is instant and free. PayTrie has the tightest CAD/USDC spread (~0.5%) and supports direct stablecoin minting.
2.  **Polygon:** Lowest withdrawal fees from PayTrie (< $0.10).
3.  **Houdini Swap:** Acts as a mixer. It receives your USDC on Polygon, swaps via Monero (XMR) backend, and dispenses clean USDC on Base to the destination address. This breaks the deterministic link between your KYC'd PayTrie account and the Kerne Treasury.

---

## 2. Execution Steps

### Phase 1: The Fiat Bridge (BMO -> PayTrie)
*Target Time: 15 Minutes*

1.  **Login to PayTrie:** Ensure your account is active. (*Note: Account registered with ProtonMail*).
2.  **Initiate Trade:**
    -   **Buy:** USDC.
    -   **Network:** Polygon (MATIC).
    -   **Amount:** $2,000 CAD (or USD equivalent).
    -   **Wallet Address:** Use your personal "Burner" wallet (Metamask/Rabby). **DO NOT** send directly to the final Kerne Treasury yet.
3.  **Send Funds:**
    -   Open BMO App.
    -   Send Interac e-Transfer to the email provided by PayTrie.
    -   *Note:* BMO may flag >$2k. If so, confirm via SMS/Call immediately.
4.  **Wait:** Funds usually arrive in your Burner Wallet (Polygon) within 10-20 minutes.

### Phase 2: The Privacy Tunnel (Polygon -> Base)
*Target Time: 10-20 Minutes*

1.  **Go to FixedFloat.com (Alternative UI) or SideShift.ai:**
    -   These are "No-Account" exchanges that break the direct on-chain link by routing through internal liquidity pools.
2.  **Configure Swap:**
    -   **Deposit:** `USDC` (Polygon). *Note: Ensure you select the version that matches your wallet (Native vs USDC.e).*
    -   **Receive:** `USDC` (Base).
    -   **Rate Type:** `Variable` (Recommended for USDC-to-USDC to minimize fees).
    -   **Recipient Address:** `0x57D400cED462a01Ed51a5De038F204Df49690A99` (Kerne Treasury).
3.  **Execute:**
    -   Send the USDC from your Burner Wallet to the deposit address provided by the swap service.
4.  **The Wash:**
    -   The service will route funds through a privacy pool or obfuscated exchange ledger.
    -   Clean funds arrive in the Kerne Treasury on Base.

---

## 3. Cost Analysis (Estimated)

| Leg | Fee/Spread | Cost on $2k |
| :--- | :--- | :--- |
| **BMO Transfer** | $0.00 | $0.00 |
| **PayTrie Spread** | ~0.5% | ~$10.00 |
| **Polygon Gas** | < $0.01 | $0.00 |
| **Privacy Swap Fee** | ~0.5% - 1.0% | ~$15.00 |
| **Base Gas** | < $0.01 | $0.00 |
| **TOTAL** | **~1.25%** | **~$25.00** |

**Result:** You land ~$1,975 in the Treasury. The source is untraceable on-chain to your BMO identity.

---

## 4. Emergency Fallback (If Privacy Tools Fail)

If Houdini/SideShift are blocked or liquidity is low:
1.  **Manual Tunnel:**
    -   Send USDC (Polygon) -> MEXC (No KYC, use VPN).
    -   Trade USDC -> XMR.
    -   Withdraw XMR -> Local Wallet (Monero GUI).
    -   Send XMR -> MEXC (New Deposit Address).
    -   Trade XMR -> USDC.
    -   Withdraw USDC (Base) -> Kerne Treasury.
    -   *Pros:* Maximum Privacy. *Cons:* High effort, ~1 hour time.