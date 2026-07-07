# Маяк Авито — Platform & Contracts Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 12 of 24
**Дата:** 2026-07-07
**Модуль:** `01-platform-and-contracts`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.1, Security and Privacy Model v1.0, MODULE_REGISTRY.md and OPEN_DECISIONS.md.
**Не является:** product-code, dependency declaration, lockfile, API schema, physical database schema, migration, runtime configuration, deployment plan or automatic permission to implement.

---

## 1. Назначение

Platform & Contracts задаёт единый технический каркас модульного монолита и повторно используемые transport-neutral conventions. Модуль обеспечивает согласованность границ, но не становится владельцем бизнес-состояния других модулей.

Его будущая реализация может включать только:

- repository/package skeleton;
- common contract metadata and lifecycle conventions;
- common result/error semantics;
- reusable idempotency decision protocol;
- typed configuration composition and redaction boundary;
- API/worker/scheduler composition conventions;
- module/import boundary enforcement;
- migration tooling conventions after separate database gates;
- shared synthetic test builders and fake protocols.

## 2. Границы и non-ownership

Модуль не владеет:

- accounts, identities, roles or sessions;
- tariffs, entitlements, subscriptions or payment records;
- Beacons, source URLs or configuration revisions;
- Avito extraction behavior;
- scan runs, listing observations, baseline/diff or listing state;
- egress routes, agents or leases;
- notification intents, outbox or delivery attempts;
- Telegram/MAX mappings and UI behavior;
- admin/support business actions;
- Web Cabinet presentation state;
- filter definitions or builder behavior.

Platform & Contracts не создаёт «универсальную бизнес-таблицу», не пишет в состояние чужого модуля и не заменяет owning module.

## 3. Подтверждённые архитектурные решения

1. Один public repository и один modular-monolith application boundary.
2. Три process roles: API, worker and scheduler.
3. Отдельный Windows Egress Agent boundary.
4. Тринадцать logical modules, а не тринадцать микросервисов.
5. Public intermodule contracts не содержат FastAPI, ORM, provider SDK or persistence-internal types.
6. Внешние adapters и UI вызывают public module interfaces; прямые записи в foreign state запрещены.
7. Future primary database — PostgreSQL 18, но physical schema и provisioning отсутствуют.
8. Core implementation line: CPython 3.14, uv, FastAPI/Uvicorn, Pydantic v2/settings, HTTPX, SQLAlchemy 2, Psycopg 3, Alembic, approved quality tools and OpenTelemetry boundary.
9. Product-code начинается только по отдельной exact task после isolated toolchain proof.

## 4. Будущий singular source layout

Первый implementation task обязан использовать один layout, если заранее не опубликован approved architecture change:

```text
pyproject.toml
uv.lock
src/
  mayak/
    platform/
      config/
      errors/
      idempotency/
      observability/
      persistence/
    contracts/
    entrypoints/
      api/
      worker/
      scheduler/
    modules/
      identity_and_access/
      entitlements_and_billing/
      beacon_management/
      avito_parser_adapter/
      scan_orchestration/
      egress_routing/
      notification_delivery/
      telegram_adapter/
      max_adapter/
      admin_and_support/
      web_cabinet/
      filter_catalog/
tests/
  unit/
  contract/
  architecture/
  integration/
```

`migrations/` остаётся отсутствующим до отдельного migration/database task.

Rules:

- `platform/` and `contracts/` do not import business-module internals;
- one module does not import another module’s internal package;
- cross-module calls use the producer’s approved public port/contract;
- entrypoints compose modules but do not own domain state;
- provider adapters remain at module boundaries;
- no parallel source tree or alternate layout is allowed.

## 5. Data ownership

Platform & Contracts owns only future platform-level records/conventions that are explicitly approved, such as:

- contract name/version registry semantics;
- common message/correlation/causation identifier conventions;
- reusable idempotency decision protocol;
- configuration schema metadata without sensitive values;
- migration-plan registration metadata after applicable gates;
- safe audit/correlation context conventions.

Each business module owns its authoritative state, commit point and persisted business idempotency outcome. Shared tooling does not transfer ownership.

## 6. Public input families

Exact Python or wire shapes remain implementation-task scope. Required semantic families are:

