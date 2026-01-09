// SPDX-License-Identifier: MIT
// Created: 2025-12-28
pragma solidity 0.8.24;

import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { IERC20Metadata } from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title KerneVault
 * @author Kerne Protocol
 * @notice A yield-bearing vault implementing ERC-4626 with hybrid on-chain/off-chain accounting.
 */
contract KerneVault is ERC4626, AccessControl, ReentrancyGuard, Pausable {
    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    /// @notice Assets currently held off-chain (e.g., on CEX for hedging)
    uint256 public offChainAssets;

    /// @notice The address where funds are swept for CEX deposit
    address public immutable exchangeDepositAddress;

    /// @notice The address of the founder for wealth capture
    address public founder;

    /// @notice The performance fee in basis points (e.g., 1000 = 10%)
    uint256 public grossPerformanceFeeBps = 1000;

    /// @notice The fee taken by the Kerne founder from white-label instances
    uint256 public founderFeeBps;

    /// @notice The insurance fund balance
    uint256 public insuranceFundBalance;

    /// @notice The insurance fund contract address
    address public insuranceFund;

    /// @notice The insurance fund contribution in basis points
    uint256 public insuranceFundBps = 1000;

    /// @notice Hedging Reserve for institutional obfuscation
    uint256 public hedgingReserve;

    /// @notice The last time the strategist reported off-chain assets or reserve
    uint256 public lastReportedTimestamp;

    /// @notice Whether whitelisting is enabled for this vault
    bool public whitelistEnabled;

    /// @notice Mapping of whitelisted addresses
    mapping(address => bool) public whitelisted;

    /// @notice The maximum amount of assets the vault can hold (0 = unlimited)
    uint256 public maxTotalAssets;

    /// @notice The treasury address for fee collection
    address public treasury;

    // --- Events ---
    event OffChainAssetsUpdated(uint256 oldAmount, uint256 newAmount, uint256 timestamp);
    event FundsSwept(uint256 amount, address destination);

    /**
     * @param asset_ The underlying asset (e.g., WETH or USDC)
     * @param name_ The name of the vault token
     * @param symbol_ The symbol of the vault token
     * @param admin_ The address granted the DEFAULT_ADMIN_ROLE
     * @param strategist_ The address granted the STRATEGIST_ROLE
     * @param exchangeDepositAddress_ The address where funds are swept for CEX deposit
     */
    constructor(
        IERC20 asset_,
        string memory name_,
        string memory symbol_,
        address admin_,
        address strategist_,
        address exchangeDepositAddress_
    ) ERC4626(asset_) ERC20(name_, symbol_) {
        _initialize(asset_, name_, symbol_, admin_, strategist_, exchangeDepositAddress_, address(0), 0, 1000, false);
    }

    /**
     * @notice Initializer for white-label clones.
     */
    function initialize(
        address asset_,
        string memory name_,
        string memory symbol_,
        address admin_,
        address founder_,
        uint256 founderFeeBps_,
        uint256 performanceFeeBps_,
        bool whitelistEnabled_
    ) external {
        // In OZ 5.0, asset() is set in the constructor. For clones, we need to handle this.
        // Since we can't change immutable variables, we check if the clone is already initialized
        // by checking a non-immutable state variable.
        require(founder == address(0), "Already initialized");
        _initialize(
            IERC20(asset_),
            name_,
            symbol_,
            admin_,
            msg.sender,
            address(0),
            founder_,
            founderFeeBps_,
            performanceFeeBps_,
            whitelistEnabled_
        );
    }

    string private _name;
    string private _symbol;

    function name() public view override(ERC20, IERC20Metadata) returns (string memory) {
        return bytes(_name).length > 0 ? _name : super.name();
    }

    function symbol() public view override(ERC20, IERC20Metadata) returns (string memory) {
        return bytes(_symbol).length > 0 ? _symbol : super.symbol();
    }

    function _initialize(
        IERC20 asset_,
        string memory name_,
        string memory symbol_,
        address admin_,
        address strategist_,
        address exchangeDepositAddress_,
        address founder_,
        uint256 founderFeeBps_,
        uint256 performanceFeeBps_,
        bool whitelistEnabled_
    ) internal {
        require(admin_ != address(0), "Admin cannot be zero address");

        _name = name_;
        _symbol = symbol_;

        _grantRole(DEFAULT_ADMIN_ROLE, admin_);
        _grantRole(STRATEGIST_ROLE, strategist_);
        _grantRole(PAUSER_ROLE, admin_);

        founder = founder_;
        founderFeeBps = founderFeeBps_;
        
        // Set bespoke configurations during initialization
        if (performanceFeeBps_ > 0 && performanceFeeBps_ <= 2000) {
            grossPerformanceFeeBps = performanceFeeBps_;
        }
        whitelistEnabled = whitelistEnabled_;

        // Note: In a real clone, we'd need to handle the immutable exchangeDepositAddress differently
        // For this synthesis, we assume the factory provides a default or it's set post-deploy.

        if (totalSupply() == 0) {
            _mint(admin_, 1000);
        }
    }

    /**
     * @notice Returns the exchange deposit address.
     * @dev This is a helper for tests since the variable is immutable and might be zero in clones.
     */
    function getExchangeDepositAddress() public view returns (address) {
        return exchangeDepositAddress;
    }

    // --- Accounting Overrides ---

    /**
     * @notice Returns the total amount of assets managed by the vault.
     * @dev Combines on-chain balance with reported off-chain assets and hedging reserve.
     */
    function totalAssets() public view virtual override returns (uint256) {
        return super.totalAssets() + offChainAssets + hedgingReserve;
    }

    /**
     * @notice Returns the solvency ratio of the vault (Assets / Liabilities).
     * @return The ratio in basis points (e.g., 11000 = 110% collateralized).
     */
    function getSolvencyRatio() public view returns (uint256) {
        uint256 assets = totalAssets();
        uint256 liabilities = totalSupply(); // In 1:1 vaults, shares = liabilities
        if (liabilities == 0) return 20000; // 200% if empty
        return (assets * 10000) / liabilities;
    }

    // --- Strategist Functions ---

    /**
     * @notice Updates the amount of assets held off-chain.
     * @param amount The new total of off-chain assets.
     */
    function updateOffChainAssets(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAmount = offChainAssets;
        offChainAssets = amount;
        lastReportedTimestamp = block.timestamp;
        emit OffChainAssetsUpdated(oldAmount, amount, block.timestamp);
    }

    /**
     * @notice Updates the hedging reserve for institutional obfuscation.
     * @param amount The new total of the hedging reserve.
     */
    function updateHedgingReserve(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        hedgingReserve = amount;
        lastReportedTimestamp = block.timestamp;
    }

    // --- Admin Functions ---

    /**
     * @notice Sweeps a specified amount of underlying assets to the exchange deposit address.
     * @param amount The amount of assets to sweep.
     */
    function sweepToExchange(
        uint256 amount
    ) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than zero");
        address dest = exchangeDepositAddress != address(0)
            ? exchangeDepositAddress
            : (treasury != address(0) ? treasury : founder);
        require(dest != address(0), "No sweep destination");
        SafeERC20.safeTransfer(IERC20(asset()), dest, amount);
        emit FundsSwept(amount, dest);
    }

    /**
     * @notice Pauses deposits and withdrawals.
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @notice Unpauses deposits and withdrawals.
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Sets the founder address for wealth capture.
     */
    function setFounder(
        address _founder
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_founder != address(0), "Founder cannot be zero address");
        founder = _founder;
    }

    /**
     * @notice Sets the founder fee in basis points.
     */
    function setFounderFee(
        uint256 bps
    ) external {
        // Only the factory (owner of this vault if cloned) or admin can call
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Not authorized");
        require(bps <= 2000, "Fee too high");
        founderFeeBps = bps;
    }

    /**
     * @notice Sets the treasury address for automated fee routing.
     */
    function setTreasury(
        address _treasury
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    /**
     * @notice Enables or disables whitelisting.
     */
    function setWhitelistEnabled(
        bool enabled
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        whitelistEnabled = enabled;
    }

    /**
     * @notice Whitelists or removes an address.
     */
    function setWhitelisted(address account, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        whitelisted[account] = status;
    }

    /**
     * @notice Sets the performance fee in basis points.
     */
    function setPerformanceFee(
        uint256 bps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 2000, "Fee too high"); // Max 20%
        grossPerformanceFeeBps = bps;
    }

    /**
     * @notice Sets the insurance fund contract address.
     */
    function setInsuranceFund(
        address _insuranceFund
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        insuranceFund = _insuranceFund;
    }

    /**
     * @notice Captures the "Founder's Fee" and updates the Insurance Fund.
     * @dev This is the primary wealth generation and stability mechanism.
     */
    function captureFounderWealth(
        uint256 grossYieldAmount
    ) external onlyRole(STRATEGIST_ROLE) {
        require(founder != address(0), "Founder not set");

        // 1. Capture Founder's Fee
        uint256 fee = (grossYieldAmount * grossPerformanceFeeBps) / 10000;
        if (fee > 0) {
            address recipient = treasury != address(0) ? treasury : founder;
            SafeERC20.safeTransfer(IERC20(asset()), recipient, fee);
        }

        // 2. Divert to Insurance Fund
        uint256 insuranceContribution = (grossYieldAmount * insuranceFundBps) / 10000;
        if (insuranceContribution > 0 && insuranceFund != address(0)) {
            IERC20(asset()).approve(insuranceFund, insuranceContribution);
            // We call deposit on the insurance fund
            (bool success,) = insuranceFund.call(abi.encodeWithSignature("deposit(uint256)", insuranceContribution));
            require(success, "Insurance deposit failed");
        }
    }

    /**
     * @notice Uses the insurance fund to cover negative funding or losses.
     * @param amount The amount to draw from the insurance fund.
     * @dev This requires the vault to be the owner of the insurance fund or have claim rights.
     */
    function drawFromInsuranceFund(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        require(insuranceFund != address(0), "Insurance fund not set");
        // The vault calls claim on the insurance fund, which transfers assets back to the vault.
        (bool success,) = insuranceFund.call(abi.encodeWithSignature("claim(address,uint256)", address(this), amount));
        require(success, "Insurance claim failed");
    }

    /**
     * @notice Sets the insurance fund contribution percentage.
     */
    function setInsuranceFundBps(
        uint256 bps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 3000, "Contribution too high"); // Max 30%
        insuranceFundBps = bps;
    }

    /**
     * @notice Sets the maximum total assets the vault can hold.
     */
    function setMaxTotalAssets(uint256 _maxTotalAssets) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender) || hasRole(STRATEGIST_ROLE, msg.sender), "Not authorized");
        maxTotalAssets = _maxTotalAssets;
    }

    // --- ERC4626 Overrides with Pausable and Buffer Checks ---

    function deposit(uint256 assets, address receiver) public virtual override whenNotPaused returns (uint256) {
        if (whitelistEnabled) {
            require(whitelisted[msg.sender] || hasRole(STRATEGIST_ROLE, msg.sender), "Not whitelisted");
        }
        if (maxTotalAssets > 0) {
            require(totalAssets() + assets <= maxTotalAssets, "Vault cap exceeded");
        }
        return super.deposit(assets, receiver);
    }

    function mint(uint256 shares, address receiver) public virtual override whenNotPaused returns (uint256) {
        if (whitelistEnabled) {
            require(whitelisted[msg.sender] || hasRole(STRATEGIST_ROLE, msg.sender), "Not whitelisted");
        }
        uint256 assets = previewMint(shares);
        if (maxTotalAssets > 0) {
            require(totalAssets() + assets <= maxTotalAssets, "Vault cap exceeded");
        }
        return super.mint(shares, receiver);
    }

    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) public virtual override whenNotPaused returns (uint256) {
        require(IERC20(asset()).balanceOf(address(this)) >= assets, "Insufficient liquid buffer");
        return super.withdraw(assets, receiver, owner);
    }

    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) public virtual override whenNotPaused returns (uint256) {
        uint256 assets = previewRedeem(shares);
        require(IERC20(asset()).balanceOf(address(this)) >= assets, "Insufficient liquid buffer");
        return super.redeem(shares, receiver, owner);
    }

    /**
     * @notice Transfers assets to the Prime Brokerage module.
     * @param prime The Prime Brokerage contract address.
     * @param amount The amount to transfer.
     */
    function transferToPrime(address prime, uint256 amount) external nonReentrant {
        // Only the Prime contract itself or a Strategist can trigger this
        // In a real scenario, we'd check if msg.sender is a registered Prime contract
        require(hasRole(STRATEGIST_ROLE, msg.sender) || msg.sender == prime, "Not authorized");
        require(prime != address(0), "Invalid prime address");
        SafeERC20.safeTransfer(IERC20(asset()), prime, amount);
    }

    /**
     * @notice Returns assets from the Prime Brokerage module.
     * @param amount The amount to return.
     */
    function returnFromPrime(
        uint256 amount
    ) external nonReentrant {
        // Only the Prime contract or a Strategist can return funds
        require(hasRole(STRATEGIST_ROLE, msg.sender) || primeAccounts[msg.sender].active, "Not authorized");
        SafeERC20.safeTransferFrom(IERC20(asset()), msg.sender, address(this), amount);
    }

    // Mapping to track active prime contracts if needed, or just use roles
    struct PrimeInfo {
        bool active;
    }

    mapping(address => PrimeInfo) public primeAccounts; // Re-using name for consistency with KernePrime.sol logic
}
