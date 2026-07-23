# Quality documentation

**Статус:** `MODULE_14_RF03_COMPLETE_RF04_NEXT`
**Дата актуализации:** 2026-07-23

## Current documents

- `TEST_STRATEGY_v1.0.md`;
- `FIXTURE_REGISTRY_v1.0.md`;
- `ACCEPTANCE_MATRIX_v1.1.md`;
- `REFERENCE_REGRESSION_POLICY_v1.0.md`.

Historical revision retained:

- `ACCEPTANCE_MATRIX_v1.0.md`.

These documents remain accepted quality, fixture, acceptance and regression foundations.

## Current executable quality contour

The repository contains:

- source under `src/mayak`;
- executable unit, contract and architecture tests;
- synthetic fixture files;
- `pyproject.toml`;
- `uv.lock`.

The accepted RF-02 baseline records 4511 passing tests on Python 3.14.

This baseline does not prove future GitHub Actions CI, isolated dependency synchronization, PostgreSQL integration, Alembic migration, Docker, deployed E2E, security, backup/restore, recovery or deployed failure-drill gates.

## Current roadmap state

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 is complete at repository-content level: RF-03-01 is independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`, RF-03-02 is independently accepted through `061757c4cfd9c5c4ea466539c4a92499e5b269d5`, RF-03-03 is independently accepted at `e8a38a1ce3e506f5d880129bb9781802cd69f48b`, and RF-03-04 closure evidence was published at `a6c5277fcb5596d3c53a59fbcdaec5c06e3456ff`; this corrective index-state repair is published for independent acceptance, and RF-03 closure acceptance remains pending independent ChatGPT verification of the corrective commit. RF-04 is next but not started and must not start before independent acceptance of this corrective chain; runtime remains unaccepted, runtime mutation is none, production remains blocked, and `PRODUCTION_READY` is not claimed.
- RF-07, RF-09, RF-24, RF-25, RF-26 and RF-28 — not accepted.

Modules 01–13 have accepted semantic, contract, ownership, test and evidence foundations. Those foundations do not prove DB-backed or deployed runtime completion.

The existing project server is authorized only through exact Module 14 tasks. Foreign resources remain protected. Live provider profiles remain disabled by default, and missing optional provider credentials do not block core automatic work.

GitHub Actions CI, Docker Compose, PostgreSQL 18 persistence, migrations from zero, API/worker/scheduler entry points, deployed Web Cabinet/Admin, deployed E2E, backup/restore, server deployment, operator pack and final handoff are not yet accepted.

Module 14 targets `READY_FOR_OPERATOR_ACCEPTANCE` and must not claim `PRODUCTION_READY`.
