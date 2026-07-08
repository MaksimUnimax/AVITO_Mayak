# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.25
**Статус:** APPROVED snapshot
**Дата:** 2026-07-08

## Фаза

`A0.15 — Runs 1–24 published; Run 23 server sync accepted; Run 24 server synchronization required before final audit`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 23 Web Cabinet was independently accepted on the server at GitHub SHA `1f86b8c131b8ac7d456184e4ed2ba7c1ddad8b05`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact nine-commit publication range, nine-path set, Web Cabinet presentation/draft/read/command/support/analytics-blocking/redaction evidence and `WEB-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 24 publishes `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md`. It defines evidence-bound filter definitions, immutable catalog versions, filter option/range/dependency semantics, builder draft validation, Beacon/Web/Parser separation, OD-009 blocking, catalog compatibility warnings, false-success prohibition and redaction/minimization boundaries without creating exact supported-filter list, frontend builder, parser probes, provider calls, database schema, migration, service, port, credential, secret or runtime.

Public `main` remains the factual source of truth. Run 24 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 24 published SHA and that report is independently verified.

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
- `docs/04-modules/12-web-cabinet/MODULE_PLAYBOOK.md` — Run 23 accepted;
- `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` — Run 24 published; exact server sync pending.

## Filter Catalog & Builder consequences

- Filter Catalog & Builder owns filter evidence references, filter definitions/options/ranges, capability profiles, dependency/compatibility rules, builder field semantics, catalog versioning, compatibility warnings and safe builder read models.
- Beacon Management owns actual source URLs, accepted extracted snapshots, override sets, effective configuration, immutable revisions and lifecycle.
- Avito Parser Adapter owns extraction/normalization evidence and warnings only; parser success does not approve supported editability.
- Web Cabinet may render builder forms only from approved catalog definitions and cannot invent filter definitions.
- Exact supported first-stage editable Avito filters by category remain blocked by OD-009; Run 24 does not approve a concrete filter list.
- Internal Avito endpoint/embedded-state behavior remains unsupported as stable public contract.
- Multivalue, range, unit, dependency, category/geography and compatibility semantics must be explicit before filter editability is accepted.
- Catalog versions are immutable; supersession does not rewrite historical Beacon revisions.
- OD-001–OD-014 remain unresolved.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, frontend, pages, API routes, UI components, analytics, payment UI, CI/CD, migrations, database, dependency installation, auth/session implementation, account merge, phone requirement, filter catalog implementation, exact supported-filter list, parser probe, provider call, Windows/server agent, service, scheduled task, queue, worker, notification outbox implementation, provider adapter implementation, admin UI, support CRM, role implementation, audit store, bot, webhook, Mini App, token, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate/trust-store change, parser/provider request, notification delivery execution, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 24 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal Filter Catalog evidence/catalog/builder/Beacon/Web/Parser/OD-009/redaction boundaries and no prohibited mutation.
3. After independent acceptance, perform final independent documentation audit across all Runs 1–24.
4. Publish final governance acceptance only if the audit proves readiness.
