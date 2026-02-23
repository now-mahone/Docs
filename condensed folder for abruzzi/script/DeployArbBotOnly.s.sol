// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneFlashArbBot.sol";
import "../src/KerneInsuranceFund.sol";

contract DeployArbBotOnly is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        address insuranceFund = 0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9;
        address treasury = 0xB656440287f8A1112558D3df915b23326e9b89ec;
        address aeroRouter = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
        address uniRouter = 0x2626664c2603336E57B271c5C0b26F421741e481;
        address maverickRouter = 0xBE0e5b6B3F0c3BC8E59273c52431478D8D303E97;

        address weth = 0x4200000000000000000000000000000000000006;
        address usdc = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

        vm.startBroadcast(deployerPrivateKey);

        KerneFlashArbBot arbBot = new KerneFlashArbBot(
            admin,
            treasury,
            insuranceFund,
            address(0), // vault
            address(0), // psm
            aeroRouter,
            uniRouter,
            maverickRouter
        );
        console.log("KerneFlashArbBot deployed at:", address(arbBot));

        // Initial Configuration
        arbBot.setTokenApproval(weth, true);
        arbBot.setTokenApproval(usdc, true);
        
        // Grant permissions in Insurance Fund
        KerneInsuranceFund(insuranceFund).setAuthorization(address(arbBot), true);

        vm.stopBroadcast();
    }
}
