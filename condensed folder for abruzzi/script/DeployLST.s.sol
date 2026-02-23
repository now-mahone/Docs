// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { KerneLSTHook } from "../src/KerneLSTHook.sol";
import { KerneLSTSolver } from "../src/KerneLSTSolver.sol";

contract DeployLST is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        address vaultAddress = vm.envAddress("VAULT_ADDRESS");
        address strategist = vm.envAddress("STRATEGIST_ADDRESS");
        address insuranceFund = vm.envAddress("INSURANCE_FUND_ADDRESS");
        
        // Base Mainnet Addresses
        address aerodromeRouter = 0xcf77a3Ba9A5cA399eB7352985f693DA059145373;
        address uniswapV3Router = 0x2626664c2603336E57B271c5C0b26F421741e481;

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy KerneLSTHook
        KerneLSTHook hook = new KerneLSTHook(admin);
        console.log("KerneLSTHook deployed at:", address(hook));

        // 2. Deploy KerneLSTSolver
        KerneLSTSolver solver = new KerneLSTSolver(
            admin,
            vaultAddress,
            insuranceFund,
            aerodromeRouter,
            uniswapV3Router
        );
        console.log("KerneLSTSolver deployed at:", address(solver));

        // 3. Configure Roles
        hook.grantRole(hook.STRATEGIST_ROLE(), strategist);
        solver.grantRole(solver.SOLVER_ROLE(), strategist); // Bot uses strategist address

        // 4. Link to Vault
        KerneVault vault = KerneVault(vaultAddress);
        vault.setVerificationNode(address(hook));
        
        // Grant strategist role to solver for 0-fee flash loans
        vault.grantRole(vault.STRATEGIST_ROLE(), address(solver));

        vm.stopBroadcast();
    }
}
