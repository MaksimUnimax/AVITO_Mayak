# Маяк Авито — backlog документации

**Версия:** 2.3
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

Technical Baseline package and exact server synchronization accepted.

## DB-07 — Telegram and MAX references — RUN 11 ACCEPTED

- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

Exact server synchronization was independently accepted at `642655a523af3591b1a024c39efa6978a064b2b8`. No provider runtime or sensitive access material was created.

## DB-08 — Module playbooks — RUNS 12–24

### Run 12 — Platform & Contracts — ACCEPTED

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md`.

Exact server synchronization was independently accepted at `728b9062126fd7c2e816dde3a1a3ed9d42431cf2`. The playbook remains a prerequisite only and creates no implementation artifact.

### Run 13 — Identity & Access — PUBLISHED

- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md`.

The playbook fixes account, identity, contact point, credential-reference, role assignment, session, auth challenge and identity-link challenge boundaries. It keeps OD-006, OD-007 and OD-008 open and creates no implementation artifact. Exact server synchronization to the Run 13 SHA is pending before acceptance.

### Runs 14–24 — RESERVED

One autonomous `MODULE_PLAYBOOK.md` remains required for each module 03–13 in route order. Later playbooks must use Identity & Access public contracts for actor/account/role/ownership checks and must not duplicate identity storage.

## DB-09 — Final audit

After Run 24 reconcile manifest/state/roadmap/backlog, links, historical/current versions, append-only integrity, open decisions, external evidence, all playbooks and absence of forbidden implementation artifacts. Then publish final governance acceptance and synchronize the exact final SHA.
