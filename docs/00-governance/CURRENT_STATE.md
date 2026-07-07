# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.18
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–17 published; Run 16 server sync accepted; Run 17 server synchronization required before Run 18`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 16 Avito Parser Adapter was independently accepted on the server at GitHub SHA `9907b22d2192e60680bcdd9e4e98f6bb104cb18f`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact three-commit publication range, nine-path set, playbook/reference/governance evidence and `APA-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 17 publishes `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md`. It defines durable scan intent/run/claim semantics, immutable Beacon revision pinning, explicit Parser outcome consumption, per-Beacon immutable observations and state, first complete baseline without notification, subsequent listing-ID and ID+price-pair difference semantics, reconciliation and post-commit domain-event boundaries without creating implementation artifacts.

Public `main` remains the factual source of truth. Run 17 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 17 published SHA and that report is independently verified.

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
- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- current Avito, Telegram and MAX policy/evidence documents.

### Module playbooks

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12 accepted;
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13 accepted;
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14 accepted;
- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md` — Run 15 accepted;
- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md` — Run 16 accepted;
- `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md` — Run 17 published; exact server sync pending.
- Modules 07–13 remain RESERVED and are scheduled as Runs 18–24.

## Scan Orchestration & Listing State consequences

- Every logical run is bound to one `beacon_id` and one immutable `configuration_revision_id`; a newer revision never silently reinterprets a recorded run.
- The module owns durable scan/run state, observations, per-Beacon listing state, baseline/difference decisions and scan-domain events; it does not own Beacon configuration, Parser mappings, Egress routes or notification delivery.
- Only a complete, explicit, comparison-eligible Parser outcome may establish or advance baseline/difference state.
- The first complete accepted scan establishes the Beacon baseline and emits no listing-change notification event for baseline contents.
- After baseline, a previously unseen listing identity produces a new-listing domain event; a known identity with a previously unseen normalized price pair produces a price-pair event; an already known identity+price pair produces no new event.
- If price returns to a previously observed value, that pair is already known and no new price-pair event is produced under v1.0 semantics.
- Observations are immutable and history/state remain isolated by `beacon_id` even when provider listing identity is equal.
- A missing listing in one result does not prove removal or inactivity.
- Partial, malformed, restricted, route-failed, stale-evidence or ambiguous outcomes never become clean success, never establish baseline and never erase state.
- Exact intervals, expiry behavior, supported filters/markets, safe cadence and retention remain blocked by OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, scheduler/worker/queue implementation, parser/provider request, notification delivery, service, container, listener, port, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 17 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal baseline/diff/reconciliation boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 18 of 24 — Egress Routing `MODULE_PLAYBOOK.md`.
