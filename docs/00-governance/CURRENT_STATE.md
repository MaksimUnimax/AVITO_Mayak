# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.24
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–23 published; Run 22 server sync accepted; Run 23 server synchronization required before Run 24`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 22 Admin & Support was independently accepted on the server at GitHub SHA `1668a01a65abf7c816c85ea062741bcfcb086645`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact nine-commit publication range, nine-path set, Admin & Support support-case/read/command/audit/escalation/redaction evidence and `ADMIN-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 23 publishes `docs/04-modules/12-web-cabinet/MODULE_PLAYBOOK.md`. It defines Web Cabinet presentation state, drafts, read-model composition, customer command envelopes, support handoff, analytics-blocking, Identity/session separation, owning-module dispatch and redaction/minimization boundaries without creating frontend, pages, API routes, authentication/session implementation, analytics, payment UI, database schema, migration, service, port, credential, secret or runtime.

Public `main` remains the factual source of truth. Run 23 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 23 published SHA and that report is independently verified.

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
- `docs/04-modules/11-admin-and-support/MODULE_PLAYBOOK.md` — Run 22 accepted;
- `docs/04-modules/12-web-cabinet/MODULE_PLAYBOOK.md` — Run 23 published; exact server sync pending.
- Module 13 remains RESERVED and is scheduled as Run 24.

## Web Cabinet consequences

- Web Cabinet owns web presentation state, draft form state, read-model composition, web command envelopes, safe explanation views, support handoff references, future analytics intent placeholders and safe web error/display state.
- Web Cabinet is a presentation and command boundary over public module services. It does not write directly to Identity, Entitlements, Beacon, Scan, Egress, Notification, Telegram, MAX, Admin & Support or Filter Catalog state.
- Identity & Access owns account, authentication, sessions, roles and identity linking. Web Cabinet does not create a second user database or treat browser/session state as Identity authority.
- Draft form state and client-side validation are not authoritative business state until the owning module accepts a public command.
- Web reads must preserve actor context, ownership scope, provenance, freshness/staleness, redaction and safe error semantics.
- Analytics, screen composition, public site depth, retention/deletion/export, phone+password recovery, phone requirement and account merge remain open-decision scope.
- Filter Catalog & Builder remains reserved until Run 24; Web Cabinet cannot invent visual filter definitions or builder behavior before that playbook is accepted.
- OD-001–OD-014 remain unresolved.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, frontend, pages, API routes, UI components, analytics, payment UI, CI/CD, migrations, database, dependency installation, auth/session implementation, account merge, phone requirement, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, admin UI, support CRM, role implementation, audit store, provider request, bot, webhook, Mini App, token, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate/trust-store change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 23 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal Web Cabinet presentation/draft/read/command/support/analytics-blocking/redaction boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 24 of 24 — Filter Catalog & Builder `MODULE_PLAYBOOK.md`.
