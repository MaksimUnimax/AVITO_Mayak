# Маяк Авито — дорожная карта

**Версия:** 1.1
**Статус:** APPROVED planning baseline
**Правило:** roadmap показывает этапы и факт прохождения. Детали конкретной работы живут в task packet, report и модульных playbook-документах.

## Статусы

- `[x]` — принято и завершено.
- `[~]` — в работе.
- `[ ]` — ещё не начато.
- `[!]` — заблокировано доказанным вопросом или внешней зависимостью.

## A. Управление и документация

- `[x] A0.1` Зафиксирована целевая модель продукта v0.1 как DRAFT.
- `[x] A0.2` Зафиксирована архитектурная карта 13 модулей v0.1 как DRAFT.
- `[x] A0.3` Зафиксированы правила руководства ChatGPT, запрет на догадки, поиск причины на уровень выше и запрет на постоянные костыли.
- `[x] A0.4` Создан отдельный GitHub deploy key и проверен доступ к пустому репозиторию.
- `[x] A0.5` Documentation Bootstrap: структура репозитория, точка входа, governance, журналы, реестры и импорт исходных документов.
- `[x] A0.6` Bootstrap commit проверен и принят: 48 исходных файлов совпали с буквальным текстом; историческая URL-опечатка сохранена и исправлена append-only записью.
- `[~] A0.7` Собрать доказательства технической среды для Technical Baseline and Contract Package v1.0 (`TASK-001`).
- `[ ] A0.8` На основе принятых доказательств подготовить Architecture Baseline, Security/Privacy Model и Contract Package v1.0.
- `[ ] A0.9` Подготовить физическую data model, migration policy и compatibility policy.
- `[ ] A0.10` Подготовить test strategy, fixture registry, acceptance matrix и reference regression policy.
- `[ ] A0.11` Подготовить operations/deployment runbooks и реестр внешних референсов.
- `[ ] A0.12` Проверить, переработать и принять автономные playbook-документы 13 модулей на основе утверждённых контрактов.

## B. Общая основа продукта

- `[ ] B1` Platform & Contracts.
- `[ ] B2` Identity & Access: минимальный контур account, identity, role и link challenge.
- `[ ] B3` Entitlements & Billing: только тарифные права и лимиты без платёжного провайдера.
- `[ ] B4` Beacon Management: Маяки, source URL, snapshot, overrides и versioned effective configuration.

## C. Рабочее ядро Маяка

- `[ ] C1` Egress Routing: route abstraction, Windows Egress Agent development path, lease and heartbeat contracts.
- `[ ] C2` Avito Parser Adapter: только по доказанным источникам, fixtures и реальным test URLs.
- `[ ] C3` Scan Orchestration & Listing State: run lifecycle, baseline, `listing_id + price`, observations and safe failure.
- `[ ] C4` Notification Delivery: durable outbox, deduplication, retries and delivery log.

## D. Bot-first интерфейсы

- `[ ] D1` Telegram Adapter.
- `[ ] D2` MAX Adapter.
- `[ ] D3` Closed Admin & Support interface.

## E. Последующие этапы

- `[ ] E1` Public Web Cabinet.
- `[ ] E2` Filter Catalog & Builder.
- `[ ] E3` Payment provider and subscription lifecycle as a submodule of Entitlements & Billing.
- `[ ] E4` Scaling, additional routes/channels and operational maturity.

## Гейты перехода

1. Нельзя начинать product-code до принятия A0.8–A0.11.
2. Нельзя начинать модуль, если его входные/выходные контракты, владелец данных, fake dependencies и acceptance checks не утверждены.
3. Нельзя начинать внешнюю интеграцию по памяти: до кода нужна актуальная официальная документация и контрактная задача.
4. Нельзя считать этап завершённым только по отчёту CLI: ChatGPT обязан проверить код, diff, тесты и evidence.
