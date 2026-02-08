# Glass House Standard (PoR)

Kerne adheres to the **Glass House Standard** — a commitment to absolute transparency in a post-FTX world.

## Automated Proof of Reserve (PoR)

The protocol implements an automated PoR system that provides real-time, cryptographically verifiable proof of solvency.

1. **On-Chain Aggregation**: The system monitors all KerneVaults across multiple chains (Base, Arbitrum, etc.) to calculate total liabilities (user deposits).
2. **Off-Chain Verification**: The `por_automated.py` engine connects to the protocol's CEX accounts (e.g., Hyperliquid) to verify the equity and positions held in reserve.
3. **Attestation**: Every 24 hours, the system generates a signed attestation (JSON and Markdown) that proves `Total Assets >= Total Liabilities`.
4. **Public Dashboard**: These reports are published directly to the Kerne dashboard and shared via Discord/Twitter, allowing anyone to audit the protocol's health at any time.

## Multi-Sig & Custody

All core protocol parameters and treasury funds are managed via a multi-sig wallet (Gnosis Safe) with key signers distributed across the core team. For institutional capital, Kerne supports integration with qualified custodians like Fireblocks and Coinbase Prime.

---