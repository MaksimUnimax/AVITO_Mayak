# Маяк Авито — Scan Persistence, Scheduler and Worker Gates v1.0

## Metadata
- status: approved semantic gate documentation for SOLS-13;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f, SOLS-08 accepted at 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6, SOLS-09 accepted at dbfa556c1e6b78091b76005cd7f68cb2bca2565f, SOLS-10 accepted at ab8959cc1134b5c00973ef69814ec4c97a33bb1e, SOLS-11 accepted at 7d20eaffadaa2373eb3ea409251b119d8e6479bc, SOLS-12 accepted at 8b013d5124b565be014f80dfcdc7d2e5e925dc28;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization;
- persistence/scheduler/worker/claim/DB implementation remains gated.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines what remains gated and what semantic boundary is allowed before implementation approval.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- document the semantic gate boundary for durable persistence, scheduling, worker execution, claims and database implementation;
- keep the module docs-only until exact future implementation decisions are accepted;
- identify which runtime, schema and dispatch families remain blocked;
- preserve neutral ownership boundaries across persistence, scheduler, worker, parser, egress, notification and deploy concerns;
- provide synthetic markdown-only examples for future review without authorizing executable artifacts.

Non-goals:

- no code, tests, runtime, schema, migration, deploy, parser, egress, notification or UI authorization;
- no transport/provider/framework/ORM decision;
- no database model, table, index, transaction, lock, queue, broker, cache, lease, heartbeat, retry, backoff or circuit-breaker choice;
- no scheduler interval, due-slot identity, worker concurrency, worker fairness or dispatch mechanics choice;
- no numeric defaults for interval, due slot, claim lease, heartbeat, retry/backoff, retention, deletion, compaction, page depth, queue visibility timeout, worker concurrency or fairness;
- no closure of OD-013 by assumption;
- no executable fixture files and no tests in this task.

## 2. Gate summary

- Durable persistence remains gated until an explicit physical schema and migration decision exists.
- Scheduler runtime remains gated until an explicit scheduler/time policy decision exists.
- Worker runtime remains gated until an explicit worker gate exists.
- Claim lease, heartbeat, renewal, locks, transactions and stale-claim handling remain gated until an explicit claim/concurrency implementation decision exists.
- Retry/backoff/circuit-breaker policy remains gated until an explicit retry policy decision exists.
- Queue, broker, Redis, RabbitMQ, Celery, cache and any equivalent dispatch infrastructure remain gated until an explicit queue/broker/cache decision exists.
- Parser calls, live Avito calls, Egress route calls and notification delivery are owned by their own modules and gates.
- Notification outbox, delivery attempts, delivery retries and provider-success claims are owned by Notification Delivery.
- Read-model rebuild, retention, deletion and compaction jobs remain gated by OD-013 and DB/runtime decisions.
- Semantic contracts and docs-only boundary decisions are allowed before implementation approval.
- Codex/CLI must not infer implementation permission from the existence of semantic docs.

## 3. Durable persistence gate

The following blocked implementation families remain docs-only and unresolved. They do not authorize implementation.