| Input family | Purpose | Required semantics |
|---|---|---|
| `ContractValidationRequest` | Validate contract identity and metadata | contract/version, producer, scope, correlation |
| `ContractChangeAssessmentRequest` | Classify a proposed change | old/new version, reason, consumers, compatibility impact |
| `IdempotencyEvaluationRequest` | Evaluate first call, replay, conflict or pending state | owner, contract/version, scope, key, normalized fingerprint |
| `ErrorNormalizationRequest` | Normalize a known failure | source, evidence, safe details, correlation |
| `ConfigurationValidationRequest` | Validate typed configuration before readiness | environment, component, schema version, presence/provenance |
| `ModuleBoundaryCheckRequest` | Check import/dependency direction | producer, consumer, public/internal boundary |
| `MigrationPlanRegistrationRequest` | Register future migration metadata | migration ID, owner, plan fingerprint, compatibility and rollback evidence |
| `ProcessCompositionRequest` | Compose approved process role | enabled modules, configuration readiness, dependency readiness |

Protected mutation-capable inputs require verified actor context and server-side authorization when applicable.

## 7. Public output families

| Output family | Meaning |
|---|---|
| `ContractValidationOutcome` | valid, rejected or unsupported identity/metadata |
| `ContractChangeAssessment` | clarification, compatible extension, breaking or blocked |
| `IdempotencyDecision` | `NEW`, `REPLAY_TERMINAL`, `PENDING`, `MISMATCH`, `RECONCILE_REQUIRED` |
| `CommonErrorOutcome` | approved category, retry class and safe diagnostics |
| `ConfigurationValidationOutcome` | ready, invalid, missing, blocked or source-unproven |
| `ModuleBoundaryCheckOutcome` | pass/fail with exact forbidden edge evidence |
| `MigrationPlanRegistrationOutcome` | accepted metadata, rejected mismatch, blocked or reconcile-required |
| `ProcessReadinessOutcome` | ready/not-ready with separated configuration and dependency reasons |

Outputs do not imply HTTP status, database transaction, queue action or provider result unless a later approved adapter explicitly maps them.

## 8. Immutable common contract invariants

Every applicable contract preserves:

- stable `contract_name` and explicit `contract_version`;
- `message_id` and `correlation_id`;
- `causation_id` when a prior message/action exists;
- logical producer;
- issued time under an approved time policy;
- `account_id` and `beacon_id` when scope requires them;
- verified actor context for protected actions;
- `idempotency_key` for mutation-capable or retryable actions;
- explicit result or error category;
- no sensitive-value fields;
- no framework, ORM, persistence-internal or provider-specific public types.

Unknown fields, versions and error categories are never silently accepted. Breaking changes require a new explicit version and consumer/migration plan.

## 9. Authorization and ownership order

For every protected mutation, semantic order is:

1. identify contract and version;
2. validate required metadata;
3. establish verified actor context;
4. apply server-side authorization;
5. validate owner/account/Beacon scope;
6. evaluate idempotency;
7. invoke only the owning module’s public action;
8. reach the owning module’s commit point;
9. record safe audit/outcome;
10. emit an approved event only after commit.

Client visibility, display names, provider profile data or possession of a correlation identifier never authorizes an action.

## 10. Idempotency and interruption

- Scope includes contract/version, owning module, applicable actor/account scope, key and normalized request fingerprint.
- Same key + same fingerprint + terminal outcome reuses the original outcome.
- Same key + different fingerprint returns `IDEMPOTENCY_MISMATCH` without effect.
- Pending or unknown commit state remains pending/reconciliation-required.
- The owning module defines and proves its commit point.
- Platform tooling cannot report business success before that commit point.
- A replay after pre-commit interruption may retry safely; post-commit replay must not create a second effect.
- Batch operations expose per-unit outcomes.
- TTL, physical storage and cleanup remain deferred; OD-013 remains open.

## 11. Common error rules

