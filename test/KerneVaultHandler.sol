// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "src/KerneVault.sol";
import { MockERC20 } from "./unit/KerneVault.t.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";

contract MockFlashBorrower is IERC3156FlashBorrower {
    function onFlashLoan(
        address,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata
    ) external override returns (bytes32) {
        IERC20(token).approve(msg.sender, amount + fee);
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}

contract MockVerificationNode {
    mapping(address => uint256) public verifiedAssets;
    function setVerifiedAssets(address vault, uint256 amount) external {
        verifiedAssets[vault] = amount;
    }
    function getVerifiedAssets(address vault) external view returns (uint256) {
        return verifiedAssets[vault];
    }
}

contract KerneVaultHandler is Test {
    KerneVault public vault;
    MockERC20 public asset;
    MockFlashBorrower public flashBorrower;
    MockVerificationNode public verificationNode;

    address[] public users;
    address public currentActor;

    address public admin;
    address public strategist;
    address public exchange;

    // Ghost variables for invariant checking
    uint256 public ghost_totalDeposited;
    uint256 public ghost_totalWithdrawn;
    uint256 public ghost_totalYieldGenerated;
    uint256 public ghost_unprocessedYield;
    uint256 public ghost_totalFeesCaptured;

    uint256 public constant MAX_AMOUNT = 1_000_000 ether;

    constructor(
        KerneVault _vault,
        MockERC20 _asset,
        address _admin,
        address _strategist,
        address _exchange
    ) {
        vault = _vault;
        asset = _asset;
        admin = _admin;
        strategist = _strategist;
        exchange = _exchange;
        flashBorrower = new MockFlashBorrower();
        verificationNode = new MockVerificationNode();

        vm.prank(admin);
        vault.setVerificationNode(address(verificationNode));

        for (uint160 i = 100; i < 110; i++) {
            users.push(address(i));
            asset.mint(address(i), MAX_AMOUNT);
        }
    }

    modifier useActor(uint256 userIndex) {
        currentActor = users[userIndex % users.length];
        vm.startPrank(currentActor);
        _;
        vm.stopPrank();
    }

    // --- User Actions ---

    function deposit(uint256 amount, uint256 userIndex) public useActor(userIndex) {
        amount = bound(amount, 1, asset.balanceOf(currentActor));
        uint256 maxDep = vault.maxDeposit(currentActor);
        if (maxDep == 0) return;
        amount = bound(amount, 1, maxDep);

        uint256 limit = vault.maxDepositLimit();
        if (limit > 0 && amount > limit) amount = limit;

        asset.approve(address(vault), amount);
        try vault.deposit(amount, currentActor) {
            ghost_totalDeposited += amount;
        } catch { }
    }

    function withdraw(uint256 amount, uint256 userIndex) public useActor(userIndex) {
        uint256 userShares = vault.balanceOf(currentActor);
        if (userShares == 0) return;
        
        uint256 maxAssets = vault.maxWithdraw(currentActor);
        if (maxAssets == 0) return;
        
        amount = bound(amount, 1, maxAssets);
        
        uint256 limit = vault.maxWithdrawLimit();
        if (limit > 0 && amount > limit) amount = limit;

        if (asset.balanceOf(address(vault)) < amount) return;

        try vault.withdraw(amount, currentActor, currentActor) {
            ghost_totalWithdrawn += amount;
        } catch { }
    }

    function flashLoan(uint256 amount) public {
        uint256 maxLoan = vault.maxFlashLoan(address(asset));
        if (maxLoan == 0) return;
        amount = bound(amount, 1, maxLoan);

        uint256 fee = vault.flashFee(address(asset), amount);
        asset.mint(address(flashBorrower), fee);

        try vault.flashLoan(flashBorrower, address(asset), amount, "") {
            ghost_totalYieldGenerated += fee;
            ghost_unprocessedYield += fee;
        } catch { }
    }

    // --- Strategist Actions ---

    function updateOffChainAssets(uint256 amount) public {
        amount = bound(amount, 0, MAX_AMOUNT);
        vm.prank(strategist);
        vault.updateOffChainAssets(amount);
    }

    function updateHedgingReserve(uint256 amount) public {
        amount = bound(amount, 0, MAX_AMOUNT);
        vm.prank(strategist);
        vault.updateHedgingReserve(amount);
    }

    function setVerifiedAssets(uint256 amount) public {
        amount = bound(amount, 0, MAX_AMOUNT);
        verificationNode.setVerifiedAssets(address(vault), amount);
    }

    function captureFounderWealth(uint256 grossYield) public {
        grossYield = bound(grossYield, 0, ghost_unprocessedYield);
        if (grossYield == 0) return;

        vm.prank(strategist);
        try vault.captureFounderWealth(grossYield) {
            uint256 perfFeeBps = vault.grossPerformanceFeeBps();
            uint256 insFeeBps = vault.insuranceFundBps();
            ghost_totalFeesCaptured += (grossYield * (perfFeeBps + insFeeBps)) / 10000;
            ghost_unprocessedYield -= grossYield;
        } catch { }
    }

    // --- Admin Actions ---

    function sweepToExchange(uint256 amount) public {
        uint256 bal = asset.balanceOf(address(vault));
        if (bal == 0) return;
        amount = bound(amount, 1, bal);

        vm.prank(admin);
        try vault.sweepToExchange(amount) {
        } catch { }
    }

    function setCircuitBreakers(uint256 maxDep, uint256 maxWith, uint256 minSolv) public {
        maxDep = bound(maxDep, 0, MAX_AMOUNT);
        maxWith = bound(maxWith, 0, MAX_AMOUNT);
        minSolv = bound(minSolv, 0, 20000);

        vm.prank(admin);
        vault.setCircuitBreakers(maxDep, maxWith, minSolv);
    }

    // --- Environmental Simulation ---

    function distributeYield(uint256 amount) public {
        amount = bound(amount, 0, 1000 ether);
        asset.mint(address(vault), amount);
        ghost_totalYieldGenerated += amount;
        ghost_unprocessedYield += amount;
    }

    function forceUpdateSolvency() public {
        vault.checkAndPause();
    }

    function getActors() public view returns (address[] memory) {
        return users;
    }
}
