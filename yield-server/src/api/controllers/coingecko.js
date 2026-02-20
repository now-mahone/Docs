const kerneAdapter = require('../../adaptors/kerne/index');

const getCoinGeckoYield = async (req, res) => {
  try {
    // Fetch data from the Kerne adapter
    const pools = await kerneAdapter.apy();

    // Format the data to match CoinGecko Yield API schema
    const formattedData = pools.map(pool => ({
      pool_id: pool.pool,
      pool_name: `${pool.project} ${pool.symbol} ${pool.poolMeta}`,
      tvl: pool.tvlUsd,
      apy: (pool.apyBase || 0) + (pool.apyReward || 0),
      base_apy: pool.apyBase || 0,
      reward_apy: pool.apyReward || 0,
      reward_tokens: pool.rewardTokens || [],
      underlying_tokens: pool.underlyingTokens || [],
      chain: pool.chain,
      url: kerneAdapter.url
    }));

    res.status(200).json({
      status: 'success',
      data: formattedData,
    });
  } catch (error) {
    console.error('Error fetching CoinGecko yield data:', error);
    res.status(500).json({
      status: 'error',
      message: 'Failed to fetch yield data',
    });
  }
};

module.exports = {
  getCoinGeckoYield,
};