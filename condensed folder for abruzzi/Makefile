# Kerne Command Center

.PHONY: fork deploy-local

# Start a local fork of Base Mainnet
fork:
	anvil --fork-url https://mainnet.base.org --chain-id 8453

# Deploy KerneVault to the local Anvil fork
deploy-local:
	forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
