# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.15
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–14 published; Run 13 server sync accepted; Run 14 server synchronization required before Run 15`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 13 Identity & Access was independently accepted on the server at GitHub SHA `bcc33aa7120d60f977819319195000ab3a27a2c7`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact publication range/path set, playbook/governance evidence and `IA-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 14 publishes `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md`. It defines tariff, entitlement, subscription, manual-access, usage-limit and future payment-record boundaries without creating implementation artifacts or choosing a payment provider.

Public `main` remains the factual source of truth. Run 14 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 14 published SHA and that report is independently verified.

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
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14 published; exact server sync pending.
- Modules 04–13 remain RESERVED and are scheduled as Runs 15–24.

## Entitlements & Billing consequences

- Entitlements & Billing owns TariffDefinition, Subscription, EntitlementGrant, ManualAccessGrant, future PaymentRecord/PaymentEvent and any later approved usage-consumption record.
- Tariff, subscription, entitlement and payment are distinct states; a provider response never grants access without a server-authorized transition.
- Other modules request an effective entitlement decision through public contracts and do not read/write billing tables directly.
- Target-model tariff values remain DRAFT context and are not implementation defaults.
- OD-001–OD-005 remain explicit blockers for period, future tiers, intervals, expiry behavior, provider, recurrence, refunds and manual-payment rules.
- OD-010, OD-011 and OD-013 remain relevant to country-wide access, safe scan frequency and retention.
- Manual access requires actor, reason, scope, effective interval, idempotency and audit evidence.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, payment integration, provider account, service, container, listener, port, credential, secret, external call, parser, bot, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 14 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, expected paths and no prohibited mutation.
3. After independent acceptance, continue with Run 15 of 24 — Beacon Management `MODULE_PLAYBOOK.md`.
