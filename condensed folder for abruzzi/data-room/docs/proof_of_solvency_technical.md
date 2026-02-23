# Technical Specification: Kerne Proof of Solvency (PoS)

**Date:** 2026-01-12
**Status:** Production Ready

## 1. Introduction
Kerne Protocol implements a hybrid on-chain/off-chain architecture to achieve delta-neutral yield. To maintain institutional-grade transparency, we utilize a cryptographic Proof of Solvency (PoS) mechanism that bridges off-chain hedging reserves with on-chain TVL reporting.

## 2. The KerneVerificationNode
The `KerneVerificationNode` is a standalone smart contract that acts as the registry for verified asset attestations.

### 2.1 Cryptographic Attestations
Attestations are submitted in the following format:
`keccak256(abi.encodePacked(vault, amount, timestamp))`

These hashes are signed by authorized **Institutional Verifiers** (e.g., the Kerne Sentinel bot or a third-party auditor). The `KerneVerificationNode` verifies the signature using `ECDSA.recover` before accepting the data.

### 2.2 Staleness Protection
To prevent the use of outdated data, attestations have a strict validity window:
- **Submission Window:** Attestations must be submitted within 1 hour of the data timestamp.
- **Validity Window:** The `KerneVault` only considers attestations valid for 24 hours. If no fresh attestation is provided, the vault's `totalAssets()` calculation excludes the off-chain portion.

## 3. Vault Integration (ERC-4626)
The `KerneVault` integrates with the `KerneVerificationNode` to calculate its total net asset value (NAV).

```solidity
function totalAssets() public view override returns (uint256) {
    uint256 onChainAssets = IERC20(asset()).balanceOf(address(this));
    uint256 verifiedOffChainAssets = IVerificationNode(node).getVerifiedAssets(address(this));
    return onChainAssets + verifiedOffChainAssets;
}
```

## 4. Verification Workflow
1. **Data Collection:** The Kerne Sentinel bot fetches real-time equity data from CEX APIs (Bybit/OKX).
2. **Signing:** The data is hashed and signed using a secure, hardware-isolated key.
3. **Submission:** The signed attestation is pushed to the `KerneVerificationNode` on Base.
4. **Indexing:** DefiLlama and other aggregators call `totalAssets()`, which now includes the cryptographically verified off-chain reserves.

## 5. Security Considerations
- **Role-Based Access:** Only addresses with `VERIFIER_ROLE` can submit attestations.
- **Transparency:** All attestations are emitted as events, allowing anyone to audit the history of reported reserves.
- **Circuit Breakers:** If the `KerneVerificationNode` reports a sudden drop in assets, the Sentinel engine can autonomously pause the vault.
