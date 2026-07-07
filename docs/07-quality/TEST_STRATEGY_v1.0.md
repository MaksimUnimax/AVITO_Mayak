# Маяк Авито — Test Strategy

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, MODULE_REGISTRY.md, OPEN_DECISIONS.md.
**Не является:** executable test suite, выбором test framework, CI/CD configuration, implementation task, production validation или разрешением создавать product-code.

---

## 1. Назначение

Стратегия определяет обязательные quality gates, виды доказательств и минимальное покрытие для будущих contracts, data changes, adapters, modules, operations и reference-dependent behavior.

Она задаёт семантику проверки до выбора языка, framework, runner, CI, storage или runtime topology.

## 2. Иерархия источников

1. Public GitHub `main` и governance documents.
2. Approved append-only decisions в пределах их scope.
3. Approved architecture, security, contract, data and compatibility baselines.
4. Этот документ, Fixture Registry, Acceptance Matrix и Reference Regression Policy.
5. Module playbook и exact implementation task после отдельного approval.
6. Runtime/test evidence после выполнения конкретной разрешённой задачи.

Тест или отчёт не может самостоятельно переопределить approved requirement. DRAFT context и open decision не получают default через fixture или expected result.

## 3. Quality principles

1. Проверяется наблюдаемая семантика, а не только exit code.
2. Success допускается только после доказанного commit point.
3. Failure, partial, ambiguous and unsupported outcomes остаются различимыми.
4. Account и Beacon isolation проверяются отрицательными и положительными сценариями.
5. External source failure не превращается в clean empty result.
6. Mutation-capable path проверяется на idempotency, replay и interruption.
7. Read model не используется как скрытый source of truth.
8. Secrets и unnecessary personal data отсутствуют в fixtures, logs и reports.
9. Fake dependency воспроизводит contract boundary, а не придумывает provider behavior.
10. Reference-dependent expectation требует current official or primary evidence.
11. Open decisions остаются `BLOCKED` или `NOT_APPLICABLE`, но не получают выдуманное expected value.
12. Acceptance требует независимой проверки ChatGPT, когда это установлено governance.

## 4. Уровни проверки

### 4.1. Documentation consistency

Проверяет:

- canonical path и статус документа;
- отсутствие противоречий между manifest, current state, roadmap and backlog;
- корректные ссылки на approved dependencies;
- отсутствие закрытия `OPEN_DECISIONS.md` по умолчанию;
- append-only integrity;
- отсутствие запрещённых implementation artifacts.

### 4.2. Contract semantics

Проверяет:

- contract type, version and owner;
- mandatory semantic metadata;
- authorization before mutation;
- ownership and scope;
- idempotency key and request fingerprint behavior;
- explicit result/error class;
- commit point and allowed event timing;
- partial and ambiguous outcomes;
- redaction.

### 4.3. Module boundary

Проверяет:

- mutation выполняет только owning module;
- adapter/UI/admin не пишет напрямую в foreign state;
- public command/event/read boundary различим;
- dependency может быть заменена approved fake;
- module playbook перечисляет owned data, inputs, outputs, fixtures and acceptance evidence.

### 4.4. Data invariants

Проверяет:

- `account_id` как базовую account boundary;
- one-account ownership для Beacon;
- isolation history по `beacon_id`;
- неизменность historical observation/revision;
- source URL provenance и отдельность overrides;
- authoritative/read-model distinction;
- privacy class и redaction;
- absence of fabricated defaults для unresolved semantics.

### 4.5. Error, replay and interruption

Проверяет минимум:

- same idempotency key + same request + terminal outcome;
- same key + different fingerprint;
- duplicate external delivery;
- interruption before commit;
- interruption after possible commit;
- reconcile-first path;
- partial batch;
- unauthorized retry prohibition;
- retryable vs non-retryable classification.

### 4.6. External adapter and reference regression

Проверяет:

- authenticity/verification boundary;
- malformed, blocked, CAPTCHA, timeout and route failure;
- unsupported provider field or mapping;
- provider change classification;
- evidence date, URL, scope, status and limitations;
- stale or absent reference evidence;
- prohibition on converting external ambiguity into success.

### 4.7. Migration and compatibility

До любой future migration проверяются:

- empty and minimum valid datasets;
- mixed old/new versions;
- deterministic backfill source;
- duplicate replay;
- interruption before/after commit;
- partial batch and reconciliation;
- account/Beacon isolation;
- unauthorized mutation;
- read-model rebuild provenance;
- rollback/roll-forward branch;
- provider mapping regression when applicable;
- secret/redaction boundary.

Этот уровень не разрешает создавать migration files или подключаться к database.

### 4.8. Operations evidence

Будущие operations documents обязаны определить безопасные checks для:

