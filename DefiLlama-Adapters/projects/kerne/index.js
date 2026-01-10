// Created: 2026-01-10
// Kerne Protocol - Delta-Neutral Yield Infrastructure on Base
// https://kerne.ai

const KERNE_VAULT = "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd";

async function tvl(api) {
  // Phased Listing Strategy:
  // Initially, we report the total assets managed by the vault.
  // We use the standard ERC-4626 totalAssets() call which is the industry standard.
  // This ensures the adapter is simple and follows DefiLlama's preferred patterns.
  const [totalAssets, asset] = await api.batchCall([
    { target: KERNE_VAULT, abi: "uint256:totalAssets" },
    { target: KERNE_VAULT, abi: "address:asset" },
  ]);
  
  api.add(asset, totalAssets);
}

module.exports = {
  methodology: "TVL is calculated by calling totalAssets() on the KerneVault ERC-4626 contract, which returns the total underlying assets (WETH) managed by the protocol.",
  base: {
    tvl,
  },
};
