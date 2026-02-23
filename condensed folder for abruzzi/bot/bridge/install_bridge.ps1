# Created: 2026-02-07
# ProtonMail Bridge Installer for Kerne Protocol
# Run this script as Administrator to download and install ProtonMail Bridge.
#
# Usage: Right-click -> Run with PowerShell (as Admin)
#   OR:  powershell -ExecutionPolicy Bypass -File bot\bridge\install_bridge.ps1

$ErrorActionPreference = "Stop"
$BridgeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallerPath = Join-Path $BridgeDir "Bridge-Installer.exe"
$DownloadUrl = "https://proton.me/download/bridge/Bridge-Installer.exe"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Kerne Protocol - ProtonMail Bridge Setup  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download Bridge installer
if (Test-Path $InstallerPath) {
    $fileSize = (Get-Item $InstallerPath).Length
    if ($fileSize -gt 1000000) {
        Write-Host "[OK] Bridge installer already downloaded ($([math]::Round($fileSize/1MB, 1)) MB)" -ForegroundColor Green
    } else {
        Write-Host "[!] Existing installer appears corrupt. Re-downloading..." -ForegroundColor Yellow
        Remove-Item $InstallerPath -Force
    }
}

if (-not (Test-Path $InstallerPath)) {
    Write-Host "[1/4] Downloading ProtonMail Bridge installer..." -ForegroundColor Yellow
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $InstallerPath -UseBasicParsing
        $fileSize = (Get-Item $InstallerPath).Length
        Write-Host "[OK] Downloaded ($([math]::Round($fileSize/1MB, 1)) MB)" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Download failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Manual download: https://proton.me/mail/bridge#download" -ForegroundColor Yellow
        Write-Host "Save the installer to: $InstallerPath" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Run installer
Write-Host "[2/4] Launching ProtonMail Bridge installer..." -ForegroundColor Yellow
Write-Host "       Follow the installation wizard to complete setup." -ForegroundColor Gray
Start-Process -FilePath $InstallerPath -Wait

# Step 3: Post-install instructions
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  POST-INSTALLATION SETUP                   " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[3/4] Configure ProtonMail Bridge:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Open ProtonMail Bridge (should auto-launch)" -ForegroundColor White
Write-Host "  2. Sign in with your kerne.systems ProtonMail account" -ForegroundColor White
Write-Host "  3. Click on your account name in Bridge" -ForegroundColor White
Write-Host "  4. Copy the SMTP password (NOT your ProtonMail password)" -ForegroundColor White
Write-Host "  5. Note the SMTP settings:" -ForegroundColor White
Write-Host "     - Host: 127.0.0.1" -ForegroundColor Gray
Write-Host "     - Port: 1025" -ForegroundColor Gray
Write-Host "     - Security: STARTTLS" -ForegroundColor Gray
Write-Host ""

# Step 4: Update .env
Write-Host "[4/4] Update bot/.env with your Bridge credentials:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  PROTON_SMTP_HOST=127.0.0.1" -ForegroundColor Gray
Write-Host "  PROTON_SMTP_PORT=1025" -ForegroundColor Gray
Write-Host "  PROTON_EMAIL=contact@kerne.systems" -ForegroundColor Gray
Write-Host "  PROTON_PASSWORD=<paste-bridge-password-here>" -ForegroundColor Gray
Write-Host "  AUTONOMOUS_OUTREACH=true" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup complete! Bridge must be running    " -ForegroundColor Green
Write-Host "  whenever the email outreach bot operates. " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Optional: Add Bridge to startup
$addStartup = Read-Host "Add ProtonMail Bridge to Windows startup? (y/n)"
if ($addStartup -eq "y") {
    $bridgeExe = "$env:LOCALAPPDATA\protonmail\bridge\Proton Mail Bridge.exe"
    if (-not (Test-Path $bridgeExe)) {
        $bridgeExe = "${env:ProgramFiles}\Proton\Bridge\Proton Mail Bridge.exe"
    }
    if (Test-Path $bridgeExe) {
        $startupFolder = [Environment]::GetFolderPath("Startup")
        $shortcutPath = Join-Path $startupFolder "ProtonMail Bridge.lnk"
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $bridgeExe
        $shortcut.Save()
        Write-Host "[OK] Bridge added to Windows startup" -ForegroundColor Green
    } else {
        Write-Host "[!] Could not find Bridge executable. Add it manually to startup." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "To test the email system, run:" -ForegroundColor Cyan
Write-Host "  python -c `"from bot.email_manager import EmailManager; m = EmailManager(); print(m.get_outreach_stats())`"" -ForegroundColor Gray
Write-Host ""