# Маяк Авито — Technical Baseline

**Версия:** 1.0
**Статус:** APPROVED technical baseline
**Дата:** 2026-07-07
**Основание:** ADR-0001, ADR-0007, ADR-0008, Technology Selection Method v1.0, Technical Baseline Evidence v1.0, Architecture Baseline v1.0, Contract Package v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Avito Reference Evidence v1.0.
**Не является:** product-code, dependency lock, installation task, database schema, provider implementation, deployment topology или production readiness.

---

## 1. Назначение

Документ выбирает минимальный core stack, необходимый для Platform & Contracts playbook и последующих exact implementation tasks.

Governance, security, contract и data boundaries имеют приоритет. Module playbook может сузить dependency scope, но не может молча заменить core technology. Provider-specific, UI-specific и operations-specific решения принимаются отдельно.

## 2. Выбранный core stack

| Область | Решение | Статус |
|---|---|---|
| Language/runtime | CPython `3.14.x`, standard GIL build | `SELECTED` |
| Project/dependencies | `uv`, `pyproject.toml`, committed `uv.lock`; exact uv pin при bootstrap | `SELECTED` |
| API | FastAPI on ASGI, Uvicorn | `SELECTED` |
| Validation/settings | Pydantic v2, pydantic-settings | `SELECTED` |
| HTTP client | HTTPX | `SELECTED_WITH_GATE` |
| Database | PostgreSQL `18.x` | `SELECTED_WITH_GATE` |
| Persistence | SQLAlchemy `2.x`, Psycopg `3.x` | `SELECTED_WITH_GATE` |
| Migrations | Alembic | `SELECTED_WITH_GATE` |
| Tests | pytest, pytest-asyncio, RESpx | `SELECTED` |
| Static quality | Ruff, mypy, import-linter, coverage.py | `SELECTED` |
| Telemetry boundary | OpenTelemetry Python API/SDK | `SELECTED_WITH_GATE` |
| Durable work/outbox | PostgreSQL-owned records and claims; no required external broker | `SELECTED_WITH_GATE` |

`SELECTED_WITH_GATE` означает, что решение принято документально, но использование начинается только после isolated proof task и applicable module playbook. HTTPX дополнительно требует exact Python 3.14 compatibility proof, потому что current package metadata не перечисляет Python 3.14 явно.

## 3. Runtime and process model

1. API, worker и scheduler являются отдельными process entry points одного modular-monolith codebase.
2. Network/database I/O использует `asyncio`; blocking или CPU-heavy work не выполняется на API event loop.
3. Используется standard CPython build; experimental runtime modes вне baseline.
4. Windows Egress Agent использует ту же Python line, пока отдельное compatibility decision не докажет иное.
5. Durable work существует только после approved commit point; process-local state не является authoritative work state.
6. External clients имеют explicit lifecycle, timeouts, cancellation и bounded response handling.

## 4. Package and module boundaries

Exact layout определяет Platform & Contracts playbook. Обязательные инварианты:

- один repository;
- один server project для API, worker и scheduler;
- отдельно buildable Windows Egress Agent boundary;
- framework, provider и persistence types не являются public intermodule contracts;
- module implementation packages запрещают foreign internal imports;
- runtime, development/test и provider-specific dependencies разделены;
- adapter-specific libraries устанавливаются только в owning adapter scope.

## 5. API and contract implementation

- FastAPI реализует внешний HTTP transport и OpenAPI publication.
- Pydantic v2 применяется на serialized и external boundaries.
- Domain state остаётся framework-independent.
- SQLAlchemy entities остаются persistence-internal.
- Public commands, results and events сохраняют approved metadata, versioning и explicit result/error semantics.
- Authorization и ownership checks не заменяются framework behavior.
- Generated OpenAPI не доказывает domain authorization.
- Provider ingress доверяется только после provider-specific verification evidence.

## 6. Persistence and migrations

1. PostgreSQL — единственная primary authoritative database.
2. SQLAlchemy 2 — default persistence toolkit; direct SQL допустим только у owning module с review и tests.
3. Psycopg 3 — PostgreSQL driver.
4. Alembic — migration tool, но Run 10 не создаёт migrations.
5. Transaction не может обходить module ownership.
6. Idempotency, authoritative mutation и outbox/event creation используют общий proven commit boundary, когда это требуется.
7. Approved uniqueness and integrity поддерживаются database constraints, а не только application checks.
8. ORM lazy loading across module boundaries запрещён.
9. PostgreSQL extensions требуют отдельного decision.

## 7. Worker, scheduler and outbox

Baseline не вводит Redis, RabbitMQ, Celery или иной broker.

Начальная модель:

- module-owned schedule, work and outbox records хранят authoritative state в PostgreSQL;
- scheduler создаёт или claims due work по будущему Scan Orchestration playbook;
- workers claim work transactionally с lease, retry and reconciliation semantics;
- Notification Delivery владеет delivery outbox;
- ambiguous external effect reconciles before retry.

Exact tables, lease duration, polling interval, priority, concurrency и retry timings не выбираются здесь. Broker/cache допускается только после measured need и отдельного ADR с operations, recovery and migration impact.

