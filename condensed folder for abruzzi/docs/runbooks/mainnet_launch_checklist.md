# Kerne Protocol: Mainnet Launch Checklist

## 1. Smart Contract Deployment
- [ ] **Yield Oracle:** Deploy `KerneYieldOracle.sol` using `script/DeployYieldOracle.s.sol`.
- [ ] **OFT V2 (Base):** Deploy kUSD and $KERNE OFT V2 using `script/DeployOFT.s.sol`.
- [ ] **OFT V2 (Arbitrum):** Deploy kUSD and $KERNE OFT V2 on Arbitrum.
- [ ] **OFT V2 (Optimism):** Deploy kUSD and $KERNE OFT V2 on Optimism.
- [ ] **OFT Peer Wiring:** Configure LayerZero peers between Base, Arbitrum, and Optimism (kUSD + KERNE).
- [ ] **Compliance Hook:** Deploy `KerneComplianceHook.sol` using `script/DeployCompliance.s.sol`.
- [ ] **Vault Factory Update:** Ensure `KerneVaultFactory` tiers are updated with the compliance hook address.

## 2. Bot & Infrastructure
- [x] **Mainnet Bot:** `DRY_RUN` disabled in `bot/main.py`.
- [ ] **VPS Deployment:** Deploy bot to production VPS (DigitalOcean/Hetzner).
- [ ] **Monitoring:** Verify Discord alerts and Sentinel API connectivity.
- [ ] **Yield Reporting:** Verify bot is pushing verifiable APY to the Yield Oracle.
- [ ] **PoR Attestation:** Verify `por_attestation.py` is generating daily cryptographic proofs.

## 3. Liquidity & Capitalization
- [ ] **Insurance Fund:** Transfer initial $50,000 seed capital to `KerneInsuranceFund.sol`.
- [ ] **Aerodrome Pool:** Create kUSD/USDC pool on Aerodrome and seed initial liquidity.
- [ ] **Bribes:** Set up initial voting bribes for the Aerodrome pool to attract organic liquidity.
- [ ] **PSM Exposure:** Set initial stablecoin caps in `KUSDPSM.sol`.

## 4. Institutional & Legal
- [ ] **Foundation:** Initiate Kerne Foundation incorporation (Cayman/BVI).
- [ ] **KYC Provider:** Finalize integration with Quadrata/Civic for the Compliance Hook.
- [ ] **Prime Client:** Onboard the first institutional partner to `KernePrime.sol`.
- [ ] **Audit:** Finalize engagement with a Tier-1 security audit firm.

## 5. Marketing & Discovery
- [ ] **DefiLlama:** Follow up on PR #17645 for TVL listing.
- [ ] **Yield Aggregators:** Submit Kerne Yield Oracle to Yearn/Beefy/DefiLlama Yields.
- [ ] **Twitter/X:** Launch official Kerne Protocol account and start weekly yield threads.
- [ ] **Documentation:** Publish unified GitBook/Docusaurus site.
