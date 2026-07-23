# Runtime Process and Package Model

Version: 1.0
Status: RF-04_ACTIVE_THIRD_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE
Date: 2026-07-23
Module: 14-runtime-foundation-and-autonomous-integration
Roadmap step: RF-04
Technical-ID: RF-04-03-RUNTIME-PROCESS-AND-PACKAGE-MODEL-20260723
Source branch: main
Source base SHA: 710f965a66488f99b4c3cc9cf9f44bef54c7434a
RF-04-01 accepted chain head: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
RF-04-02 accepted chain head: 710f965a66488f99b4c3cc9cf9f44bef54c7434a
Runtime mutation: none
Production verdict: NOT_CLAIMED
Final target: READY_FOR_OPERATOR_ACCEPTANCE

## 1. Authority and scope

GitHub `main` is the sole source of truth. This is the third RF-04 design-only artifact. RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`; RF-04-02 is accepted through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`. This document records a future runtime process shell, package layout and ownership model; it creates no runtime implementation, package, entry point, settings, dependency, CI, Docker, database, migration, service or server resource.

The labels are normative: `CURRENT_REPOSITORY_FACT` means verified in the source tree or accepted document; `PLANNED_RUNTIME_ARTIFACT` means a future path or behavior defined here; `FUTURE_ROADMAP_OWNER` means the later RF step that may implement it. Modules 01–13 retain domain-state ownership. Module 14 owns assembly design, not foreign domain state. Existing domain packages are not renamed or moved.

## 2. Accepted invariants

The planned runtime preserves these accepted invariants: PostgreSQL 18 is authoritative persistence; SQLAlchemy 2, Psycopg 3 and Alembic are the future persistence stack; FastAPI/Uvicorn is the API stack; API, worker and scheduler are separate processes; durable work, leases and outboxes are PostgreSQL-backed; no Redis, Celery, RabbitMQ, Kafka or other broker is allowed; no durable framework background task is allowed; durable work never uses an in-memory authoritative scheduler; no direct foreign-module table writes are allowed; no provider call occurs while a DB transaction is open; an ambiguous external effect is reconciled before retry; provider acceptance is not human reading; one application image has process-specific commands; acceptance runtime is local-only; providers are disabled by default; public ingress is forbidden; `PRODUCTION_READY` is not claimed.

RF-04-01 remains the authoritative physical table catalogue and ownership model. RF-04-02 remains the authoritative transaction, outbox, lease, commit-point and reconciliation boundary. This artifact invents no authoritative table and does not change either document.

## 3. Current source-tree inventory

The following are `CURRENT_REPOSITORY_FACT` observations at the source base. No `mayak.runtime` directory or callable below is claimed to exist.

| Exact current path | Current role and owner | Reusable unchanged | Runtime absent / FUTURE_ROADMAP_OWNER |
|---|---|---|---|
| `src/mayak/__init__.py` | Package root; Module 01/platform foundation | Yes | Process shell absent; RF-06 |
| `src/mayak/contracts/` | Public transport-neutral contracts; Module 01 | Yes | Runtime binding absent; RF-10 |
| `src/mayak/platform/` | Semantic platform primitives (configuration, correlation, process, readiness, redaction); Module 01 | Yes, as contracts/primitives | Runtime integration absent; RF-10 |
| `src/mayak/entrypoints/api/__init__.py` | Existing package marker only; Module 14 boundary | Yes | No API callable verified; RF-06/RF-23 |
| `src/mayak/entrypoints/worker/__init__.py` | Existing package marker only; Module 14 boundary | Yes | No worker callable verified; RF-06/RF-23 |
| `src/mayak/entrypoints/scheduler/__init__.py` | Existing package marker only; Module 14 boundary | Yes | No scheduler callable verified; RF-06/RF-23 |
| `src/mayak/modules/` | Domain semantic packages; modules 01–13 | Yes, domain ownership unchanged | DB-backed runtime absent; RF-10–RF-22 |
| `src/mayak/modules/avito_parser_adapter/` | Parser boundary and semantic adapter contracts; Module 05 | Yes | Live/runtime adapter absent; RF-14 |
| `src/mayak/modules/telegram_adapter/` | Telegram adapter contracts and semantic gates; Module 09 | Yes | Provider runtime absent; RF-18 |
| `src/mayak/modules/max_adapter/` | MAX adapter contracts and semantic gates; Module 10 | Yes | Provider runtime absent; RF-19 |
| `src/mayak/modules/notification_delivery/` | Delivery and outbox semantics; Module 08 | Yes | Durable implementation absent; RF-17 |
| `tests/architecture/`, `tests/contract/`, `tests/unit/` | Executable architecture, contract and semantic tests | Yes | Runtime integration tests absent; RF-24 |
| `pyproject.toml` | Current package and dependency declaration | Yes | Full runtime dependency proof absent; RF-06 |
| `uv.lock` | Current lock identity | Yes | Expanded runtime lock proof absent; RF-06 |

