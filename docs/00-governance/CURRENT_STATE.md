# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.2
**Статус:** APPROVED snapshot
**Дата:** 2026-07-06

## Фаза

`A0.7 — TASK-001 evidence accepted; A0.8 Architecture Foundation pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.
Pre-package evidence baseline: `e017241824b3b3e90db1116faefc466791bef2e5`.
Public `main` is factual source of truth; procedure: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 is accepted as limited proof-only evidence and is in `docs/05-tasks/completed/`. Shared-host facts do not permit use of foreign containers, databases, Nginx, ports, networks, volumes or secrets.

No product code, CI/CD, migrations, project service, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 2 of 23: Architecture Baseline, Environment Isolation Policy and Security/Privacy Model as documentation only.
