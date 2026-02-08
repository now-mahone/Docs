
# Institutional On-Ramp

Kerne's institutional strategy is designed to capture the largest untapped capital pool in crypto: treasury management and yield allocation from funds, DAOs, and corporate treasuries.

## The Opportunity

Institutional capital (hedge funds, family offices, DAO treasuries) is looking for:
1. **Predictable yields** without directional market exposure
2. **Regulatory clarity** and compliance tooling
3. **Transparent custody** with real-time auditability
4. **Enterprise-grade** infrastructure and SLAs

Kerne provides all four through its delta-neutral architecture and Glass House Standard.

## Pro Mode Vaults

Kerne operates a separate tier of **whitelisted vaults** specifically designed for institutional allocators:

### Features
- **KYC/AML Gating**: Access requires completion of institutional onboarding via the `IComplianceHook` smart contract interface.
- **Custom Risk Parameters**: Institutional vaults can be configured with tighter hedge ratios, lower leverage limits, and dedicated Insurance Fund allocations.
- **Dedicated Reporting**: Automated weekly and monthly reports with PnL attribution, risk metrics, and compliance documentation.
- **Multi-Sig Custody**: All institutional deposits are managed via Gnosis Safe with configurable signer thresholds.

### Supported Custodians
- **Fireblocks** — API-integrated for automated workflow
- **Coinbase Prime** — Native Base chain support
- **Gnosis Safe** — On-chain multi-sig for DAOs

## Onboarding Flow

1. **Application**: Institution submits interest via the Kerne partner portal.
2. **KYC/AML**: Compliance verification through our licensed partner.
3. **Vault Configuration**: Custom vault parameters are agreed upon (min deposit, hedge ratio, fee structure).
4. **Whitelisting**: Institution's wallet addresses are added to the `IComplianceHook` allowlist.
5. **Deployment**: Capital is deposited and the hedging engine begins operation.
6. **Ongoing Monitoring**: Real-time dashboard access + scheduled reporting.

## Capital Tiers

| Tier | Minimum Deposit | Fee | Features |
|------|----------------|-----|----------|
| Standard | $100K | 15% performance | Pro Mode vault, weekly reports |
| Premium | $1M | 12% performance | Dedicated vault, daily reports, priority support |
| Sovereign | $10M+ | Negotiable | Custom parameters, direct team access, co-investment rights |

## Strategic Partnerships

Kerne actively pursues partnerships with:
- **DeFi protocols** seeking treasury yield (e.g., DAO treasuries holding idle stablecoins)
- **Crypto funds** looking for market-neutral strategies
- **Traditional finance** allocators exploring on-chain yield
- **RWA issuers** seeking liquidity and distribution

---