The inventory is evidence-backed by the current tree. Existing semantic modules are not empty; the missing claim is specifically acceptance-runtime assembly and physical persistence.

## 4. Canonical planned package layout

The following are `PLANNED_RUNTIME_ARTIFACT` paths under `src/mayak/runtime/`; none exists in the current source tree. Each row has a single future owner.

| Planned file | One responsibility | Allowed imports | Forbidden imports/effects and import-time rule | FUTURE_ROADMAP_OWNER |
|---|---|---|---|---|
| `src/mayak/runtime/__init__.py` | Stable runtime package boundary | stdlib typing/version-safe metadata | No DB/provider/filesystem/process side effect; no secrets | RF-06 |
| `src/mayak/runtime/api.py` | `create_app()` and API `main()` lifecycle | FastAPI/Uvicorn, public services, bootstrap/container | No direct tables, provider call, scheduler/worker loop or import-time binding | RF-23 |
| `src/mayak/runtime/worker.py` | `run_worker()` and worker `main()` lifecycle | bootstrap/container, public services, durable work ports | No broker, API server, scheduler authority or import-time work | RF-23 |
| `src/mayak/runtime/scheduler.py` | `run_scheduler()` and scheduler `main()` lifecycle | bootstrap/container, schedule/public services | No provider call, notification send, in-memory authority or import-time work | RF-23 |
| `src/mayak/runtime/bootstrap.py` | Shared startup sequencing and cleanup | settings, logging, container, health, public ports | No business rules, direct foreign state or import-time initialization | RF-23 |
| `src/mayak/runtime/container.py` | Dependency assembly and explicit injection | concrete adapters, public services, ports | No business decisions, migration execution or import-time connections | RF-09/RF-23 |
| `src/mayak/runtime/settings.py` | Typed configuration acquisition | Pydantic Settings and stdlib | No secret generation, secret constants, DB connection or provider call at import | RF-05/RF-06 |
| `src/mayak/runtime/health.py` | Liveness, readiness, version and safe diagnostics | public readiness contracts, safe metadata | No raw payload, secret, personal data or effectful probe at import | RF-26 |
| `src/mayak/runtime/version.py` | Build/source identity projection | stdlib and build metadata | No network, secret, DB or mutable filesystem action | RF-06/RF-26 |
| `src/mayak/runtime/logging.py` | Redacted structured logging setup | stdlib logging and approved observability boundary | No secret/raw payload logging or process start at import | RF-26 |

Canonical rules: no import-time DB connection, provider call, filesystem mutation or process start; no secrets in constants; domain packages never import the runtime package. Persistence internals are future RF-09 scope and are not invented as current files. The composition root may bind concrete ports and adapters to public interfaces.

## 5. Process entry-point matrix

Exactly three primary process entry points are planned. The commands are design commands only.

| Process | Python module / callable | Process command | Primary responsibility | Allowed durable mutations | Startup / readiness dependencies | Liveness / shutdown / forbidden work | FUTURE_ROADMAP_OWNER |
|---|---|---|---|---|---|---|---|
| `mayak-api` | `mayak.runtime.api:create_app()`, `main()` | `python -m mayak.runtime.api` | FastAPI HTTP transport and request dispatch | Owning public application-service mutations and request UoW | Typed config, core DB/schema, wired services; liveness means process alive | Uvicorn lifecycle; no worker claims, scheduler loop, broker or direct tables | RF-23 |
| `mayak-worker` | `mayak.runtime.worker:run_worker()`, `main()` | `python -m mayak.runtime.worker` | Bounded durable work claims and handlers | Claimed owning-module work, guarded terminal state and outbox effects | Typed config, DB/schema, claim subsystem and handlers | Stop claims, bounded drain; no API server, scheduler authority or broker | RF-23 |
| `mayak-scheduler` | `mayak.runtime.scheduler:run_scheduler()`, `main()` | `python -m mayak.runtime.scheduler` | Discover due durable schedules and enqueue work | Schedule-owned due-work records through public Scan boundary | Typed config, DB/schema and durable schedule subsystem | Stop batches, bounded drain; no provider call, send or foreign mutation | RF-23 |

