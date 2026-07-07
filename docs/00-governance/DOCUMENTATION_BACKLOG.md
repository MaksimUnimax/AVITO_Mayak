# Маяк Авито — backlog документации

**Версия:** 2.7
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

Reference Registry v1.1, Telegram Reference Policy v1.0 and MAX Reference Policy v1.0 were accepted at `642655a523af3591b1a024c39efa6978a064b2b8`. No provider runtime or sensitive access material was created.

## DB-08 — Module playbooks — RUNS 12–24

### Run 12 — Platform & Contracts — ACCEPTED

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `728b9062126fd7c2e816dde3a1a3ed9d42431cf2`.

### Run 13 — Identity & Access — ACCEPTED

- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `bcc33aa7120d60f977819319195000ab3a27a2c7`.

### Run 14 — Entitlements & Billing — ACCEPTED

- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `2346ccbbeaa8f1be18281fdf16fbec75cdb5052e`.

### Run 15 — Beacon Management — ACCEPTED

- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `2a73078c42cb03ef89d62b6161752f2069d35129`.

### Run 16 — Avito Parser Adapter — ACCEPTED

- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `9907b22d2192e60680bcdd9e4e98f6bb104cb18f`.
- Adapter extraction/normalization, explicit external outcomes and false-empty prohibition are fixed without live provider traffic or parser implementation.

### Run 17 — Scan Orchestration & Listing State — PUBLISHED

- `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md`.

The playbook fixes durable scan intent/run/claim semantics, immutable Beacon revision pinning, Parser outcome preservation, per-Beacon immutable observations/state, first-complete baseline suppression, subsequent listing-ID and ID+price-pair differences, reconciliation and post-commit domain events. OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain unresolved. Exact server synchronization to the Run 17 SHA is pending before acceptance.

### Runs 18–24 — RESERVED

One autonomous `MODULE_PLAYBOOK.md` remains required for each module 07–13 in route order. Egress Routing must provide explicit route/lease/outcome contracts without owning Scan state; Notification Delivery must consume committed Scan domain events and never infer them from Parser/route outcomes.

## DB-09 — Final audit

After Run 24 reconcile manifest/state/roadmap/backlog, links, historical/current versions, append-only integrity, open decisions, external evidence, all playbooks and absence of forbidden implementation artifacts. Then publish final governance acceptance and synchronize the exact final SHA.
