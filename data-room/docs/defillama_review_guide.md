# DefiLlama Human Review Guide: Kerne Protocol

## 1. The "Compliance First" Response
**Context:** Use this when a reviewer asks: *"How are off-chain reserves accounted for in TVL?"*

> "Kerne Protocol utilizes a standard ERC-4626 vault architecture. The `totalAssets()` function on-chain provides the definitive source of truth for TVL. This value is composed of two parts:
> 1. **On-chain Collateral:** WETH/LSTs held directly in the vault contract on Base.
> 2. **Verified Hedging Reserves:** Assets held in delta-neutral hedging positions on Tier-1 CEXs (Bybit/OKX).
>
> To ensure transparency and prevent 'ghost' assets, these off-chain reserves are attested on-chain via the `KerneVerificationNode`. Every 24 hours, an authorized institutional verifier submits a cryptographically signed attestation of the CEX equity. If an attestation is stale or missing, the vault's reported assets automatically revert to only the on-chain portion. This ensures that the TVL reported to DefiLlama is always backed by verifiable data."

## 2. Handling "Double Counting" Objections
**Context:** Use this if they ask about kUSD or recursive leverage.

> "Kerne's TVL adapter specifically reports only the underlying collateral (WETH). We do not count the minted kUSD or any internal protocol debt as TVL. Our adapter uses the `totalAssets()` call which reflects the net asset value of the vault, ensuring zero double-counting of synthetic assets."

## 3. Technical Evidence Links
- **Vault Contract:** `0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd` (Base)
- **Verification Node:** `0x...` (Insert deployed address)
- **Proof of Solvency Spec:** [Link to docs/proof_of_solvency_technical.md]

## 4. Key Talking Points for Scofield
- **Institutional Grade:** Emphasize that we use the same verification standards as institutional prime brokers.
- **Delta-Neutrality:** Explain that for every 1 ETH in TVL, there is a corresponding 1x short position, making the TVL "stable" in ETH terms regardless of market volatility.
- **Transparency:** We welcome a deep dive into our `KerneVerificationNode.sol` code to prove the cryptographic integrity of our reporting.
