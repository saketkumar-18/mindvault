# MindVault backend dev server launcher (Windows).
# Usage: powershell -File scripts\dev.ps1   (optionally --port 8001)

param([int]$Port = 8000)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root "backend")
try {
    & ".\.venv\Scripts\python.exe" -m mindvault --port $Port
} finally {
    Pop-Location
}
