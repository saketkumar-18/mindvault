# MindVault backend development setup.
# Creates a virtualenv and installs the backend with dev dependencies.

param(
    [switch]$ML
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"

Write-Host "Setting up MindVault backend..."
Push-Location $backend
try {
    python -m venv .venv
    $venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
    if ($ML) {
        & $venvPython -m pip install -e ".[dev,ml]" --quiet
    } else {
        & $venvPython -m pip install -e ".[dev]" --quiet
    }
    Write-Host "Backend ready. Activate:  backend\.venv\Scripts\Activate.ps1"
    Write-Host "Run:                  python -m mindvault"
    Write-Host "OpenAPI docs:         http://127.0.0.1:8000/docs"
} finally {
    Pop-Location
}
