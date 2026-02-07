@echo off
:: Created: 2026-02-07
:: One-click ProtonMail Bridge installer for Kerne Protocol
:: Double-click this file to download and install ProtonMail Bridge

echo.
echo ============================================
echo   Kerne Protocol - ProtonMail Bridge Setup
echo ============================================
echo.
echo This will download and install ProtonMail Bridge.
echo Bridge is REQUIRED for autonomous email outreach.
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0install_bridge.ps1"

pause