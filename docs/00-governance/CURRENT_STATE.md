# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.4
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.9 — Common Contract Foundation accepted; A0.10 Data Model and Migration/Compatibility Policy pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Последний принятый Common Contract Foundation package опубликован commit `b6fd8ff5119e9b85f1e307962e97513e1ee401b2`; governance correction опубликован commit `df372c71579fe7dc1f84e479d0894803f4b22322`.

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

Принятые foundation documents фиксируют boundaries, ownership, contract semantics, error and idempotency rules, security/privacy limits and document-change control.

Они не выбирают implementation language, framework, package manager, queue, transport, serialization, ingress, ports, storage implementation, secrets product, deployment method, physical database schema или migration tool.

No product code, CI/CD, migrations, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 4 of 23: Data Model and Migration/Compatibility Policy documentation only:

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.