## 6. API process model

The future API uses a FastAPI app factory under Uvicorn. Each request receives a correlation context; structural validation, authentication, authorization and ownership checks precede mutation. Routes call public application services only. A request-scoped DB unit of work is used where applicable; transport DTOs are never domain authority. Durable work never uses a framework background task. The API has no scheduler loop and no generic delivery-worker loop.

Missing optional provider credentials do not prevent core API readiness; affected operations return the documented disabled classification. API startup does not execute migrations or make a startup live provider probe. Readiness fails on mandatory DB connectivity or schema incompatibility. Liveness only means the process is alive and never implies readiness. Binding is limited to the later accepted local-only topology, including the approved localhost range; no public ingress is created by this design.

## 7. Worker process model

The worker claims bounded batches from PostgreSQL with deterministic ordering, a lease token and expiry. The claim transaction commits before any network or provider work. A handler performs one explicit work item, then makes a guarded terminal commit whose lease token and ownership still match. Retry state is persisted and bounded. An ambiguous provider effect enters reconciliation-first handling; it is never blindly retried. A lost lease cannot commit terminal effects.

Handlers call the owning module's public application service and never write a foreign table. There is no broker, Celery, Redis, RabbitMQ, Kafka, scheduler authority or long transaction around a provider call. On graceful stop the worker takes no new claims and drains in-flight work within a bound. Durable work remains in PostgreSQL for restart.

## 8. Scheduler process model

Durable schedules in PostgreSQL are authoritative. The scheduler discovers due work using UTC timestamps and a documented clock source, emits duplicate-safe due work keyed by `(schedule_id, due_at)` or an accepted equivalent, and processes deterministic bounded batches. It enforces the accepted tariff cadence. Polling and backoff are bounded.

The scheduler makes no direct parser/provider call, sends no notification and performs no business mutation outside the Scan public boundary. It has no in-memory-only schedule. Restart-safe discovery and duplicate-safe persistence provide correctness; one scheduler process is sufficient operationally, but correctness never depends on singleton status. Graceful shutdown stops new batches and closes resources within a bound.

## 9. Composition root and bootstrap

The exact future assembly order is: (1) load and validate typed settings; (2) establish environment and source identity; (3) configure redacted structured logging; (4) construct DB engine and session factories without implicit migration; (5) construct persistence adapters; (6) construct module-owned application services; (7) bind provider adapters according to explicit profiles; (8) construct process-specific handlers and routes; (9) run readiness checks; (10) start the process loop or server; (11) perform bounded graceful cleanup.

The composition root may know concrete adapters, but domain/public contracts may not. Provider SDK types never enter common contracts. Missing optional credentials create a disabled adapter state. Mandatory core configuration failure prevents readiness. Migration execution remains an explicit separate deployment/migration action. Startup never performs a live provider probe unless a later exact operator task permits it.

## 10. Dependency direction and import boundaries

The permitted direction is:

`runtime process shell` → `composition root` → `public application services/contracts` → `domain modules` → `ports`

Concrete persistence and provider adapters are injected at the composition root. Domain packages must not import runtime, FastAPI or Uvicorn. Common contracts must not import provider SDKs, framework, persistence or transport internals. Web and Admin call owning services, never repositories or tables. An adapter cannot perform generic business-success mutation. Private cross-module implementation imports and cyclic runtime/domain imports are forbidden.

## 11. Configuration acquisition boundary

This is a documentation-only boundary, not a finalized schema. The later configuration artifact maps Pydantic Settings to an environment profile, environment ID, source SHA, DB connection references, local API bind/port, worker and scheduler timing bounds, provider enable flags, provider secret-file references, observability settings and retention settings. Secret values never enter Git, constants, logs or diagnostics. `settings.py` owns typed acquisition and validation only; it does not generate secrets. The full schema is a future RF-04 configuration artifact owned by RF-05/RF-06, while runtime wiring is RF-23.

## 12. Startup and readiness lifecycle

