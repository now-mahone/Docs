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
import { IComplianceHook } from "./interfaces/IComplianceHook.sol";

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

    /// @notice The address of the verification node for Proof of Reserve
    address public verificationNode;

    /// @notice The last time the strategist reported off-chain assets or reserve
    uint256 public lastReportedTimestamp;

    /// @notice Whether whitelisting is enabled for this vault
    bool public whitelistEnabled;

    /// @notice Mapping of whitelisted addresses
    mapping(address => bool) public whitelisted;

    /// @notice External compliance hook for automated KYC/AML
    IComplianceHook public complianceHook;

    /// @notice The maximum amount of assets the vault can hold (0 = unlimited)
    uint256 public maxTotalAssets;

    /// @notice The projected annual percentage yield (in basis points, e.g., 1500 = 15%)
    /// @dev Updated by the strategist based on funding rates and LST rewards.
    uint256 public projectedAPY;

    /// @notice The address of the yield oracle for TWAY reporting
    address public yieldOracle;

    /// @notice The treasury address for fee collection
    address public treasury;

    /// @notice Circuit breaker: Maximum deposit allowed in a single transaction
    uint256 public maxDepositLimit;

    /// @notice Circuit breaker: Maximum withdrawal allowed in a single transaction
    uint256 public maxWithdrawLimit;

    /// @notice Circuit breaker: Minimum solvency ratio required for operations (e.g., 10100 = 101%)
    uint256 public minSolvencyThreshold;

    // --- Events ---
    event OffChainAssetsUpdated(uint256 oldAmount, uint256 newAmount, uint256 timestamp);
    event FundsSwept(uint256 amount, address destination);
    event HedgingReserveUpdated(uint256 oldAmount, uint256 newAmount, uint256 timestamp);
    event ProjectedAPYUpdated(uint256 oldAPY, uint256 newAPY, uint256 timestamp);
    event CircuitBreakersUpdated(uint256 maxDeposit, uint256 maxWithdraw, uint256 minSolvency);
    event ComplianceHookUpdated(address indexed oldHook, address indexed newHook);
    event YieldOracleUpdated(address indexed oldOracle, address indexed newOracle);
    event VerificationNodeUpdated(address indexed oldNode, address indexed newNode);
    event FounderWealthCaptured(uint256 amount, address indexed recipient);
    event InsuranceFundContribution(uint256 amount);

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
        _grantRole(PAUSER_ROLE, strategist_);

        founder = founder_;
        founderFeeBps = founderFeeBps_;

        if (performanceFeeBps_ > 0 && performanceFeeBps_ <= 2000) {
            grossPerformanceFeeBps = performanceFeeBps_;
        }
        whitelistEnabled = whitelistEnabled_;

        if (totalSupply() == 0) {
            _mint(admin_, 1000);
        }
    }

    /**
     * @notice Returns the exchange deposit address.
     */
    function getExchangeDepositAddress() public view returns (address) {
        return exchangeDepositAddress;
    }

    // --- Accounting Overrides ---

    /**
     * @notice Returns the total amount of assets managed by the vault.
     */
    function totalAssets() public view virtual override returns (uint256) {
        uint256 verifiedAssets = 0;
        if (verificationNode != address(0)) {
            (bool success, bytes memory data) = verificationNode.staticcall(
                abi.encodeWithSignature("getVerifiedAssets(address)", address(this))
            );
            if (success && data.length == 32) {
                verifiedAssets = abi.decode(data, (uint256));
            }
        }

        // Use verified assets if available, otherwise fallback to reported hedgingReserve
        uint256 reserve = verifiedAssets > 0 ? verifiedAssets : hedgingReserve;
        return super.totalAssets() + offChainAssets + reserve;
    }

    /**
     * @notice Returns the solvency ratio of the vault (Assets / Liabilities).
     */
    function getSolvencyRatio() public view returns (uint256) {
        uint256 assets = totalAssets();
        uint256 liabilities = totalSupply();
        if (liabilities <= 1000) return 20000; // Account for dead shares
        return (assets * 10000) / liabilities;
    }

    function _checkSolvency() internal view {
        if (minSolvencyThreshold > 0 && totalSupply() > 1000) {
            uint256 ratio = getSolvencyRatio();
            require(ratio >= minSolvencyThreshold, "Solvency below threshold");
        }
    }

    // --- Strategist Functions ---

    /**
     * @notice Updates the amount of assets held off-chain.
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
     */
    function updateHedgingReserve(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAmount = hedgingReserve;
        hedgingReserve = amount;
        lastReportedTimestamp = block.timestamp;
        emit HedgingReserveUpdated(oldAmount, amount, block.timestamp);
    }

    /**
     * @notice Updates the projected APY for the vault.
     */
    function updateProjectedAPY(
        uint256 _projectedAPY
    ) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAPY = projectedAPY;
        projectedAPY = _projectedAPY;
        emit ProjectedAPYUpdated(oldAPY, _projectedAPY, block.timestamp);
    }

    // --- Admin Functions ---

    /**
     * @notice Sweeps a specified amount of underlying assets to the exchange deposit address.
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

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    function setFounder(
        address _founder
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_founder != address(0), "Founder cannot be zero address");
        founder = _founder;
    }

    function setFounderFee(
        uint256 bps
    ) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Not authorized");
        require(bps <= 2000, "Fee too high");
        founderFeeBps = bps;
    }

    function setTreasury(
        address _treasury
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    function setWhitelistEnabled(
        bool enabled
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        whitelistEnabled = enabled;
    }

    function setWhitelisted(address account, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        whitelisted[account] = status;
    }

    /**
     * @notice Batch sets the whitelisted status for multiple accounts.
     * @param accounts Array of addresses to update.
     * @param status True to whitelist, false to remove.
     */
    function batchSetWhitelisted(address[] calldata accounts, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        for (uint256 i = 0; i < accounts.length; i++) {
            whitelisted[accounts[i]] = status;
        }
    }

    function setComplianceHook(address _hook) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address oldHook = address(complianceHook);
        complianceHook = IComplianceHook(_hook);
        emit ComplianceHookUpdated(oldHook, _hook);
    }

    function setPerformanceFee(
        uint256 bps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 2000, "Fee too high");
        grossPerformanceFeeBps = bps;
    }

    function setInsuranceFund(
        address _insuranceFund
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        insuranceFund = _insuranceFund;
    }

    function captureFounderWealth(
        uint256 grossYieldAmount
    ) external onlyRole(STRATEGIST_ROLE) {
        require(founder != address(0), "Founder not set");
        uint256 fee = (grossYieldAmount * grossPerformanceFeeBps) / 10000;
        if (fee > 0) {
            address recipient = treasury != address(0) ? treasury : founder;
            SafeERC20.safeTransfer(IERC20(asset()), recipient, fee);
            emit FounderWealthCaptured(fee, recipient);
        }
        uint256 insuranceContribution = (grossYieldAmount * insuranceFundBps) / 10000;
        if (insuranceContribution > 0 && insuranceFund != address(0)) {
            IERC20(asset()).approve(insuranceFund, insuranceContribution);
            (bool success,) = insuranceFund.call(abi.encodeWithSignature("deposit(uint256)", insuranceContribution));
            require(success, "Insurance deposit failed");
            emit InsuranceFundContribution(insuranceContribution);
        }
    }

    function drawFromInsuranceFund(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        require(insuranceFund != address(0), "Insurance fund not set");
        (bool success,) = insuranceFund.call(abi.encodeWithSignature("claim(address,uint256)", address(this), amount));
        require(success, "Insurance claim failed");
    }

    function setInsuranceFundBps(
        uint256 bps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 3000, "Contribution too high");
        insuranceFundBps = bps;
    }

    function setVerificationNode(
        address _node
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address oldNode = verificationNode;
        verificationNode = _node;
        emit VerificationNodeUpdated(oldNode, _node);
    }

    function setYieldOracle(
        address _oracle
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address oldOracle = yieldOracle;
        yieldOracle = _oracle;
        emit YieldOracleUpdated(oldOracle, _oracle);
    }

    function setMaxTotalAssets(
        uint256 _maxTotalAssets
    ) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender) || hasRole(STRATEGIST_ROLE, msg.sender), "Not authorized");
        maxTotalAssets = _maxTotalAssets;
    }

    function setCircuitBreakers(
        uint256 _maxDepositLimit,
        uint256 _maxWithdrawLimit,
        uint256 _minSolvencyThreshold
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        maxDepositLimit = _maxDepositLimit;
        maxWithdrawLimit = _maxWithdrawLimit;
        minSolvencyThreshold = _minSolvencyThreshold;
        emit CircuitBreakersUpdated(_maxDepositLimit, _maxWithdrawLimit, _minSolvencyThreshold);
    }

    function setFlashFee(uint256 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 100, "Fee too high");
        flashFeeBps = bps;
    }

    // --- IERC3156FlashLender Implementation ---

    /**
     * @dev The amount of currency available to be lent.
     * @param token The loan currency.
     * @return The amount of `token` that can be borrowed.
     */
    function maxFlashLoan(address token) external view override returns (uint256) {
        if (token != asset()) return 0;
        if (paused()) return 0;
        return IERC20(token).balanceOf(address(this));
    }

    /**
     * @dev The fee to be charged for a given loan.
     * @param token The loan currency.
     * @param amount The amount of tokens lent.
     * @return The amount of `token` to be charged for the loan, on top of the returned principal.
     */
    function flashFee(address token, uint256 amount) public view override returns (uint256) {
        require(token == asset(), "Unsupported token");
        
        // Institutional differentiation: 0% fee for Prime partners and Strategists
        if (hasRole(STRATEGIST_ROLE, msg.sender) || primeAccounts[msg.sender].active) {
            return 0;
        }
        
        return (amount * flashFeeBps) / 10000;
    }

    /**
     * @dev Initiate a flash loan.
     * @param receiver The receiver of the tokens in the loan, and the receiver of the callback.
     * @param token The loan currency.
     * @param amount The amount of tokens lent.
     * @param data Arbitrary data structure, propagated to the receiver.
     */
    function flashLoan(
        IERC3156FlashBorrower receiver,
        address token,
        uint256 amount,
        bytes calldata data
    ) external override nonReentrant whenNotPaused returns (bool) {
        require(token == asset(), "Unsupported token");
        uint256 fee = flashFee(token, amount);
        
        // Compliance check for whitelisted vaults
        if (whitelistEnabled) {
            bool isCompliant = whitelisted[address(receiver)] || hasRole(STRATEGIST_ROLE, msg.sender);
            if (!isCompliant && address(complianceHook) != address(0)) {
                isCompliant = complianceHook.isCompliant(address(this), address(receiver));
            }
            require(isCompliant, "Receiver not compliant");
        }

        SafeERC20.safeTransfer(IERC20(token), address(receiver), amount);

        require(
            receiver.onFlashLoan(msg.sender, token, amount, fee, data) == keccak256("ERC3156FlashBorrower.onFlashLoan"),
            "Flash loan callback failed"
        );

        SafeERC20.safeTransferFrom(IERC20(token), address(receiver), address(this), amount + fee);
        
        // Ensure solvency is maintained after fee collection
        _checkSolvency();
        
        return true;
    }

    // --- ERC4626 Overrides ---

    function maxDeposit(
        address receiver
    ) public view virtual override returns (uint256) {
        if (paused()) return 0;
        if (whitelistEnabled) {
            if (!whitelisted[receiver]) {
                if (address(complianceHook) != address(0)) {
                    if (!complianceHook.isCompliant(address(this), receiver)) return 0;
                } else {
                    return 0;
                }
            }
        }
        uint256 assets = totalAssets();
        if (maxTotalAssets > 0) {
            return assets >= maxTotalAssets ? 0 : maxTotalAssets - assets;
        }
        return type(uint256).max;
    }

    function maxMint(
        address receiver
    ) public view virtual override returns (uint256) {
        if (paused()) return 0;
        if (whitelistEnabled) {
            if (!whitelisted[receiver]) {
                if (address(complianceHook) != address(0)) {
                    if (!complianceHook.isCompliant(address(this), receiver)) return 0;
                } else {
                    return 0;
                }
            }
        }
        uint256 assets = totalAssets();
        if (maxTotalAssets > 0) {
            if (assets >= maxTotalAssets) return 0;
            return convertToShares(maxTotalAssets - assets);
        }
        return type(uint256).max;
    }

    function deposit(uint256 assets, address receiver) public virtual override whenNotPaused returns (uint256) {
        if (whitelistEnabled) {
            bool isCompliant = whitelisted[receiver] || hasRole(STRATEGIST_ROLE, msg.sender);
            if (!isCompliant && address(complianceHook) != address(0)) {
                isCompliant = complianceHook.isCompliant(address(this), receiver);
            }
            require(isCompliant, "Not whitelisted or compliant");
        }
        if (maxTotalAssets > 0) {
            require(totalAssets() + assets <= maxTotalAssets, "Vault cap exceeded");
        }
        if (maxDepositLimit > 0) {
            require(assets <= maxDepositLimit, "Deposit limit exceeded");
        }
        _checkSolvency();
        return super.deposit(assets, receiver);
    }

    function mint(uint256 shares, address receiver) public virtual override whenNotPaused returns (uint256) {
        if (whitelistEnabled) {
            bool isCompliant = whitelisted[receiver] || hasRole(STRATEGIST_ROLE, msg.sender);
            if (!isCompliant && address(complianceHook) != address(0)) {
                isCompliant = complianceHook.isCompliant(address(this), receiver);
            }
            require(isCompliant, "Not whitelisted or compliant");
        }
        uint256 assets = previewMint(shares);
        if (maxTotalAssets > 0) {
            require(totalAssets() + assets <= maxTotalAssets, "Vault cap exceeded");
        }
        if (maxDepositLimit > 0) {
            require(assets <= maxDepositLimit, "Deposit limit exceeded");
        }
        _checkSolvency();
        return super.mint(shares, receiver);
    }

    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) public virtual override whenNotPaused returns (uint256) {
        require(IERC20(asset()).balanceOf(address(this)) >= assets, "Insufficient liquid buffer");
        if (maxWithdrawLimit > 0) {
            require(assets <= maxWithdrawLimit, "Withdraw limit exceeded");
        }
        _checkSolvency();
        return super.withdraw(assets, receiver, owner);
    }

    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) public virtual override whenNotPaused returns (uint256) {
        uint256 assets = previewRedeem(shares);
        require(IERC20(asset()).balanceOf(address(this)) >= assets, "Insufficient liquid buffer");
        if (maxWithdrawLimit > 0) {
            require(assets <= maxWithdrawLimit, "Withdraw limit exceeded");
        }
        _checkSolvency();
        return super.redeem(shares, receiver, owner);
    }

    function getProjectedAPY() external view returns (uint256) {
        if (yieldOracle != address(0)) {
            (bool success, bytes memory data) = yieldOracle.staticcall(
                abi.encodeWithSignature("getTWAY(address)", address(this))
            );
            if (success && data.length == 32) {
                uint256 tway = abi.decode(data, (uint256));
                if (tway > 0) return tway;
            }
        }
        return projectedAPY;
    }

    function transferToPrime(address prime, uint256 amount) external nonReentrant {
        require(hasRole(STRATEGIST_ROLE, msg.sender) || msg.sender == prime, "Not authorized");
        require(prime != address(0), "Invalid prime address");
        _checkSolvency();
        SafeERC20.safeTransfer(IERC20(asset()), prime, amount);
    }

    function returnFromPrime(
        uint256 amount
    ) external nonReentrant {
        require(hasRole(STRATEGIST_ROLE, msg.sender) || primeAccounts[msg.sender].active, "Not authorized");
        SafeERC20.safeTransferFrom(IERC20(asset()), msg.sender, address(this), amount);
        _checkSolvency();
    }

    struct PrimeInfo {
        bool active;
    }

    mapping(address => PrimeInfo) public primeAccounts;
}