| Family | Why blocked | Required future gate | Forbidden current assumption | Safe semantic placeholder if any |
|---|---|---|---|---|
| `PostgreSQLTableImplementation` | Physical storage shape is unresolved. | Explicit physical schema/migration gate. | A semantic gate doc authorizes a table. | `PHYSICAL_SCHEMA_GATE_REQUIRED` |
| `SQLAlchemyModelImplementation` | ORM mapping is unresolved. | Explicit physical schema/migration gate. | Docs imply a model class is chosen. | `PHYSICAL_SCHEMA_GATE_REQUIRED` |
| `PsycopgRuntimeUsage` | DB client/runtime choice is unresolved. | Explicit physical schema/migration gate. | Docs imply direct DB access is permitted. | `PERSISTENCE_IMPLEMENTATION_BLOCKED` |
| `AlembicMigrationImplementation` | Migration strategy is unresolved. | Explicit physical schema/migration gate. | Docs imply migration authoring is allowed. | `MIGRATION_GATE_REQUIRED` |
| `SchedulerRuntimeImplementation` | Runtime scheduling is unresolved. | Explicit scheduler/time policy gate. | Docs imply a scheduler process is selected. | `SCHEDULER_RUNTIME_BLOCKED` |
| `PollingLoopImplementation` | Polling mechanics are unresolved. | Explicit scheduler/time policy gate. | Docs imply a polling loop is chosen. | `SCHEDULER_RUNTIME_BLOCKED` |
| `DueSlotIdentityPolicy` | Due-slot identity is unresolved. | Explicit scheduler/time policy gate. | Docs imply due-slot identity is fixed. | `DUE_SLOT_POLICY_UNRESOLVED` |
| `ScanIntervalValuePolicy` | Interval policy is unresolved. | Explicit scheduler/time policy gate. | Docs imply an interval default exists. | `SCAN_INTERVAL_POLICY_UNRESOLVED` |
| `WorkerRuntimeImplementation` | Worker execution model is unresolved. | Explicit worker gate. | Docs imply a worker process is selected. | `WORKER_RUNTIME_BLOCKED` |
| `WorkerConcurrencyPolicy` | Concurrency policy is unresolved. | Explicit worker gate. | Docs imply a concurrency value exists. | `WORKER_CONCURRENCY_POLICY_UNRESOLVED` |
| `WorkerFairnessPolicy` | Fairness policy is unresolved. | Explicit worker gate. | Docs imply fairness ordering is chosen. | `WORKER_CONCURRENCY_POLICY_UNRESOLVED` |
| `ClaimLeaseDurationPolicy` | Claim lease duration is unresolved. | Explicit claim/concurrency implementation gate. | Docs imply a lease default exists. | `CLAIM_LEASE_POLICY_UNRESOLVED` |
| `ClaimHeartbeatPolicy` | Claim heartbeat policy is unresolved. | Explicit claim/concurrency implementation gate. | Docs imply a heartbeat default exists. | `CLAIM_HEARTBEAT_POLICY_UNRESOLVED` |
| `ClaimRenewalPolicy` | Claim renewal policy is unresolved. | Explicit claim/concurrency implementation gate. | Docs imply renewal mechanics are fixed. | `CLAIM_HEARTBEAT_POLICY_UNRESOLVED` |
| `PhysicalLockImplementation` | Lock mechanics are unresolved. | Explicit claim/concurrency implementation gate. | Docs imply physical lock usage is allowed. | `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` |
| `TransactionBoundaryImplementation` | Transaction boundary is unresolved. | Explicit claim/concurrency implementation gate. | Docs imply transaction shape is fixed. | `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` |
| `StaleClaimHandlingPolicy` | Stale claim handling is unresolved. | Explicit claim/concurrency implementation gate. | Docs imply stale claims are already solved. | `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` |
| `RetryBackoffPolicy` | Retry policy is unresolved. | Explicit retry policy gate. | Docs imply retry/backoff defaults exist. | `RETRY_BACKOFF_POLICY_UNRESOLVED` |
| `CircuitBreakerPolicy` | Circuit breaker policy is unresolved. | Explicit retry policy gate. | Docs imply circuit breaker behavior is chosen. | `CIRCUIT_BREAKER_POLICY_UNRESOLVED` |
| `QueueBrokerCacheImplementation` | Dispatch infrastructure is unresolved. | Explicit queue/broker/cache gate. | Docs imply a queue or cache is selected. | `QUEUE_BROKER_CACHE_BLOCKED` |
| `RedisRabbitCeleryOrEquivalentImplementation` | Specific dispatch technology choice is unresolved. | Explicit queue/broker/cache gate. | Docs imply Redis, RabbitMQ, Celery or equivalent is chosen. | `QUEUE_BROKER_CACHE_BLOCKED` |
| `EgressRouteCallImplementation` | Egress routing is not Scan-owned. | Egress route implementation gate in Egress module. | Scan may call routes directly. | `EGRESS_ROUTE_CALLS_NOT_SCAN_OWNED` |
| `ParserCallImplementation` | Parser calling contract is not Scan-owned. | Parser Adapter accepted implementation contract. | Scan may parse or call parser internals directly. | `PARSER_CALLS_NOT_SCAN_OWNED` |
| `LiveAvitoProviderCallImplementation` | Live provider traffic is not Scan-owned. | Parser Adapter accepted implementation contract. | Scan may issue live Avito calls. | `PARSER_CALLS_NOT_SCAN_OWNED` |
| `NotificationOutboxImplementation` | Notification delivery is not Scan-owned. | Notification Delivery accepted implementation contract. | Scan may own outbox state. | `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` |
| `DeliveryAttemptImplementation` | Notification delivery attempts are not Scan-owned. | Notification Delivery accepted implementation contract. | Scan may own delivery attempts. | `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` |
| `ProviderRetryImplementation` | Notification/provider retry is not Scan-owned. | Notification Delivery accepted implementation contract. | Scan may own provider retry policy. | `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` |
| `ProviderDeliverySuccessClaim` | Provider-success claims are not Scan-owned. | Notification Delivery accepted implementation contract. | Scan may claim provider delivery success. | `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` |
| `ReadModelRebuildJob` | Rebuild jobs are unresolved and gated. | Read-model rebuild policy gate. | Docs imply a rebuild job exists. | `READ_MODEL_REBUILD_JOB_BLOCKED` |
| `RetentionJobImplementation` | Retention policy is gated. | OD-013 and DB/runtime gates. | Docs imply a retention job is chosen. | `RETENTION_JOB_GATED_BY_OD_013` |
| `DeletionJobImplementation` | Deletion policy is gated. | OD-013 and DB/runtime gates. | Docs imply a deletion job is chosen. | `DELETION_JOB_GATED_BY_OD_013` |
| `CompactionJobImplementation` | Compaction policy is gated. | OD-013 and DB/runtime gates. | Docs imply a compaction job is chosen. | `COMPACTION_JOB_GATED_BY_OD_013` |
| `RuntimeServiceImplementation` | Service runtime is unresolved. | Runtime service/deploy gate. | Docs imply a runtime service is approved. | `RUNTIME_SERVICE_BLOCKED` |
| `DockerDeployImplementation` | Deploy artifact/runtime packaging is unresolved. | Runtime service/deploy gate. | Docs imply Docker or deploy artifacts are approved. | `DOCKER_DEPLOY_BLOCKED` |

