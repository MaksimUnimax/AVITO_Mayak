# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.14
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–13 published; Run 12 server sync accepted; Run 13 server synchronization required before Run 14`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 12 Platform & Contracts was independently accepted on the server at GitHub SHA `728b9062126fd7c2e816dde3a1a3ed9d42431cf2`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, expected parent/subject/paths, playbook evidence and `WL-0016` confirmed, no GitHub/configuration mutation.

Run 13 publishes `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md`. It defines account, identity, contact point, credential-reference, role assignment, session and challenge boundaries without creating implementation artifacts.

Public `main` remains the factual source of truth. Run 13 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 13 published SHA and that report is independently verified.

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
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13 published; exact server sync pending.
- Modules 03–13 remain RESERVED and are scheduled as Runs 14–24.

## Identity & Access consequences

- `account_id` remains the internal account boundary and is not replaced by Telegram, MAX, email, phone or username.
- Messenger identity is required for bot-first entry; phone is a separate verified contact point and not a primary key.
- Automatic merge by weak signals is prohibited; account merge remains blocked by OD-008.
- Phone+password and recovery policy remain blocked by OD-006; mandatory phone policy remains blocked by OD-007.
- Roles and administrative privileges require server-side assignment and audit; UI flags or provider names are not authorization.
- Credential material, one-time codes and provider payloads are not common contracts, audit payloads or fixture content.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, service, container, listener, port, credential, secret, external call, parser, bot, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 13 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, expected paths and no prohibited mutation.
3. After independent acceptance, continue with Run 14 of 24 — Entitlements & Billing `MODULE_PLAYBOOK.md`.
