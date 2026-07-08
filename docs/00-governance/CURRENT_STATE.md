# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.23
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–22 published; Run 21 server sync accepted; Run 22 server synchronization required before Run 23`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 21 MAX Adapter was independently accepted on the server at GitHub SHA `c114818a23a400e97ee6d83c8ab54e419fa401df`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact nine-commit publication range, nine-path set, MAX eligibility/Webhook/Long-Polling/Mini-App/contact/outbound/reconciliation evidence and `MAX-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 22 publishes `docs/04-modules/11-admin-and-support/MODULE_PLAYBOOK.md`. It defines support cases, safe support reads, protected support commands, operator actor/scope gates, support audit records, escalation/reconciliation coordination, redaction/minimization boundaries and owning-module dispatch without creating admin UI, support CRM, role implementation, database schema, migration, audit store, service, port, credential, secret or runtime.

Public `main` remains the factual source of truth. Run 22 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 22 published SHA and that report is independently verified.

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
- `docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md` — Run 21 accepted;
- `docs/04-modules/11-admin-and-support/MODULE_PLAYBOOK.md` — Run 22 published; exact server sync pending.
- Modules 12–13 remain RESERVED and are scheduled as Runs 23–24.

## Admin & Support consequences

- Admin & Support owns support case/work-item records, safe support notes, support action requests, support audit references, escalation records and support read-model projections.
- Admin & Support uses public module services and read models only. It does not write directly to Identity, Entitlements, Beacon, Scan, Egress, Notification, Telegram, MAX, Web Cabinet or Filter Catalog state.
- Operator authority comes from Identity & Access verified actor context and server-assigned roles, not UI flags, provider usernames, chat names or local configuration.
- Support reads must preserve provenance, freshness/staleness, authorization scope, redaction and safe error semantics.
- Protected support mutations require actor verification, role/scope authorization, target validation, policy gate, explicit reason, idempotency, owning-module public command and audit outcome.
- Support notes are not authoritative business state and cannot close open decisions or mask ambiguous owning-module outcomes.
- Break-glass, impersonation, manual entitlement correction, manual Beacon correction, notification resend/suppression, data export/deletion, support note visibility and audit retention remain unselected.
- OD-006, OD-007, OD-008, OD-013 and OD-014 remain unresolved and all OD-001–OD-014 remain open.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, admin UI, support CRM, role implementation, audit store, break-glass, impersonation, provider request, bot, webhook, Mini App, token, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate/trust-store change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 22 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal Admin & Support support-case/read/command/audit/escalation/redaction boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 23 of 24 — Web Cabinet `MODULE_PLAYBOOK.md`.
