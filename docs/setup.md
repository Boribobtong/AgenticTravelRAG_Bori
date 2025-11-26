# Setup & dependency guide

This project separates dependencies into modular requirement files so you can install only what you need.

Files
- `requirements-base.txt` — minimal runtime dependencies (lightweight). Installs core libraries such as `aiohttp`, `elasticsearch`, `pydantic`.
- `requirements-dev.txt` — development and CI testing dependencies (pytest, vcrpy, pytest-asyncio, etc.). Lightweight and safe for CI.
- `requirements-ml.txt` — heavy ML libraries (torch, transformers, sentence-transformers). Install only when you need local ML inference or training and have sufficient disk/CPU/GPU resources.
- `requirements.txt` — a convenience file referencing `requirements-base.txt` and `requirements-ml.txt` (for full install).

Recommended install workflows

- CI / Lightweight developer run (fast, small):

```bash
python -m pip install --upgrade pip
pip install -r requirements-base.txt
pip install -r requirements-dev.txt
```

- Full development (with ML):

```bash
# Base deps
pip install -r requirements-base.txt
# ML deps (large; only when needed)
pip install -r requirements-ml.txt
# Dev/test tools
pip install -r requirements-dev.txt
```

Notes
- The CI workflow uses `requirements-base.txt` and `requirements-dev.txt` to avoid installing heavy ML packages that can exhaust runner disk. Heavy-model tests should run on a separate, appropriately provisioned runner (self-hosted or separate job).
- If you need GPU-accelerated testing locally, install `requirements-ml.txt` and ensure you have compatible CUDA/CuDNN versions.
