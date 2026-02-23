const axios = require("axios");

// Created: 2026-01-13
// Yield Adapter for DefiLlama yield-server

const VAULT_ADDRESS = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC";
const WETH_ADDRESS = "0x4200000000000000000000000000000000000006";

async function apy() {
  // Pulls from Kerne's public stats API which reflects the dynamic hedging engine's performance
  try {
    const response = await axios.get("https://kerne.finance/api/stats");
    const data = response.data;
    
    return [
      {
        pool: `${VAULT_ADDRESS}-base`,
        chain: "Base",
        project: "kerne-protocol",
        symbol: "kLP",
        tvlUsd: parseFloat(data.tvl_usd) || 0,
        apyBase: parseFloat(data.current_apy) || 0,
        underlyingTokens: [WETH_ADDRESS],
        rewardTokens: [], // Kerne yield is auto-compounding in kLP price
        url: "https://kerne.finance/terminal"
      }
    ];
  } catch (e) {
    console.error("Failed to fetch APY stats:", e);
    return [];
  }
}

module.exports = {
  timetravel: false,
  apy: apy,
  url: "https://kerne.finance",
};
