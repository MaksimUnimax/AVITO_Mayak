# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.13
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–12 published; Run 11 server sync accepted; Run 12 server synchronization required before Run 13`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 11 Telegram/MAX references were independently accepted on the server at GitHub SHA `642655a523af3591b1a024c39efa6978a064b2b8`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, expected parent/subject/paths and `WL-0015` confirmed, no GitHub/configuration mutation.

Run 12 publishes `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md`. It defines future application/package, common contract, idempotency, configuration, process-composition, dependency, fake, fixture and acceptance boundaries without creating implementation artifacts.

Public `main` remains the factual source of truth. Run 12 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 12 published SHA and that report is independently verified.

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

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12 published; exact server sync pending.
- Modules 02–13 remain RESERVED and are scheduled as Runs 13–24.

## Platform & Contracts consequences

- future source layout is singular under `src/mayak/` with platform/contracts/entrypoints/modules boundaries;
- public contracts remain transport/framework/persistence/provider neutral;
- Platform owns common conventions and reusable protocols, not foreign business state;
- owning modules define commit points and persist business idempotency outcomes;
- typed configuration, process composition, import rules, fake boundaries and migration gates are documented;
- toolchain/dependency/code/database/migration work remains blocked until a separate exact task and proof gates.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, service, container, listener, port, credential, secret, external call, parser, bot, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 12 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, expected paths and no prohibited mutation.
3. After independent acceptance, continue with Run 13 of 24 — Identity & Access `MODULE_PLAYBOOK.md`.
