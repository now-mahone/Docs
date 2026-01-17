# Implementation Plan: Kerne LST-Solver & Shadow-Yield Hook

## 1. Smart Contracts (Solidity 0.8.24)

### 1.1 IKerneLSTHook & IKerneLSTSolver
- Define `IKerneLSTHook` with:
    - `updateShadowYield(address vault, uint256 amount)`
    - `getVerifiedAssets(address vault) external view returns (uint256)`
- Define `IKerneLSTSolver` with:
    - `executeLSTSwap(address tokenIn, address tokenOut, uint256 amount, bytes calldata data)`

### 1.2 KerneLSTHook.sol
- **Purpose**: Tracks accrued LST yield (shadow yield) that is not yet reflected in on-chain balances.
- **Architecture**:
    - Stores `mapping(address => uint256) public shadowYield`.
    - Implements `getVerifiedAssets` to return `shadowYield[vault]`.
    - Restricts `updateShadowYield` to `STRATEGIST_ROLE`.
- **Location**: `src/KerneLSTHook.sol`

### 1.3 KerneLSTSolver.sol
- **Purpose**: Executes high-frequency LST yield capture and arbitrage.
- **Architecture**:
    - Authorized to perform swaps on Aerodrome and Uniswap V3.
    - Uses `IERC3156FlashBorrower` for capital efficiency.
    - Profit distribution: 20% to `KerneInsuranceFund`, remainder to `KerneVault`.
- **Location**: `src/KerneLSTSolver.sol`

## 2. Bot Logic (Python 3.10)

### 2.1 LST Capture Engine
- **Location**: `bot/solver/lst_capture_engine.py`
- **Responsibilities**:
    - **Rate Tracking**: Fetch APR/rebase data for wstETH, cbETH, and rETH.
    - **Yield Accounting**: Calculate shadow yield based on vault LST holdings.
    - **Execution**: Identify "LST Gaps" (price vs. backing) and trigger `KerneLSTSolver`.
- **Integration**: Uses `Web3.py` for contract interaction and `loguru` for auditing.

## 3. Test Suite

### 3.1 Foundry (Contract Tests)
- `test/KerneLSTHook.t.sol`: Test yield reporting and access control.
- `test/KerneLSTSolver.t.sol`: Test flash-loan swaps and profit splits.
- `test/Integration_LST.t.sol`: Full cycle: Bot report -> Hook update -> Vault totalAssets check.

### 3.2 Pytest (Bot Tests)
- `bot/tests/test_lst_engine.py`: Test rate fetching and shadow yield math using mocks.

## 4. Deployment & Configuration

### 4.1 Deployment Script
- `script/DeployLST.s.sol`:
    1. Deploy `KerneLSTHook`.
    2. Deploy `KerneLSTSolver`.
    3. Grant `STRATEGIST_ROLE` to bot on Hook.
    4. Grant `SOLVER_ROLE` to bot on Solver.
    5. Set `KerneVault.setVerificationNode(KerneLSTHook)`.

## 5. Success Criteria
- `KerneVault.totalAssets()` increases correctly when `KerneLSTHook` is updated.
- `KerneLSTSolver` generates net profit in LST/WETH spreads.
- Zero unauthorized access to shadow yield updates.
- Bot maintains < 1s latency for LST gap capture.
