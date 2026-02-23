# Work Plan: Institutional Solvency Proof (Attestation)

## Objective
Decentralize the trust in the `STRATEGIST_ROLE` by implementing a multi-node attestation system for CEX equity reporting. This ensures that the share price of `KerneVault` is backed by verified off-chain assets.

## User Review Required
> [!IMPORTANT]
> This plan assumes we will use a set of "Verification Nodes" (EVM addresses) that sign the equity reports. Do we want to use a simple multi-sig threshold on-chain or a more complex EIP-712 signature verification in the `KerneVault`?

## Proposed Changes

### 1. Smart Contracts (`src/`)
- **KerneYieldAttestation.sol**: New contract to collect and verify signatures from authorized Verification Nodes.
- **KerneVault.sol**: Update `totalAssets()` to pull `offChainAssets` from the `KerneYieldAttestation` contract instead of a local variable.
- **KerneTrustAnchor.sol**: Implement the logic to cross-reference CEX equity vs. on-chain KUSD supply.

### 2. Hedging Engine (`bot/`)
- **attestation_signer.py**: New module for the bot to fetch exchange equity, sign the data (EIP-712), and submit it to the `KerneYieldAttestation` contract.
- **multi_node_orchestrator.py**: Logic to coordinate multiple bot instances to provide a threshold of signatures.

### 3. SDK (`sdk/`)
- Add methods to query the attestation status and verify solvency proofs in the frontend (for Mahone's future work).

## Verification Plan

### Automated Tests
- `forge test --match-path test/KerneYieldAttestation.t.sol`: Verify signature threshold logic and replay protection.
- `python -m pytest bot/tests/test_attestation.py`: Verify EIP-712 signature generation matches Solidity expectations.

### Manual Verification
- Deploy `KerneYieldAttestation` to Base Sepolia.
- Run two bot instances with different keys to meet a 2/2 signature threshold.
- Confirm `KerneVault.totalAssets()` updates correctly.