- environment identity;
- target revision;
- health/readiness semantics;
- observability without secrets;
- backup/recovery proof;
- release/rollback gate;
- no use of foreign shared-host resources.

До Run 6–8 конкретные operational checks остаются pending.

## 5. Обязательные scenario dimensions

Каждый будущий module playbook или implementation task выбирает применимые dimensions и явно отмечает неприменимые:

| Dimension | Минимальные варианты |
|---|---|
| Input validity | valid, missing, malformed, unsupported |
| Authorization | allowed, unauthenticated, forbidden, wrong account |
| Ownership | correct owner, foreign owner, missing reference |
| State | initial, active, terminal, conflicting, stale |
| Idempotency | first request, exact replay, mismatched replay |
| Interruption | before commit, after possible commit, after confirmed commit |
| Dependency | success, explicit rejection, unavailable, malformed, ambiguous |
| Batch | all success, partial, all failure, duplicate unit |
| Privacy | allowed fields, redacted fields, forbidden secret/personal content |
| Version | current, supported previous, unknown, incompatible |
| Reference | current evidence, stale evidence, absent evidence, changed evidence |

## 6. Fake dependency rules

Approved fake dependency:

- реализует только documented contract surface;
- имеет stable fixture identity;
- явно сообщает success, rejection, failure, ambiguity and timeout;
- не обращается к production provider;
- не содержит real credentials or personal data;
- не расширяет supported behavior beyond official evidence;
- сохраняет correlation/idempotency semantics;
- позволяет доказать retry/reconciliation behavior;
- имеет provenance: fixture ID, version and source document.

Запрещено использовать mock, который всегда возвращает success, скрывает unsupported state или подменяет authorization.

## 7. Evidence package

Каждый принятый test run в будущем должен возвращать:

1. task/iteration identifier;
2. exact Git revision and document/contract versions;
3. environment identity без secrets;
4. selected fixture IDs and versions;
5. expected and actual semantic outcome;
6. per-check status;
7. failed/ambiguous inventory;
8. redacted diagnostics;
9. proof of clean repository and allowed scope when relevant;
10. explicit statement about GitHub, Git/SSH config and server changes;
11. exact final marker;
12. independent acceptance result when required.

Screenshot, log fragment или exit code alone не являются достаточным evidence.

## 8. Entry gates before implementation testing

Implementation test task допустима только если:

- affected module playbook APPROVED;
- contracts/data ownership identified;
- applicable fixture IDs exist in Fixture Registry;
- Acceptance Matrix rows selected;
- open decisions do not require guessed values;
- external behavior has current evidence when needed;
- allowed and forbidden paths/actions explicit;
- fake dependencies and secrets boundary defined;
- rollback/reconciliation behavior defined;
- exact acceptance authority named.

## 9. Stop and failure rules

Acceptance останавливается при:

- wrong Git revision or document version;
- dirty/unidentified target state;
- missing fixture provenance;
- expected result derived from DRAFT/open decision;
- unexpected cross-account or cross-Beacon access;
- secret or unnecessary personal data exposure;
- ambiguous effect reported as success;
- external failure reported as empty result;
- missing idempotency or reconciliation evidence;
- provider evidence absent/stale for a reference-dependent assertion;
- forbidden artifact or out-of-scope mutation.

Corrective action targets the first proven wrong object, value or action. Broad normalization without proven defect is prohibited.

## 10. Open decisions

Эта стратегия не определяет:

- test language/framework/runner;
- CI provider or pipeline;
- coverage percentage;
- performance/load thresholds;
- exact retry timings;
- production datasets;
- retention of test evidence;
- provider-specific fields;
- exact business results blocked by OD-001–OD-014;
- release certification process.

## 11. Explicit prohibitions

Этот документ не разрешает:

- создавать executable tests, scripts or fixtures;
- создавать CI/CD;
- запускать providers, bots, parser or payments;
- подключаться к database;
- создавать migrations, Dockerfiles, services or ports;
- использовать real credentials or production personal data;
- изменять GitHub, server, Git or SSH configuration through a test task;
- закрывать open decisions expected result.

## 12. Acceptance criteria для quality documentation

Quality Foundation считается документально полной, когда:

- Test Strategy определяет gates and evidence;
- Fixture Registry содержит canonical semantic fixtures;
- Acceptance Matrix связывает approved requirements с fixtures/evidence;
- Reference Regression Policy определяет lifecycle внешнего evidence;
- governance state и manifest синхронизированы;
- append-only worklog содержит запись принятия;
- public GitHub result независимо проверен;
- server checkout синхронизирован с exact accepted SHA.

## 13. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый framework-neutral quality baseline: gates, scenario dimensions, fake dependencies and evidence без executable tests или CI. |
