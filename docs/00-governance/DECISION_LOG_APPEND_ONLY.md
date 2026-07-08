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

## ADR-0009 — 2026-07-08 — Entitlements & Billing owner decisions for Free/Basic and first-stage billing policy

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Закрывает:** `OD-001`, `OD-002`, `OD-003`, `OD-004`, `OD-005`.

**Контекст:** Module playbook `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` left tariff period, later tiers, intervals, expiry behavior and payment policy open. The owner supplied explicit product decisions for the first Entitlements & Billing implementation planning stage. These decisions must be captured in governance before they are used in contracts, tests, documentation, code, tariff semantics or later runtime tasks.

**Решение:**

1. `OD-001`: the Basic tariff price `990 ₽` is for one month.
2. `OD-002`: at the current stage there are only two approved product tariff families: `Free` and `Basic`. No additional paid tariffs are introduced now as concrete product defaults. Future tariffs must be possible through Admin capability, but their names, prices and limits are not predeclared by this decision.
3. `OD-003`: Basic allows monitoring intervals starting from 5 minutes with a 5-minute step: 5, 10, 15, 20 and further by the same step. Free allows one Beacon, reduced functionality and monitoring intervals starting from 3 hours with a 3-hour step: 3, 6, 9, 12 hours and further by the same step. Free uses the same entitlement mechanism as a paid tariff, but with stricter limits.
4. `OD-004`: after paid access expires, only Free remains available. All Beacons are frozen. The user receives a message that the tariff has ended. The user must choose one Beacon that will remain under Free, must bring that Beacon into Free requirements and must manually start that Beacon. The system must not automatically choose the remaining Free Beacon.
5. `OD-005`: first-stage payment provider candidates are YooKassa, Telegram Stars and Tinkoff. The first stage uses manual renewal only. Recurring payments are not needed now. Refunds are manual only. Supported monetary/payment units for the first stage are RUB and Telegram Stars. There is no trial, grace period or proration; Free tariff is the alternative to trial/grace. Manual access is required as an Admin capability. Admin capability must eventually allow changing roles, adding new tariffs, editing existing tariffs and manually assigning tariffs/access to accounts.

**Scope boundary:** This decision captures product policy only. It does not authorize payment provider integration, payment account setup, real provider SDK calls, webhook endpoints, invoice/receipt/tax implementation, card data handling, Telegram Stars runtime integration, Tinkoff runtime integration, YooKassa runtime integration, Admin UI implementation, database schema, migrations, billing runtime service, Docker, CI/CD, deploy, runtime configuration, secrets, tokens or payment credentials.

**Consequences:**

- Entitlements & Billing may use `Free` and `Basic` as approved current product policy in later exact semantic-contract tasks.
- Any later provider-specific task still requires current official provider evidence and a separate exact task.
- Payment provider responses remain external evidence and never grant access by themselves.
- Manual access must require verified actor context, authorization, reason, scope, effective interval, idempotency and audit reference.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
- Persistence, migrations, Admin UI, provider runtime integration, Beacon runtime mutation, scheduler integration and notification sending remain blocked until their own gates are opened.

---

## ADR-0010 — 2026-07-08 — Entitlements precedence policy for effective entitlement evaluation

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-03 `Effective entitlement evaluation semantics` for semantic evaluator contracts/tests only.

**Не открывает:** runtime evaluator, billing runtime service, database persistence, migrations, provider integration, payment SDK/API calls, webhooks, invoice/receipt/tax implementation, Admin UI, Web Cabinet, Beacon runtime mutation, scheduler integration, notification sending, Docker, CI/CD, deploy, secrets, tokens or payment credentials.

**Контекст:** `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` states that exact precedence among tariff, subscription and manual grants remains a future contract/task detail and must be explicit before implementation. `ADR-0009` approved the first-stage Free/Basic billing policy and confirmed that payment provider responses remain external evidence and never grant access by themselves. EB-02 added semantic contracts and fixtures, but EB-03 effective entitlement evaluation remained blocked until an explicit precedence decision.

**Решение:**

1. `TariffDefinition` defines the baseline tariff policy: approved capability set, limits, scan interval rules, price/period semantics where applicable and explicit future gates.
2. An active `Subscription` selects the currently applicable tariff family for an account. If the paid subscription is active, it selects the paid tariff policy. If paid access is expired or unavailable, evaluation must move to the Free-only requirement state described below.
3. `EntitlementGrant` may add, restrict or qualify individual capabilities only inside its explicit account scope, capability scope and effective interval. It must not silently mutate the selected tariff definition or create a new tariff family.
4. `ManualAccessGrant` has highest precedence only inside its explicit target account, capability/scope, effective interval, reason, actor context, idempotency reference and audit reference. A valid manual grant may override a tariff/subscription denial only for that exact explicit scope and interval. Outside that scope or interval, normal tariff/subscription/grant evaluation applies.
5. `PaymentRecord` and `PaymentEvent` are non-authority evidence. They never grant access directly and never produce an entitlement by themselves. Any future payment-derived access requires a separate server-authorized transition and its own exact task.
6. If paid access is expired, the effective result must represent a Free-only requirement state. All paid Beacons are treated as requiring user action: user-choice-required and free-compliance-required. The system must not automatically choose the remaining Free Beacon.
7. If sources disagree or the evaluator cannot prove a safe deterministic result, the result must be `AMBIGUOUS` or `CONFLICT`; it must not silently allow access.
8. EB-03 semantic evaluator contracts/tests may use the following result statuses only as semantic outcomes: `ALLOWED`, `DENIED`, `BLOCKED`, `EXPIRED`, `AMBIGUOUS`, `UNSUPPORTED`, `USER_CHOICE_REQUIRED`, `FREE_COMPLIANCE_REQUIRED`, `CONFLICT`.

**Evaluation precedence order for EB-03 semantic contracts/tests:**

1. Validate account ownership/scope first. Foreign-account or missing-account-scope inputs must not evaluate to silent allow.
2. Treat payment records/events as evidence only and never as authority.
3. Determine the baseline tariff policy from the active subscription state and approved tariff definitions.
4. If paid access is expired, return the Free-only requirement state instead of choosing a Beacon or mutating Beacon state.
5. Apply valid entitlement grants only within their explicit scope and effective interval.
6. Apply valid manual access grants only within their explicit scope and effective interval, with actor, reason, idempotency and audit reference.
7. If a deterministic safe decision remains impossible, return `AMBIGUOUS` or `CONFLICT`.

**Consequences:**

- EB-03 may proceed only for deterministic semantic evaluator contracts/tests.
- EB-03 must remain transport/provider/framework/ORM neutral.
- EB-03 must not implement database-backed evaluation, repositories, provider adapters, webhooks, runtime services, Beacon mutation, scheduler integration, notification sending or Admin UI.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
- Usage counters, Beacon integration, provider adapters, reconciliation/refunds, persistence/migrations and Admin tariff management remain gated by their own roadmap steps.