Approved categories include:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`;
- `FORBIDDEN`;
- `NOT_FOUND`;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `RATE_LIMITED`;
- `EXTERNAL_UNAVAILABLE`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

Errors expose no sensitive access material or foreign-account data. External/provider failure is never converted into empty business success. Retry remains `never`, `conditional` or `reconcile-first`. HTTP mappings belong to a later transport task.

## 12. Configuration boundary

Future typed configuration uses Pydantic Settings.

- Repository may contain schemas and non-sensitive defaults only.
- Sensitive-value delivery mechanism remains deferred.
- Missing required configuration fails startup/readiness before serving or claiming work.
- Provenance is recorded without values.
- Unknown configuration keys/versions are explicit.
- Runtime configuration cannot silently alter contract or ownership boundaries.

Run 12 creates no configuration file or environment value.

## 13. Process composition

### API role

- hosts future external HTTP transport after an exact implementation task;
- calls public module interfaces;
- does not execute durable business work in framework background tasks;
- separates liveness, readiness and business outcome.

### Worker role

- processes approved durable work owned by modules;
- claims work only through authoritative state;
- preserves leases, idempotency and reconciliation semantics.

### Scheduler role

- creates or claims due scheduling intent through owning module contracts;
- does not own Beacon, entitlement or listing state.

Run 12 creates no process, listener, service or port.

## 14. Persistence and migration boundary

- PostgreSQL 18 is the future authoritative database.
- SQLAlchemy/Psycopg/Alembic are selected but gated.
- Platform owns common engine/session/transaction and Alembic environment conventions only.
- Each module owns migrations changing its authoritative state.
- ORM entities/sessions never cross public module boundaries.
- Cross-module transactions are prohibited unless a later approved decision explicitly defines one.
- Migration files require exact ID, owner, plan fingerprint, compatibility, rollback/roll-forward and fixture evidence.
- No schema, table, index, role, database or migration is created by this playbook.

## 15. Observability and audit context

Future common context may carry safe semantic identifiers:

- correlation/request/message/run/work IDs;
- module and operation;
- result/error category;
- latency and readiness state;
- redacted actor category and target scope;
- configuration/contract version.

OpenTelemetry is the instrumentation boundary; collector/exporter/backend remain deferred. Telemetry failure cannot fabricate success or change a business commit.

## 16. Dependencies

Allowed after exact implementation gates:

- Python standard library;
- Pydantic v2 and pydantic-settings at config/serialization boundaries;
- FastAPI/Uvicorn only in API entrypoint/transport scope;
- SQLAlchemy/Psycopg/Alembic only after persistence gates;
- OpenTelemetry API/SDK at instrumentation boundary;
- pytest, pytest-asyncio, Ruff, mypy, import-linter and coverage.py in development/test scope.

Forbidden leakage:

- provider SDK in common contracts;
- FastAPI request/response types in domain contracts;
- SQLAlchemy models/session in public interfaces;
- test-framework objects in runtime contracts;
- environment-specific infrastructure client in core module;
- external broker/cache without accepted decision/evidence.

HTTPX and provider-specific libraries are not Platform & Contracts dependencies unless a separately approved core need is proven.

## 17. Fake dependencies and test doubles

Future deterministic test support may define protocols/fakes for:

- `Clock`;
- `IdGenerator`;
- `ActorContextVerifier`;
- `AuthorizationDecision`;
- `IdempotencyStore`;
- `ContractRegistry`;
- `ConfigurationSource`;
- `AuditSink`;
- `TelemetrySink`;
- `ModulePublicPort`;
- `MigrationStateStore`.

Fakes use synthetic/redacted data, produce deterministic outcomes, model rejection/unavailability/malformed/ambiguous states where relevant, and never prove production behavior. Run 12 creates no executable fake.

## 18. Required fixtures and test vectors

Minimum fixture IDs:

### Contracts and authorization

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-OWNER-FOREIGN-ACCOUNT-001`;
- `FX-OWNER-FOREIGN-BEACON-001`.

### Idempotency and interruption

- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-INTERRUPT-PRECOMMIT-001`;
- `FX-INTERRUPT-UNKNOWN-001`;
- `FX-INTERRUPT-POSTCOMMIT-001`;
- `FX-BATCH-PARTIAL-001`.

### Data, security and configuration

- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`.

### Migration and compatibility

- `FX-MIG-EMPTY-001`;
- `FX-MIG-MINIMAL-001`;
- `FX-MIG-MIXED-VERSIONS-001`;
- `FX-MIG-DUPLICATE-REPLAY-001`;
- `FX-MIG-PLAN-MISMATCH-001`;
- `FX-MIG-PARTIAL-001`;
- `FX-MIG-ROLLBACK-001`;
- `FX-MIG-ROLLFORWARD-001`;
- `FX-MIG-READMODEL-REBUILD-001`.

Run 12 creates no fixture data files.

## 19. Acceptance Matrix coverage

Documentation acceptance requires traceability to:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-002`–`AM-TECH-004`, `AM-TECH-006`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-BATCH-001`;
- `AM-DATA-006`–`AM-DATA-007`;
- `AM-SEC-001`, `AM-SEC-003`;
- `AM-MIG-001`–`AM-MIG-009`.

Rows requiring future run/state/lock/reconciliation evidence remain gates and are not marked executed by this document.

## 20. Allowed future changes

A separately approved exact task may:

- prove isolated Python/uv/tool compatibility;
- create the declared repository skeleton;
- create `pyproject.toml` and exact `uv.lock`;
- implement common semantic primitives;
- add API/worker/scheduler composition skeletons;
- add import-linter/static architecture rules;
- add synthetic test builders/fakes;
- add persistence/migration infrastructure only after database gates.

