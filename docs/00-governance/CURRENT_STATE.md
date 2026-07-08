# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.21
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–20 published; Run 19 server sync accepted; Run 20 server synchronization required before Run 21`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 19 Notification Delivery was independently accepted on the server at GitHub SHA `c1fd2f78883880a58e337753a5013d81a65e50d7`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact nine-commit publication range, nine-path set, notification event/outbox/attempt/reconciliation evidence and `ND-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 20 publishes `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md`. It defines Telegram provider identity mapping, inbound update authenticity/replay boundaries, command/callback/deep-link normalization, Mini App initData validation boundary, outbound provider request/outcome mapping and provider-effect reconciliation without creating a bot, token, webhook, polling loop, Mini App, SDK, provider call, database schema, migration, endpoint, certificate, port, service or runtime.

Public `main` remains the factual source of truth. Run 20 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 20 published SHA and that report is independently verified.

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
- `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md` — Run 19 accepted;
- `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md` — Run 20 published; exact server sync pending.
- Modules 10–13 remain RESERVED and are scheduled as Runs 21–24.

## Telegram Adapter consequences

- Telegram Adapter is the only owner of Telegram provider identity mapping, update intake evidence, Telegram update replay/deduplication state, command/callback/deep-link normalization, Mini App validation result references and Telegram provider outcome mapping.
- Telegram user/chat/message/update IDs are external provider identifiers and do not replace internal `account_id`, `beacon_id`, Notification outbox/attempt IDs or common correlation IDs.
- Telegram Adapter does not own generic notification outbox, Identity account/linking state, Beacon configuration, Scan state, Egress route state or MAX provider mapping.
- Webhook and `getUpdates` remain unselected operational modes. Run 20 does not create endpoint, polling loop, certificate, port or provider runtime.
- `initDataUnsafe` is not trusted. Future Mini App usage must validate raw `Telegram.WebApp.initData` server-side and still route identity/linking through Identity & Access.
- Telegram Bot API `ok=true` is a provider API result class, not human read, click, generic Notification delivery success or business success.
- Unknown Telegram provider send/update effect is reconcile-first and must not be retried blindly.
- Exact command catalog, supported surfaces, mode per environment, bot token storage, retry/rate values, retention, Mini App screens and provider SDK remain unselected.
- OD-006, OD-007, OD-008, OD-012, OD-013 and OD-014 remain unresolved and all OD-001–OD-014 remain open.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, bot, Telegram/MAX request, webhook, polling loop, Mini App, token, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 20 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal Telegram identity/update/Mini-App/outbound/reconciliation boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 21 of 24 — MAX Adapter `MODULE_PLAYBOOK.md`.
