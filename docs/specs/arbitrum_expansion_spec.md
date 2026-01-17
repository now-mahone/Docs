# Technical Specification: Kerne Protocol Arbitrum Expansion

**Date:** 2026-01-16  
**Status:** FINALIZED  
**Author:** Kerne Core Architecture Team

## 1. Overview
The Arbitrum expansion marks Kerne Protocol's first major step toward becoming a dominant omnichain yield engine. By deploying on Arbitrum, Kerne taps into the deepest LST (Liquid Staking Token) liquidity pool in the Ethereum L2 ecosystem, specifically targeting `wstETH`.

This expansion utilizes **LayerZero V2** for seamless, burn-and-mint token transfers between Base (Genesis Chain) and Arbitrum, ensuring zero liquidity fragmentation and a unified user experience.

## 2. Omnichain Infrastructure (LayerZero V2)

### 2.1. Contract Addresses
The following `KerneOFTV2` contracts have been deployed to facilitate cross-chain movement of kUSD and KERNE tokens.

| Token | Chain | Address |
| :--- | :--- | :--- |
| **kUSD OFT** | Base | `0xb50bfec5ff426744b9d195a8c262da376637cb6a` |
| **KERNE OFT** | Base | `0xe828810b6b60a3de21ab9d0bdba962bf9fbdc255` |
| **kUSD OFT** | Arbitrum | `0xbf039eb5cf2e1d0067c0918462fdd211e252efdb` |
| **KERNE OFT** | Arbitrum | `0x5d8dde6264df8a0963253693f32e057e1aa37afd` |

### 2.2. Peer Wiring Configuration
To enable communication, each OFT must recognize its counterpart on the remote chain as a "peer".

*   **Base EID:** `30184`
*   **Arbitrum EID:** `30110`

**Wiring Matrix:**
1.  **Base (30184)** sets Arbitrum Peer: `setPeer(30110, Arb_OFT_Address)`
2.  **Arbitrum (30110)** sets Base Peer: `setPeer(30184, Base_OFT_Address)`

## 3. Arbitrum Vault Specification
The Arbitrum-native KerneVault is optimized for wstETH, allowing users to earn delta-neutral yield while maintaining exposure to Ethereum's premier LST.

| Parameter | Value |
| :--- | :--- |
| **Asset** | wstETH (`0x5979D7b546E38E414F7E9822514be443A4800529`) |
| **Name** | Kerne wstETH Vault |
| **Symbol** | k-wstETH |
| **Exchange Deposit** | `0x57D400cED462a01Ed51a5De038F204Df49690A99` |
| **Compliance Hook** | Enabled (Gated for institutional partners) |

## 4. Security Considerations

### 4.1. LayerZero V2 Security
*   **Decentralized Verification Networks (DVNs):** Kerne utilizes a multi-DVN security stack. Messages require confirmation from at least 3 independent verifiers (e.g., LayerZero, Google Cloud, and Animoca).
*   **Executor Configuration:** Dedicated executors ensure sub-10 second cross-chain settlement times for kUSD.

### 4.2. Institutional Guardrails
*   **Sentinel V2 Integration:** The Arbitrum Vault is protected by the Sentinel autonomous defense loop. It monitors the `wstETH/ETH` peg and the protocol's global solvency (Total Assets >= Total Liabilities).
*   **Circuit Breakers:** Both the Vault and the OFTs inherit `Pausable` functionality, allowing the `PAUSER_ROLE` (Sentinel/Strategist) to halt operations during extreme market volatility or security incidents.
*   **Institutional Compliance:** All deposits on Arbitrum are subject to the `KerneComplianceHook`, ensuring only KYC-verified entities or whitelisted addresses can access the core yield engine.

## 5. Deployment and Activation

### 5.1. Prerequisites
- `PRIVATE_KEY` with gas on both Base and Arbitrum.
- Forge installed and configured.

### 5.2. Activation Steps
The expansion is executed via the `OmnichainActivation.s.sol` script, which handles vault deployment and peer wiring in a single unified workflow.

1.  **Deploy Arbitrum Suite:**
    ```bash
    forge script script/OmnichainActivation.s.sol:OmnichainActivation \
        --rpc-url arbitrum \
        --broadcast \
        --verify
    ```

2.  **Cross-Chain Peer Wiring (Base Side):**
    ```bash
    # Ensure ARB addresses are exported to env first
    export ARB_KUSD_OFT=0xbf039eb5cf2e1d0067c0918462fdd211e252efdb
    export ARB_KERNE_OFT=0x5d8dde6264df8a0963253693f32e057e1aa37afd
    
    forge script script/OmnichainActivation.s.sol:OmnichainActivation \
        --rpc-url base \
        --broadcast
    ```

3.  **Verification:**
    Run `verify_peers.py` (Bot utility) to ensure all paths are configured correctly and ready for institutional traffic.

---
**Kerne Core Architecture Team**  
*Capital Efficiency. Institutional Security. Omnichain Scale.*