## 4. Physical schema and migration gate

- PostgreSQL tables, SQLAlchemy models, Psycopg usage and Alembic migrations remain blocked until an explicit physical schema/migration gate is accepted.
- No table, model, index, constraint or migration shape is chosen here.
- This document may state what remains gated, but it must not invent schema, ORM or migration ownership.
- Safe current effect: keep `PHYSICAL_SCHEMA_GATE_REQUIRED` and `MIGRATION_GATE_REQUIRED` as docs-only classes.
- Forbidden current outcome: treating semantic documentation as permission to create tables, ORM models or migrations.

## 5. Scheduler gate

- Scheduler runtime, polling loop, due slot identity, interval values and missed-scan scheduling mechanics remain blocked until an explicit scheduler/time policy gate is accepted.
- No scan interval default is introduced here.
- No due-slot identity, polling cadence, missed-scan algorithm or scheduling window is selected here.
- Safe current effect: keep `SCHEDULER_RUNTIME_BLOCKED`, `DUE_SLOT_POLICY_UNRESOLVED` and `SCAN_INTERVAL_POLICY_UNRESOLVED` as docs-only classes.
- Forbidden current outcome: inferring a production schedule from a semantic gate doc.

## 6. Worker gate

- Worker runtime, worker concurrency, worker fairness and worker dispatch mechanics remain blocked until an explicit worker gate is accepted.
- No worker pool size, priority scheme, fairness order or dispatch loop is chosen here.
- Safe current effect: keep `WORKER_RUNTIME_BLOCKED`, `WORKER_CONCURRENCY_POLICY_UNRESOLVED` and related docs-only classes unresolved.
- Forbidden current outcome: assuming runtime worker execution is authorized because a semantic worker gate exists.

## 7. Claim and concurrency implementation gate

