# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.16
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–15 published; Run 14 server sync accepted; Run 15 server synchronization required before Run 16`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 14 Entitlements & Billing was independently accepted on the server at GitHub SHA `2346ccbbeaa8f1be18281fdf16fbec75cdb5052e`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact parent/subject/path set, playbook/governance evidence and `EB-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 15 publishes `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md`. It defines Beacon ownership, immutable source URL, extracted snapshot, user overrides, deterministic effective configuration, immutable revisions, lifecycle commands and entitlement/parser/scan boundaries without creating implementation artifacts.

Public `main` remains the factual source of truth. Run 15 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 15 published SHA and that report is independently verified.

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
- Avito, Telegram and MAX current policy/evidence documents.

### Module playbooks

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12 accepted;
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13 accepted;
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14 accepted;
- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md` — Run 15 published; exact server sync pending.
- Modules 05–13 remain RESERVED and are scheduled as Runs 16–24.

## Beacon Management consequences

- One Beacon belongs to exactly one `account_id`; external adapters and UI do not own Beacon state.
- `BeaconSourceUrl` is preserved as submitted evidence and is not rewritten by extracted data or user overrides.
- Extracted snapshot, override and effective configuration remain distinct by provenance.
- Every effective configuration change creates a new immutable `BeaconConfigurationRevision`; historical revisions are not edited.
- Entitlements & Billing supplies an effective decision for active count, geography, interval and edit capability; Beacon Management does not duplicate tariff state.
- Avito Parser Adapter may return normalized extraction/validation outcomes but cannot create, activate or mutate a Beacon directly.
- Scan Orchestration consumes an explicit immutable configuration revision reference and does not own Beacon configuration.
- OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain blockers for exact intervals, expiry behavior, supported filters, country-wide behavior, safe frequency and retention/deletion.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, parser implementation, external call, service, container, listener, port, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 15 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, expected paths and no prohibited mutation.
3. After independent acceptance, continue with Run 16 of 24 — Avito Parser Adapter `MODULE_PLAYBOOK.md`.
