const axios = require("axios");

// Kerne Protocol Yield Adapter for DefiLlama
// VAULT_ADDRESS: 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
// ASSET: WETH (0x4200000000000000000000000000000000000006)

const VAULT_ADDRESS = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC";
const WETH_ADDRESS = "0x4200000000000000000000000000000000000006";

async function apy() {
  // This function is used by DefiLlama Yields to track APY over time
  // It pulls from our public stats API which reflects the bot's actual performance
  const response = await axios.get("https://kerne.finance/api/stats");
  const data = response.data;
  
  return [
    {
      pool: `${VAULT_ADDRESS}-base`,
      chain: "Base",
      project: "kerne-protocol",
      symbol: "kLP",
      tvlUsd: parseFloat(data.tvl_usd),
      apyBase: parseFloat(data.current_apy),
      underlyingTokens: [WETH_ADDRESS],
      rewardTokens: [], // Kerne yield is auto-compounding in kLP price
      url: "https://kerne.finance/terminal"
    }
  ];
}

module.exports = {
  timetravel: false,
  apy: apy,
  url: "https://kerne.finance",
};