- Claim lease duration, claim heartbeat, claim renewal, physical locks, transactions, conflict rows and stale-claim handling remain blocked until an explicit claim/concurrency implementation gate is accepted.
- No lease, lock or transaction design is chosen here.
- No stale-claim retry path or conflict-row strategy is selected here.
- Safe current effect: keep `CLAIM_LEASE_POLICY_UNRESOLVED`, `CLAIM_HEARTBEAT_POLICY_UNRESOLVED` and `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` as docs-only classes.
- Forbidden current outcome: using semantic docs to justify a physical lock or transaction implementation.

## 8. Retry/backoff/circuit-breaker gate

- Retry/backoff/circuit breaker policy remains blocked until an explicit retry policy gate is accepted.
- No retry count, delay, backoff curve, circuit-breaker threshold or recovery policy is chosen here.
- Safe current effect: keep `RETRY_BACKOFF_POLICY_UNRESOLVED` and `CIRCUIT_BREAKER_POLICY_UNRESOLVED` as docs-only classes.
- Forbidden current outcome: selecting defaults by assumption or convenience.

## 9. Queue/broker/cache gate

- Queue, broker, Redis, RabbitMQ, Celery, cache or any other dispatch infrastructure remains blocked until an explicit queue/broker/cache gate is accepted.
- No dispatch technology choice is made here.
- No visibility timeout, queue name, broker topology or cache usage is chosen here.
- Safe current effect: keep `QUEUE_BROKER_CACHE_BLOCKED` as a docs-only class.
- Forbidden current outcome: treating transport-neutral semantics as infrastructure authorization.

## 10. Egress/Parser/Notification runtime dependency gate

- External route calls, parser calls, live Avito calls and notification delivery remain blocked and owned by their own modules and gates.
- Notification outbox, delivery attempts, delivery retries and provider-success claims remain blocked and owned by Notification Delivery.
- Parser Adapter owns parser execution contracts and provider mappings.
- Egress owns route-call behavior and route-specific runtime decisions.
- Safe current effect: keep `PARSER_CALLS_NOT_SCAN_OWNED`, `EGRESS_ROUTE_CALLS_NOT_SCAN_OWNED` and `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` as docs-only classes.
- Forbidden current outcome: deriving runtime authorization from ownership references alone.

## 11. Read-model rebuild, compaction and retention job gate

- Read-model rebuild jobs, retention jobs, deletion jobs and compaction jobs remain blocked by OD-013 and DB/runtime gates.
- OD-013 remains open and is not closed by assumption.
- No retention duration, deletion cadence, compaction algorithm or rebuild job is chosen here.
- Safe current effect: keep `READ_MODEL_REBUILD_JOB_BLOCKED`, `RETENTION_JOB_GATED_BY_OD_013`, `DELETION_JOB_GATED_BY_OD_013` and `COMPACTION_JOB_GATED_BY_OD_013` as docs-only classes.
- Forbidden current outcome: using this document to pretend the physical retention question is resolved.

## 12. Allowed before implementation gate

The following allowed-before-gate semantic-only families are docs-only and do not authorize runtime or schema work.

| Family | Allowed meaning | Boundary | Forbidden escalation |
|---|---|---|---|
| `DocsOnlySemanticBoundary` | State what remains semantic-only. | No runtime, schema or deploy permission. | Becoming implementation authorization. |
| `GateInventoryDocumentation` | Inventory unresolved gate families. | Reference only, no chosen mechanism. | Turning inventory into architecture choice. |
| `OpenDecisionReference` | Point to unresolved decisions. | Must remain blocked until accepted elsewhere. | Treating the reference as acceptance. |
| `FutureImplementationPrerequisiteChecklist` | List future prerequisites. | Checklist only, not approval. | Skipping verification of missing gates. |
| `SyntheticScenarioDescriptionMarkdownOnly` | Describe synthetic cases in markdown only. | No executable fixtures or code. | Becoming executable fixtures or tests. |
| `StaticBoundaryRequirementDescription` | Describe static boundary checks as future work. | No test creation in this task. | Becoming a test implementation. |
| `PublicContractReference` | Reference public contracts as source facts. | Reference only, no contract mutation. | Editing or expanding the contract here. |
| `CrossModuleOwnershipReference` | Name the owning module. | Ownership reference only. | Using ownership as authorization. |
| `NoRuntimeAuthorizationStatement` | State that runtime is not authorized. | Documentation statement only. | Reversing into runtime approval. |
| `NoPhysicalSchemaAuthorizationStatement` | State that physical schema is not authorized. | Documentation statement only. | Reversing into schema approval. |

