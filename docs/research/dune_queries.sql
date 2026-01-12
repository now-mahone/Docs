-- Kerne Protocol Dune Analytics Queries
-- Created: 2025-12-28

-- 1. KerneVault Share Price Over Time
-- This query calculates the share price by combining on-chain assets and reported off-chain assets.
-- Note: Replace '0xYourVaultAddress' with the actual deployed address.

WITH offchain_updates AS (
    SELECT 
        evt_block_time,
        newAmount / 1e18 as offchain_eth
    FROM kerne_protocol_base.KerneVault_evt_OffChainAssetsUpdated
    -- WHERE contract_address = 0xYourVaultAddress
),
onchain_balances AS (
    SELECT 
        block_time,
        amount / 1e18 as onchain_eth
    FROM erc20_base.evt_Transfer
    -- WHERE to = 0xYourVaultAddress OR from = 0xYourVaultAddress
    -- This is a simplified placeholder; actual on-chain balance tracking requires summing transfers.
),
total_supply AS (
    SELECT 
        block_time,
        totalSupply / 1e18 as shares
    -- Placeholder for ERC20 total supply tracking
)
SELECT 
    o.evt_block_time,
    (o.offchain_eth + COALESCE(on.onchain_eth, 0)) / ts.shares as share_price
FROM offchain_updates o
LEFT JOIN onchain_balances on ON on.block_time <= o.evt_block_time
LEFT JOIN total_supply ts ON ts.block_time <= o.evt_block_time
ORDER BY 1 DESC;


-- 2. Binance ETH-PERP Funding Rate Correlation
-- Compares Binance funding rates with Kerne's reported yield.

WITH binance_funding AS (
    -- Placeholder for Binance funding rate data (often available in Dune's community datasets)
    SELECT 
        time,
        value as funding_rate
    FROM binance.funding_rates
    WHERE symbol = 'ETHUSDT'
),
kerne_yield AS (
    SELECT 
        evt_block_time,
        (newAmount - oldAmount) / oldAmount as reported_yield
    FROM kerne_protocol_base.KerneVault_evt_OffChainAssetsUpdated
    WHERE oldAmount > 0
)
SELECT 
    k.evt_block_time,
    k.reported_yield,
    b.funding_rate,
    (k.reported_yield - b.funding_rate) as basis_spread
FROM kerne_yield k
JOIN binance_funding b ON b.time = k.evt_block_time
ORDER BY 1 DESC;
