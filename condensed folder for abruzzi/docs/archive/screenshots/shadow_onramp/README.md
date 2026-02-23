// Created: 2026-02-04
# Shadow Onramp Screenshot Archive

This directory serves as a chronological audit trail for the Shadow Onramp operations.

## Phase 2: Polygon to Base (SideShift.ai) - 2026-02-04

### 1. [16:30] - Initial SideShift Configuration (Error Detected)
- **Description:** User attempted to configure Polygon USDC to Base USDC.
- **Audit Note:** Identified two critical errors:
    1. Recipient address was set to the Burner Wallet (`0x14...3946`) instead of the Treasury.
    2. Token mismatch warning (Native vs Bridged USDC).
- **Action:** Instructed user to cancel and reconfigure.

### 2. [16:33] - Corrected SideShift Configuration
- **Description:** User reconfigured the swap.
- **Audit Note:** Verified correct Treasury recipient (`0x57D4...0A99`), Variable Rate, and correct token pair.
- **Action:** Authorized user to proceed.

### 3. [16:34] - Waiting for Deposit
- **Description:** SideShift generated the deposit address `0x5701...8C9A`.
- **Audit Note:** Confirmed deposit address and receiving treasury address are aligned.
- **Action:** Instructed user to click "Send from Wallet".

### 4. [16:36] - Deposit Modal (Switch Network)
- **Description:** SideShift modal showing balance and gas fees.
- **Audit Note:** Wallet was on the wrong network.
- **Action:** Instructed user to click "Switch Network" to Polygon.

### 5. [16:37] - Final Transaction Review
- **Description:** Wallet extension review screen for 362.3 USDC.
- **Audit Note:** Blockaid simulation confirmed safety.
- **Action:** Authorized final confirmation.

### 6. [16:39] - Final Send Confirmation
- **Description:** Final "Send" screen showing contract address `0x5701...8c9a` and $0.01 fee.
- **Audit Note:** Final verification of the destination contract.
- **Action:** Final authorization to execute.