## 13. Forbidden assumptions

- PostgreSQL tables, SQLAlchemy models, Psycopg usage or Alembic migrations are authorized by this document.
- Scheduler runtime, polling loop, due-slot identity, interval values or missed-scan mechanics are authorized by this document.
- Worker runtime, worker concurrency, worker fairness or worker dispatch mechanics are authorized by this document.
- Claim lease duration, heartbeat, renewal, physical locks, transactions, conflict rows or stale-claim handling are authorized by this document.
- Retry/backoff/circuit-breaker policy is authorized by this document.
- Queue, broker, Redis, RabbitMQ, Celery or cache usage is authorized by this document.
- Parser calls, live Avito calls, Egress route calls or notification delivery are Scan-owned runtime concerns.
- Notification outbox, delivery attempts, delivery retries or provider-success claims are Scan-owned runtime concerns.
- Read-model rebuild, retention, deletion or compaction policy is resolved here.
- Any numeric default is introduced for interval, due slot, claim lease, heartbeat, retry/backoff, retention, deletion, compaction, page depth, queue visibility timeout, worker concurrency or fairness.
- Semantic docs-only classes imply implementation permission.
- Semantic documentation allows executable fakes, fixture files or tests in this task.
- Synthetic deterministic fakes may be allowed only by a future exact task; this SOLS-13 task must not create executable fakes or fixture files.
- Scan may define what remains gated, but must not choose the implementation.
- OD-013 is closed by assumption.
- docs-only boundary references may be used as a substitute for accepted future gate decisions.

## 14. Open decisions that remain open

Open means blocked.

- physical schema and table ownership;
- migration strategy;
- transaction, lock and claim strategy;
- scheduler clock and time policy;
- scan interval and due-slot policy;
- worker concurrency and fairness policy;
- claim lease, heartbeat and renewal policy;
- retry, backoff and circuit-breaker policy;
- queue, broker and cache decision;
- Parser Adapter accepted implementation contract;
- Egress Routing accepted implementation contract;
- Notification Delivery accepted implementation contract;
- retention, compaction and deletion policy and OD-013 resolution;
- read-model rebuild policy;
- runtime service and deploy policy;
- architecture and static tests permission;
- synthetic executable fake and fixture permission.

## 15. Cross-module ownership boundary

- Scan owns docs-only semantic gate documentation and no runtime authorization.
- Parser Adapter owns parser-call behavior, parser compatibility and provider-response mapping.
- Egress owns route calls, route mechanics and route-specific runtime decisions.
- Notification Delivery owns outbox, delivery attempts, provider retries and provider-success claims.
- Persistence/runtime owners own physical schema, ORM mapping, database client usage and migrations.
- Scheduler and worker runtime owners own actual polling, due-work dispatch, concurrency and fairness.
- No other module may infer Scan runtime permission from this document.

