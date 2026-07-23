# Architecture documentation

**Статус:** `MODULE_14_RF03_ACTIVE`
**Дата актуализации:** 2026-07-23

## Accepted semantic and design foundations

Current retained foundations include:

- `ARCHITECTURE_BASELINE_v1.1.md`;
- `TECHNICAL_BASELINE_v1.0.md`;
- `SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `DATA_MODEL_v1.0.md`;
- `MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

Historical revision retained:

- `ARCHITECTURE_BASELINE_v1.0.md`.

These documents remain semantic, logical, security and compatibility foundations. They do not prove that the physical acceptance runtime has already been implemented or deployed.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 retain ownership of their domain state and have accepted semantic, contract, test and evidence foundations.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 — active; RF-03-01 completion matrix is published for independent acceptance.

Exact physical PostgreSQL tables, keys, indexes, constraints, transaction/outbox boundaries, work leases, read projections, process model, migration plan, runtime topology, configuration schema and secrets boundary remain RF-04 scope.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Acceptance runtime remains local-only, PostgreSQL must not be host-published, and live providers remain disabled by default.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
