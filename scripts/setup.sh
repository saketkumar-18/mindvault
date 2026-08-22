#!/usr/bin/env bash
# MindVault backend development setup (Linux/macOS).
# Usage: ./scripts/setup.sh [--ml]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

python3 -m venv .venv
source .venv/bin/activate

if [[ "${1:-}" == "--ml" ]]; then
  pip install -e ".[dev,ml]" --quiet
else
  pip install -e ".[dev]" --quiet
fi

echo "Backend ready. Activate:  source backend/.venv/bin/activate"
echo "Run:                      python -m mindvault"
echo "OpenAPI docs:             http://127.0.0.1:8000/docs"
