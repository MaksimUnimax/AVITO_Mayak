# Маяк Авито — Fixture Registry

**Версия:** 1.0
**Статус:** APPROVED documentation registry
**Дата:** 2026-07-07
**Основание:** Test Strategy v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Security and Privacy Model v1.0, MODULE_REGISTRY.md, OPEN_DECISIONS.md.
**Не является:** каталогом executable fixture files, seed data, database dump, provider payload archive, test framework configuration или разрешением использовать production data.

---

## 1. Назначение

Registry задаёт canonical semantic fixture identities для будущих module playbooks, contract tests, migration checks and reference regressions.

Fixture здесь — документированный входной контекст, dependency state и ожидаемый semantic outcome. Physical encoding и executable representation выбираются только отдельной implementation task.

## 2. Fixture identity and lifecycle

Каждая fixture обязана иметь:

| Поле | Значение |
|---|---|
| `fixture_id` | Стабильный идентификатор из этого registry или future approved extension |
| `fixture_version` | Версия semantic meaning fixture |
| `status` | DRAFT, CANDIDATE, APPROVED, SUPERSEDED or ARCHIVED |
| `scope` | Contract, module, data, migration, security, operations or reference |
| `source_documents` | Approved requirements, которые fixture проверяет |
| `input_class` | Synthetic/redacted semantic input, без secrets |
| `dependency_state` | Success, rejection, unavailable, malformed, ambiguous or not applicable |
| `expected_outcome` | Явный success/error/partial/ambiguous/reconciliation result |
| `forbidden_outcome` | Ошибка классификации, которую fixture должна обнаружить |
| `privacy_class` | Public/reference, internal, personal-synthetic, external-untrusted-synthetic |
| `open_decisions` | Связанные OD, которые fixture не закрывает |

Изменение expected semantic meaning требует новой fixture version и оценки совместимости.

## 3. Общие fixture rules

1. Используются только synthetic or irreversibly redacted values.
2. Raw passwords, tokens, one-time codes, private keys and real personal messages запрещены.
3. Real phone/email/provider identifiers не нужны; используются явно фиктивные значения.
4. Fixture не объявляет provider field supported без current reference evidence.
5. Fixture не заполняет OD-001–OD-014 default values.
6. Cross-account and cross-Beacon cases используют заведомо разные synthetic IDs.
7. Expected success разрешён только при определённом commit point.
8. Unknown effect ожидается как `AMBIGUOUS` or reconciliation-required, не как success.
9. External failure не ожидается как empty business result.
10. Fixture version не является contract version.

## 4. Canonical fixture registry

### 4.1. Contract and authorization

| Fixture ID | Назначение | Ключевой вход | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-CONTRACT-VALID-001` | Минимальный valid command | Approved contract version, verified actor, correct owner/scope, idempotency key | Defined command outcome after commit point | Success before authorization/commit |
| `FX-CONTRACT-MISSING-META-001` | Missing mandatory semantic metadata | Missing contract version or correlation identity | `INVALID_ARGUMENT`; no effect | Implicit defaults or partial mutation |
| `FX-AUTH-UNAUTHENTICATED-001` | Actor context absent | Protected command without verified actor | `UNAUTHENTICATED`; no effect | Client-side identity accepted |
| `FX-AUTH-FORBIDDEN-001` | Role lacks permission | Verified actor, insufficient server-side role | `FORBIDDEN`; no effect; safe audit | Hidden UI treated as authorization |
| `FX-OWNER-FOREIGN-ACCOUNT-001` | Foreign account target | Actor account A, target owned by account B | Reject without foreign data disclosure | Cross-account read or mutation |
| `FX-OWNER-FOREIGN-BEACON-001` | Foreign Beacon history | Correct account but different `beacon_id` scope | Reject or scoped not-found result | History mixed between Beacons |

### 4.2. Idempotency, replay and interruption

| Fixture ID | Назначение | Ключевой вход/state | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-IDEMP-FIRST-001` | Первый mutation request | New key and request fingerprint | Single authorized effect and terminal outcome | Duplicate effect |
| `FX-IDEMP-REPLAY-SAME-001` | Exact replay | Same key, same request, known terminal outcome | Original outcome returned/referenced; no new effect | Second effect |
| `FX-IDEMP-REPLAY-MISMATCH-001` | Key reused for different request | Same key, different fingerprint | `IDEMPOTENCY_MISMATCH`; no effect | New request executed |
| `FX-INTERRUPT-PRECOMMIT-001` | Interruption before commit | No authoritative effect committed | Retry only under approved policy; no fabricated success | Success/event emitted |
| `FX-INTERRUPT-UNKNOWN-001` | Interruption after possible commit | Commit state cannot be proven | `AMBIGUOUS`/reconciliation-required | Blind retry or success |
| `FX-INTERRUPT-POSTCOMMIT-001` | Interruption after confirmed commit | Authoritative effect exists | Replay references committed outcome; no duplicate | Compensation/duplicate without decision |
| `FX-BATCH-PARTIAL-001` | Mixed batch | Succeeded, failed, pending and ambiguous units | Per-unit inventory and partial result | One generic success |

