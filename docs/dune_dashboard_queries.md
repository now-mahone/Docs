# Kerne Protocol Dune Dashboard Queries
<!-- Created: 2026-02-19 -->

## Overview
This document contains SQL queries for the Kerne Protocol Dune Analytics dashboard. These queries track key protocol metrics across Base, Optimism, and Arbitrum.

## Prerequisites
**UPDATE THESE CONTRACT ADDRESSES** with your actual deployed vault addresses:
- Base Vault: `0xYOUR_BASE_VAULT_ADDRESS`
- Optimism Vault: `0xYOUR_OPTIMISM_VAULT_ADDRESS`
- Arbitrum Vault: `0xYOUR_ARBITRUM_VAULT_ADDRESS`
- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- USDC on Optimism: `0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85`
- USDC on Arbitrum: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`

---

## Query 1: Chain Exposure (TVL by Chain)

**Title**: Kerne Protocol - Chain Exposure
**Description**: Total Value Locked across Base, Optimism, and Arbitrum chains

```sql
WITH base_tvl AS (
    SELECT
        'Base' as chain,
        CAST(value AS DOUBLE) / 1e6 AS tvl_usd,
        block_time,
        block_number
    FROM base.logs
    WHERE contract_address = 0xYOUR_BASE_VAULT_ADDRESS -- Base Vault
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef -- Transfer event
        AND block_time >= NOW() - INTERVAL '7' day
),

optimism_tvl AS (
    SELECT
        'Optimism' as chain,
        CAST(value AS DOUBLE) / 1e6 AS tvl_usd,
        block_time,
        block_number
    FROM optimism.logs
    WHERE contract_address = 0xYOUR_OPTIMISM_VAULT_ADDRESS -- Optimism Vault
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND block_time >= NOW() - INTERVAL '7' day
),

arbitrum_tvl AS (
    SELECT
        'Arbitrum' as chain,
        CAST(value AS DOUBLE) / 1e6 AS tvl_usd,
        block_time,
        block_number
    FROM arbitrum.logs
    WHERE contract_address = 0xYOUR_ARBITRUM_VAULT_ADDRESS -- Arbitrum Vault
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND block_time >= NOW() - INTERVAL '7' day
),

combined AS (
    SELECT * FROM base_tvl
    UNION ALL
    SELECT * FROM optimism_tvl
    UNION ALL
    SELECT * FROM arbitrum_tvl
)

SELECT
    chain,
    SUM(tvl_usd) as total_tvl,
    ROUND(SUM(tvl_usd) / SUM(SUM(tvl_usd)) OVER () * 100, 2) as percentage
FROM combined
GROUP BY chain
ORDER BY total_tvl DESC
```

**Visualization**: Pie chart showing percentage distribution across chains

---

## Query 2: Solvency Ratio

**Title**: Kerne Protocol - Solvency Ratio
**Description**: Real-time solvency ratio (Total Assets / Total Liabilities) across all chains

```sql
WITH base_assets AS (
    SELECT
        'Base' as chain,
        contract_address as vault,
        CAST(data AS DOUBLE) / 1e6 AS total_assets
    FROM base.logs
    WHERE contract_address = 0xYOUR_BASE_VAULT_ADDRESS
        AND topic0 = 0x4cf088d65e7e2853e5e11cf0b4b7c3e4a1671cf3a8e8e1b8e7b8c3f4e1e2e3e4 -- totalAssets() call
        AND block_time >= NOW() - INTERVAL '1' day
    ORDER BY block_time DESC
    LIMIT 1
),

optimism_assets AS (
    SELECT
        'Optimism' as chain,
        contract_address as vault,
        CAST(data AS DOUBLE) / 1e6 AS total_assets
    FROM optimism.logs
    WHERE contract_address = 0xYOUR_OPTIMISM_VAULT_ADDRESS
        AND topic0 = 0x4cf088d65e7e2853e5e11cf0b4b7c3e4a1671cf3a8e8e1b8e7b8c3f4e1e2e3e4
        AND block_time >= NOW() - INTERVAL '1' day
    ORDER BY block_time DESC
    LIMIT 1
),

