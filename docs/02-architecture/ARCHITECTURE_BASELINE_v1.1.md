# Маяк Авито — Architecture Baseline

**Версия:** 1.1
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Заменяет:** `ARCHITECTURE_BASELINE_v1.0.md` как current architecture baseline; v1.0 сохраняется как historical accepted revision.
**Основание:** ADR-0001, ADR-0005, ADR-0007, ADR-0008, Technical Baseline v1.0, Technology Selection Method v1.0, `MAYAK_AVITO_TARGET_MODEL_v0.1.md`, `MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md`, `MODULE_REGISTRY.md`.
**Не является:** разрешением на product-code, migration, deployment, runtime provisioning или provider access.

---

## 1. Назначение

Документ фиксирует архитектурные инварианты, current technology authority и обязательные design gates.

## 2. Иерархия источников

1. Public GitHub `main` и `docs/MANIFEST.md`.
2. Append-only ADR в пределах их scope.
3. Этот Architecture Baseline.
4. Technical Baseline v1.0 для core implementation technologies.
5. Approved security, contracts, data, quality, operations and reference documents.
6. DRAFT target model/architecture map только как context.
7. `OPEN_DECISIONS.md` как register запрещённых предположений.

## 3. Стартовая форма системы

Принята форма:

- один repository;
- modular monolith;
- 13 logical modules;
- явные internal boundaries;
- отдельные API, worker and scheduler process entry points;
- отдельный Windows Egress Agent boundary;
- одна primary PostgreSQL database;
- возможное дальнейшее выделение компонентов только по evidence и ADR.

Это не означает 13 microservices, 13 databases или независимые module deployments.

## 4. Logical modules

1. Platform & Contracts;
2. Identity & Access;
3. Entitlements & Billing;
4. Beacon Management;
5. Avito Parser Adapter;
6. Scan Orchestration & Listing State;
7. Egress Routing;
8. Notification Delivery;
9. Telegram Adapter;
10. MAX Adapter;
11. Admin & Support;
12. Web Cabinet;
13. Filter Catalog & Builder.

Сквозные контуры:

- Security & Privacy;
- Observability & Operations;
- Data & Compatibility Governance.

## 5. Неподвижные границы

- Внешний adapter не пишет напрямую в foreign module state.
- Intermodule interaction использует approved commands, results, events or read models.
- Parser не доставляет уведомления напрямую.
- Telegram/MAX/Web/Admin не владеют отдельной пользовательской базой.
- Один Beacon принадлежит одному `account_id`.
- Listing/notification history изолируется по `beacon_id`.
- Source URL не переписывается overrides.
- Framework, ORM и provider SDK types не являются public domain contracts.
- Open decisions не получают неявного значения в design/code/tests.
- Shared-host resources не становятся project resources из-за видимости или наличия команды.

## 6. Data and process boundaries

Primary authoritative database — PostgreSQL.

Current core line and tools определяет Technical Baseline v1.0.

Database decision не разрешает:

- подключаться к существующей/foreign database;
- создавать schema/tables/migrations;
- использовать чужие queues/caches/storage;
- вводить cross-module transactions без owner boundary;
- считать local SQLite reference design допустимым SaaS storage.

API, worker and scheduler are separate process roles, но принадлежат одному modular-monolith application boundary.

Windows Egress Agent не владеет business data и не становится альтернативным parser/database source of truth.

## 7. Technology authority

Current core selections:

- CPython 3.14;
- uv;
- FastAPI/Uvicorn;
- Pydantic v2/pydantic-settings;
- HTTPX;
- PostgreSQL 18;
- SQLAlchemy 2, Psycopg 3, Alembic;
- pytest/pytest-asyncio/RESpx;
- Ruff, mypy, import-linter, coverage.py;
- OpenTelemetry instrumentation boundary;
- PostgreSQL-backed durable work/outbox without external broker at baseline.

Полное scope, deferred decisions and gates находятся в `TECHNICAL_BASELINE_v1.0.md`.

Host snapshot не выбирает версии. Provider/browser/frontend/deployment technology остаётся отдельным решением.

## 8. Required gates before implementation

До первого product-code должны быть приняты и применимы:

1. Common Contract Foundation.
2. Data Model and Migration/Compatibility Policy.
3. Test Strategy, current Fixture Registry, current Acceptance Matrix and Reference Regression Policy.
4. Environment, observability, recovery and release boundaries.
5. Official/reference evidence для затронутых providers.
6. Technology Selection Method and Technical Baseline.
7. Isolated toolchain proof для selected core stack.
8. Autonomous module playbook для receiving module.
9. Exact implementation task with literal scope/tests/acceptance.

Отсутствующий gate означает `BLOCKED`, а не best-effort implementation.

## 9. Explicit non-goals

Этот baseline не определяет:

- API endpoints and exact payloads;
- physical database schema;
- exact worker lease/retry intervals;
- provider access details or request cadence;
- payment implementation;
- browser/bot/web UI;
- deployment topology;
- ingress/TLS/ports;
- sensitive-configuration delivery product;
- telemetry backend;
- production readiness.

## 10. Change control

Изменение module boundary, data ownership, security boundary, common contract, core technology или process authority требует:

1. evidence;
2. append-only ADR;
3. compatibility/migration analysis;
4. updates to canonical documents;
5. selected acceptance rows;
6. independent GitHub acceptance;
7. exact server synchronization.

## 11. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial architecture boundaries without stack selection. |
| 1.1 | 2026-07-07 | Added current Technical Baseline authority, toolchain proof gate and 24-run route dependency. |