### 4.3. Data ownership and invariants

| Fixture ID | Назначение | Ключевой state | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-DATA-ACCOUNT-BOUNDARY-001` | Internal account boundary | Two external identities with weak correlation | Accounts remain separate | Automatic merge |
| `FX-DATA-BEACON-ISOLATION-001` | Same external listing in two Beacons | Same provider listing reference, different `beacon_id` | Two isolated Beacon states/histories | Cross-Beacon deduplication of authoritative state |
| `FX-DATA-SOURCE-URL-IMMUTABLE-001` | Beacon override | Source URL + extracted snapshot + user override | New configuration revision; source URL preserved | Source URL overwritten |
| `FX-DATA-HISTORY-IMMUTABLE-001` | Historical observation/revision | New observation/config revision | Append/new record semantics | Historical record rewritten |
| `FX-DATA-READMODEL-STALE-001` | Stale projection | Authoritative version newer than read model | Staleness/provenance explicit | Read model treated as truth |
| `FX-DATA-UNKNOWN-NO-DEFAULT-001` | Missing value blocked by open decision | Unknown retention/tariff/filter/lifecycle value | Explicit unknown/blocked state | Fabricated default |

### 4.4. External dependency and parser outcomes

| Fixture ID | Назначение | Dependency state | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-EXT-SUCCESS-001` | Verified external success | Well-formed synthetic provider response supported by evidence | Normalized explicit success | Raw payload trusted without verification |
| `FX-EXT-REJECTED-001` | Explicit provider rejection | Provider returns stable rejection | `EXTERNAL_REJECTED` or approved equivalent | Empty result or automatic retry |
| `FX-EXT-UNAVAILABLE-001` | Transport/provider unavailable | No usable response | `EXTERNAL_UNAVAILABLE`; retry only by policy | No listings / success |
| `FX-EXT-MALFORMED-001` | Malformed/incomplete response | Required structure absent | Explicit malformed/insufficient outcome | Partial data treated complete |
| `FX-EXT-AMBIGUOUS-001` | Final effect unknown | Request may have been processed | `EXTERNAL_AMBIGUOUS`; reconciliation | Blind replay or success |
| `FX-AVITO-CAPTCHA-001` | Access challenge | CAPTCHA or blocked access indicator | Explicit restricted/failed outcome | Clean empty listing set |
| `FX-ROUTE-FAILURE-001` | Egress route failure | Route unavailable/quarantined | Explicit route/dependency failure | Parser success |

### 4.5. Security, privacy and redaction