arbitrum_assets AS (
    SELECT
        'Arbitrum' as chain,
        contract_address as vault,
        CAST(data AS DOUBLE) / 1e6 AS total_assets
    FROM arbitrum.logs
    WHERE contract_address = 0xYOUR_ARBITRUM_VAULT_ADDRESS
        AND topic0 = 0x4cf088d65e7e2853e5e11cf0b4b7c3e4a1671cf3a8e8e1b8e7b8c3f4e1e2e3e4
        AND block_time >= NOW() - INTERVAL '1' day
    ORDER BY block_time DESC
    LIMIT 1
),

base_liabilities AS (
    SELECT
        SUM(CAST(value AS DOUBLE) / 1e6) AS total_shares_value
    FROM base.logs
    WHERE contract_address = 0xYOUR_BASE_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND from_address = 0x0000000000000000000000000000000000000000 -- Mints
        AND block_time >= NOW() - INTERVAL '1' day
),

optimism_liabilities AS (
    SELECT
        SUM(CAST(value AS DOUBLE) / 1e6) AS total_shares_value
    FROM optimism.logs
    WHERE contract_address = 0xYOUR_OPTIMISM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND from_address = 0x0000000000000000000000000000000000000000
        AND block_time >= NOW() - INTERVAL '1' day
),

arbitrum_liabilities AS (
    SELECT
        SUM(CAST(value AS DOUBLE) / 1e6) AS total_shares_value
    FROM arbitrum.logs
    WHERE contract_address = 0xYOUR_ARBITRUM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND from_address = 0x0000000000000000000000000000000000000000
        AND block_time >= NOW() - INTERVAL '1' day
),

totals AS (
    SELECT
        (SELECT SUM(total_assets) FROM (
            SELECT total_assets FROM base_assets
            UNION ALL SELECT total_assets FROM optimism_assets
            UNION ALL SELECT total_assets FROM arbitrum_assets
        )) AS total_assets,
        (SELECT SUM(total_shares_value) FROM (
            SELECT total_shares_value FROM base_liabilities
            UNION ALL SELECT total_shares_value FROM optimism_liabilities
            UNION ALL SELECT total_shares_value FROM arbitrum_liabilities
        )) AS total_liabilities
)

SELECT
    total_assets,
    total_liabilities,
    ROUND(total_assets / NULLIF(total_liabilities, 0), 4) AS solvency_ratio,
    CASE
        WHEN total_assets / NULLIF(total_liabilities, 0) >= 1.0 THEN 'SOLVENT'
        ELSE 'UNDERCOLLATERALIZED'
    END AS status
FROM totals
```

**Visualization**: Counter showing the solvency ratio with color coding:
- Green if >= 1.0
- Yellow if 0.95-1.0
- Red if < 0.95

---

## Query 3: Total Supply (Shares Outstanding)

**Title**: Kerne Protocol - Total Supply
**Description**: Total shares minted across all vaults over time

```sql
WITH base_supply AS (
    SELECT
        'Base' as chain,
        DATE_TRUNC('day', block_time) AS day,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000
            THEN CAST(value AS DOUBLE)
            ELSE -CAST(value AS DOUBLE)
        END) / 1e6 AS net_supply_change
    FROM base.logs
    WHERE contract_address = 0xYOUR_BASE_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef -- Transfer
        AND (from_address = 0x0000000000000000000000000000000000000000
             OR to_address = 0x0000000000000000000000000000000000000000)
        AND block_time >= NOW() - INTERVAL '30' day
    GROUP BY 1, 2
),

optimism_supply AS (
    SELECT
        'Optimism' as chain,
        DATE_TRUNC('day', block_time) AS day,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000
            THEN CAST(value AS DOUBLE)
            ELSE -CAST(value AS DOUBLE)
        END) / 1e6 AS net_supply_change
    FROM optimism.logs
    WHERE contract_address = 0xYOUR_OPTIMISM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND (from_address = 0x0000000000000000000000000000000000000000
             OR to_address = 0x0000000000000000000000000000000000000000)
        AND block_time >= NOW() - INTERVAL '30' day
    GROUP BY 1, 2
),

