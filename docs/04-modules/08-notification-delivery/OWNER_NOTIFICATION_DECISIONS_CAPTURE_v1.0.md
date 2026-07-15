# Маяк Авито — Owner Notification Decisions Capture v1.0

**Статус:** APPROVED owner decision capture for Module 08 semantic planning

**Дата:** 2026-07-12

**Модуль:** `08-notification-delivery`

**Roadmap step:** `ND-01`

**Technical task:** `ND-01-GOVERNANCE-CAPTURE-20260712-001`

**Source-of-truth playbook:** `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md`

**Governance decision:** `ADR-0020`, corrected by `ADR-0021`

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
```

Exact adapter wording and UI remain adapter/Web scope.

## 5. External unavailable and recovery

При начале внешней проблемы разрешён один понятный generic status effect.

Одинаковый problem status не повторяется на каждом scan interval. Material change может быть отдельным source fact только после approved classification.

После восстановления разрешён один recovery-result:

1. with new listings;
2. recovered with no new listings;
3. lost anchors restored with latest fresh listings, not confirmed-new;
4. blocked or ambiguous when required evidence is insufficient.

Если problem began while access was active, один owed recovery-result может пройти approved entitlement grace. После него снова действуют current entitlement rules.

Notification failure не удаляет Scan pending recovery state и не создаёт несколько recovery notifications за пропущенные интервалы.

## 6. Grouped listing result

Один scan result с несколькими новыми объявлениями является одним generic notification effect.

Notification Delivery сохраняет:

1. полный count;
2. все безопасные listing-card references;
3. source and reason classification;
4. account/Beacon scope;
5. correlation/causation evidence.

Notification Delivery не:

1. обрезает данные до preview limit;
2. создаёт отдельное generic notification для каждого listing по умолчанию;
3. выбирает Telegram/MAX pagination;
4. выбирает buttons, carousel or Mini App;
5. определяет Web UI.

## 7. Listing-card boundary

Разрешённые безопасные facts, если они уже существуют в approved upstream contract:

1. title;
2. price;
3. city/geography;
4. safe listing URL/reference;
5. approved photo/preview reference;
6. Beacon reference/name;
7. reason label;
8. provenance/source reference.

Phone, seller, seller rating and description допустимы только после отдельного Parser/detail/privacy gate.

Notification Delivery не fetch, parse or enrich missing fields and не хранит raw Avito HTML/JSON or provider payload.

## 8. Channel planning

Default product direction:

```text
create generic delivery work for all enabled and verified channels
```

User preference может отключить конкретный channel.

Telegram Adapter владеет Telegram-specific mapping/rendering/delivery.

MAX Adapter владеет MAX-specific mapping/rendering/delivery.

Web Cabinet владеет UI and read presentation.

Notification Delivery владеет generic channel plan and attempt state only.

Success одного channel не стирает failure or ambiguous state другого channel.

Exact priority and fallback policy remain deferred.

## 9. Unknown send and reconciliation

Unknown, ambiguous or interrupted provider send:

1. сохраняет attempt identity;
2. переходит в reconciliation-first reconciliation-required/ambiguous semantic state;
3. не retry blindly;
4. не создаёт duplicate user-visible effect;
5. replay возвращает original known, pending or ambiguous outcome.

Provider HTTP success, Egress transport success, queue success or callback receipt сами по себе не являются accepted delivery.

## 10. Minimal delivery history

Минимальная safe history требуется для:

1. deduplication;
2. support;
3. reconciliation;
4. user/admin safe read models.

Она может содержать safe references and outcome classes, но не является:

1. full listing archive;
2. full message/chat history;
3. raw provider archive;
4. credentials store;
5. personal-data warehouse.

Retention, deletion, archive and compaction remain gated by `OD-013`.

## 11. Deferred behavior

Не разрешены этим документом:

1. read/click/open tracking;
2. quiet hours;
3. digest;
4. time batching;
5. exact retry/backoff;
6. provider rate limits;
7. exact preference schema;
8. exact unsubscribe UI;
9. provider templates;
10. Telegram/MAX payloads;
11. database schema or migrations;
12. queue, worker, broker or scheduler;
13. provider credentials;
14. provider API calls;
15. runtime services;
16. Docker, CI/CD or deploy.

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

```text
ND-02 — Semantic source event intake contracts
```

ND-02 разрешается только отдельной exact task после повторной проверки GitHub `main`, parallel-main state, Module 08 playbook and upstream Scan contract prerequisites.
