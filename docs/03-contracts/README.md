# Contracts documentation

**Статус:** `MODULE_14_RF03_ACTIVE`
**Дата актуализации:** 2026-07-23

## Canonical documents

- `CONTRACT_PACKAGE_v1.0.md`;
- `ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `CONTRACT_CHANGE_POLICY_v1.0.md`.

These documents remain the accepted transport-neutral semantic, ownership, error, idempotency and change-control foundation.

## Current ownership boundary

Modules 01–13 retain ownership of their domain state.

Runtime assembly must use public contracts. Direct foreign-module table writes and private implementation imports replacing public contracts are forbidden.

Transport DTOs, UI state and provider payloads do not become domain authority or internal contracts.

Provider acceptance is not proof of human reading. Ambiguous external effects are reconcile-first.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 — active; RF-03-01 is independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 is independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`; RF-03-03 is published for independent acceptance; RF-03 closure remains pending; RF-04 is not started; runtime mutation is none and production remains blocked.

Runtime persistence adapters, PostgreSQL-backed contract behavior and cross-module HTTP/command wiring remain later Module 14 work.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Live provider profiles remain disabled by default, and missing optional provider credentials do not block core automatic work.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
## Current Module 14 governance

RF-03 is complete at repository-content level and closure evidence is published for independent acceptance. RF-04 is next but not started and may begin only after independent acceptance of the RF-03 closure commit. Runtime remains unaccepted, runtime mutation is none, and production remains blocked.
