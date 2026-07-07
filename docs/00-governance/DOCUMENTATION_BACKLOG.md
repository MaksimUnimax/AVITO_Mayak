# Маяк Авито — backlog документации

**Версия:** 2.0
**Статус:** APPROVED planning register

## DB-00 — evidence and supervision — ACCEPTED

TASK-001, REPORT-001/errata, remote supervision, ADR-0006 and append-only worklog. No code/deploy permission.

## DB-01 — Architecture Foundation — ACCEPTED

Historical architecture v1.0, security/privacy and environment isolation boundaries.

Current architecture authority is `ARCHITECTURE_BASELINE_v1.1.md`.

## DB-02 — Common Contract Foundation — ACCEPTED

- `CONTRACT_PACKAGE_v1.0.md`;
- `ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `CONTRACT_CHANGE_POLICY_v1.0.md`.

## DB-03 — Data and Compatibility — ACCEPTED

- `DATA_MODEL_v1.0.md`;
- `MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

## DB-04 — Quality — ACCEPTED

- `TEST_STRATEGY_v1.0.md`;
- `FIXTURE_REGISTRY_v1.0.md`;
- `ACCEPTANCE_MATRIX_v1.1.md`;
- `REFERENCE_REGRESSION_POLICY_v1.0.md`.

Acceptance Matrix v1.1 supersedes v1.0 for future work and adds Technical Baseline gates plus module run numbering 12–24.

## DB-05 — Operations and Avito references — ACCEPTED

### Run 6

- `ENVIRONMENT_MATRIX_v1.0.md` historical;
- `OBSERVABILITY_AND_ALERTING_v1.0.md`.

### Run 7

- `BACKUP_AND_RECOVERY_v1.0.md`;
- `DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`.

### Run 8

- `WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### Run 9

- `REFERENCE_REGISTRY_v1.0.md`;
- `AVITO_REFERENCE_POLICY_v1.0.md`;
- `AVITO_REFERENCE_EVIDENCE_v1.0.md`.

## DB-06 — Technical Baseline — RUN 10 PUBLISHED

- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`.

This package selects core language, toolchain, framework, persistence, quality and telemetry boundaries and explicitly defers provider, frontend and deployment technologies.

It creates no code, lockfile, packages, environment, database or runtime.

## DB-07 — Telegram and MAX references — RUN 11 NEXT

- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

Only current official/primary evidence. No bots, credentials, external calls or runtime.

## DB-08 — Module playbooks — RUNS 12–24

One autonomous `MODULE_PLAYBOOK.md` for each of 13 modules.

Each playbook uses current Architecture Baseline v1.1, Technical Baseline v1.0, Acceptance Matrix v1.1 and applicable provider evidence.

## DB-09 — Final audit

After Run 24 reconcile manifest/state/roadmap/backlog, links, historical/current versions, append-only integrity, open decisions, external evidence, all playbooks and absence of forbidden implementation artifacts. Then publish final governance acceptance and synchronize exact SHA.
