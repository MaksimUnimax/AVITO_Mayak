# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.6
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.11 — Quality Foundation accepted; A0.12 Operations and external-reference documentation pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 5 Quality package опубликован commits `bbd27bd522d994e929eda79663f58ce80766b1d3`, `fe705dedf7cc8640c632118ee150ffc83a86578f`, `f804da85b270d4e782faa2375e0fb6c2aa15ab7b` и `b6c7469e41c8f096f5c666f61cceea95378967fe` как один заранее определённый documentation change set.

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

### Quality Foundation

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

Принятые foundation documents фиксируют modular boundaries, ownership, conceptual data domains, contract semantics, error/idempotency rules, migration/compatibility gates, security/privacy limits, quality gates, canonical semantic fixtures, acceptance traceability and reference-regression control.

Они не выбирают implementation language, framework, package manager, test framework, CI provider, queue, transport, serialization, ingress, ports, storage implementation, secrets product, deployment method, physical database schema, migration tool или runtime topology.

No product code, executable tests, fixture data files, CI/CD, migrations, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 6 of 23: Operations environment and observability documentation only:

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`.

Run 6 must not create runtime configuration, services, containers, ports, monitoring stack, alerts, credentials, deploy, CI/CD or product-code. It defines environment and observability boundaries, gates and safe evidence only.
