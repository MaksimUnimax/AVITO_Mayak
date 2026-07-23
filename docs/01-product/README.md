# Product documentation

**Статус:** `MODULE_14_RF02_COMPLETE_RF03_NEXT`
**Дата актуализации:** 2026-07-23

## Historical product input

- `MAYAK_AVITO_TARGET_MODEL_v0.1.md` remains the retained historical product target and context according to its own document status.
- Historical product text remains traceability evidence and is not silently rewritten by this index.

## Current authority

Current MVP scope and owner decisions are governed by:

- current GitHub `main`;
- accepted append-only decisions;
- `docs/00-governance/OPEN_DECISIONS.md`;
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`;
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md`.

Deferred production expansion, live-provider evidence and operator acceptance do not create a new unanswered owner product question inside Module 14.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 have accepted semantic, contract, ownership, test and evidence foundations. Those foundations do not by themselves prove DB-backed or deployed runtime completion.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — complete at repository-content level; closure evidence published for independent acceptance.
- RF-03 — next permitted roadmap step after independent acceptance of the RF-02 closure commit.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Live provider profiles remain disabled by default, and missing optional provider credentials do not block core automatic work.

Product documentation does not itself prove runtime deployment.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