arbitrum_supply AS (
    SELECT
        'Arbitrum' as chain,
        DATE_TRUNC('day', block_time) AS day,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000
            THEN CAST(value AS DOUBLE)
            ELSE -CAST(value AS DOUBLE)
        END) / 1e6 AS net_supply_change
    FROM arbitrum.logs
    WHERE contract_address = 0xYOUR_ARBITRUM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        AND (from_address = 0x0000000000000000000000000000000000000000
             OR to_address = 0x0000000000000000000000000000000000000000)
        AND block_time >= NOW() - INTERVAL '30' day
    GROUP BY 1, 2
),

all_chains AS (
    SELECT * FROM base_supply
    UNION ALL
    SELECT * FROM optimism_supply
    UNION ALL
    SELECT * FROM arbitrum_supply
),

cumulative AS (
    SELECT
        chain,
        day,
        net_supply_change,
        SUM(net_supply_change) OVER (PARTITION BY chain ORDER BY day) AS cumulative_supply
    FROM all_chains
)

SELECT
    day,
    chain,
    cumulative_supply,
    SUM(cumulative_supply) OVER (PARTITION BY day) AS total_protocol_supply
FROM cumulative
ORDER BY day DESC, chain
```

**Visualization**: Line chart showing:
- Total protocol supply over time (primary line)
- Individual chain supply (stacked area or separate lines)

---

## Alternative Query: Simplified Total Supply (Current State)

If you only need the current total supply across all chains:

```sql
WITH base_current AS (
    SELECT
        'Base' as chain,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000 THEN CAST(value AS DOUBLE)
            WHEN to_address = 0x0000000000000000000000000000000000000000 THEN -CAST(value AS DOUBLE)
            ELSE 0
        END) / 1e6 AS total_supply
    FROM base.logs
    WHERE contract_address = 0xYOUR_BASE_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
),

optimism_current AS (
    SELECT
        'Optimism' as chain,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000 THEN CAST(value AS DOUBLE)
            WHEN to_address = 0x0000000000000000000000000000000000000000 THEN -CAST(value AS DOUBLE)
            ELSE 0
        END) / 1e6 AS total_supply
    FROM optimism.logs
    WHERE contract_address = 0xYOUR_OPTIMISM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
),

arbitrum_current AS (
    SELECT
        'Arbitrum' as chain,
        SUM(CASE
            WHEN from_address = 0x0000000000000000000000000000000000000000 THEN CAST(value AS DOUBLE)
            WHEN to_address = 0x0000000000000000000000000000000000000000 THEN -CAST(value AS DOUBLE)
            ELSE 0
        END) / 1e6 AS total_supply
    FROM arbitrum.logs
    WHERE contract_address = 0xYOUR_ARBITRUM_VAULT_ADDRESS
        AND topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
)

SELECT
    chain,
    total_supply,
    ROUND(total_supply / SUM(total_supply) OVER () * 100, 2) AS percentage
FROM (
    SELECT * FROM base_current
    UNION ALL
    SELECT * FROM optimism_current
    UNION ALL
    SELECT * FROM arbitrum_current
)
ORDER BY total_supply DESC
```

---

## Notes

1. **Event Topics**: 
   - `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` = Transfer event
   - Mints: `from = 0x0000000000000000000000000000000000000000`
   - Burns: `to = 0x0000000000000000000000000000000000000000`

2. **Decimal Handling**: All USDC values use 6 decimals, so we divide by 1e6

3. **Time Ranges**: Adjust the `INTERVAL` clauses based on your dashboard needs

4. **Performance**: Consider materializing these queries as views if they run slowly

5. **Real-time Updates**: Dune refreshes materialized views periodically. For real-time data, you may need to adjust caching settings.

## Deployment Checklist

- [ ] Update all vault contract addresses (3x per query)
- [ ] Verify USDC addresses for each chain
- [ ] Test each query individually in Dune
- [ ] Create visualizations for each metric
- [ ] Set up dashboard refresh schedule
- [ ] Add dashboard description and context