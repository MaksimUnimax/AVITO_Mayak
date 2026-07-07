# Маяк Авито — backlog документации

**Версия:** 2.1
**Статус:** APPROVED planning register

## DB-00 — evidence and supervision — ACCEPTED

TASK-001, REPORT-001/errata, remote supervision, ADR-0006 and append-only worklog. No code/deploy permission.

## DB-01 — Architecture Foundation — ACCEPTED

Historical architecture v1.0, security/privacy and environment isolation boundaries. Current authority: `ARCHITECTURE_BASELINE_v1.1.md`.

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

## DB-05 — Operations and Avito references — ACCEPTED

Runs 6–9 delivered Environment/Observability, Backup/Recovery, Deployment/Release, Windows Egress and Avito reference documents.

## DB-06 — Technical Baseline — RUN 10 ACCEPTED

- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`.

Server synchronization was independently accepted at GitHub SHA `099c9f0e35bb710f498d9f75ab38d542feb76be5` with clean `main` and `0/0` divergence.

## DB-07 — Telegram and MAX references — RUN 11 PUBLISHED

- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

Only current official/primary evidence is used. Run 11 creates no bots, credentials, provider traffic or runtime. Exact server synchronization to the Run 11 SHA is pending before acceptance.

## DB-08 — Module playbooks — RUNS 12–24

One autonomous `MODULE_PLAYBOOK.md` for each of 13 modules. Each playbook uses current architecture/technical/contracts/data/quality baselines and applicable provider evidence.

## DB-09 — Final audit

After Run 24 reconcile manifest/state/roadmap/backlog, links, historical/current versions, append-only integrity, open decisions, external evidence, all playbooks and absence of forbidden implementation artifacts. Then publish final governance acceptance and synchronize the exact final SHA.
