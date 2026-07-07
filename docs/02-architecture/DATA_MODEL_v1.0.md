# Маяк Авито — Data Model

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, MODULE_REGISTRY.md, OPEN_DECISIONS.md.
**Не является:** физической схемой БД, DDL, ORM-моделью, migration, seed-набором, выбором PostgreSQL tooling, разрешением на создание базы данных или product-code.

---

## 1. Назначение

Этот документ фиксирует концептуальную модель данных, границы владения и обязательные инварианты, которые должны сохраняться в будущих contracts, storage design, tests и module playbooks.

Он не превращает DRAFT-предположения из product target model или architecture map в принятые продуктовые решения. Любая деталь, не подтверждённая APPROVED-источником, остаётся явно открытой или контекстной.

## 2. Иерархия источников

1. Public GitHub `main`, `docs/MANIFEST.md` и governance documents.
2. Append-only ADR в пределах принятых записей.
3. Architecture Baseline, Security and Privacy Model и Common Contract Foundation.
4. Этот Data Model как концептуальный data-governance baseline.
5. `MAYAK_AVITO_TARGET_MODEL_v0.1.md` и architecture map v0.1 только как DRAFT context.
6. `OPEN_DECISIONS.md` как обязательный реестр незакрытых решений.

При конфликте DRAFT-контекста с APPROVED-документом применяется APPROVED-документ. Open decision не получает значения по умолчанию.

## 3. Уровень модели

Модель определяет:

- логические data domains;
- owning module для mutation authority;
- устойчивые semantic identifiers;
- обязательные связи и isolation boundaries;
- authoritative records и производные read models;
- требования к audit, privacy, idempotency and compatibility;
- данные, которые запрещено создавать или копировать без отдельного решения.

Модель не определяет:

- таблицы, колонки, индексы, foreign keys или partitions;
- exact identifier encoding;
- timestamp type or format;
- transaction isolation level;
- storage engine, schema names или database roles;
- soft-delete/hard-delete mechanism;
- retention periods;
- migration tool, ORM или query language;
- event broker, queue или cache;
- physical audit storage;
- provider-specific payload schema.

## 4. Общие правила владения

1. Только owning module разрешает изменение принадлежащего ему authoritative state.
2. Другой модуль запрашивает изменение только через future approved command или service contract.
3. External adapter не пишет напрямую в state другого модуля.
4. Read model не становится источником истины и должен быть восстановим из authoritative records или approved events.
5. Дублирование authoritative customer identity, Beacon configuration, entitlement или delivery state в client adapters запрещено.
6. Межмодульная ссылка хранит semantic identifier, но не даёт права менять целевой объект.
7. Cross-cutting audit фиксирует факт разрешённого действия, но не заменяет state owning module.
8. Любая смена data ownership требует append-only decision, изменения module registry/affected contracts и независимой acceptance.

## 5. Базовые идентификаторы

| Идентификатор | Семантика | Минимальная область уникальности | Владелец семантики |
|---|---|---|---|
| `account_id` | Внутренняя учётная запись клиента или сотрудника | Система | Identity & Access |
| `identity_id` | Связь account с одним проверяемым внешним или локальным способом идентификации | Система | Identity & Access |
| `beacon_id` | Один Маяк и граница его configuration/history | Система | Beacon Management |
| `beacon_config_revision_id` | Неизменяемая ревизия конфигурации Маяка | В пределах `beacon_id` или система; exact encoding не выбран | Beacon Management |
| `run_id` | Один логический запуск мониторинга | Система | Scan Orchestration & Listing State |
| `observation_id` | Один зафиксированный результат наблюдения объявления в запуске | Система | Scan Orchestration & Listing State |
| `notification_event_id` | Внутреннее событие, требующее оценки доставки | Система | Notification Delivery |
| `delivery_attempt_id` | Одна попытка доставки по конкретному endpoint/channel | Система | Notification Delivery |
| `route_id` | Логический маршрут выхода | Система | Egress Routing |
| `agent_id` | Зарегистрированный egress agent | Система | Egress Routing |
| `correlation_id` | Сквозная связь действий и evidence | В пределах принятой contract policy | Platform & Contracts semantics |
| `message_id` | Идентификатор конкретного contract message/event | В пределах принятой contract policy | Producer по Common Contract Package |

Точный тип, длина, формат и генератор идентификаторов не выбраны.

## 6. Identity & Access domain

**Owning module:** Identity & Access.

Концептуальные authoritative records:

