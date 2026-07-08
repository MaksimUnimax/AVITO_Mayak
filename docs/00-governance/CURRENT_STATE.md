# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.20
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–19 published; Run 18 server sync accepted; Run 19 server synchronization required before Run 20`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 18 Egress Routing was independently accepted on the server at GitHub SHA `fb55ec29708cb0f4de745504393fb02afb62ce3a`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact one-commit publication range, nine-path set, route/lease/outcome/reconciliation evidence and `ER-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 19 publishes `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md`. It defines authoritative notification event intake, durable outbox state, deduplication, delivery attempts, delivery logs, channel routing intent, retry/reconciliation boundaries and provider-adapter handoff without choosing or creating queue, worker, provider runtime, Telegram/MAX implementation, database schema, migration, notification delivery execution or infrastructure.

Public `main` remains the factual source of truth. Run 19 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 19 published SHA and that report is independently verified.

## Current approved foundations

### Architecture and Technical

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

### Contracts, data and quality

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`;
- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`;
- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

### Operations and references

- current operations documents listed by `docs/MANIFEST.md`;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`;
- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- current Avito, Telegram and MAX policy/evidence documents.

### Module playbooks

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12 accepted;
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13 accepted;
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14 accepted;
- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md` — Run 15 accepted;
- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md` — Run 16 accepted;
- `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md` — Run 17 accepted;
- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md` — Run 18 accepted;
- `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md` — Run 19 published; exact server sync pending.
- Modules 09–13 remain RESERVED and are scheduled as Runs 20–24.

## Notification Delivery consequences

- Notification Delivery is the only owner of notification event intake records, durable outbox items, delivery attempts, delivery logs, deduplication state and provider-delivery reconciliation state.
- The module consumes only committed Scan domain events after the Scan commit point. Parser success, Egress transport success and Scan comparison success are not notification delivery success.
- Baseline-established facts and baseline contents do not create user-visible listing-change deliveries under current v1.0 semantics.
- Notification failure, ambiguity or retry state never rolls back committed Scan observations, listing state or domain events.
- Telegram Adapter and MAX Adapter own provider-specific mapping/transport details after their playbooks; Notification Delivery owns generic outbox and delivery-attempt semantics.
- Provider callback/webhook, message rendering, chat identity, bot runtime, Mini App behavior and channel-specific payload schemas remain adapter scope and are not selected by Run 19.
- Exact queue/worker technology, delivery schedule, retry/backoff values, rate limits, channel priority, quiet hours, message templates, retention and read/ack semantics remain unselected.
- OD-004, OD-012 and OD-013 remain unresolved and all OD-001–OD-014 remain open.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, bot, Telegram/MAX request, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 19 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal notification event/outbox/attempt/reconciliation boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 20 of 24 — Telegram Adapter `MODULE_PLAYBOOK.md`.
