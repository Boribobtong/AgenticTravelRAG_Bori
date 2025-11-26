# CI Notes — Phase3 Core Enhancements

This document summarizes CI considerations for the Phase3 changes (PriceAggregator,
ClimateDB, streaming responses) and guidance for optional heavy tests.

1) Keep base workflows lightweight
- Do not install ML/Cloud SDK libraries by default in the base CI workflow. This keeps
  runners lean and avoids "No default credentials" or large dependency installs.

2) Optional ML / Cloud integration job
- Add a separate workflow `ci-ml-tests.yml` that runs only on-demand or via `workflow_dispatch`.
- This workflow can install `requirements-ml.txt` and run ML-heavy integration tests.

3) Secrets and credentials for LLMs
- Any job that initializes a cloud LLM (e.g., Google Gemini) must have required
  credentials set in Actions Secrets (e.g., `GOOGLE_APPLICATION_CREDENTIALS_JSON`)
  and load them securely during the job.

4) Test bootstrap
- Add `tests/conftest.py` which ensures the repository root is on `sys.path` so
  tests import `src` reliably across different CI working directories.

5) Streaming and async tests
- Streaming tests are implemented with pure-Python fallbacks and do not require
  network access. Use pytest-asyncio for any advanced async tests.
