# Kerne Protocol: Insurance Fund Policy

## 1. Purpose
The Kerne Insurance Fund (KIF) is a protocol-owned backstop designed to protect depositor principal and maintain the kUSD peg during extreme market volatility, exchange failures, or smart contract exploits.

## 2. Capitalization Strategy
The KIF is capitalized through multiple streams to ensure robust coverage:

- **Protocol Fees:** 10% of all protocol founder fees are automatically diverted to the KIF.
- **Seed Capital:** Initial capitalization of $50,000 (in WETH/USDC) from the Kerne Foundation.
- **Yield Diversion:** In high-yield environments (>20% APY), the protocol may divert a portion of excess yield to the KIF.
- **$KERNE Buybacks:** A portion of $KERNE buybacks may be held in the KIF to provide reflexive value.

## 3. Management & Governance
- **Custody:** The KIF assets are held in the `KerneInsuranceFund.sol` contract, governed by the Kerne Foundation multi-sig.
- **Investment Strategy:** Idle KIF assets may be deployed into low-risk, delta-neutral strategies (e.g., Kerne's own vaults) to generate organic growth for the fund.
- **Target Capitalization:** The protocol aims to maintain a KIF balance equal to at least 5% of the total protocol TVL.

## 4. Claim & Socialization Logic
The KIF uses a "Socialized Loss" model to ensure equitable protection:

- **Trigger Events:** A claim can be triggered by the Foundation Council in the event of a verified loss (e.g., CEX hack, LST depeg > 10%).
- **Socialization:** When a loss occurs in a specific vault, the KIF socializes the loss by transferring assets to the affected vault, effectively "filling the gap" in the share price.
- **Safety Limits:** To prevent fund drain, individual claims are capped at 50% of the total KIF balance per event.

## 5. Transparency & Reporting
- **Real-time Monitoring:** The KIF balance and total covered amount are displayed on the Kerne Solvency Dashboard.
- **Proof of Reserve:** KIF assets held off-chain (if any) are subject to the same daily PoR attestations as vault assets.
- **Annual Audit:** The KIF will undergo an annual financial audit to verify solvency and management compliance.

## 6. Implementation Status
- **Contract:** `KerneInsuranceFund.sol` is deployed on Base Mainnet.
- **Automation:** `bot/liquidity_manager.py` includes logic for automated KIF rebalancing.
- **Initial Capitalization:** Pending Foundation seed transfer.
