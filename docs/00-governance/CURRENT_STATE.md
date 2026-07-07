# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.11
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.13 — Technical Baseline published; Runs 1–10 documented; Run 10 server synchronization required before Run 11`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 9 Avito reference package is accepted in GitHub.

Run 10 adds the missing Technical Baseline gate and expands the documentation route from 23 to 24 runs. It selects the core stack without creating code, dependency files, environments or infrastructure.

Public `main` remains the factual source of truth. Server checkout acceptance always refers to one exact published SHA.

## Current approved foundations

### Architecture and Technical

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

### Contracts

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

### Data and compatibility

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

### Quality

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

### Operations

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`;
- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### Avito references

- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`.

## Selected core technical baseline

- CPython 3.14 standard build;
- uv with `pyproject.toml` and `uv.lock` after bootstrap;
- FastAPI and Uvicorn;
- Pydantic v2 and pydantic-settings;
- HTTPX;
- PostgreSQL 18;
- SQLAlchemy 2, Psycopg 3 and Alembic;
- pytest, pytest-asyncio and RESpx;
- Ruff, mypy, import-linter and coverage.py;
- OpenTelemetry instrumentation boundary;
- PostgreSQL-backed durable work/outbox; no external broker at baseline.

Provider SDKs, exact Avito adapter stack, frontend, containerization, ingress, configuration delivery, telemetry backend and Windows packaging remain deferred.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, service, container, listener, port, sensitive access material, external call, parser, bot, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize server checkout to the exact Run 10 published GitHub SHA.
2. Verify clean worktree and exact SHA.
3. Continue with Run 11 of 24 — Telegram and MAX Reference Policies.
4. Module playbooks begin at Run 12; Platform & Contracts is Run 12.
