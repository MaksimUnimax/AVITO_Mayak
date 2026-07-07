# Маяк Авито — журнал решений (append-only)

**Статус:** APPROVED append-only log  
**Правило:** записи не редактируются, не удаляются и не переставляются. Новое решение или корректировка добавляется только новой записью в конец.

---

## ADR-0001 — 2026-07-06 — Стартовая архитектура: modular monolith first

**Статус:** APPROVED  
**Контекст:** проект состоит из 13 логических модулей, но команда и процесс работы нерегулярны; отдельные микросервисы на старте создадут лишнюю операционную нагрузку.

**Решение:**

Стартовать как модульный монолит: один репозиторий, одна основная PostgreSQL-база, явные внутренние границы модулей, отдельные процессы worker/scheduler и отдельный Windows Egress Agent. Это не означает отказ от будущего выделения нагруженных частей.

**Последствие:**

Нельзя создавать отдельные базы и независимые production-deployments модулей без нового доказанного архитектурного решения.

---

## ADR-0002 — 2026-07-06 — Управление проектом и роль CLI

**Статус:** APPROVED  
**Контекст:** для предотвращения архитектурной самодеятельности Codex/CLI нельзя передавать исполнителю принятие решений.

**Решение:**

ChatGPT является разработчиком, архитектором и руководителем проекта. CLI-исполнитель только выполняет точное задание, запускает проверки и возвращает доказательства. Он не выбирает архитектуру, контракт, следующий шаг или содержание документации.

**Последствие:**

Каждая задача CLI должна содержать доказанный baseline, решение ChatGPT, разрешённый и запрещённый scope, проверки и критерии приёмки.

---

## ADR-0003 — 2026-07-06 — Буквальная передача документации CLI-исполнителю

**Статус:** APPROVED  
**Контекст:** документация, написанная CLI «по смыслу», создаёт неотслеживаемые предположения и расхождения.

**Решение:**

Каждый документ или append-only блок передаётся CLI-исполнителю ChatGPT полным точным текстом. CLI создаёт, заменяет или добавляет только этот текст и не вносит самостоятельных дополнений, исправлений или сокращений.

**Последствие:**

При отсутствии полного текста или append-блока CLI обязан остановиться со статусом `STOP_DOCUMENT_TEXT_MISSING`.

---

## ADR-0004 — 2026-07-06 — Исправлять причину на уровень выше симптома

**Статус:** APPROVED  
**Контекст:** локальные патчи скрывают следствия, оставляют неверный source of truth и повторно создают ошибки.

**Решение:**

Перед любым постоянным исправлением ChatGPT обязан проверить механизм симптома, владельца неверного состояния, нарушенный контракт/инвариант и подтверждённую корневую причину на уровень выше симптома. Постоянные костыли запрещены. Временная защита допустима только как явно помеченная `TEMPORARY_MITIGATION` с отдельной задачей на устранение причины.

**Последствие:**

Отчёт об исправлении должен доказывать проверку уровня выше, устранение причины или ограниченной временной защиты, а также тест против повторения класса ошибки.

---

## ADR-0005 — 2026-07-06 — Целевая модель и архитектурная карта сохраняются как DRAFT

**Статус:** APPROVED  
**Контекст:** текущие документы v0.1 фиксируют большую часть продукта, но сами имеют статус черновиков и содержат открытые решения.

**Решение:**

Хранить их в репозитории без тихого переписывания, со статусом `DRAFT`. Они являются обязательной базой для анализа, но не закрывают открытые решения и не заменяют утверждённые контрактные документы.

**Последствие:**

Нельзя выдумывать незакрытые значения — период тарифа, интервалы, платежи, phone-login, retention и другие пункты. Они остаются в `OPEN_DECISIONS.md` до отдельного решения.

## ADR-0006 — 2026-07-06 — Independent remote repository supervision

**Статус:** APPROVED

**Решение:** public GitHub `main` is the factual source of truth. ChatGPT independently reads it before repository-changing decisions and independently verifies commit, diff, final content, append-only integrity, forbidden scope and remote state after CLI reports. CLI verifies its local baseline but does not replace this review. Foreign shared-host resources do not belong to the project.

**Последствие:** handoff, local worktree and CLI report cannot independently close a task; baseline mismatch stops without self-repair; code and deploy remain gated by separate approved documentation.

---

## ADR-0007 — 2026-07-07 — Technical Baseline becomes a separate mandatory Run 10

**Статус:** APPROVED

**Контекст:**

Architecture Baseline v1.0 explicitly left the implementation stack unselected, while the Platform & Contracts README requires an approved Technical Baseline before its module playbook. The existing 23-run route moved directly from provider references to module playbooks and therefore omitted a required gate.

**Решение:**

Expand the documentation cycle from 23 to 24 runs. Insert Technical Baseline as Run 10. Move Telegram and MAX reference policies to Run 11. Move the thirteen module playbooks to Runs 12–24 without combining modules. Final independent documentation audit follows Run 24.

Run 10 consists of the Technology Selection Method, Technical Baseline Evidence, Technical Baseline, and necessary architecture/environment/quality version updates. It is documentation only and creates no implementation or runtime artifacts.

**Последствие:**

Platform & Contracts cannot receive a playbook before Run 10 is accepted and synchronized. Existing references to Runs 11–23 as the module-playbook interval are superseded by the current manifest, roadmap, current state and Acceptance Matrix v1.1. The second documentation agent must resume from Run 11 and use the 24-run route.

---

## ADR-0008 — 2026-07-07 — Core implementation technology baseline

**Статус:** APPROVED

**Контекст:**

The project requires one reproducible core toolchain compatible with the modular-monolith boundaries, PostgreSQL ownership, typed contracts, background work, Windows egress boundary and the mandatory `Duff89/parser_avito` implementation reference. The reference is a local Python application and is not a SaaS architecture or a permission to copy source.

**Решение:**

Select the following core baseline:

- CPython 3.14 supported line, standard GIL build;
- `uv` project management with `pyproject.toml` and committed `uv.lock`, with the exact `uv` version pinned by the first toolchain task;
- FastAPI and Uvicorn for the HTTP application boundary;
- Pydantic v2 and pydantic-settings for external DTO and configuration validation;
- HTTPX as the default HTTP client;
- PostgreSQL 18 supported line;
- SQLAlchemy 2, Psycopg 3 and Alembic for persistence and migration tooling;
- PostgreSQL-backed durable work claims and transactional outbox for the initial worker/scheduler model, without a required external broker;
- pytest, pytest-asyncio, RESpx, Ruff, mypy, import-linter and coverage.py for the initial quality toolchain;
- OpenTelemetry Python API/SDK as the telemetry instrumentation boundary, while exporter/backend selection remains deferred.

Framework and ORM objects are not intermodule contracts. Module-specific and operations-specific dependencies remain deferred to their own evidence and playbooks.

Flet, SQLite, Excel dependencies, VK integration, local TOML as multiuser state, Requests as a second default HTTP client and direct parser-to-notification coupling are not part of the core baseline.

**Последствие:**

The first implementation authorization must be a separate proof/toolchain task that creates exact dependency pins and demonstrates isolated reproducibility. This ADR does not authorize implementation, installation, migration, database creation, external access, deployment or server mutation. A major technology change requires new evidence, compatibility analysis, rollback/roll-forward implications and a new append-only decision.
