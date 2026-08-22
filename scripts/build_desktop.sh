#!/usr/bin/env bash
# MindVault desktop packaging build (Linux/macOS).
# Builds the PyInstaller native bundle.
# Usage: ./scripts/build_desktop.sh [--with-tauri]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building frontend..."
(cd "$ROOT/frontend" && npm run build)

echo "Installing PyInstaller..."
"$ROOT/backend/.venv/bin/python" -m pip install pyinstaller --quiet

echo "Building PyInstaller bundle..."
(cd "$ROOT/desktop" && "$ROOT/backend/.venv/bin/python" -m PyInstaller --noconfirm mindvault.spec)
echo "Done: desktop/dist/MindVault/"

if [[ "${1:-}" == "--with-tauri" ]]; then
  echo "Tauri requires the Rust toolchain. See desktop/README.md."
fi
