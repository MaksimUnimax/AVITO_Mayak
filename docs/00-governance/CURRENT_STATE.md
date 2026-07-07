# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.7
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.12 — Operations and external-reference documentation active; Run 6 environment/observability accepted; Run 7 backup/release pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 6 Operations Environment package опубликован commits `3150fe4621d1d92f65fa2b4b0fdbb1557c1ac582` и `2c333a6ce4c21e70201deeab42965c546f562e4d` как один заранее определённый documentation change set.

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

### Operations Environment Foundation

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`.

Принятые documents фиксируют modular boundaries, ownership, conceptual data domains, contract semantics, error/idempotency rules, migration/compatibility gates, security/privacy limits, quality gates, canonical semantic fixtures, acceptance traceability, environment readiness/ownership and observability/alerting semantics.

Они не выбирают implementation language, framework, package manager, test framework, CI provider, queue, transport, serialization, monitoring stack, alert thresholds/channels, ingress, ports, storage implementation, secrets product, deployment method, physical database schema, migration tool или runtime topology.

No product code, executable tests, fixture data files, CI/CD, migrations, monitoring configuration, live alerts, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 7 of 23: Backup and release boundaries documentation only:

- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`.

Run 7 must not create backups, snapshots, deploy pipelines, runtime configuration, ingress, ports, TLS, services, containers, credentials, CI/CD or product-code. Undefined operational conditions remain explicit gates.
