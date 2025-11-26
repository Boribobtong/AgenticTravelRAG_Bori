# Verification branch and how to run

This small helper explains how to run the verification tests added as part of Phase 1.

Files added:
- `tests/verification/` - pytest tests that follow `docs/VERIFICATION_PLAN.md` checks.
- `scripts/run_verification.sh` - convenience script to run the verification tests locally.
- `.github/workflows/verification.yml` - CI workflow that runs tests on branches matching `verification/**`.

Run locally:

```bash
./scripts/run_verification.sh
```

Notes:
- Tests are written to skip gracefully if project modules are not importable. This prevents false negatives when running in minimal environments.
