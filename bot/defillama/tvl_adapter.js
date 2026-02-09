const { createPublicClient, http } = require("viem");
const { base } = require("viem/chains");

// Kerne Protocol TVL Adapter for DefiLlama
// VAULT_ADDRESS: 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
// ASSET: WETH (0x4200000000000000000000000000000000000006)

const VAULT_ADDRESS = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC";
const WETH_ADDRESS = "0x4200000000000000000000000000000000000006";

async function tvl(timestamp, block, chainBlocks) {
  const client = createPublicClient({
    chain: base,
    transport: http(),
  });

  const totalAssets = await client.readContract({
    address: VAULT_ADDRESS,
    abi: [
      {
        inputs: [],
        name: "totalAssets",
        outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
        stateMutability: "view",
        type: "function",
      },
    ],
    functionName: "totalAssets",
    blockNumber: chainBlocks.base,
  });

  // DefiLlama requires the return to be a balances object
  // We use the WETH address on Base
  return {
    [`base:${WETH_ADDRESS}`]: totalAssets.toString(),
  };
}

module.exports = {
  timetravel: true,
  misrepresentedTokens: false,
  base: {
    tvl,
  },
  methodology: "TVL is calculated by calling totalAssets() on the KerneVault contract, which includes both on-chain LST collateral and off-chain CEX hedging positions reported by the protocol strategist.",
};