Every task names exact paths, dependency versions, fixtures, matrix rows, rollback and final marker.

## 21. Forbidden changes

Without a new approved decision/task, this module must not:

- implement another module’s business logic or state;
- write foreign module tables;
- define provider payloads or SDK mappings;
- choose frontend, broker/cache, ingress, TLS, service manager or deployment topology;
- create production sensitive access material;
- create database/migrations before gates;
- decide tariff, account merge, filter, retention or provider behavior;
- promote DRAFT assumptions to APPROVED defaults;
- weaken authorization, ownership, idempotency or privacy;
- create parallel layouts;
- start product-code automatically after documentation acceptance.

## 22. Open decisions and deferred details

OD-001–OD-014 remain open and receive no default here.

Deferred technical details include:

- exact identifier generator/encoding;
- timestamp format/time-source implementation;
- idempotency TTL/storage;
- sensitive-value delivery;
- HTTP endpoint/error mapping and OpenAPI details;
- transaction isolation/session lifecycle;
- migration filename/revision convention;
- health/readiness endpoint shape;
- telemetry exporter/backend;
- coverage threshold and CI provider;
- release/deployment mechanism.

Deferred means blocked until named evidence, decision and task.

## 23. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `PC-01` | Isolated Python 3.14 + uv + selected toolchain proof | `NOT_STARTED` | exact proof-only task |
| `PC-02` | Repository skeleton, dependency groups and exact lock | `NOT_STARTED` | PC-01 PASS; exact task |
| `PC-03` | Common contract metadata/result/error primitives | `NOT_STARTED` | PC-02; named fixtures |
| `PC-04` | Idempotency/fingerprint/replay decision primitives | `NOT_STARTED` | PC-03; interruption fixtures |
| `PC-05` | Typed configuration composition/redaction | `NOT_STARTED` | sensitive-delivery boundary external |
| `PC-06` | API/worker/scheduler composition/readiness | `NOT_STARTED` | PC-02/03/05 |
| `PC-07` | Audit/correlation/telemetry context | `NOT_STARTED` | PC-03; redaction evidence |
| `PC-08` | Import-linter/static architecture gates | `NOT_STARTED` | declared source packages exist |
| `PC-09` | Persistence/Alembic conventions | `BLOCKED` | database/environment/migration gates |
| `PC-10` | Full contract/architecture evidence and handoff | `NOT_STARTED` | applicable prior subtasks complete |

This is dependency order, not permission or schedule.

## 24. Task packet requirements

A future task must include:

1. stable task/iteration ID;
2. exact parent GitHub SHA;
3. one atomic goal;
4. exact CREATE/REPLACE/APPEND_ONLY paths;
5. exact dependencies/versions when applicable;
6. allowed and forbidden actions;
7. backup/rollback point;
8. idempotency rule;
9. fixtures and Acceptance Matrix rows;
10. required tests/static checks;
11. evidence/report format;
12. exact final marker;
13. prohibition on unrelated module work.

CLI does not choose architecture, scope completeness, dependencies or next task.

## 25. Report and handoff format

Every future module-task report includes:

- `TASK_ID`;
- `STATUS`;
- `BASE_SHA` and `FINAL_SHA` when publication is authorized;
- `FILES_CHANGED`;
- dependency/lock evidence when applicable;
- test/static results;
- fixture and matrix results;
- ownership-boundary check;
- idempotency/interruption check;
- sensitive-data/privacy check;
- rollback evidence;
- out-of-scope findings;
- commit/push status;
- `CHATGPT_REVIEW_REQUIRED: YES`;
- exact final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 26. Acceptance criteria

The playbook is acceptable only when:

- purpose, boundaries and non-ownership are explicit;
- singular future layout and import direction are defined;
- public input/output families preserve common semantics without inventing wire schemas;
- authorization, ownership, idempotency, error, configuration, process and migration gates are explicit;
- dependencies and fake boundaries are scoped;
- fixture IDs and matrix rows are named;
- roadmap does not start work automatically;
- OD-001–OD-014 remain open;
- no code, dependency file, lock, executable test, migration, database, Docker/CI/CD, deploy/runtime, service, port or sensitive access material is created;
- GitHub publication and exact server synchronization are independently verified.

## 27. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### PC-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 12 initial Platform & Contracts boundaries, ownership, contracts, layout, dependencies, fake interfaces, fixtures, matrix coverage, roadmap and handoff defined.
- No implementation artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
