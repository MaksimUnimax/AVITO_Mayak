# Маяк Авито — Architecture Baseline

**Версия:** 1.0  
**Статус:** APPROVED documentation baseline  
**Дата:** 2026-07-07  
**Основание:** ADR-0001, ADR-0005, `MAYAK_AVITO_TARGET_MODEL_v0.1.md`, `MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md`, `MODULE_REGISTRY.md`, TASK-001 accepted evidence.  
**Не является:** разрешением на product-code, migration, deployment, runtime provisioning или выбор конкретного technology stack.

---

## 1. Назначение

Этот документ фиксирует минимальные архитектурные инварианты, уже подтверждённые проектной документацией, и границы того, что пока не выбрано.

Он нужен, чтобы следующие документы о contracts, data, quality, operations и module playbooks не создавали несовместимые локальные решения.

## 2. Иерархия источников

1. Public GitHub `main` и `docs/MANIFEST.md` — фактическое состояние и canonical documentation layout.
2. Append-only ADR — принятые решения в пределах своей записи.
3. Этот baseline — утверждённые архитектурные границы без выбора implementation stack.
4. `MAYAK_AVITO_TARGET_MODEL_v0.1.md` и architecture map v0.1 — DRAFT context; они не закрывают open decisions.
5. `OPEN_DECISIONS.md` — незакрытые решения, которые запрещено подменять предположением.

Ни один пример будущей структуры из DRAFT-документа не создаёт альтернативный canonical layout. Новые documentation files создаются только в путях, определённых `docs/MANIFEST.md`.

## 3. Подтверждённая стартовая форма системы

### 3.1. Modular monolith first

Принята стартовая форма: один репозиторий, модульный монолит, явные внутренние module boundaries, отдельные процессы worker/scheduler и отдельный Windows Egress Agent.

Это не означает:

- готовую физическую topology;
- запуск сервисов;
- создание containers;
- утверждение языка, framework, package manager или queue technology;
- создание отдельных deployment units для 13 модулей.

### 3.2. Логические модули

Границы 13 модулей определяются `MODULE_REGISTRY.md`:

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

Три сквозных контура: Security & Privacy, Observability & Operations, Data & Compatibility Governance.

### 3.3. Неподвижные границы

- Внешний adapter не пишет напрямую в таблицу или внутреннее состояние другого модуля.
- Межмодульное взаимодействие допускается только через будущие утверждённые contracts, public commands, events или read-models.
- Parser не доставляет уведомление напрямую в Telegram/MAX.
- Telegram, MAX, Web и Admin не владеют отдельной пользовательской базой.
- Один Маяк принадлежит одному внутреннему `account_id`.
- История объявлений и уведомлений изолируется по `beacon_id`.
- Source URL Маяка не переписывается пользовательскими overrides.
- Open decisions не получают неявного значения в дизайне, коде или документации.

## 4. Data and process boundaries

ADR-0001 фиксирует целевую primary PostgreSQL database как часть будущей modular-monolith architecture.

Эта запись не разрешает:

- устанавливать PostgreSQL;
- подключаться к существующей PostgreSQL;
- использовать foreign database;
- создавать physical schema, tables, migrations, credentials или backups;
- выбирать queue/cache/storage implementation.

Физическая data model, migration policy, compatibility rules, unique constraints, retry semantics и storage topology относятся к отдельным будущим documentation gates.

## 5. Technology selection boundary

TASK-001 подтвердил доступность некоторых инструментов на shared host. Это evidence о snapshot, а не approval использовать их в проекте.

До отдельного принятого решения не выбраны:

- implementation language;
- application framework;
- package manager;
- runtime and process model;
- queue and cache technology;
- object/file storage;
- API transport and schema format;
- observability stack;
- ingress, reverse proxy, TLS and ports;
- secrets delivery mechanism;
- database provisioning and migration tool.

Любая будущая технология должна быть выбрана отдельным доказанным документом с compatibility, security, operation and rollback implications.

## 6. Required design gates before implementation

До первого product-code должны быть приняты:

1. Common Contract Foundation.
2. Data Model and Migration/Compatibility Policy.
3. Test Strategy, Fixture Registry, Acceptance Matrix and Reference Regression Policy.
4. Environment, observability, recovery and release boundaries.
5. Official/reference evidence for Avito, Telegram and MAX.
6. Autonomous module playbook for the module receiving work.
7. Exact CLI task packet with literal scope, tests and acceptance criteria.

## 7. Explicit non-goals

Этот baseline не определяет:

- API endpoints;
- DTO, JSON Schema, OpenAPI or event payloads;
- database schema;
- worker protocol;
- authentication implementation;
- deployment topology;
- production readiness;
- payment implementation;
- parser implementation;
- browser or bot UI.

## 8. Change control

Изменение module boundary, data ownership, security boundary, route boundary, common invariant или technology decision требует:

1. доказанной причины;
2. append-only decision-log entry, когда это требуется governance;
3. обновления зависимых canonical documents;
4. отдельной acceptance проверки ChatGPT.

## 9. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый architecture baseline: modular-monolith boundaries, technology-selection limits и implementation gates без выбора stack. |
