# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.22
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–21 published; Run 20 server sync accepted; Run 21 server synchronization required before Run 22`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 20 Telegram Adapter was independently accepted on the server at GitHub SHA `6fcc1b9a77a48b7f02cc5aba640f20a3ff23a461`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact nine-commit publication range, nine-path set, Telegram identity/update/Mini-App/outbound/reconciliation evidence and `TG-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 21 publishes `docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md`. It defines MAX partner/eligibility gates, provider identity mapping, Webhook and Long Polling boundaries, update authenticity/replay semantics, Mini App WebAppData validation boundary, contact-request boundary, outbound provider request/outcome mapping and provider-effect reconciliation without creating a partner profile, bot, token, webhook subscription, Long Polling loop, Mini App, SDK, provider call, database schema, migration, endpoint, certificate/trust-store change, port, service or runtime.

Public `main` remains the factual source of truth. Run 21 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 21 published SHA and that report is independently verified.

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
- `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md` — Run 20 accepted;
- `docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md` — Run 21 published; exact server sync pending.
- Modules 11–13 remain RESERVED and are scheduled as Runs 22–24.

## MAX Adapter consequences

- MAX Adapter is the only owner of MAX provider identity mapping, eligibility/moderation evidence references, update intake evidence, Webhook/Long Polling receipt evidence, event replay/deduplication state, command/callback/button/deep-link normalization, contact-validation references, Mini App validation result references and MAX provider outcome mapping.
- MAX user/chat/message/update-related IDs are external provider identifiers and do not replace internal `account_id`, `beacon_id`, Notification outbox/attempt IDs or common correlation IDs.
- MAX Adapter does not own generic notification outbox, Identity account/linking state, Beacon configuration, Scan state, Egress route state, Telegram provider mapping or legal eligibility decisions.
- Partner eligibility, verified profile and moderation are explicit gates and are not assumed.
- Production MAX update delivery uses Webhook under current official evidence; Long Polling remains development/test only and not production fallback.
- Webhook endpoint/TLS/443/certificate/trust-store/secret verification are operations/security gates and are not created by Run 21.
- MAX Mini App launch data is not trusted until server-side WebAppData validation succeeds; account linking still routes through Identity & Access.
- MAX API success is a provider operation result class, not human read, click, generic Notification delivery success or business success.
- Unknown MAX provider send/update effect is reconcile-first and must not be retried blindly.
- Exact command catalog, supported surfaces, eligibility evidence, partner/bot/moderation workflow, token storage, retry/rate values, retention, Mini App screens and provider SDK remain unselected.
- OD-006, OD-007, OD-008, OD-012, OD-013 and OD-014 remain unresolved and all OD-001–OD-014 remain open.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, bot, Telegram/MAX request, webhook, Long Polling loop, Mini App, token, partner profile, moderation submission, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate/trust-store change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 21 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal MAX eligibility/Webhook/Long-Polling/Mini-App/contact/outbound/reconciliation boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 22 of 24 — Admin & Support `MODULE_PLAYBOOK.md`.
