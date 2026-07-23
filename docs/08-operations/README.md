# Operations documentation

**Статус:** `MODULE_14_RF03_ACTIVE`
**Дата актуализации:** 2026-07-23

## Accepted operations foundations

Current operations documents define accepted boundaries for:

- environment isolation;
- environment matrix;
- observability;
- backup and recovery;
- deployment and release;
- Windows Egress Agent behavior.

`WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md` remains an accepted operations foundation.

These documents do not prove that the complete project runtime is already deployed.

## Current repository and roadmap state

The repository contains source under `src/mayak`, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 have accepted semantic, contract, ownership, test and evidence foundations.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 — active; RF-03-01 is independently accepted through corrective SHA `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 matrix is published for independent acceptance; RF-03-03 and RF-03 closure remain pending; RF-04 is not started.
- RF-27 deployment — not accepted.

The existing project server is the authorized Module 14 runtime host, but project-owned deployment may occur only through exact gated tasks.

Acceptance runtime must be local-only. PostgreSQL must not be host-published.

Foreign containers, networks, volumes, databases, Nginx, listeners and services must not be altered or reused. Firewall, DNS, TLS and public ingress remain outside current authorization.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, SQLAlchemy, Psycopg, Alembic, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

Live provider profiles remain disabled by default, and missing optional provider credentials do not block core automatic work.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