The process state sequence is `BOOTSTRAP_PENDING` → `CONFIG_VALIDATED` → `DEPENDENCIES_CONSTRUCTED` → `CORE_CHECKS_RUNNING` → `READY`, with `DEGRADED_OPTIONAL_PROVIDER` as a valid optional-provider branch, and `NOT_READY` on failed mandatory checks. Shutdown transitions through `SHUTTING_DOWN` to `STOPPED`.

API readiness requires valid configuration, DB connectivity, the current migration revision and required services wired. Worker readiness additionally requires the claim subsystem and handlers. Scheduler readiness additionally requires the durable schedule subsystem. A missing optional provider is `BLOCKED_CREDENTIAL` or disabled and may leave the core process ready; its result classification is `PROVIDER_DISABLED_CONTINUE`. A mandatory DB/schema mismatch is `NOT_READY`, runs no silent migration and performs no partial business processing.

## 13. Graceful shutdown and restart

SIGTERM and SIGINT initiate bounded shutdown. Uvicorn stops new API acceptance according to its lifecycle; the worker stops new claims; the scheduler stops new batches. In-flight work drains within a bound. Terminal completion is guarded by a valid lease; uncommitted DB transactions roll back; sessions and the engine close. Durable work is never deleted.

Restart resumes from PostgreSQL. Expired or lost leases are reconciled. A crash before commit has no durable effect; a crash after commit recovers from durable state and outbox. Forced termination may leave an expired lease, which the next claim/reconciliation cycle handles. No process relies on memory for authoritative state.

## 14. Health, version and diagnostics contract

Liveness reports process-alive only. Readiness reports dependency and business-processing eligibility. Version/build diagnostics expose process kind, source SHA, environment ID and migration revision plus provider readiness summaries. Safe diagnostics contain only redacted operational facts: no secret values, raw provider payload, production personal data, credentials, cookies or private key material. Health output does not imply that a provider was called or that a human read provider output. Implementation and verification belong to RF-26.

## 15. Runtime commands and one-image model

One application image carries one source SHA and lock identity. Its role is selected by exactly these commands: `python -m mayak.runtime.api`, `python -m mayak.runtime.worker` and `python -m mayak.runtime.scheduler`. The process command determines the role; mutable code is not installed at container startup. An explicit migration command belongs to RF-08/RF-09 and is never embedded in API startup. The runtime has no public ingress. Compose implementation is deferred to RF-08.

## 16. Failure and recovery matrix

Each row has a future RF proof owner; persisted state names only accepted ownership boundaries and does not authorize direct foreign writes.