## 8. External adapters

HTTPX — default sync/async client, если current provider evidence не докажет необходимость другого transport.

Обязательная политика:

- explicit client lifecycle;
- connect, read, write and pool timeouts;
- retries только по approved error category;
- ambiguous non-idempotent effect не повторяется без reconciliation;
- route and session concerns остаются за owning interfaces;
- raw external response не становится success без validation;
- access restriction, malformed response и route failure остаются explicit failures.

Requests из reference-проекта не сохраняется как второй default client.

## 9. Avito reference boundary

Mandatory reference: `Duff89/parser_avito` commit `48441c352e36919abef13c436f41a3a62636da17`.

Разрешено использовать behavioral evidence, test-case discovery и понимание current parsing flow.

Запрещено:

- копировать source code при недоказанной reuse permission;
- переносить local SQLite, Flet, Excel, TOML, VK и direct parser-to-notification architecture;
- делать global listing history или phone extraction;
- объявлять observed internal Avito structures стабильным contract;
- добавлять reference-specific optional libraries в core dependencies.

Exact parser libraries и access strategy отложены до Avito Parser Adapter playbook and proof.

## 10. Testing and static gates

Future tasks используют Acceptance Matrix v1.1.

Core tool classes:

- pytest unit and contract tests;
- pytest-asyncio;
- RESpx for HTTPX fakes;
- isolated PostgreSQL integration and migration tests after environment approval;
- Ruff formatting and lint checks;
- mypy type checks;
- import-linter module-boundary checks;
- coverage.py evidence.

Global coverage percentage не устанавливается. Tests доказывают behavior, ownership, replay, interruption и failure semantics, а не только execution.

## 11. Observability and configuration

OpenTelemetry API/SDK выбран как vendor-neutral traces and metrics instrumentation boundary. Collector, exporter, backend, dashboards, alert delivery, retention и thresholds отложены.

Application signals используют structured standard Python logging compatibility, correlation/request/run/work IDs, module, operation, result class, latency и mandatory redaction. Telemetry failure не меняет business commit semantics.

Pydantic Settings выбран для typed configuration validation. Конкретный mechanism доставки sensitive configuration не выбран. Repository содержит только schema и non-sensitive defaults; missing required configuration вызывает startup/readiness failure.

## 12. Dependency and lock policy

1. `pyproject.toml` — canonical dependency declaration после bootstrap.
2. `uv.lock` коммитится и проверяется на reproducibility.
3. Runtime, development/test and provider groups разделяются.
4. Direct dependencies имеют bounded compatible versions.
5. Exact `uv` pin обязателен, пока tool pre-1.0.
6. Patch update требует lock diff и tests; major/minor change следует Technology Selection Method.
7. Vulnerability and license evidence входит в release acceptance.
8. Dependency не добавляется только потому, что она есть в reference.
9. Run 10 не создаёт dependency files и ничего не устанавливает.

## 13. Deferred decisions

До named evidence, playbook or task отложены:

- Telegram and MAX SDK/framework;
- exact Avito parser access stack;
- frontend stack;
- object storage, cache and external broker;
- container runtime and service manager;
- ingress, TLS and ports;
- sensitive-configuration delivery product;
- telemetry backend and export path;
- Windows packaging/service model;
- payment provider;
- hosting provider;
- physical schema and migration files.

Deferred означает blocked, а не free choice implementation agent.

## 14. Rejected baseline components

- Flet as product UI framework;
- SQLite as authoritative storage;
- Excel libraries as core dependencies;
- Requests as second default HTTP client;
- local TOML as multi-user source of truth;
- Celery/Redis/RabbitMQ without measured and operations evidence;
- framework background tasks as durable jobs;
- provider SDK types as common contracts;
- direct code reuse from unclear-license reference.

## 15. Entry gates before product-code

Перед first product-code обязательны:

1. Run 10 GitHub publication and server sync accepted;
2. affected provider references accepted;
3. receiving module playbook accepted;
4. exact implementation task accepted;
5. isolated environment record ready;
6. Python, uv and core dependency toolchain proof passed;
7. exact lock created and verified;
8. fixtures, fake dependencies and Acceptance Matrix rows named;
9. no open decision guessed;
10. no live provider or foreign infrastructure dependency required.

Platform & Contracts может начаться до остальных playbooks только после собственного playbook и toolchain proof.

## 16. Revisit triggers

- Python, uv, framework or database lifecycle/incompatibility;
- official provider contract change;
- measured need for broker, cache or storage;
- failed module-boundary tests;
- performance evidence;
- security, license or supply-chain incident;
- Windows incompatibility;
- inability to recover or roll back.

## 17. Acceptance verdict

**Verdict:** `APPROVED_CORE_TECHNICAL_BASELINE`.

Verdict разрешает module playbook authors использовать выбранный stack. Он не разрешает code, dependency files, installation, database, migration, provider access, deployment или infrastructure.

## 18. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Selected Python 3.14, uv, FastAPI, Pydantic, HTTPX, PostgreSQL 18, SQLAlchemy, Psycopg, Alembic and quality/telemetry boundaries. |
