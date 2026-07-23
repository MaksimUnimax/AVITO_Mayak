# Маяк Авито

**Статус репозитория:** `MODULE_14_AUTONOMOUS_RUNTIME_COMPLETION_ACTIVE` — RF-02 is accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`; RF-03 integration inventory is active.

«Маяк Авито» — сервис мониторинга поисковой выдачи Avito. Пользователь создаёт отдельный Маяк из ссылки поиска, а принятая текущая семантика уведомляет только о вновь наблюдаемых объявлениях. Первый baseline уведомление не создаёт. Изменение цены само по себе не является notification event текущего scope.

## Точка входа

Перед любой работой читать в указанном порядке:

1. [`docs/00-governance/PROJECT_ENTRYPOINT.md`](docs/00-governance/PROJECT_ENTRYPOINT.md)
2. [`docs/00-governance/CURRENT_STATE.md`](docs/00-governance/CURRENT_STATE.md)
3. [`docs/00-governance/ROADMAP.md`](docs/00-governance/ROADMAP.md)
4. [`docs/MANIFEST.md`](docs/MANIFEST.md)
5. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md)
6. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md)
7. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md)
8. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md)
9. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_COMPLETION_MATRIX_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_COMPLETION_MATRIX_v1.0.md)
10. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_RUNTIME_GAP_MATRIX_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_RUNTIME_GAP_MATRIX_v1.0.md)
11. affected module playbooks, contracts, handoffs and append-only decisions.

Exact current GitHub `main` SHA must be fetched before every task. SHA values recorded in governance documents are evidence baselines, not permission to skip a fresh check.

## Неподвижные правила

- Public GitHub `main` — единственный repository source of truth.
- Владелец задаёт product goals and fixed owner decisions.
- ChatGPT является developer, architect, roadmap lead, release manager and independent reviewer.
- Codex/CLI выполняет только один literal atomic task и не выбирает следующий roadmap step.
- Modules 01–13 retain ownership of their domain state.
- Module 14 assembles the runtime only through public module boundaries.
- Direct foreign-module table writes are forbidden.
- Provider payloads do not become internal contracts or business authority.
- Provider acceptance is not proof of human reading.
- Ambiguous external effects are reconcile-first and are never blindly retried.
- Secrets, credentials, private keys, populated `.env` files and production personal data must not enter Git or reports.
- Foreign server resources must not be altered, deleted or reused.
- Public production launch remains blocked.

Полные правила Module 14:
[`docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md).

## Current accepted repository contour

The repository contains:

- Python source under `src/mayak`;
- executable unit, contract and architecture tests;
- synthetic fixture data;
- committed `pyproject.toml`;
- committed `uv.lock`;
- accepted semantic implementations and evidence handoffs for modules 01–13;
- approved Module 14 governance;
- a lock-compatible Python 3.14 suite with 4511 passing tests at the accepted RF-02 audit baseline.

The semantic implementation contour exists and must not be described as absent.

This does not prove that the complete acceptance runtime is assembled or deployed.

## Current module state

- Modules 01–13: accepted semantic, contract, ownership, test and evidence prerequisites.
- Module 14: active cross-cutting implementation and integration module.
- RF-00: accepted.
- RF-01: accepted.
- RF-02: independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03: active; RF-03-01 is independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 is independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`; RF-03-03 is published for independent acceptance; RF-03 closure remains pending; RF-04 is not started; runtime mutation is none and production remains blocked.
- RF-04–RF-30: not accepted and may begin only through their exact prerequisites and one exact task.

Historical Final Documentation Acceptance remains evidence for the earlier documentation cycle. It is not the current roadmap endpoint.

## Runtime target

The accepted Module 14 target is:

- existing project server;
- Docker Engine and Docker Compose;
- project-owned Compose namespace;
- PostgreSQL 18;
- SQLAlchemy 2, Psycopg 3 and Alembic;
- separate FastAPI API, worker and scheduler entry points;
- PostgreSQL-backed durable work, leases, idempotency and outbox;
- localhost-only API;
- no host-published PostgreSQL port;
- provider-disabled-by-default profiles;
- synthetic and operator-acceptance environment;
- Web Cabinet and Admin through owning module services;
- backup, restore, recovery and observability evidence.

These runtime components are roadmap targets, not current completion claims.

## Current runtime gaps

The following remain future exact RF steps:

- GitHub Actions quality gates;
- Docker/Compose foundation;
- PostgreSQL/Alembic physical persistence;
- API/worker/scheduler runtime assembly;
- DB-backed module runtimes;
- cross-module HTTP and command wiring;
- synthetic E2E;
- security and recovery proof;
- deployment on the existing server;
- operator acceptance pack;
- final evidence handoff.

## Production boundary

Module 14 completes only with the final verdict `READY_FOR_OPERATOR_ACCEPTANCE`.

The repository must not claim `PRODUCTION_READY` before separate operator acceptance and a future production launch gate.

No public ingress, DNS, TLS, firewall or production-provider activation is authorized by this README.
