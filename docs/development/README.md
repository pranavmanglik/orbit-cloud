# Orbit Cloud: development

This package declares support for `>=3.11,<3.15` in `pyproject.toml`. That declaration is distinct from evidence that hosted CI ran.

Use the checks for each language manifest present in this repository:

### Python package

```bash
python -m pip install -e '.[dev]' build
pytest
ruff check src tests
ruff format --check src tests
mypy
```

Provider adapters are installed as sibling local packages during development. Their unit tests use injected fake asynchronous SDK clients and must not require ambient cloud credentials. Live checks remain separate, explicit jobs and must use a dedicated non-production account, project, or subscription.

## Contribution expectations

Add focused regression coverage for input bounds, query translation, cursor replay, cancellation, sanitized failures, timeouts, concurrency, partial results, and client lifecycle. Update the README, ADR, and relevant guide when the public contract, configuration, security property, provider support, or operational behavior changes. Report exact Python and SDK versions and services exercised; local checks do not imply hosted CI, live provider support, or release validation.
