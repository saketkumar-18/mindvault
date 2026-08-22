# MindVault desktop packaging build (Windows).
# Builds the PyInstaller native bundle.
# Usage: powershell -File scripts\build_desktop.ps1   [--with-tauri]

param([switch]$WithTauri)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "Building frontend..."
Push-Location (Join-Path $root "frontend")
try { npm run build } finally { Pop-Location }

Write-Host "Installing PyInstaller..."
& (Join-Path $root "backend\.venv\Scripts\python.exe") -m pip install pyinstaller --quiet

Write-Host "Building PyInstaller bundle..."
Push-Location (Join-Path $root "desktop")
try {
    & (Join-Path $root "backend\.venv\Scripts\python.exe") -m PyInstaller --noconfirm mindvault.spec
    Write-Host "Done: desktop\dist\MindVault\MindVault.exe"
} finally { Pop-Location }

if ($WithTauri) {
    Write-Host "Tauri requires the Rust toolchain. See desktop/README.md."
}
