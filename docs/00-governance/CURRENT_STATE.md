# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.17
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.15 — Runs 1–16 published; Run 15 server sync accepted; Run 16 server synchronization required before Run 17`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 15 Beacon Management was independently accepted on the server at GitHub SHA `2a73078c42cb03ef89d62b6161752f2069d35129`: branch `main`, local and remote SHA equal, ahead/behind `0/0`, clean worktree, exact three-commit publication range, nine-path set, playbook/governance evidence and `BM-HISTORY-0001` confirmed, no GitHub/configuration mutation.

Run 16 publishes `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md`. It defines an evidence-bound Avito external adapter: source-analysis and page-parse request families, explicit transport/parser outcome separation, safe extraction/normalization, multivalue preservation, reference-profile versioning and strict false-empty prohibition without making live Avito requests or creating implementation artifacts.

Public `main` remains the factual source of truth. Run 16 is not fully accepted until `/opt/avito-mayak` is synchronized to the exact Run 16 published SHA and that report is independently verified.

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
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- Telegram and MAX current policy/evidence documents.

### Module playbooks

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12 accepted;
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13 accepted;
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14 accepted;
- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md` — Run 15 accepted;
- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md` — Run 16 published; exact server sync pending.
- Modules 06–13 remain RESERVED and are scheduled as Runs 17–24.

## Avito Parser Adapter consequences

- Avito-dependent behavior is accepted only through current reference records with exact scope, status and limitations.
- `AVITO-PRIMARY-PARSER-001` at commit `48441c352e36919abef13c436f41a3a62636da17` is implementation evidence only, not an official provider contract or permission.
- Observed `loaderData.data`, `searchCore`, `context`, `catalog` and `/web/1/js/items` behavior is not declared stable.
- Transport success is not parser success; parser success is not scan/business success.
- No request sent, route failure, rejection, restriction/CAPTCHA, malformed/incomplete response, stale/unsupported evidence and ambiguity remain explicit outcomes and never become a clean empty listing set.
- Repeated filter values must not be silently collapsed.
- Parser Adapter does not own Beacon configuration, Scan/listing history, Egress routes or Notification Delivery.
- Raw provider payload retention, exact fields/identity, filters, markets, cadence, cookies/sessions, headers, pagination, retry/backoff and access strategy remain blocked until evidence/decisions/tasks.
- OD-009, OD-010, OD-011 and OD-013 remain unresolved.

## Current prohibitions

No product code, `pyproject.toml`, `uv.lock`, executable tests, fixture data files, CI/CD, migrations, database, dependency installation, parser implementation, live/provider request, endpoint probing, cookie/session/proxy setup, service, container, listener, port, credential, secret, deployment or runtime configuration has been created.

OD-001–OD-014 remain unresolved.

## Next safe step

1. Synchronize `/opt/avito-mayak` to the exact Run 16 published GitHub SHA.
2. Verify local SHA, remote SHA, clean worktree, publication scope, literal parser/reference boundaries and no prohibited mutation.
3. After independent acceptance, continue with Run 17 of 24 — Scan Orchestration & Listing State `MODULE_PLAYBOOK.md`.
