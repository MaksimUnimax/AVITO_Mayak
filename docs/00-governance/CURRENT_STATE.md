# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.12
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.14 — Runs 1–11 published; Run 10 server sync accepted; Run 11 server synchronization required before Run 12`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 10 Technical Baseline was independently accepted on the server at GitHub SHA `099c9f0e35bb710f498d9f75ab38d542feb76be5`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, no GitHub/configuration mutation.

Run 11 publishes current official-source policies for Telegram and MAX plus the current cross-provider registry index. It creates no bot, credential, provider request, executable test, service or runtime.

Public `main` remains the factual source of truth. Run 11 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 11 published SHA and that report is independently verified.

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

### Operations

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`;
- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### External references

- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

## Provider-policy consequences

- Telegram webhook/getUpdates are mutually exclusive; provider updates and Mini App inputs are trusted only after the documented verification boundary.
- Telegram `update_id` supports duplicate/order handling in provider scope but does not replace internal idempotency and ownership rules.
- MAX production integrations use Webhook; Long Polling is development/test only according to current official documentation.
- MAX currently requires migration from `platform-api.max.ru` to `platform-api2.max.ru` by 19 July 2026; this is a revalidation gate, not a runtime change made by Run 11.
- MAX partner eligibility and moderation are adoption gates; they are not assumed satisfied.
- Neither policy chooses SDKs, hosting, certificates, secrets delivery, retry budgets, UI scope or provider credentials.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, service, container, listener, port, credential, secret, external call, parser, bot, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 11 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree and no prohibited mutation.
3. After independent acceptance, continue with Run 12 of 24 — Platform & Contracts `MODULE_PLAYBOOK.md`.