## 16. Semantic gate classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed current effect | Forbidden false outcome |
|---|---|---|---|---|
| `PERSISTENCE_IMPLEMENTATION_BLOCKED` | Durable persistence implementation remains blocked. | SOLS-13 gate summary, module playbook, physical schema gate reference. | Keep persistence unresolved in docs. | Treating docs as DB authorization. |
| `PHYSICAL_SCHEMA_GATE_REQUIRED` | Physical schema gate must be accepted first. | Physical schema/migration gate decision, module playbook. | Keep schema decisions external. | Creating tables or models now. |
| `MIGRATION_GATE_REQUIRED` | Migration gate must be accepted first. | Physical schema/migration gate decision, module playbook. | Keep migrations unresolved. | Authoring Alembic work now. |
| `SCHEDULER_RUNTIME_BLOCKED` | Scheduler runtime is blocked. | Scheduler/time policy gate, module playbook. | Keep scheduler runtime unresolved. | Starting a polling loop now. |
| `DUE_SLOT_POLICY_UNRESOLVED` | Due-slot identity policy is unresolved. | Scheduler/time policy gate, module playbook. | Keep due-slot semantics unresolved. | Fixing due-slot identity by assumption. |
| `SCAN_INTERVAL_POLICY_UNRESOLVED` | Scan interval policy is unresolved. | Scheduler/time policy gate, module playbook. | Keep interval values unresolved. | Introducing a default interval. |
| `WORKER_RUNTIME_BLOCKED` | Worker runtime is blocked. | Worker gate, module playbook. | Keep worker runtime unresolved. | Starting worker dispatch now. |
| `WORKER_CONCURRENCY_POLICY_UNRESOLVED` | Worker concurrency policy is unresolved. | Worker gate, module playbook. | Keep concurrency unresolved. | Choosing a concurrency default. |
| `CLAIM_LEASE_POLICY_UNRESOLVED` | Claim lease policy is unresolved. | Claim/concurrency gate, module playbook. | Keep lease duration unresolved. | Introducing a lease duration default. |
| `CLAIM_HEARTBEAT_POLICY_UNRESOLVED` | Claim heartbeat policy is unresolved. | Claim/concurrency gate, module playbook. | Keep heartbeat unresolved. | Introducing a heartbeat default. |
| `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` | Lock and transaction gate must be accepted first. | Claim/concurrency gate, module playbook. | Keep locks and transactions unresolved. | Treating lock/transaction choice as approved. |
| `RETRY_BACKOFF_POLICY_UNRESOLVED` | Retry/backoff policy is unresolved. | Retry policy gate, module playbook. | Keep retry policy unresolved. | Introducing retry defaults. |
| `CIRCUIT_BREAKER_POLICY_UNRESOLVED` | Circuit breaker policy is unresolved. | Retry policy gate, module playbook. | Keep circuit breaker unresolved. | Treating circuit breaker choice as fixed. |
| `QUEUE_BROKER_CACHE_BLOCKED` | Queue/broker/cache dispatch is blocked. | Queue/broker/cache gate, module playbook. | Keep dispatch infra unresolved. | Choosing Redis, RabbitMQ, Celery or equivalent now. |
| `PARSER_CALLS_NOT_SCAN_OWNED` | Parser calls are not Scan-owned. | Parser Adapter ownership boundary, module playbook. | Keep parser runtime outside Scan. | Scan calling parser internals directly. |
| `EGRESS_ROUTE_CALLS_NOT_SCAN_OWNED` | Egress route calls are not Scan-owned. | Egress ownership boundary, module playbook. | Keep route calls outside Scan. | Scan owning route mechanics. |
| `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` | Notification outbox is not Scan-owned. | Notification Delivery ownership boundary, module playbook. | Keep outbox state outside Scan. | Scan owning delivery state. |
| `READ_MODEL_REBUILD_JOB_BLOCKED` | Read-model rebuild job is blocked. | Read-model rebuild policy gate, module playbook. | Keep rebuild job unresolved. | Creating a rebuild job now. |
| `RETENTION_JOB_GATED_BY_OD_013` | Retention job is gated by OD-013. | OD-013 open status, module playbook. | Keep retention unresolved. | Selecting retention duration now. |
| `DELETION_JOB_GATED_BY_OD_013` | Deletion job is gated by OD-013. | OD-013 open status, module playbook. | Keep deletion unresolved. | Selecting deletion cadence now. |
| `COMPACTION_JOB_GATED_BY_OD_013` | Compaction job is gated by OD-013. | OD-013 open status, module playbook. | Keep compaction unresolved. | Selecting compaction algorithm now. |
| `RUNTIME_SERVICE_BLOCKED` | Runtime service implementation is blocked. | Runtime service/deploy gate, module playbook. | Keep runtime service unresolved. | Shipping a runtime service by inference. |
| `DOCKER_DEPLOY_BLOCKED` | Docker/deploy implementation is blocked. | Runtime service/deploy gate, module playbook. | Keep deploy artifacts unresolved. | Shipping deploy artifacts by inference. |
| `SEMANTIC_DOCS_ONLY_ALLOWED` | Only semantic docs are allowed here. | SOLS-13 docs-only boundary, module playbook. | Keep output in markdown documentation. | Creating runtime artifacts or code. |
| `SYNTHETIC_MARKDOWN_ONLY_ALLOWED` | Synthetic cases may be described only in markdown. | Synthetic-example gate, module playbook. | Keep examples non-executable. | Creating executable fixtures or code. |
| `ARCHITECTURE_STATIC_CHECKS_FUTURE_TASK_ONLY` | Static boundary checks belong to a future exact task. | Future test gate, module playbook. | Keep tests out of this task. | Writing tests now. |
| `NO_NUMERIC_DEFAULT_ALLOWED` | No numeric defaults may be introduced. | SOLS-13 numeric-default prohibition, module playbook. | Keep values unresolved. | Adding a default interval or concurrency. |

