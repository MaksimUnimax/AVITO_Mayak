# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.5
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.10 — Data Model and Migration/Compatibility Policy accepted; A0.11 Quality documentation pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 4 Data and Compatibility package опубликован commits `3d267e4a9ebe8a27b199ab07aa4e1973e0f7e030` и `805837abc67c0423ea391669d51e352fa9bedc48` и принят после независимого literal review public `main`.

Public `main` — фактический источник истины. Процедура независимой проверки: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 принят только как ограниченное proof-only evidence. Shared-host facts не разрешают использовать foreign containers, databases, Nginx, ports, networks, volumes или secrets.

## Принятые foundation documents

### Architecture Foundation

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

### Common Contract Foundation

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

### Data and Compatibility Foundation

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

Принятые foundation documents фиксируют modular boundaries, ownership, conceptual data domains, contract semantics, error/idempotency rules, migration/compatibility gates, security/privacy limits and document-change control.

Они не выбирают implementation language, framework, package manager, queue, transport, serialization, ingress, ports, storage implementation, secrets product, deployment method, physical database schema, migration tool или runtime topology.

No product code, CI/CD, migrations, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 5 of 23: Quality documentation only:

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

Run 5 must not create tests, fixtures as executable code, CI/CD, product-code, migrations, databases, deploy or runtime configuration. It defines documentation gates and evidence expectations only.
