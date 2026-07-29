# Маяк Авито

**Статус репозитория:** `MODULE_14_RF10_PLATFORM_CONTRACTS_RUNTIME_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE` — RF-09 is independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; RF-10 is published for independent acceptance; RF-11 is not started.

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
11. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_CONSISTENCY_AUDIT_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_CONSISTENCY_AUDIT_v1.0.md)
12. [`docs/04-modules/14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_INTEGRATION_INVENTORY_CLOSURE_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_INTEGRATION_INVENTORY_CLOSURE_v1.0.md)
13. affected module playbooks, contracts, handoffs and append-only decisions.

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
- RF-03: complete at repository-content level and independently accepted at its recorded chain heads.
- RF-04 and RF-05 are accepted; RF-06 is accepted; RF-07 is open only for deferred runtime gates; RF-08 and RF-09 are independently accepted; RF-10 corrective is published and pending independent acceptance; RF-11 is not started; complete runtime/deployment is not reached; `NOT_PRODUCTION_READY` remains current.

Current RF-04 evidence: [`PHYSICAL_DATA_MODEL_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/PHYSICAL_DATA_MODEL_v1.0.md), [`TRANSACTION_AND_OUTBOX_BOUNDARIES_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/TRANSACTION_AND_OUTBOX_BOUNDARIES_v1.0.md), [`RUNTIME_PROCESS_AND_PACKAGE_MODEL_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/RUNTIME_PROCESS_AND_PACKAGE_MODEL_v1.0.md), [`MIGRATION_AND_SCHEMA_EVOLUTION_PLAN_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/MIGRATION_AND_SCHEMA_EVOLUTION_PLAN_v1.0.md), [`RUNTIME_TOPOLOGY_AND_ENVIRONMENT_RECORD_CANDIDATE_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/RUNTIME_TOPOLOGY_AND_ENVIRONMENT_RECORD_CANDIDATE_v1.0.md), [`CONFIGURATION_AND_SECRETS_BOUNDARY_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/CONFIGURATION_AND_SECRETS_BOUNDARY_v1.0.md), and [`RUNTIME_ARCHITECTURE_AND_PHYSICAL_DATA_MODEL_CLOSURE_v1.0.md`](docs/04-modules/14-runtime-foundation-and-autonomous-integration/RUNTIME_ARCHITECTURE_AND_PHYSICAL_DATA_MODEL_CLOSURE_v1.0.md).

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

## Current RF-11 boundary (2026-07-29)

RF-10 is independently accepted through `74997f4da04fd9ae9e225ea39b22c20acd45353e`; RF-11 implementation and closure are published for independent acceptance. RF-12 has not started. Remaining RF-07 runtime gates are deferred; the environment remains `RUNTIME_ELIGIBLE`, complete runtime/deployment is not reached, and `NOT_PRODUCTION_READY` remains authoritative. RF-30 is the only route to `READY_FOR_OPERATOR_ACCEPTANCE`.