| Record | Назначение | Обязательные границы |
|---|---|---|
| Account | Внутренняя account boundary | Не заменяется Telegram/MAX/email/phone identifier |
| AccountIdentity | Связь Account с provider/local identity | Weak correlation не разрешает automatic merge |
| ContactPoint | Разрешённый канал контакта и verification state | Политика обязательности телефона остаётся OD-007 |
| CredentialReference | Ссылка на защищённый credential material | Raw password/token/code не входит в common data model |
| RoleAssignment | Server-authorized роль в разрешённом scope | UI-флаг не является authorization |
| AuthSession | Разрешённая session state | Exact session technology/TTL не выбраны |
| AuthChallenge | Ограниченный challenge lifecycle | Raw one-time code не хранится в ordinary logs |
| IdentityLinkChallenge | Проверяемое намерение связать identities | Merge policy остаётся OD-008 |

Инварианты:

- `account_id` является единственной базовой границей account-owned state.
- Provider identity не становится самостоятельным account.
- Automatic merge по username, avatar, display name, phone, email или другому weak signal запрещён.
- Credential material и audit/read models разделяются.
- Политика phone+password, recovery и обязательности телефона остаётся OD-006/OD-007.

## 7. Entitlements & Billing domain

**Owning module:** Entitlements & Billing.

Концептуальные authoritative records:

- TariffDefinition;
- Subscription;
- EntitlementGrant;
- ManualAccessGrant;
- PaymentRecord;
- PaymentEvent;
- UsageCounter или equivalent entitlement-consumption record после отдельного approval.

Обязательные границы:

- Tariff, subscription, entitlement и payment не смешиваются в один неразличимый статус.
- Payment provider response не является entitlement без server-authorized business transition.
- Manual access имеет actor, reason, scope, effective interval и audit reference.
- Provider payload не становится authoritative record без verification and normalization.
- Периоды, цены, лимиты, expiry behavior, provider, refunds, recurrence and manual-payment rules остаются OD-001–OD-005.
- Data Model не вводит default tariff values или billing states, отсутствующие в APPROVED decisions.

## 8. Beacon Management domain

**Owning module:** Beacon Management.

Концептуальные authoritative records:

| Record | Назначение |
|---|---|
| Beacon | Account-owned monitoring object и lifecycle boundary |
| BeaconSourceUrl | Исходный source URL с происхождением и validation state |
| BeaconConfigurationRevision | Неизменяемый snapshot разрешённой конфигурации |
| ExtractedSearchConfigurationSnapshot | Нормализованное извлечение параметров source URL, не заменяющее URL |
| BeaconFilterOverride | Явное пользовательское изменение поверх extracted snapshot |
| BeaconActivationState | Разрешённое состояние доступности/активации без неутверждённых enum |

Инварианты:

- Один Beacon принадлежит ровно одному `account_id`.
- Source URL не переписывается filter override или новым extraction result.
- Изменение effective configuration создаёт новую revision; historical revision не переписывается.
- Extracted snapshot и user override различимы по происхождению.
- Effective configuration должна быть воспроизводима из source reference, extracted snapshot, override и revision metadata.
- Exact supported filters, intervals и country-wide behavior остаются OD-003, OD-009, OD-010 и OD-011.
- Поведение после окончания entitlement остаётся OD-004.

## 9. Avito Parser Adapter boundary

**Owning module:** Avito Parser Adapter для adapter request/outcome semantics и ограниченного provider evidence. Adapter не владеет Beacon, Listing State или Notification authoritative state.

Концептуальные records/evidence:

- ParserRequestReference;
- FetchOutcome;
- ParseOutcome;
- NormalizedSearchResult;
- SourceStructureEvidence;
- ProviderRestrictionEvidence;
- ParserWarning/ErrorReference.

Правила:

- Failure, CAPTCHA, blocked access, malformed structure, incomplete result или route failure не превращаются в clean empty listing set.
- Raw external payload сохраняется только при отдельной evidence/retention policy, с minimization and redaction.
- Parser outcome передаётся Scan Orchestration через future approved contract.
- Parser не создаёт notification delivery и не меняет Beacon configuration напрямую.
- Поля и mapping Avito не считаются стабильными без current reference evidence.

## 10. Scan Orchestration & Listing State domain

**Owning module:** Scan Orchestration & Listing State.

Концептуальные authoritative records:

