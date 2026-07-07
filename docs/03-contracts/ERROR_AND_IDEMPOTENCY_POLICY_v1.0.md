# Маяк Авито — Error and Idempotency Policy

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Common Contract Package v1.0, Security and Privacy Model v1.0, Architecture Baseline v1.0.
**Не является:** retry implementation, queue configuration, database transaction design, provider-specific protocol or production incident procedure.

---

## 1. Назначение

Политика определяет единый смысл ошибок, повторов, duplicate delivery and ambiguous outcomes.

Она предотвращает две запрещённые подмены:

1. повторная mutation без явного idempotency control;
2. ошибка внешнего или внутреннего пути, превращённая в ложный clean result.

## 2. Error model

Будущий error contract обязан различать:

| Поле | Назначение |
|---|---|
| `error_code` | Стабильный machine-readable semantic code |
| `error_category` | Класс ошибки из этой policy |
| `message` | Безопасное описание для разрешённой аудитории |
| `correlation_id` | Связь с исходной операцией |
| `retry_class` | Never, conditional or reconcile-first |
| `details` | Redacted diagnostic facts without secrets |
| `source` | Logical producer or external boundary |
| `contract_version` | Версия error semantics |

Error output must not reveal credentials, secrets, raw tokens, one-time codes, hidden provider payloads, foreign infrastructure details or protected data belonging to another account.

## 3. Approved error categories

| Code | Meaning | Default retry class |
|---|---|---|
| `INVALID_ARGUMENT` | Structural or semantic input validation failed | never |
| `UNAUTHENTICATED` | Verified actor context is absent or invalid | never |
| `FORBIDDEN` | Actor lacks required server-side authorization | never |
| `NOT_FOUND` | Requested visible object is absent in permitted scope | never |
| `PRECONDITION_FAILED` | Required known state is not satisfied | never |
| `CONFLICT` | Request conflicts with current owned state | never |
| `IDEMPOTENCY_MISMATCH` | Same idempotency key reused with a different request fingerprint | never |
| `RATE_LIMITED` | Approved rate boundary denied the action | conditional |
| `EXTERNAL_UNAVAILABLE` | External dependency did not provide a usable response | conditional |
| `EXTERNAL_REJECTED` | External provider explicitly rejected a validly formed request | never unless provider evidence changes |
| `EXTERNAL_AMBIGUOUS` | External effect cannot be confirmed safely | reconcile-first |
| `TEMPORARY_FAILURE` | Internal or dependency failure may be transient | conditional |
| `INTERNAL_FAILURE` | Unexpected failure requiring protected diagnostics | reconcile-first |

No category implies a specific HTTP status, queue action, retry delay, transport or implementation mechanism.

## 4. Retry rules

### 4.1. Never retry automatically

Automatic retry is prohibited for:

- authorization or authentication failure;
- invalid input;
- ownership violation;
- explicit conflict;
- idempotency mismatch;
- known non-retryable provider rejection;
- protected action requiring fresh human confirmation.

### 4.2. Conditional retry

Conditional retry is permitted only when future contract and module policy prove:

1. the action has an idempotency boundary;
2. duplicate effect is prevented or detectable;
3. retry does not bypass authorization;
4. retry limit and delay are separately approved;
5. external provider rules allow it;
6. failure is not classified as ambiguous.

### 4.3. Reconcile-first

For `EXTERNAL_AMBIGUOUS` or `INTERNAL_FAILURE` after an unknown commit point:

- do not fabricate success;
- do not repeat mutation blindly;
- preserve correlation and idempotency context;
- run an approved reconciliation path before another effectful attempt;
- expose a safe pending/ambiguous state to the authorized caller.

## 5. Idempotency rules

### 5.1. Required operations

An idempotency key is required for:

- account or role mutation;
- protected merge action;
- entitlement or manual-access change;
- Beacon mutation;
- scan or notification action that can produce duplicated user-visible effect;
- adapter request with external side effect;
- administrator or support action with state mutation;
- any retryable command.

### 5.2. Scope

Idempotency evaluation is scoped to:

- contract name and version;
- owning module;
- account scope when applicable;
- actor scope when required for authorization;
- idempotency key;
- normalized request fingerprint.

The precise storage, expiry and retention of idempotency records remain open data-policy decisions.

### 5.3. Same key behavior

| Situation | Required outcome |
|---|---|
| Same key, same semantic request, known terminal outcome | Return or reference the original outcome; do not create a second effect |
| Same key, same request, original outcome pending | Return explicit pending or reconciliation-required outcome |
| Same key, different request fingerprint | Return `IDEMPOTENCY_MISMATCH`; do not execute |
| Missing key for required mutation | Reject before effect with `INVALID_ARGUMENT` or future stricter policy |
| Duplicate external delivery with trusted stable provider identity | Deduplicate before duplicate internal effect |
| Duplicate delivery without safe stable identity | Preserve ambiguity and require approved reconciliation |

## 6. Commit-point rule

Every mutation-capable contract must define, before implementation:

1. the exact logical effect it intends;
2. the owner of that effect;
3. the commit point after which success may be emitted;
4. the effect visible before commit;
5. the reconciliation state after interruption;
6. the event allowed after commit;
7. the rollback or compensation boundary, if one exists.

No event of confirmed success may be emitted before its defined commit point.

## 7. Partial and batch operations

A batch contract must not use one generic success result when individual items differ.

It must expose:

- accepted item count;
- succeeded item identities or safe references;
- failed item identities or safe references;
- per-item error category;
- whether retry is safe;
- whether reconciliation is required.

This does not define the future wire payload shape.

## 8. External adapter requirements

Adapter outcomes must distinguish at least:

- no request was sent;
- request was sent and explicit success confirmed;
- request was sent and explicit rejection confirmed;
- request may have been sent but final effect is unknown;
- provider response was malformed or insufficient;
- route or transport failure occurred;
- rate limit or provider restriction occurred.

Parser and scan flow must never convert source failure, blocked access, CAPTCHA, ambiguity or malformed result into “no new listings”.

## 9. Audit and redaction

For protected or external-effectful operation, audit must preserve:

- contract name and version;
- correlation id;
- actor category and authorized identity reference;
- target account and Beacon scope when applicable;
- outcome category;
- retry/reconciliation state;
- time;
- safe reason code.

Audit must not preserve raw passwords, tokens, one-time codes, private keys or unnecessary personal content.

## 10. Open decisions

This policy does not decide:

- idempotency record TTL;
- idempotency persistence technology;
- retry count or delay;
- backoff strategy;
- circuit-breaker policy;
- rate-limit values;
- provider-specific replay identifiers;
- transaction implementation;
- compensation implementation;
- exact audit retention;
- incident escalation channel.

## 11. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый common error and idempotency policy without runtime, queue, database or provider implementation choices. |
