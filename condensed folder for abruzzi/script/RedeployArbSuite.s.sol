// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneFlashArbBot.sol";
import "../src/KerneTreasury.sol";
import "../src/KerneInsuranceFund.sol";

contract RedeployArbSuite is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        // Base Mainnet Addresses
        address weth = 0x4200000000000000000000000000000000000006;
        address usdc = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
        address aeroRouter = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
        address uniRouter = 0x2626664c2603336E57B271c5C0b26F421741e481;
        address maverickRouter = 0xBE0e5b6B3F0c3BC8E59273c52431478D8D303E97;
        
        // Real Token and Staking addresses
        address kerneToken = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;
        address staking = 0x032Af1631671126A689614c0c957De774b45D582;
        
        // Existing Insurance Fund
        address insuranceFund = 0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9;

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy New Treasury
        KerneTreasury treasury = new KerneTreasury(admin, kerneToken, staking, aeroRouter);
        console.log("New KerneTreasury deployed at:", address(treasury));

        // 2. Configure Treasury
        treasury.setApprovedBuybackToken(weth, true);
        treasury.setApprovedBuybackToken(usdc, true);

        // 3. Deploy New Flash Arb Bot
        KerneFlashArbBot arbBot = new KerneFlashArbBot(
            admin,
            address(treasury),
            insuranceFund,
            0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC, // Vault
            0x7286200Ba4C6Ed5041df55965c484a106F4716FD, // PSM
            aeroRouter,
            uniRouter,
            maverickRouter
        );
        console.log("New KerneFlashArbBot deployed at:", address(arbBot));

        // 4. Initial Configuration for Bot
        arbBot.setTokenApproval(weth, true);
        arbBot.setTokenApproval(usdc, true);
        
        // Grant permissions in Insurance Fund (needs to be done by owner of Insurance Fund)
        KerneInsuranceFund(payable(insuranceFund)).setAuthorization(address(arbBot), true);

        vm.stopBroadcast();
    }
}