| Record | Назначение |
|---|---|
| ScanRun | Один логический запуск с Beacon/config/route references и outcome |
| ListingIdentityReference | Нормализованная ссылка на внешнюю identity объявления |
| ListingObservation | Наблюдение объявления в конкретном run и Beacon scope |
| BeaconListingState | Текущее authoritative state объявления только внутри `beacon_id` |
| BaselineReference | Ссылка на принятый baseline для конкретного Beacon |
| DifferenceResult | Объяснимый результат сравнения двух разрешённых состояний |
| ScanWarning/Error | Явное incomplete/ambiguous/failure state |

Инварианты:

- Scan and listing history изолированы по `beacon_id` даже при одинаковом external listing identifier.
- Observation не переписывает historical observation.
- Run с incomplete external outcome не помечается как clean success.
- Baseline/difference semantics должны быть приняты в module playbook и fixtures до implementation.
- DRAFT-правила о первом запуске, новом listing ID и сочетании listing ID/price не становятся APPROVED только из-за наличия этих records.
- Exact normalization, deduplication, listing attribute set и price semantics требуют current Avito evidence и module acceptance.

## 11. Egress Routing domain

**Owning module:** Egress Routing.

Концептуальные authoritative records:

- EgressRoute;
- EgressAgent;
- AgentHeartbeat;
- RouteLease;
- RouteHealthState;
- RouteRestriction/QuarantineRecord;
- RouteSelectionDecision evidence.

Инварианты:

- Route lease не передаёт агенту владение Beacon, account, listing или secrets.
- Windows Egress Agent не хранит primary project database.
- Foreign host containers, networks, ports, databases, volumes, Nginx and secrets не становятся project resources.
- Exact route technology, lease duration, health thresholds and switching policy не выбраны.

## 12. Notification Delivery domain

**Owning module:** Notification Delivery.

Концептуальные authoritative records:

| Record | Назначение |
|---|---|
| NotificationEndpoint | Account-owned разрешённая точка доставки и channel type |
| NotificationEvent | Внутреннее immutable намерение/факт после approved domain outcome |
| OutboxRecord | Durable pending-delivery boundary |
| DeliveryAttempt | Одна channel-specific попытка с explicit outcome |
| DeliveryReconciliation | Состояние проверки ambiguous external effect |
| DeliveryLogEntry | Безопасная operational/audit запись без secrets |

Инварианты:

- Notification всегда связана с внутренним event и Beacon scope, когда событие относится к Beacon.
- Parser не отправляет сообщение напрямую.
- Failure одного channel не отменяет independently authorized delivery другого channel.
- Duplicate external effect предотвращается idempotency/reconciliation policy, а не скрывается постфактум.
- Telegram/MAX adapters не владеют отдельной customer database.
- Provider-specific identifiers и payload mappings проходят adapter boundary и verification.
- Retention notification history остаётся частью OD-013.

## 13. Telegram Adapter и MAX Adapter

Adapters владеют только provider-specific mapping, verified ingress/egress evidence и ограниченным operational state, необходимым для future approved contracts.

Они не владеют:

- Account;
- RoleAssignment;
- Beacon;
- Entitlement;
- NotificationEvent;
- business delivery decision;
- отдельной копией customer profile.

Provider updates должны ссылаться на `account_id`, `notification_event_id`, `delivery_attempt_id` или другой approved internal identifier после verification. Exact provider fields требуют current official reference evidence.

## 14. Admin & Support и Web Cabinet

Admin & Support может владеть support work item, moderation case и protected operator-action reference, но меняет customer/business state только через owning module contract.

Web Cabinet владеет presentation/session view state, но не создаёт вторую user database, Beacon store, tariff store или notification history.

Admin/read models:

- являются производными;
- ограничиваются authorization and privacy scope;
- не дают bypass owning module;
- содержат safe references вместо secrets;
- должны иметь freshness/provenance metadata, если могут быть устаревшими.

## 15. Filter Catalog & Builder domain

**Owning module:** Filter Catalog & Builder.

Концептуальные authoritative records:

- FilterDefinition;
- FilterOptionDefinition;
- CategoryFilterApplicability;
- ReferenceEvidenceLink;
- CatalogVersion;
- BuilderValidationRule.

Правила:

- Catalog definition не переписывает Beacon source URL.
- Effective Beacon configuration остаётся у Beacon Management.
- Catalog data требует current official/primary Avito evidence.
- Unsupported или uncertain filter не помечается supported.
- Initial supported filter set остаётся OD-009.

## 16. Cross-cutting audit, idempotency and system evidence

Концептуальные records:

- AuditEntry;
- IdempotencyRecord;
- SystemEvent;
- CorrelationTraceReference;
- ReferenceEvidenceLink.

