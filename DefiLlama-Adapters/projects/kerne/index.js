// Created: 2026-01-10
// Kerne Protocol - Delta-Neutral Yield Infrastructure on Base
// https://kerne.ai

// KerneVault - ERC-4626 compliant vault holding WETH
// Deployed on Base Mainnet
const KERNE_VAULT = "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd";

async function tvl(api) {
  const [totalAssets, asset] = await api.batchCall([
    { target: KERNE_VAULT, abi: "uint256:totalAssets" },
    { target: KERNE_VAULT, abi: "address:asset" },
  ]);
  
  // Institutional Hardening: Ensure no double-counting of kUSD if it's minted against the reserve
  // We only report the underlying asset (WETH) held by the vault.
  // Any kUSD liquidity on Aerodrome is excluded here to prevent "Double Counting" flags.
  api.add(asset, totalAssets);
}

module.exports = {
  methodology: "TVL is calculated by calling totalAssets() on the KerneVault ERC-4626 contract, which returns the total WETH held including both on-chain collateral and off-chain hedging positions reported by the protocol strategist.",
  base: {
    tvl,
  },
};
