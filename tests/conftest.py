"""
Test bootstrap for CI: ensure repository root is on sys.path so tests can import `src`.

This file is intentionally minimal and safe: it only prepends the project
root to sys.path if not already present. This mirrors how developers run tests
locally with PYTHONPATH=. and prevents `ModuleNotFoundError: No module named 'src'`
in CI environments that run pytest from different working directories.
"""
import os
import sys

# repo root (one level up from tests/)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
