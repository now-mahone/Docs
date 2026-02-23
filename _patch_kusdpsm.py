# Patch KUSDPSM.sol for KRN-24-008 and KRN-24-012
with open('k:/kerne mid feb/src/KUSDPSM.sol', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# Fix KRN-24-008: Move currentExposure update BEFORE the insurance fund external call.
# Checks-Effects-Interactions pattern: effect (state update) must happen before interaction (external call).
content = content.replace(
    '''        if (psmBalance < normalizedAmountAfterFee && insuranceFund != address(0)) {
            uint256 deficit = normalizedAmountAfterFee - psmBalance;

            // SECURITY: Rate limit insurance fund draws to prevent drain attacks
            if (block.timestamp >= lastInsuranceDrawTimestamp + insuranceDrawCooldown) {
                // Reset the period
                insuranceDrawnThisPeriod = 0;
                lastInsuranceDrawTimestamp = block.timestamp;
            }

            // Enforce per-period draw limit (if configured)
            if (maxInsuranceDrawPerPeriod > 0) {
                require(
                    insuranceDrawnThisPeriod + deficit <= maxInsuranceDrawPerPeriod,
                    "Insurance draw limit exceeded for this period"
                );
            }

            (bool success, ) = insuranceFund.call(
                abi.encodeWithSignature("claim(address,uint256)", address(this), deficit)
            );
            if (success) {
                insuranceDrawnThisPeriod += deficit;
                psmBalance = IERC20(stable).balanceOf(address(this));
            }
        }

        require(psmBalance >= normalizedAmountAfterFee, "Insufficient stable reserves (Peg Defense Failed)");


        if (currentExposure[stable] >= amount) {
            currentExposure[stable] -= amount;
        } else {
            currentExposure[stable] = 0;
        }

        kUSD.safeTransferFrom(msg.sender, address(this), amount);
        IERC20(stable).safeTransfer(msg.sender, normalizedAmountAfterFee);

        emit Swap(msg.sender, address(kUSD), stable, amount, fee);
        emit ExposureUpdated(stable, currentExposure[stable]);
    }''',
    '''        // SECURITY FIX (KRN-24-008): Update state BEFORE external call (Checks-Effects-Interactions).
        // Moving currentExposure update here prevents a re-entrant call from using stale exposure data
        // to bypass stableCaps or other limits.
        if (currentExposure[stable] >= amount) {
            currentExposure[stable] -= amount;
        } else {
            currentExposure[stable] = 0;
        }
        emit ExposureUpdated(stable, currentExposure[stable]);

        if (psmBalance < normalizedAmountAfterFee && insuranceFund != address(0)) {
            uint256 deficit = normalizedAmountAfterFee - psmBalance;

            // SECURITY: Rate limit insurance fund draws to prevent drain attacks
            if (block.timestamp >= lastInsuranceDrawTimestamp + insuranceDrawCooldown) {
                // Reset the period
                insuranceDrawnThisPeriod = 0;
                lastInsuranceDrawTimestamp = block.timestamp;
            }

            // Enforce per-period draw limit (if configured)
            if (maxInsuranceDrawPerPeriod > 0) {
                require(
                    insuranceDrawnThisPeriod + deficit <= maxInsuranceDrawPerPeriod,
                    "Insurance draw limit exceeded for this period"
                );
            }

            // INTERACTION: External call happens after all state updates
            (bool success, ) = insuranceFund.call(
                abi.encodeWithSignature("claim(address,uint256)", address(this), deficit)
            );
            if (success) {
                insuranceDrawnThisPeriod += deficit;
                psmBalance = IERC20(stable).balanceOf(address(this));
            }
        }

        require(psmBalance >= normalizedAmountAfterFee, "Insufficient stable reserves (Peg Defense Failed)");

        kUSD.safeTransferFrom(msg.sender, address(this), amount);
        IERC20(stable).safeTransfer(msg.sender, normalizedAmountAfterFee);

        emit Swap(msg.sender, address(kUSD), stable, amount, fee);
    }''',
    1
)

# Fix KRN-24-012: Add array length check to setTieredFees
content = content.replace(
    '''    function setTieredFees(address stable, TieredFee[] calldata fees) external onlyRole(MANAGER_ROLE) {
        delete tieredFees[stable];''',
    '''    /// @dev SECURITY FIX (KRN-24-012): Bounded loop to prevent gas griefing.
    function setTieredFees(address stable, TieredFee[] calldata fees) external onlyRole(MANAGER_ROLE) {
        require(fees.length <= 20, "Too many fee tiers");
        delete tieredFees[stable];''',
    1
)

with open('k:/kerne mid feb/src/KUSDPSM.sol', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Done. File grew by {len(content)-original_len} chars.')
print('KRN-24-008 (CEI pattern) applied:', 'SECURITY FIX (KRN-24-008)' in content)
print('KRN-24-012 (unbounded loop) applied:', 'Too many fee tiers' in content)