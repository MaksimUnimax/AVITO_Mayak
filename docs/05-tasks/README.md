# Task packets

**Статус:** `MODULE_14_RF04_COMPLETE_RF05_NEXT`
**Дата актуализации:** 2026-07-23

## Historical task evidence

Historical TASK-001 and REPORT-001 references remain retained evidence through task lifecycle directories, manifests, governance logs and accepted reports.

Retained lifecycle directories:

- `active/`;
- `completed/`;
- `blocked/`;
- `change-requests/`.

Template:

- `TASK_TEMPLATE.md`.

Historical packets are not the current roadmap authority.

## Current task authority

Current task selection is derived from:

- fresh GitHub `main`;
- current governance;
- accepted append-only decisions;
- the Module 14 playbook;
- current prerequisites and independently verified evidence.

CLI receives one literal atomic task and must not select the next roadmap step.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 have accepted semantic, contract, ownership, test and evidence foundations. Those foundations do not prove deployed runtime completion.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 remains historically accepted; RF-04 repository content is complete and closure is published for independent acceptance. RF-05 is next but not started and must not start before independent acceptance of the RF-04 closure; runtime remains unaccepted, runtime mutation is none, production remains blocked, and `PRODUCTION_READY` is not claimed.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Live provider profiles remain disabled by default, and missing optional provider credentials do not block core automatic work.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
