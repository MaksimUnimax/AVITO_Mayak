# Маяк Авито — Owner Notification Decisions Capture v1.0

**Статус:** APPROVED owner decision capture for Module 08 semantic planning

**Дата:** 2026-07-12

**Модуль:** `08-notification-delivery`

**Roadmap step:** `ND-01`

**Technical task:** `ND-01-GOVERNANCE-CAPTURE-20260712-001`

**Source-of-truth playbook:** `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md`

**Governance decision:** `ADR-0020`

## 1. Назначение

Этот документ фиксирует решения владельца для последующих точных semantic-only задач Notification Delivery.

Документ не является physical schema, queue, worker, provider adapter, provider payload, message template, bot, webhook, Mini App, runtime configuration or deploy authorization.

## 2. Current user-visible notification families

Текущий approved product scope допускает generic notification work для:

1. новых объявлений после committed Scan fact;
2. понятного статуса при начале или материальном изменении внешней проблемы Avito, route or parser;
3. одного результата одного recovery scan;
4. lost-anchors recovery как `latest fresh / state restored`, not confirmed-new;
5. optional no-new status при включённой user preference и frequency gate;
6. approved service/access facts после отдельного Entitlements/Beacon gate.

Не создают user-visible listing notification:

1. initial baseline;
2. начало каждого scan;
3. Parser-only outcomes;
4. Egress-only outcomes;
5. technical stack traces;
6. raw provider events;
7. unapproved callbacks;
8. изменение цены старого объявления в текущем product scope.

## 3. Price-change and baseline

`ListingPricePairFirstSeen` не является активным user-visible trigger в текущем scope.

Price разрешено использовать как approved listing-card display fact. Изменение price само по себе не создаёт outbox item.

Initial baseline не отправляется пользователю как найденные новые объявления.

## 4. No-new status

No-new push notification:

1. suppressed/off by default;
2. не создаётся после каждого scan;
3. не создаётся каждые пять минут;
4. может быть включено пользователем в будущей preference model;
5. не может отправляться чаще одного раза в час;
6. не заменяет status/read model.

Пример product direction:

```text
Маяк работает. Новых объявлений нет.

Exact adapter wording and UI remain adapter/Web scope.

## 5. External unavailable and recovery

При начале внешней проблемы разрешён один понятный generic status effect.

Одинаковый problem status не повторяется на каждом scan interval. Material change может быть отдельным source fact только после approved classification.

После восстановления разрешён один recovery-result:

with new listings;

recovered with no new listings;

lost anchors restored with latest fresh listings, not confirmed-new;

blocked or ambiguous when required evidence is insufficient.

Если problem began while access was active, один owed recovery-result может пройти approved entitlement grace. После него снова действуют current entitlement rules.

Notification failure не удаляет Scan pending recovery state и не создаёт несколько recovery notifications за пропущенные интервалы.

## 6. Grouped listing result

Один scan result с несколькими новыми объявлениями является одним generic notification effect.

Notification Delivery сохраняет:

полный count;

все безопасные listing-card references;

source and reason classification;

account/Beacon scope;

correlation/causation evidence.

Notification Delivery не:

обрезает данные до preview limit;

создаёт отдельное generic notification для каждого listing по умолчанию;

выбирает Telegram/MAX pagination;

выбирает buttons, carousel or Mini App;

определяет Web UI.

## 7. Listing-card boundary

Разрешённые безопасные facts, если они уже существуют в approved upstream contract:

title;

price;

city/geography;

safe listing URL/reference;

approved photo/preview reference;

Beacon reference/name;

reason label;

provenance/source reference.

Phone, seller, seller rating and description допустимы только после отдельного Parser/detail/privacy gate.

Notification Delivery не fetch, parse or enrich missing fields и не хранит raw Avito HTML/JSON or provider payload.

## 8. Channel planning

Default product direction:

create generic delivery work for all enabled and verified channels

User preference может отключить конкретный channel.

Telegram Adapter владеет Telegram-specific mapping/rendering/delivery.

MAX Adapter владеет MAX-specific mapping/rendering/delivery.

Web Cabinet владеет UI and read presentation.

Notification Delivery владеет generic channel plan and attempt state only.

Success одного channel не стирает failure or ambiguous state другого channel.

Exact priority and fallback policy remain deferred.

## 9. Unknown send and reconciliation

Unknown, ambiguous or interrupted provider send:

сохраняет attempt identity;

переходит в reconciliation-required/ambiguous semantic state;

не retry blindly;

не создаёт duplicate user-visible effect;

replay возвращает original known, pending or ambiguous outcome.

Provider HTTP success, Egress transport success, queue success or callback receipt сами по себе не являются accepted delivery.

## 10. Minimal delivery history

Минимальная safe history требуется для:

deduplication;

support;

reconciliation;

user/admin safe read models.

Она может содержать safe references and outcome classes, но не является:

full listing archive;

full message/chat history;

raw provider archive;

credentials store;

personal-data warehouse.

Retention, deletion, archive and compaction remain gated by OD-013.

## 11. Deferred behavior

Не разрешены этим документом:

read/click/open tracking;

quiet hours;

digest;

time batching;

exact retry/backoff;

provider rate limits;

exact preference schema;

exact unsubscribe UI;

provider templates;

Telegram/MAX payloads;

database schema or migrations;

queue, worker, broker or scheduler;

provider credentials;

provider API calls;

runtime services;

Docker, CI/CD or deploy.

## 12. Module boundaries

Scan owns committed source facts, baseline, listing state, no-new facts and recovery facts.

Parser owns extraction and provider response classification.

Egress Routing owns routes, agents, leases and transport outcomes.

Identity owns verified account and target-link authority.

Entitlements owns effective access decisions.

Beacon Management owns Beacon configuration and lifecycle.

Telegram/MAX adapters own provider-specific behavior.

Web Cabinet owns UI rendering.

Notification Delivery owns only generic notification intake, eligibility, outbox, channel plan, attempts, deduplication, reconciliation and safe delivery-history semantics.

## 13. Next gate

После принятия ND-01 следующий возможный roadmap step:

ND-02 — Semantic source event intake contracts

ND-02 разрешается только отдельной exact task после повторной проверки GitHub main, parallel-main state, Module 08 playbook and upstream Scan contract prerequisites.