| # / scenario | Process / detection | Authoritative persisted state | Readiness effect | Retry or reconciliation action | Safe operator evidence | Forbidden response | FUTURE_RF_PROOF_OWNER |
|---|---|---|---|---|---|---|---|
| 1. Invalid typed configuration | Any / settings validation | None | `NOT_READY` | Correct profile, restart | Redacted error, environment ID | Start partially | RF-06 |
| 2. Missing mandatory core secret | Any / bootstrap validation | None | `NOT_READY` | Supply through approved secret boundary | Secret reference name only | Log value or continue | RF-06 |
| 3. Missing optional provider credential | API/worker / adapter bind | Provider disabled state | Core may be `READY`; provider degraded | `PROVIDER_DISABLED_CONTINUE` | Provider code and disabled reason | Block core or fabricate success | RF-18/RF-19 |
| 4. PostgreSQL unavailable at startup | Any / core check | No new state | `NOT_READY` | Bounded startup backoff, then stop | Connectivity class and source SHA | Migrate, process, or use memory | RF-09 |
| 5. PostgreSQL unavailable after readiness | Any / health/UoW error | Existing committed state | Not ready for affected work | Stop new work; resume after check | Redacted DB error class | Claim from memory or discard work | RF-09/RF-26 |
| 6. Migration revision behind expected head | Any / revision check | Existing schema unchanged | `NOT_READY` | Explicit migration action | Current/expected revision | Auto-migrate silently | RF-09 |
| 7. Migration revision ahead/unknown | Any / revision check | Existing schema preserved | `NOT_READY` | Stop and operator compatibility review | Revisions only | Downgrade or guess compatibility | RF-09 |
| 8. API request cancellation | API / request lifecycle | Committed state only; UoW rollback otherwise | Process remains eligible | Return cancellation safely; reconcile if effect unknown | Correlation and outcome class | Duplicate mutation or claim success | RF-23 |
| 9. Worker crash before claim commit | Worker / transaction boundary | No claim | Worker restarts ready | Work remains claimable | Work ID and no-claim evidence | Mark terminal or delete work | RF-17 |
| 10. Worker crash after claim commit | Worker / lease expiry | Claimed lease in PostgreSQL | Worker may remain ready | Expiry/reclaim then handler policy | Lease token hash/class and timestamps | Assume success or blindly duplicate | RF-17 |
| 11. Worker lost lease | Worker / guarded update | Prior durable state and lease record | Affected item withheld/reconciled | Reconcile; guarded commit rejects | Lease conflict class | Commit without lease | RF-17 |
| 12. Worker ambiguous provider effect | Worker / adapter outcome | Explicit ambiguous/reconciliation state | Affected work ineligible for blind retry | Reconcile first, then approved retry | Correlation, provider-safe metadata | Blind retry or clean success | RF-16/RF-18/RF-19 |
| 13. Scheduler duplicate due-work race | Scheduler / unique/idempotent insert | One accepted due-work identity | Scheduler remains eligible | Treat duplicate as already scheduled | Schedule ID and UTC due_at | Create second work effect | RF-15 |
| 14. Scheduler restart | Scheduler / startup discovery | Durable schedules and due work | Ready after checks | Rediscover due bounded batch | Process/source/revision identity | Depend on memory cursor | RF-15 |
| 15. Graceful SIGTERM | Any / signal handler | Committed state and leases | `SHUTTING_DOWN` then stopped | Stop new work, bounded drain | Signal time and drain result | Delete durable work | RF-26 |
| 16. Forced process termination | Any / next startup reconciliation | Last committed state; possible lease | Restart checks required | Expire/reconcile leases and outboxes | Exit class and recovery evidence | Claim prior in-flight success | RF-26 |
| 17. Telemetry backend unavailable | Any / exporter failure | Business state unaffected | Core may remain ready | Bounded local logging and retry policy | Redacted local health summary | Block business or log secrets | RF-26 |
| 18. Provider disabled | API/worker / profile gate | Disabled provider status | Core ready, provider degraded | `PROVIDER_DISABLED_CONTINUE` | Feature/provider readiness summary | Live call or fabricated result | RF-18/RF-19 |
| 19. Provider definite failure | Worker/API / normalized outcome | Retryable or terminal provider outcome | Usually affected operation only | Policy-bounded retry; no retry for definite rejection | Safe outcome and correlation | Convert to empty success | RF-14/RF-18/RF-19 |
| 20. Foreign-resource collision detected | Any / isolation preflight | No project mutation | Deployment/runtime action blocked | Stop and obtain separately accepted project resource | Path/resource class without foreign contents | Reuse, alter, delete or inspect foreign resource | RF-05/RF-08/RF-27 |

## 17. Roadmap implementation ownership

No implementation gap is unassigned: RF-05 owns the server environment record and configuration boundary; RF-06 owns Python/uv/dependency and executable import proof; RF-07 owns CI checks; RF-08 owns image, Compose and process commands; RF-09 owns engine/session/Alembic/persistence foundation; RF-10–RF-22 own module runtime services and adapters; RF-23 owns API/application wiring; RF-24 owns synthetic E2E; RF-25 owns security verification; RF-26 owns observability, restart and recovery; RF-27 owns deployment; RF-28 owns final drills. This artifact does not close RF-04, select a next roadmap step, or start RF-05.

## 18. Acceptance checklist and final state

RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`; RF-04-02 is accepted through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`; this is the RF-04 third artifact. It defines exactly three primary process entry points and ten planned runtime files, distinguishes current and planned paths, and makes package/import ownership explicit. No existing domain package is renamed. No runtime code, dependency, CI, Docker, DB, migration, server, provider call or foreign-resource mutation was created or performed. Physical table ownership and transaction/outbox rules remain unchanged; direct foreign-module mutation and broker dependencies remain forbidden.

RF-04 remains active and not closed. RF-05 remains not started. The production verdict is `NOT_CLAIMED`; `PRODUCTION_READY` is not claimed. The artifact is ready for independent operator acceptance.

RF04_RUNTIME_PROCESS_AND_PACKAGE_MODEL_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE

RF04_RUNTIME_PROCESS_AND_PACKAGE_MODEL_PUBLISHED
