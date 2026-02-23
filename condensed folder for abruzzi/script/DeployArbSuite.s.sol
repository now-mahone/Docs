// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneFlashArbBot.sol";
import "../src/KerneTreasury.sol";
import "../src/KerneInsuranceFund.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract DeployArbSuite is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        console.log("Deploying from:", admin);

        // Base Mainnet Addresses
        address weth = 0x4200000000000000000000000000000000000006;
        address usdc = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
        address aeroRouter = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
        address uniRouter = 0x2626664c2603336E57B271c5C0b26F421741e481;
        address maverickRouter = 0xBE0e5b6B3F0c3BC8E59273c52431478D8D303E97;
        
        // Use deployer as placeholder for tokens not yet identified
        address kerneToken = admin; 
        address staking = admin;

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Insurance Fund
        KerneInsuranceFund insuranceFund = new KerneInsuranceFund(weth, admin);
        console.log("KerneInsuranceFund deployed at:", address(insuranceFund));

        // 2. Deploy Treasury
        KerneTreasury treasury = new KerneTreasury(admin, kerneToken, staking, aeroRouter);
        console.log("KerneTreasury deployed at:", address(treasury));

        // 3. Deploy Flash Arb Bot
        KerneFlashArbBot arbBot = new KerneFlashArbBot(
            admin,
            address(treasury),
            address(insuranceFund),
            address(0), // vault
            address(0), // psm
            aeroRouter,
            uniRouter,
            maverickRouter
        );
        console.log("KerneFlashArbBot deployed at:", address(arbBot));

        // 4. Initial Configuration
        arbBot.setTokenApproval(weth, true);
        arbBot.setTokenApproval(usdc, true);
        
        // Grant permissions
        insuranceFund.setAuthorization(address(arbBot), true);

        vm.stopBroadcast();
    }
}
