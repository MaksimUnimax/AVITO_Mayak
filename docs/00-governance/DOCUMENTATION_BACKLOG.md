# Маяк Авито — backlog документации

**Версия:** 2.8
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

### Run 17 — Scan Orchestration & Listing State — ACCEPTED

- `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md`.
- Exact server synchronization accepted at `7dc5eb6c26c7cbe82a5db42dfeffaff521f01d90`.
- Durable scan/run state, immutable revision pinning, per-Beacon baseline/difference rules and post-commit scan-domain events are fixed without scheduler/worker/database/provider implementation.

### Run 18 — Egress Routing — PUBLISHED

- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`.

The playbook fixes agent/route registration, capability/readiness/health/quarantine ownership, bounded leases, server-side selection evidence, explicit transport outcomes, false-success prohibition, reconciliation-first ambiguity and replaceable Windows-agent boundaries. OD-009, OD-010, OD-011 and OD-013 remain unresolved. Route technology, topology, ports, tunnels/VPN/proxy, credentials, priority/fallback, thresholds, retry/rate values, cookies/sessions and retention remain blocked. Exact server synchronization to the Run 18 SHA is pending before acceptance.

### Runs 19–24 — RESERVED

One autonomous `MODULE_PLAYBOOK.md` remains required for each module 08–13 in route order. Notification Delivery must consume committed Scan domain events, own outbox/delivery attempts and preserve channel/provider ambiguity without treating Egress or Parser outcomes as delivery success.

## DB-09 — Final audit

After Run 24 reconcile manifest/state/roadmap/backlog, links, historical/current versions, append-only integrity, open decisions, external evidence, all playbooks and absence of forbidden implementation artifacts. Then publish final governance acceptance and synchronize the exact final SHA.
