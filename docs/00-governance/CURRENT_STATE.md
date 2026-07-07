# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.3
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.8 — Architecture Foundation accepted; A0.9 Common Contract Foundation pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Последний принятый foundation package опубликован commit `6c0d64237903d8e73248600d9f29a0cc6160b8ab`.

Public `main` — фактический источник истины. Процедура независимой проверки: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 принят только как ограниченное proof-only evidence. Shared-host facts не разрешают использовать foreign containers, databases, Nginx, ports, networks, volumes или secrets.

## Принятая Architecture Foundation

Приняты только следующие documentation baseline documents:

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

Они фиксируют modular-monolith boundaries, ограничения shared-host isolation и framework-independent security/privacy requirements.

Они не выбирают implementation language, framework, package manager, queue, ingress, ports, storage implementation, secrets product, deployment method, physical database schema или migration tool.

No product code, CI/CD, migrations, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 3 of 23: Common Contract Foundation documentation only:

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.
