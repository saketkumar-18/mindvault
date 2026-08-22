#!/usr/bin/env bash
# MindVault backend dev server launcher (Linux/macOS).
# Usage: ./scripts/dev.sh [--port 8000]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8000}"

cd "$ROOT/backend"
source .venv/bin/activate
python -m mindvault --port "$PORT"