| Fixture ID | Назначение | Input | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-SEC-SECRET-REDACTION-001` | Secret-bearing synthetic input | Synthetic token/password/code markers | Secret excluded/redacted from logs, reports and ordinary payloads | Raw secret emitted |
| `FX-SEC-PERSONAL-MINIMIZATION-001` | Unnecessary personal fields | Synthetic phone/seller/description fields outside approved scope | Fields omitted or masked | Unnecessary collection/display |
| `FX-SEC-SHELL-INTERPOLATION-001` | Hostile external string | Synthetic shell metacharacters in URL/field | Treated as data; no shell execution | Interpolated command execution |
| `FX-SEC-PROVIDER-VERIFY-001` | Unverified webhook/Mini App payload | Missing/invalid verification evidence | Rejected before trusted use | External identity accepted |

### 4.6. Migration and compatibility

| Fixture ID | Назначение | Dataset/state | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-MIG-EMPTY-001` | Empty dataset | No units | Accepted zero-scope result with explicit counts | Fabricated processed records |
| `FX-MIG-MINIMAL-001` | Minimum valid unit | One authorized deterministic record | One validated effect | Broader scope |
| `FX-MIG-MIXED-VERSIONS-001` | Old/new coexistence | Supported old and target forms | Declared compatibility behavior | Silent reinterpretation |
| `FX-MIG-DUPLICATE-REPLAY-001` | Replayed migration unit | Same migration/unit ID and plan fingerprint | No second effect | Duplicate backfill/repair |
| `FX-MIG-PLAN-MISMATCH-001` | Same ID, changed plan | Different fingerprint | Reject before mutation | New plan executed under old ID |
| `FX-MIG-PARTIAL-001` | Interrupted bounded batch | Succeeded/failed/ambiguous units | Explicit inventory and reconciliation | Whole batch success |
| `FX-MIG-ROLLBACK-001` | Safe reverse path | Reversible mapping and valid previous representation | Validated rollback boundary | Destructive reset/unproven loss |
| `FX-MIG-ROLLFORWARD-001` | Irreversible change | Reverse mapping unsafe | Explicit roll-forward-required state | Pretend rollback possible |
| `FX-MIG-READMODEL-REBUILD-001` | Derived projection rebuild | Known authoritative source/version | Idempotent rebuild with provenance | Projection becomes source of truth |

### 4.7. Reference regression

| Fixture ID | Назначение | Reference state | Expected semantic outcome | Forbidden outcome |
|---|---|---|---|---|
| `FX-REF-CURRENT-001` | Current evidence | Official/primary source with date, URL, scope, status, limitations | Reference-dependent expectation may be evaluated | Memory-only assertion |
| `FX-REF-STALE-001` | Evidence past review window or known change | Old retrieval/effective state | Block or require refresh | Treat as current silently |
| `FX-REF-MISSING-001` | No evidence | Provider-dependent behavior requested | `BLOCKED_REFERENCE_EVIDENCE_REQUIRED` | Guess mapping/behavior |
| `FX-REF-CHANGED-COMPATIBLE-001` | Additive provider change | Existing semantics remain valid | Compatible update + fixture review | Unreviewed adoption |
| `FX-REF-CHANGED-BREAKING-001` | Removed/changed provider behavior | Existing mapping invalidated | Breaking change package and blocked implementation | Same-version silent change |
| `FX-REF-UNSUPPORTED-001` | Unsupported/uncertain field | Evidence does not confirm support | Explicit unsupported/unknown state | Mark supported |

## 5. Module fixture adoption

Каждый из 13 module playbooks должен:

1. выбрать применимые fixture IDs;
2. добавить module-specific fixtures только через approved registry extension;
3. определить fake dependencies and expected outcomes;
4. связать fixtures с public inputs/outputs and owned data;
5. отметить OD dependencies;
6. перечислить evidence, необходимое для acceptance;
7. не создавать executable fixture без отдельной implementation task.

## 6. Fixture change control

Fixture change классифицируется как:

- clarification — meaning не меняется;
- compatible extension — новый optional scenario;
- breaking fixture change — изменён expected outcome, owner, authorization, privacy, error or idempotency meaning.

Breaking fixture change требует обновления Acceptance Matrix, затронутых contracts/data/playbooks и reference evidence, если применимо.

Удаление fixture выполняется через `SUPERSEDED`/`ARCHIVED`, а не silent removal.

## 7. Storage and encoding boundary

Registry не выбирает:

- YAML, JSON, CSV, SQL, code object or binary encoding;
- filesystem layout для executable fixtures;
- database seed mechanism;
- snapshot tooling;
- golden-file framework;
- CI artifact storage;
- retention period.

Любой physical fixture file в будущем должен ссылаться на `fixture_id`, `fixture_version`, approved task and source revision.

## 8. Acceptance criteria

Registry принят, когда:

- fixture IDs уникальны;
- required contract/data/migration/security/reference scenarios покрыты;
- expected/forbidden outcomes не закрывают open decisions;
- нет real credentials or personal data;
- fixtures связаны с approved source documents;
- Acceptance Matrix использует эти stable IDs;
- no executable fixture artifacts созданы.

## 9. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый semantic fixture registry для contracts, ownership, replay, external failures, privacy, migrations and reference regression без executable data files. |
