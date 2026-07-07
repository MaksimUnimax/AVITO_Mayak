# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.19
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–18 published; Run 17 server sync accepted; Run 18 server synchronization required before Run 19`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 17 Scan Orchestration & Listing State was independently accepted on the server at GitHub SHA `7dc5eb6c26c7cbe82a5db42dfeffaff521f01d90`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact one-commit publication range, nine-path set, playbook/baseline/difference/governance evidence and `SOLS-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 18 publishes `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`. It defines authoritative agent/route registration, capability/readiness/health/quarantine state, bounded route leases and transport assignments, server-side selection evidence, explicit dispatch/send outcomes, false-success prohibition, reconciliation-first ambiguity and a replaceable Windows Egress Agent boundary without choosing or creating transport/runtime infrastructure.

Public `main` remains the factual source of truth. Run 18 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 18 published SHA and that report is independently verified.

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
- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md` — Run 18 published; exact server sync pending.
- Modules 08–13 remain RESERVED and are scheduled as Runs 19–24.

## Egress Routing consequences

- Egress Routing is the only owner of logical agent/route registration, capability/readiness/health/quarantine state, route leases, route-selection decisions, bounded transport assignments and transport reconciliation records.
- `route_id`, `agent_id` and `lease_id` are semantic identifiers, not IP address, hostname, port or process aliases.
- Windows Egress Agent is a replaceable execution dependency. It does not own Beacon, account, entitlement, scan/listing state, Parser mappings, notification state, primary database or secrets.
- Agent heartbeat or an established connection does not prove readiness, route usability, request success, Parser success or business success.
- A lease is bounded authorization for one declared purpose/scope and does not transfer ownership of business state or credentials.
- Agent-side independent fallback is forbidden. Route selection, switching, restriction and quarantine decisions remain server-side and auditable.
- Transport outcomes distinguish not dispatched, ambiguous dispatch, received-not-sent, sent response, explicit rejection, unavailable, restricted, malformed/unusable, failure, ambiguous and cancelled/expired classes.
- `SENT_SUCCESS_RESPONSE` is only a transport outcome. Parser must still validate the response; Scan must still commit the business comparison.
- Unknown dispatch/send state is reconcile-first and must not be retried blindly.
- Route/agent failure, restriction, CAPTCHA, timeout, expired/revoked lease, malformed response or ambiguity never becomes clean Parser success or an empty listing set.
- Public unauthenticated inbound exposure is prohibited by default, while exact connectivity technology/topology remains unselected.
- Exact route technology, ports, tunnel/VPN/proxy, credentials, capabilities, priority, fallback, lease/heartbeat/readiness thresholds, retry/backoff/rate limits, cookies/sessions and retention remain blocked.
- OD-009, OD-010, OD-011 and OD-013 remain unresolved and all OD-001–OD-014 remain open.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, Windows/server agent, service, scheduled task, route, lease, tunnel, VPN, proxy, port, listener, firewall/DNS/certificate change, parser/provider request, notification delivery, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 18 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal route/lease/outcome/reconciliation boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 19 of 24 — Notification Delivery `MODULE_PLAYBOOK.md`.