## 17. Synthetic gate examples

All examples below are markdown-only synthetic descriptions.

| Example | Synthetic setup | Expected classification | Expected safe current effect | Future gate required | Forbidden false outcome |
|---|---|---|---|---|---|
| `EX-SOLS-13-POSTGRES-TABLE-GATED-001` | A reviewer asks whether a PostgreSQL table may be created for Scan persistence. | `PERSISTENCE_IMPLEMENTATION_BLOCKED` | Keep the table decision unresolved in docs only. | Physical schema and migration gate. | Treating the docs as table authorization. |
| `EX-SOLS-13-SQLALCHEMY-MODEL-GATED-001` | A reviewer asks whether an ORM model may be declared. | `PHYSICAL_SCHEMA_GATE_REQUIRED` | Keep ORM shape unresolved. | Physical schema and migration gate. | Creating a model from semantic docs. |
| `EX-SOLS-13-ALEMBIC-MIGRATION-GATED-001` | A reviewer asks whether a migration may be written. | `MIGRATION_GATE_REQUIRED` | Keep migration strategy unresolved. | Physical schema and migration gate. | Treating docs as migration approval. |
| `EX-SOLS-13-SCHEDULER-RUNTIME-GATED-001` | A reviewer asks whether the scheduler runtime may be implemented. | `SCHEDULER_RUNTIME_BLOCKED` | Keep scheduler runtime blocked. | Scheduler/time policy gate. | Starting a polling loop now. |
| `EX-SOLS-13-DUE-SLOT-POLICY-UNRESOLVED-001` | A reviewer asks what due-slot identity should be. | `DUE_SLOT_POLICY_UNRESOLVED` | Keep due-slot identity unresolved. | Scheduler/time policy gate. | Picking a due-slot rule by assumption. |
| `EX-SOLS-13-SCAN-INTERVAL-NO-NUMERIC-DEFAULT-001` | A reviewer asks for a default scan interval. | `NO_NUMERIC_DEFAULT_ALLOWED` | Keep interval values unresolved. | Scheduler/time policy gate. | Introducing a numeric interval default. |
| `EX-SOLS-13-WORKER-RUNTIME-GATED-001` | A reviewer asks whether worker runtime may be deployed. | `WORKER_RUNTIME_BLOCKED` | Keep worker runtime blocked. | Worker gate. | Assuming a worker process is allowed. |
| `EX-SOLS-13-WORKER-CONCURRENCY-UNRESOLVED-001` | A reviewer asks how many workers should run in parallel. | `WORKER_CONCURRENCY_POLICY_UNRESOLVED` | Keep concurrency unresolved. | Worker gate. | Introducing a concurrency default. |
| `EX-SOLS-13-CLAIM-LEASE-NO-DURATION-001` | A reviewer asks for a claim lease duration. | `CLAIM_LEASE_POLICY_UNRESOLVED` | Keep lease duration unresolved. | Claim/concurrency implementation gate. | Setting a lease by assumption. |
| `EX-SOLS-13-CLAIM-HEARTBEAT-NO-NUMERIC-DEFAULT-001` | A reviewer asks for a heartbeat interval default. | `CLAIM_HEARTBEAT_POLICY_UNRESOLVED` | Keep heartbeat unresolved. | Claim/concurrency implementation gate. | Adding a heartbeat numeric default. |
| `EX-SOLS-13-PHYSICAL-LOCK-TRANSACTION-GATED-001` | A reviewer asks whether a physical lock and transaction boundary may be selected. | `PHYSICAL_LOCK_TRANSACTION_GATE_REQUIRED` | Keep lock and transaction design unresolved. | Claim/concurrency implementation gate. | Using docs as lock/transaction approval. |
| `EX-SOLS-13-RETRY-BACKOFF-NO-POLICY-001` | A reviewer asks for a retry/backoff policy. | `RETRY_BACKOFF_POLICY_UNRESOLVED` | Keep retry policy unresolved. | Retry policy gate. | Choosing a retry curve by default. |
| `EX-SOLS-13-CIRCUIT-BREAKER-NO-POLICY-001` | A reviewer asks for circuit-breaker behavior. | `CIRCUIT_BREAKER_POLICY_UNRESOLVED` | Keep circuit-breaker policy unresolved. | Retry policy gate. | Treating circuit-breaker behavior as fixed. |
| `EX-SOLS-13-QUEUE-BROKER-CACHE-GATED-001` | A reviewer asks whether queue or cache infrastructure may be selected. | `QUEUE_BROKER_CACHE_BLOCKED` | Keep dispatch infra blocked. | Queue/broker/cache gate. | Selecting Redis, RabbitMQ, Celery or equivalent now. |
| `EX-SOLS-13-PARSER-CALL-NOT-SCAN-OWNED-001` | A reviewer asks whether Scan may call the parser directly. | `PARSER_CALLS_NOT_SCAN_OWNED` | Keep parser calls outside Scan. | Parser Adapter accepted implementation contract. | Treating ownership as runtime permission. |
| `EX-SOLS-13-EGRESS-ROUTE-CALL-NOT-SCAN-OWNED-001` | A reviewer asks whether Scan may call Egress routes directly. | `EGRESS_ROUTE_CALLS_NOT_SCAN_OWNED` | Keep route calls outside Scan. | Egress Routing accepted implementation contract. | Treating ownership as direct call permission. |
| `EX-SOLS-13-NOTIFICATION-OUTBOX-NOT-SCAN-OWNED-001` | A reviewer asks whether Scan may own notification outbox state. | `NOTIFICATION_OUTBOX_NOT_SCAN_OWNED` | Keep outbox state outside Scan. | Notification Delivery accepted implementation contract. | Treating notification ownership as Scan-owned runtime. |
| `EX-SOLS-13-READ-MODEL-REBUILD-GATED-001` | A reviewer asks whether a read-model rebuild job may be implemented. | `READ_MODEL_REBUILD_JOB_BLOCKED` | Keep rebuild job blocked. | Read-model rebuild policy gate. | Creating a rebuild job from docs. |
| `EX-SOLS-13-RETENTION-DELETION-COMPACTION-GATED-OD-013-001` | A reviewer asks whether retention, deletion and compaction jobs may be chosen now. | `RETENTION_JOB_GATED_BY_OD_013` | Keep retention/deletion/compaction unresolved. | OD-013 and DB/runtime gates. | Closing OD-013 by assumption. |
| `EX-SOLS-13-DOCS-ONLY-DOES-NOT-AUTHORIZE-RUNTIME-001` | A reviewer treats semantic docs as runtime approval. | `SEMANTIC_DOCS_ONLY_ALLOWED` | Keep the effect limited to markdown documentation. | Exact future implementation gate. | Inferring runtime authorization from documentation. |

## 18. Future implementation prerequisite checklist

Before any implementation task, ChatGPT must verify exact accepted gates for:

- [ ] physical schema/table ownership;
- [ ] migration strategy;
- [ ] transaction/lock/claim strategy;
- [ ] scheduler clock/time policy;
- [ ] scan interval/due-slot policy;
- [ ] worker concurrency/fairness policy;
- [ ] claim lease/heartbeat/renewal policy;
- [ ] retry/backoff/circuit-breaker policy;
- [ ] queue/broker/cache decision;
- [ ] Parser Adapter accepted implementation contract;
- [ ] Egress Routing accepted implementation contract;
- [ ] Notification Delivery accepted implementation contract;
- [ ] retention/compaction/deletion policy and OD-013 resolution;
- [ ] read-model rebuild policy;
- [ ] runtime service/deploy policy;
- [ ] architecture/static tests permission;
- [ ] synthetic executable fake/fixture permission.

If any prerequisite is missing, the implementation task is blocked.
