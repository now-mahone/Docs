// Created: 2026-01-15
# Kerne Omnichain OFT Deployment Runbook (Arbitrum + Optimism)

## 1. Prerequisites
- RPC URLs configured for Arbitrum and Optimism.
- `PRIVATE_KEY` funded on both chains with enough ETH for deployment + peer configuration.
- LayerZero V2 Endpoint address confirmed (shared across Base/Arbitrum/Optimism): `0x1a44076050125825900e736c501f859c50fE728c`.
- EIDs (LayerZero Endpoint IDs):
  - Arbitrum: `30110`
  - Optimism: `30111`
  - Base: `30184`

## 2. Environment Variables
```
set PRIVATE_KEY=...
set ARBITRUM_RPC_URL=...
set OPTIMISM_RPC_URL=...
set ARBISCAN_API_KEY=...
set OPTIMISM_SCAN_API_KEY=...
```

## 3. Deploy OFTs (Arbitrum)
```
forge script script/DeployOFT.s.sol:DeployOFT --rpc-url arbitrum --broadcast -vvvv
```
Record deployed addresses for `kUSD` and `KERNE`.

## 4. Deploy OFTs (Optimism)
```
forge script script/DeployOFT.s.sol:DeployOFT --rpc-url optimism --broadcast -vvvv
```
Record deployed addresses for `kUSD` and `KERNE`.

## 5. Configure Peers (Required)
Set peers in both directions for each OFT pair. Repeat for kUSD and KERNE.

### Arbitrum -> Optimism
```
set OFT_ADDRESS=ARBITRUM_OFT_ADDRESS
set PEER_EID=30111
set PEER_ADDRESS=OPTIMISM_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url arbitrum --broadcast -vvvv
```

### Optimism -> Arbitrum
```
set OFT_ADDRESS=OPTIMISM_OFT_ADDRESS
set PEER_EID=30110
set PEER_ADDRESS=ARBITRUM_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url optimism --broadcast -vvvv
```

### Base -> Arbitrum / Optimism
```
set OFT_ADDRESS=BASE_OFT_ADDRESS
set PEER_EID=30110
set PEER_ADDRESS=ARBITRUM_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url base --broadcast -vvvv

set OFT_ADDRESS=BASE_OFT_ADDRESS
set PEER_EID=30111
set PEER_ADDRESS=OPTIMISM_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url base --broadcast -vvvv
```

### Arbitrum / Optimism -> Base
```
set OFT_ADDRESS=ARBITRUM_OFT_ADDRESS
set PEER_EID=30184
set PEER_ADDRESS=BASE_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url arbitrum --broadcast -vvvv

set OFT_ADDRESS=OPTIMISM_OFT_ADDRESS
set PEER_EID=30184
set PEER_ADDRESS=BASE_OFT_ADDRESS
forge script script/SetOFTPeer.s.sol:SetOFTPeer --rpc-url optimism --broadcast -vvvv
```

## 6. Verification
```
forge verify-contract --chain-id 42161 <KUSD_ARB_ADDRESS> src/KerneOFTV2.sol:KerneOFTV2 \
  --constructor-args $(cast abi-encode "constructor(string,string,uint8,address)" "Kerne Synthetic Dollar" "kUSD" 6 0x1a44076050125825900e736c501f859c50fE728c) \
  --etherscan-api-key $ARBISCAN_API_KEY

forge verify-contract --chain-id 10 <KUSD_OPT_ADDRESS> src/KerneOFTV2.sol:KerneOFTV2 \
  --constructor-args $(cast abi-encode "constructor(string,string,uint8,address)" "Kerne Synthetic Dollar" "kUSD" 6 0x1a44076050125825900e736c501f859c50fE728c) \
  --etherscan-api-key $OPTIMISM_SCAN_API_KEY
```
Repeat for KERNE with `sharedDecimals=8` and symbol `KERNE`.

## 7. Post-Deployment Checklist
- Confirm `setPeer` has been called in both directions for all OFTs.
- Validate `lzEndpoint()` in each OFT contract points to `0x1a440760...`.
- Test a small `send()` from Arbitrum <-> Optimism and Base <-> each chain.
- Update `docs/specs/cross_chain_arch.md` with deployed addresses.
- Log deployment in `project_state.md`.
