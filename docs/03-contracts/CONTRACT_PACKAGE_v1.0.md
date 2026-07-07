# Маяк Авито — Common Contract Package

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Security and Privacy Model v1.0, MODULE_REGISTRY.md, target model v0.1, OPEN_DECISIONS.md.
**Не является:** API specification, DTO catalog, OpenAPI, JSON Schema, event-bus selection, implementation contract or permission to create code.

---

## 1. Назначение

Этот документ задаёт общие семантические правила будущих межмодульных и внешних contracts.

Он нужен для того, чтобы модули, adapters, client interfaces, worker/scheduler и будущие operations документы использовали одинаковые понятия ownership, scope, validation, versioning, correlation and failure handling.

## 2. Граница действия

Contract package применяется к будущим:

- public commands;
- internal module commands;
- queries and read requests;
- domain events;
- adapter requests and adapter outcomes;
- notification intents;
- administrative and support actions;
- provider webhook and Mini App ingress after verification;
- worker/scheduler initiated actions.

Он не создаёт transport, endpoint, queue, database table, event broker, serialization format, schema language или runtime.

## 3. Contract types

| Тип | Назначение | Разрешённый результат |
|---|---|---|
| Command | Намерение изменить принадлежащее модулю состояние | Accepted, rejected или explicit outcome |
| Query | Запрос на чтение без изменения состояния | Read result or explicit error |
| Event | Зафиксированный факт после разрешённого изменения | Immutable statement of fact |
| Adapter request | Нормализованное намерение обратиться к внешней системе | Explicit adapter outcome |
| Adapter outcome | Результат внешнего взаимодействия | Success, failure, ambiguity or warning |
| Notification intent | Намерение доставить сообщение через delivery boundary | Delivery outcome, not direct provider mutation |
| Administrative action | Защищённое операторское действие | Server-authorized, auditable result |

Нельзя выдавать Query за Command, Command за Event или adapter failure за пустой business result.

## 4. Mandatory semantic metadata

Каждый будущий contract обязан иметь или однозначно наследовать следующие семантические элементы:

| Элемент | Значение |
|---|---|
| `contract_name` | Стабильное имя contract без зависимости от transport |
| `contract_version` | Явно указанная поддерживаемая версия |
| `message_id` | Уникальный идентификатор конкретной передачи или факта |
| `correlation_id` | Идентификатор сквозной пользовательской или системной операции |
| `causation_id` | Предшествующий message/action, если он существует |
| `producer` | Логический модуль или adapter, сформировавший сообщение |
| `issued_at` | Время формирования по утверждённому future time policy |
| `account_id` | Required, когда contract относится к account-owned state |
| `beacon_id` | Required, когда contract относится к beacon-owned state |
| `actor_context` | Категория инициатора без raw credentials or secrets |
| `idempotency_key` | Required для mutation-capable command или protected action |
| `contract_status` | Draft, candidate, approved, superseded or archived |

Не каждый contract обязан передавать все значения в wire payload. Но будущая implementation обязана сохранять их семантику в одобренной форме.

## 5. Ownership and scope rules

### 5.1. Account scope

- Внутренний `account_id` является базовой границей account-owned state.
- Identity provider identifiers не заменяют `account_id`.
- Contract не имеет права автоматически соединять identities по username, phone, avatar, email or weak correlation.
- Contract, затрагивающий несколько accounts, требует отдельного approved security and ownership policy.

### 5.2. Beacon scope

- Beacon-owned state must remain isolated by `beacon_id`.
- История listing state, notification history, scan state and user-visible Beacon configuration не должны смешиваться между Маяками.
- Source URL Маяка не переписывается user override contract без отдельного approved decision.

### 5.3. Module scope

- Only the owning module may authorize mutation of its owned state.
- Другой модуль может запросить действие только через approved contract.
- External adapter не получает право писать напрямую в внутреннее state другого модуля.
- Client interface, Telegram, MAX, Web Cabinet and Admin do not become independent owners of customer identity data.

## 6. Validation and authorization order

Для protected action будущая implementation должна сохранять следующий смысловой порядок:

1. identify contract type and version;
2. validate structural completeness;
3. establish verified actor context;
4. apply server-side authorization;
5. validate ownership and scope;
6. evaluate idempotency;
7. perform approved business action;
8. create auditable outcome;
9. emit an approved event only after the action reaches its defined commit point.

UI visibility, client-side role flags and external display names are not authorization.

## 7. External-boundary rules

- Telegram, MAX and other provider payloads become trusted only after provider-specific official verification.
- Avito results, HTML, parameters, source URLs, errors and response states remain external/untrusted.
- Incomplete parser output, access denial, CAPTCHA, route failure, malformed structure or ambiguous provider result must remain explicit.
- No external URL, template or parameter may be passed to shell execution by interpolation.
- A provider adapter returns normalized outcome; it does not silently mutate unrelated module state.

## 8. Result semantics

Every command or adapter request must have one explicit semantic result:

| Result class | Meaning |
|---|---|
| `SUCCEEDED` | Defined intended effect is confirmed |
| `REJECTED` | Action was not permitted or input was invalid |
| `CONFLICT` | Request conflicts with existing state or idempotency rules |
| `FAILED_RETRYABLE` | Effect not confirmed; retry may be safe only under policy |
| `FAILED_NON_RETRYABLE` | Retry will not resolve the stated failure |
| `AMBIGUOUS` | Effect cannot be safely classified without reconciliation |
| `PARTIAL` | Only explicitly enumerated independent sub-effects completed |

An external or internal failure must never be converted into a fabricated clean empty business result.

## 9. Security and privacy requirements

Contracts must not contain:

- raw password;
- access token;
- refresh token;
- one-time code;
- private key;
- raw secret;
- unnecessary full phone number;
- private message content unless separately approved;
- foreign-host internal data;
- unredacted provider payload beyond approved evidence scope.

Contracts must support audit without disclosing secrets.

## 10. Explicit non-decisions

This package does not select:

- HTTP, RPC, webhook or queue transport;
- JSON, Protobuf, Avro or another serialization;
- OpenAPI, JSON Schema or schema registry;
- exact identifier encoding;
- timestamp format;
- database transaction implementation;
- event delivery mechanism;
- consumer retry schedule;
- external provider field mapping;
- retention period;
- physical audit storage.

These remain subject to future approved documentation and open decisions.

## 11. Required dependency chain

Before code for a module is allowed, its playbook must identify:

1. owned state;
2. inbound and outbound contracts;
3. authorization boundary;
4. idempotency requirement;
5. failure classes;
6. external evidence dependency;
7. fake dependency boundary;
8. test vectors and acceptance evidence.

## 12. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый transport-neutral common contract package without schemas, code or runtime selection. |
