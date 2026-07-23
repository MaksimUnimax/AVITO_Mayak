# External references documentation

**Статус:** `MODULE_14_RF04_COMPLETE_RF05_NEXT`
**Дата актуализации:** 2026-07-23

## Current package

- `REFERENCE_REGISTRY_v1.1.md` — current cross-provider index and Telegram/MAX official records;
- `REFERENCE_REGISTRY_v1.0.md` — retained detailed Avito records incorporated by v1.1;
- `AVITO_REFERENCE_POLICY_v1.0.md`;
- `AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `MAX_REFERENCE_POLICY_v1.0.md`.

Provider documentation remains evidence and policy input only within exact scope.

Evidence does not authorize credentials, bots, parser calls, payment calls, external endpoints, live traffic or runtime activation by itself.

Telegram behavior is not inferred for MAX, and MAX behavior is not inferred for Telegram.

Synthetic and fake providers plus sandbox-ready adapters are required by Module 14.

Telegram, MAX, Avito and payment live profiles remain disabled until exact credentials, current evidence and operator gates are satisfied.

Provider acceptance is not proof of human reading. Ambiguous external effects are reconcile-first.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 have accepted semantic, contract, ownership, test and evidence foundations. Those foundations do not prove DB-backed or deployed runtime completion.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 remains historically accepted; RF-04 repository content is complete and closure is published for independent acceptance. RF-05 is next but not started and must not start before independent acceptance of the RF-04 closure; runtime remains unaccepted, runtime mutation is none, production remains blocked, and `PRODUCTION_READY` is not claimed.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Missing optional provider credentials do not block core automatic work.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