Обязательные свойства:

- producer/owning module;
- actor category and verified identity reference;
- target account/Beacon scope when applicable;
- contract name/version;
- correlation and causation references;
- safe outcome/reason code;
- time semantics after separate approval;
- redaction classification.

Этот документ не выбирает physical owner/store для cross-cutting records. Module mutation authority остаётся у owning module. Idempotency TTL, audit retention and storage implementation не выбраны.

## 17. Authoritative state и read models

Authoritative record:

- имеет owning module;
- изменяется только через разрешённый command boundary;
- имеет определимый commit point;
- поддерживает audit/reconciliation requirements;
- не зависит от UI-копии как source of truth.

Read model:

- строится из authoritative records/events;
- может быть удалён и восстановлен;
- не используется для обхода authorization;
- имеет provenance и freshness semantics;
- не является основанием подтвердить external effect без authoritative evidence.

## 18. Privacy and security classification

Минимальные классы:

| Класс | Примеры | Правило |
|---|---|---|
| Public/reference | Approved non-secret catalog metadata | Может использоваться только с provenance |
| Internal | IDs, state, safe reason codes | Доступ по role/scope |
| Personal | Contact points, provider identity links | Minimize, mask, authorize, audit |
| Secret | Password material, tokens, private keys, one-time codes | Не входит в common payload/read model; protected storage only |
| External untrusted | Avito/provider payload, URLs, webhooks | Verify/normalize; never trust by origin alone |
| Operational sensitive | Route/agent details, diagnostics | Ограниченный доступ; без foreign-host disclosure |

Raw passwords, tokens, one-time codes, private keys и unnecessary private message content запрещены в audit, ordinary logs, fixtures and reports.

## 19. Lifecycle, retention and deletion

До отдельного решения не определены:

- retention periods;
- archival periods;
- legal hold;
- soft/hard delete;
- anonymization/pseudonymization procedure;
- cascade behavior;
- idempotency TTL;
- audit/history compaction;
- raw provider evidence retention.

Все эти вопросы блокируются OD-013 и будущими privacy/operations documents. Реализация не должна выбирать default silently.

## 20. Consistency and commit boundaries

До implementation каждый mutation-capable use case обязан определить:

1. owning module and authoritative records;
2. preconditions and authorization;
3. idempotency scope;
4. logical commit point;
5. event/outbox action после commit point;
6. ambiguous interruption state;
7. reconciliation path;
8. rollback or compensation boundary;
9. affected read models;
10. audit evidence.

Cross-module atomicity не предполагается автоматически. Synchronous transaction, outbox, saga, compensation or another mechanism не выбраны.

## 21. Compatibility dependencies

Любое изменение conceptual record, identifier semantics, ownership, required relation или privacy class должно проходить `MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

Breaking data change не может быть скрыт только новой migration file. Он требует contract/data/version/rollout/rollback evidence в зависимости от scope.

## 22. Открытые решения и DRAFT dependencies

Этот baseline намеренно не закрывает:

- OD-001–OD-014;
- exact lifecycle enums;
- first-run and listing-difference business semantics из DRAFT target model;
- physical schema and constraints;
- identifier encoding;
- storage and transaction technology;
- retention/deletion;
- provider payload fields;
- exact audit ownership implementation;
- analytics event catalog;
- tariff/payment states;
- route selection algorithm.

## 23. Acceptance criteria для будущей physical model

Physical model может быть предложена только когда:

- owning module для каждого authoritative object указан;
- все cross-module references соответствуют approved contracts;
- account and Beacon isolation доказаны constraints/tests;
- source URL and configuration revision invariants сохранены;
- secrets отделены от ordinary data and logs;
- retention gaps обозначены, а не заполнены догадкой;
- migration/rollback/compatibility plan существует;
- fixtures and acceptance matrix покрывают ownership, idempotency, ambiguity and privacy;
- external mappings основаны на current official evidence;
- implementation task packet отдельно принят.

## 24. Explicit non-goals

Этот документ не разрешает:

- создавать database, schema, table, column, index or constraint;
- писать SQL, migrations, ORM entities or seeds;
- подключаться к существующей PostgreSQL;
- использовать foreign database;
- создавать Docker, service, port, credential or secret;
- выбирать framework, language, queue, cache, storage or migration tool;
- начинать parser, bot, billing, web, admin or notification implementation.

## 25. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый conceptual data baseline: ownership, identifiers, domains, invariants, privacy and compatibility gates без physical schema или migrations. |
