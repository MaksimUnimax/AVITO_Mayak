# CI Quality Gates Foundation

Version: 1.0
Status: `INDEPENDENTLY_ACCEPTED`
Date: 2026-07-26
Technical ID: `RF-07-01-CI-QUALITY-FOUNDATION-20260726`
RF step: RF-07-01
Base: `f03e97ec433e9278247a15dafcb1d96387132eba`
RF-06: `INDEPENDENTLY_ACCEPTED`
RF-07: `ACTIVE`
Accepted through: `01752323937aef4e247b22b5d79676d5e8f61e46`
Accepted run: `30199035445`
Correction note: the pytest vulnerability and compatibility correction is independently accepted through `7c594e49db75cce8a6f411fa0c8ceea59d8b0518`; accepted quality behavior and counts remain authoritative.
Runtime: `STOPPED`
Environment: `RUNTIME_ELIGIBLE`
Production: `NOT_PRODUCTION_READY`

## Scope

This task publishes a deterministic GitHub Actions quality foundation for repository and lock integrity, isolated frozen sync, exact CPython/uv identity, accepted Ruff and mypy baselines, import-linter, the complete current semantic suite, coverage and machine-readable evidence. It does not complete RF-07.

## Accepted RF-06 prerequisite

RF06_INDEPENDENTLY_ACCEPTED_THROUGH_F03E97EC433E9278247A15DAFCB1D96387132EBA. The locked baseline is 48 sdists, 246 wheels, 294 artifacts, 294/294 hashed, mypy 249 and the current suite 4511/4511 with 85% coverage. The corrective lock identity is pyproject `5b0727b99214d58c9fab83a6567b9485afca34a93ba0358a7bbd6ea04f7dcb7d`, uv.lock `e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6`, with pytest 9.0.3 and pytest-asyncio 1.4.0.

## Workflow triggers and permissions

RF07_CI_PROVIDER_GITHUB_ACTIONS. `CI Quality Foundation` runs on pushes to `main`, pull requests and manual `workflow_dispatch`. Top-level permission is `contents: read`; concurrency is ref-scoped and cancels in progress. It has no write permissions, services, matrix, branch/actor/fork skips or continue-on-error.

## Immutable action pins

RF07_IMMUTABLE_ACTION_PINS_ENFORCED. The only external actions are checkout `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), setup-uv `08807647e7069bb48b6ef5acd8ec9567f424441b` (v8.1.0) and upload-artifact `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (v7.0.1). Exact Python is 3.14.6 and exact uv is 0.11.31.

## Integrity and lock gate

`integrity-lock` checks Python standard GIL identity, exact uv, offline and regular `uv lock --check`, unchanged dependency bytes, lock record counts and hashes, then uploads safe evidence.

## Isolated sync

`quality-suite` requires successful `integrity-lock` and runs `uv sync --frozen --all-groups --python 3.14.6` in the workflow-owned `.venv`; dependency bytes are checked again.

## Ruff baseline

The verifier runs Ruff exactly twice. Both runs must be 648 with normalized identity `23094b89436ceb7894d9bbca81552f0e44e1cbd0f82a7a13073a1a87fe65e3b3`: RF07_RUFF_BASELINE_648_ACCEPTED and classification `RUFF_PREEXISTING_DEBT_NO_REGRESSION`.

## Mypy baseline

The verifier runs mypy exactly three times, including two fresh caches and one `--no-incremental` run. Each must be 249 errors, 29 notes, summary 249 and normalized identity `4f6ac7fa39b343f16b207ff5bed187a7447f87515115dee250a25ebf06126e11`: RF07_MYPY_BASELINE_249_ACCEPTED and classification `MYPY_PREEXISTING_DEBT_NO_REGRESSION`.

## Import-linter

`lint-imports` must exit zero with RF07_IMPORT_LINTER_3_0_REQUIRED: 3 contracts kept and 0 broken.

## Full semantic suite and coverage

`coverage run --branch -m pytest` followed by `coverage report` must produce RF07_CURRENT_SUITE_4511_4511_REQUIRED: 4511 collected, 4511 passed, 0 failed, 0 errors, and RF07_COVERAGE_85_REQUIRED: 85%.

## Evidence artifact schema and retention

Each job emits deterministic UTF-8 JSON and plain-text summaries with schema version 1, source SHA, tool identities, lock and quality fields, status and safe raw logs. Artifacts are named by source SHA and retained 30 days. Evidence contains no environment dump, secrets, credentials, private keys or populated `.env`.

## Local equivalent evidence

The same pinned toolchain, lock checks, task-owned isolated environment, verifier self-test, lock mode and quality mode pass locally. JSON status is `PASS`; source and tests remain byte-identical. Dependency-byte identity is superseded by the correction artifact pending independent acceptance.

## Security boundary

The verifier uses only the Python standard library, explicit argv lists, bounded subprocesses, no network and no `shell=True`; it normalizes `<WORKTREE>`, atomically writes output and redacts unexpected URL userinfo. No runtime, Docker, database, listener, service or foreign resource is touched.

## Explicitly deferred RF-07 capability gates

This task does not implement PostgreSQL service; PostgreSQL integration tests; Alembic from-zero; migration current-head; vulnerability scan; license gate; secret scan; Docker build; Compose validation; synthetic E2E. These are not waived. They remain required future RF-07 gates and must be added by exact later tasks.

## Rollback

The original RF-07-01 backup remains historical evidence. The pytest correction has its own task-owned backup and rollback instructions; do not modify main checkout or promoted inputs.

## Limitations

This is a quality foundation only. Accepted Ruff and mypy debt remains, and runtime is stopped. RF08_NOT_STARTED. RF-07 remains active; RF-08 and later capabilities are not started.

## RF-07-02 security foundation

The deterministic security and supply-chain foundation is published pending independent acceptance in [`CI_SECURITY_AND_SUPPLY_CHAIN_FOUNDATION_v1.0.md`](CI_SECURITY_AND_SUPPLY_CHAIN_FOUNDATION_v1.0.md).

## Verdict

RF07_LOCK_AND_ISOLATED_SYNC_GATE_IMPLEMENTED. RF07_01_PUBLISHED_PENDING_ACCEPTANCE. RUNTIME_ELIGIBLE. NOT_PRODUCTION_READY.

## Next gate

RF-07-01 is independently accepted through `01752323937aef4e247b22b5d79676d5e8f61e46`. Later RF-07 tasks must add the deferred gates. The correction artifact is published pending independent acceptance. RF07_REMAINS_ACTIVE.
