#!/usr/bin/env bash
# Simple helper to run verification tests locally.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running verification tests..."
pytest -q tests/verification

echo "Verification tests finished."
