# Transaction and Outbox Boundaries

Version: 1.0
Status: RF-04_ACTIVE_SECOND_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE
Date: 2026-07-23
Module: 14-runtime-foundation-and-autonomous-integration
Roadmap step: RF-04
Technical-ID: RF-04-02-TRANSACTION-AND-OUTBOX-BOUNDARIES-20260723
Source branch: main
Source base SHA: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
RF-04-01 accepted chain head: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
Runtime mutation: none
Production verdict: NOT_CLAIMED
Final target: READY_FOR_OPERATOR_ACCEPTANCE

## 1. Authority and scope

GitHub `main` is the sole source of truth. This is the second RF-04 repository artifact and a documentation/design-only boundary for the accepted physical data model. PostgreSQL 18 is the authoritative persistence target. Modules 01–13 retain authoritative domain state; Module 14 owns runtime assembly design only. Physical table names and ownership are immutable inputs from `PHYSICAL_DATA_MODEL_v1.0.md`.

This document defines commit, claim, lease, retry, reconciliation, restart, failure and concurrency boundaries. It does not implement them. Every cross-module mutation is made through the owning public application service or contract. A foreign key is a reference, never write authority. No distributed transaction, external broker, live provider call or production/public launch is part of this scope. Optional provider credentials may be absent; that state is `PROVIDER_DISABLED_CONTINUE`.

## 2. Transaction design principles

- PostgreSQL 18 is authoritative persistence; process memory, browser state, provider state and an in-memory queue are not authority.
- The normal application isolation baseline is PostgreSQL `READ COMMITTED`.
- Validation and authorization precede mutation. A transaction is short and is never held during a provider or network call.
- Mutable commits use an expected `row_version` or an equivalent guarded predicate. A stale version fails closed and is retried only by an explicit workflow.
- Claims use bounded batches and deterministic ordering. Claimable rows use `FOR UPDATE SKIP LOCKED` or an exact PostgreSQL atomic equivalent.
- The claim transaction commits before long work begins. Work ownership is a durable lease, not a Python handle.
- A lease commit requires the matching unique `lease_token` and an unexpired lease. A lost or expired lease cannot commit terminal effects.
- Retry scheduling is a separate committed transition with bounded persisted backoff. It is never an implicit loop.
- Crash before commit has no durable effect. Crash after commit recovers from durable state and the relevant outbox.
- Cross-module atomicity is not assumed. A local ACID transaction covers one owning boundary and accepted Platform primitives only.
- No module directly mutates a foreign authoritative table. No FastAPI background task is durable work. There is no Redis, Celery, RabbitMQ, Kafka or other broker.
- A possibly completed external effect is never blindly retried. Provider acceptance is not proof of human reading.

## 3. Isolation, locking and concurrency baseline

Every due-work query orders by deterministic UTC `due_at`, then stable identifier. Claim batches are bounded, lock only eligible rows, use `FOR UPDATE SKIP LOCKED`, update ownership and commit promptly. Unique constraints remain the final race protection even when an advisory lock or row lock is used.

The idempotency serializer may use a transaction-scoped PostgreSQL advisory lock over a deterministic digest of normalized `(scope, key)`. A hash collision only serializes unrelated operations; it cannot corrupt correctness because uniqueness and fingerprint checks remain authoritative. The lock lasts only for the transaction, does not replace uniqueness constraints, does not log the sensitive raw key and is never held over a provider/network call.

All compare-and-set updates guard the expected `row_version`. Lease transitions additionally guard `lease_token` and PostgreSQL UTC time. Provider clocks are not authoritative. Correctness never depends on process memory. Retry and backoff are bounded and persisted. Graceful shutdown stops new claims; active work either completes a guarded commit or abandons/lets its lease expire safely.

## 4. Module transaction-boundary catalogue

The following matrix has exactly one row for each canonical module 01–13. “Table” means an accepted physical table only; no table is added by this design.

| Module | Owning command/work boundary | Authoritative tables | Rows read/locked | Rows inserted/updated | Public service/contract boundary | Idempotency boundary | Outbox/event boundary | Commit point | Concurrency guard | Retry/reconciliation behavior | Forbidden foreign write |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 Platform and Contracts | Platform command, audit command, event publisher and durable primitive | `platform_idempotency_records`; `platform_audit_entries`; `platform_event_outbox` | Same-scope idempotency record; owned audit/outbox rows | Idempotency result, audit entry and platform event | Platform primitive contracts | normalized `(scope,key,fingerprint)` | owning mutation plus platform event in one local transaction | guarded final idempotency result and outbox insert commit | advisory serialization, unique fingerprints, row version | publisher claims and retries internal delivery; retention cleanup; no provider call | any module’s domain state |
| 02 Identity and Access | Account, identity-link, authorization and session command | Identity-owned accepted tables | authorized account/link rows | owning identity state only | Identity public service/contract | command key and provider reference fingerprint | platform audit/event through Platform | identity mutation plus applicable platform event commit | authorization, expected version, unique provider reference | stale command fails closed; reconciliation is explicit Identity work | Beacon, billing, scan, notification or adapter tables |
| 03 Entitlements and Billing | tariff/access, usage, payment intent and reconciliation command | `entitlement_tariff_definitions`; `entitlement_access_grants`; `entitlement_usage_counters`; `billing_payment_records`; `billing_payment_operations`; `billing_reconciliations` | account, grant and counter rows; payment operation/reconciliation rows | owned entitlement/payment/reconciliation state | Entitlements/Billing public commands | payment operation key and evidence fingerprint | Platform event for committed domain result | payment intent or independent grant decision commit | expected versions, unique operation/evidence keys | unknown payment is reconcile-first; evidence never silently grants access | Identity or provider tables |
| 04 Beacon Management | Beacon create/update, revision and lifecycle command | `beacon_beacons`; `beacon_configuration_revisions`; `beacon_filter_overrides`; `beacon_lifecycle_events` | beacon aggregate, revision and lifecycle rows | beacon aggregate, immutable revision, override and lifecycle rows | Beacon public command/revision contract | command key plus beacon/revision fingerprint | Platform event after Beacon commit | revision and lifecycle mutation commit | aggregate version and immutable revision identity | stale revision fails closed; retry re-reads current revision | Scan, Filter Catalog or Notification tables |
| 05 Avito Parser Adapter | Parser invocation and normalized outcome persistence | `parser_outcomes` | pinned parser outcome/work context | normalized outcome only | Parser result contract | work/run/attempt fingerprint | result is published to Scan through accepted contract | outcome row commit | expected run/work version and unique outcome identity | explicit failure, restriction and CAPTCHA outcomes; no empty-success conversion | Scan result or Egress tables |
| 06 Scan Orchestration and Listing State | schedule, work item, run, observation, anchor and result command | `scan_schedules`; `scan_work_items`; `scan_runs`; `scan_listing_observations`; `scan_beacon_listing_state`; `scan_anchors` | due schedule/work, pinned revision, run, listing state and anchor rows | schedule/work/run/observation/state/anchor rows | Scan public scheduling/result contract | `(schedule_id,due_at)`, work identity and result fingerprint | committed newly-observed event through Platform; Scan never writes Notification | guarded result commit joins observations, state, anchor, terminal run and owning platform event | bounded claim lease, route lease, row version, unique listing identity | route/parser failure is explicit; incomplete scan does not advance anchor; retry/reconcile is persisted | Notification tables, parser internals or Egress ownership |
| 07 Egress Routing | route selection, lease acquire/renew/release/expire command | `egress_agents`; `egress_routes`; `egress_agent_heartbeats`; `egress_route_leases` | project-owned eligible routes, agent heartbeat and lease rows | lease and heartbeat state | Egress lease/session contract | work/run/route lease identity | lease state may produce internal platform evidence; no provider payload | lease transition commit before route use | unique lease token, expected version, expiry guard | route failure becomes explicit failure; expired leases reconcile/expire | foreign proxy, Scan or Parser tables |
| 08 Notification Delivery | source-event consume, fan-out, claim, attempt, result and reconciliation command | `notification_endpoints`; `notification_events`; `notification_outbox`; `notification_delivery_attempts`; `notification_delivery_reconciliations` | source fingerprint, endpoint/outbox, attempt and reconciliation rows | one event, endpoint outbox, immutable attempt and reconciliation state | Notification generic event/delivery contract | source fingerprint, `(event_id,endpoint_id)`, `(outbox_id,attempt_number)` | owns `notification_outbox`; consumes committed source event; does not own Platform outbox | each lifecycle transition commits separately; provider call is outside transaction | lease token, row version and unique identities | definite result commits; ambiguous result reconciles before resend | Telegram/MAX/Web or Scan tables |
| 09 Telegram Adapter | inbound validation/normalization and outbound adapter command | `telegram_inbound_updates`; `telegram_identity_mappings`; `telegram_delivery_mappings` | normalized provider reference, Identity link and Notification attempt | provider references/mapping only | Telegram adapter and Identity/Notification public boundaries | provider update ID plus fingerprint; delivery attempt reference | normalized inbound publication after explicit commit | normalized event or mapping commit | unique provider references and guarded mapping | disabled provider is explicit; outbound ambiguity returns adapter result for Notification reconciliation | Account creation/merge, generic event success or provider payload tables |
| 10 MAX Adapter | inbound validation/normalization, nonce consume and outbound adapter command | `max_inbound_events`; `max_identity_mappings`; `max_delivery_mappings`; `max_miniapp_nonces` | event/reference, Identity link, attempt and nonce rows | normalized event/mapping and hash-only nonce state | MAX adapter and Identity/Notification public boundaries | event ID/fingerprint and one-time nonce identity | normalized event publication after commit | consume/insert transition commit | unique event, attempt mapping and expiry/consume predicate | ambiguous outbound is reconcile-first; missing credential remains disabled | Account merge, generic success or raw MAX payload |
| 11 Admin and Support | authorized admin mutation, case command and audited note/event command | `support_cases`; `support_case_notes`; `support_case_events` plus the owning module’s public command | case and authorized owner projection rows | support case/note/event rows; owning module changes only via service | Admin/Support public commands | actor/command/reason fingerprint | audit/platform event in same owning local transaction | authorized mutation plus audit/event commit | actor authorization, expected version, idempotency | stale command fails closed; operator reconciliation is explicit | direct mutation of any foreign authoritative table |
| 12 Web Cabinet | request projection and command delegation | zero authoritative tables | read projections through owning public services | no authoritative rows; commands delegated | Web/public application service boundary | request idempotency at owning command | consumes projections/events; does not own an outbox | response follows owner’s committed result | owner guards all mutations | browser retry repeats owner command safely; browser/client state is never authority | any domain table or direct Notification/Beacon mutation |
| 13 Filter Catalog and Builder | catalog publication, validation and candidate read command | `filter_catalog_versions`; `filter_definitions`; `filter_options`; `filter_dependencies`; `filter_category_applicability`; `filter_evidence_references`; `filter_capability_profiles` | immutable active version and catalog rows | versioned catalog rows only | Filter Catalog public validation/candidate contract | version/fingerprint of immutable catalog input | Platform event for accepted catalog publication | immutable version activation commit | unique version/key and guarded active-version transition | invalid candidate fails closed; catalog publication is immutable and replay-safe | Beacon configuration, Scan or provider tables |

## 5. Idempotency protocol

For an idempotent owning command, the exact algorithm is:

1. Normalize scope, key and request fingerprint using canonical encoding and bounded length.
2. Authorize the actor and target before any mutation.
3. Serialize concurrent processing of the same `(scope,key)` with a transaction-scoped PostgreSQL advisory lock keyed by deterministic digest, or an exact PostgreSQL transaction-scoped equivalent.
4. Load the existing `platform_idempotency_records` row under the normal `READ COMMITTED` transaction.
5. A same key with the same fingerprint returns the stored committed result.
6. A same key with a different fingerprint fails closed with a conflict; it never reuses the stored result.
7. An absent record allows one owning mutation.
8. The mutation, applicable audit, `platform_event_outbox` insertion and final idempotency result commit atomically.
9. Rollback removes every uncommitted effect.
10. Return the response reconstructed from the committed result, never from an uncommitted in-memory result.

No unaccepted in-progress table or state is invented. The advisory digest is only a serializer: collisions serialize unrelated operations but cannot corrupt correctness; uniqueness and fingerprint checks remain authoritative. The lock is transaction-only and is released before any provider/network call. Sensitive raw keys are not logged. A committed result is the only replay source.

## 6. Platform event outbox protocol

The owning domain mutation and insertion into `platform_event_outbox` share one local transaction through the accepted Platform primitive. The event uses a normalized, versioned and bounded payload, a stable `event_fingerprint`, correlation and causation IDs, and explicit producer ownership. The fingerprint supplies duplicate protection; it does not replace database uniqueness.

A publisher claims bounded rows in deterministic order with a short transaction. Claim state commits before dispatch. Internal consumers are idempotent. Terminal transition is guarded by the matching lease token and expected row version. A crash after dispatch and before acknowledgement may duplicate internal delivery, but cannot lose the committed event. The publisher performs no provider call. Cleanup follows accepted retention and never removes an event needed by an active reconciliation window.

`platform_event_outbox` is an internal platform/domain event journal. `notification_outbox` is Notification’s endpoint-specific delivery work. They have different owners, identities, leases, retry and retention lifecycles; one must not be used as a substitute for the other.

## 7. Scan scheduling, work claim and result commit protocol

Scan uses separate short transactions for each boundary:

1. Due-work creation reads one durable schedule per Beacon and inserts a work item guarded by `(schedule_id,due_at)` duplicate protection.
2. Work claim locks a bounded deterministic batch with `FOR UPDATE SKIP LOCKED`, assigns a unique lease token and commits before work starts.
3. Run start creates exactly one run per work item, pins the exact Beacon configuration revision and commits.
4. Route lease acquisition is an independent Egress command and commit; no database transaction remains open while the route is used.
5. Parser outcome persistence commits the normalized `parser_outcomes` result and explicit result class.
6. Scan result commit is guarded by work/run/route lease tokens and row versions. It commits observation, Beacon-isolated listing state, anchor and terminal run state together with the owning platform event where applicable.
7. Platform event insertion is the accepted Platform primitive boundary, within the owning local commit described above.
8. Retry or reconciliation transition is a separate committed transition; no blind retry follows an ambiguous effect.

Invariants:

- There is one durable schedule per Beacon, and `(schedule_id,due_at)` prevents duplicate due work.
- There is one run per work item, with an exact Beacon revision pinned at run start.
- The first baseline emits no notification. Only newly observed listings create a generic notification source effect. Price change alone creates no notification.
- Repeated result commit is idempotent. Listing state is Beacon-isolated.
- Route failure is never parser success. CAPTCHA, restriction and incomplete/unknown outcomes never become empty success.
- A stale version or lost lease cannot commit. Observation, listing state, anchor, run terminal state and the owning platform event have an explicit commit boundary.
- Scan never writes Notification tables directly. Notification consumes the committed event idempotently.

## 8. Egress route lease protocol

Only project-owned routes are eligible. Candidate selection is deterministic and bounded by project, capability, health and lease availability. One bounded lease is acquired per work item. Acquire, renew, release and expire are separate guarded transitions. Every lease has a unique `lease_token`, owner identity and PostgreSQL UTC expiry.

The lease commits before the route is used, and no database transaction is held during route use. No foreign proxy fallback is allowed and no secret is persisted. A route failure is an explicit result class. An expired or lost lease invalidates result commit. Simulator and live-agent semantics remain separate; a missing Windows host is not a blocker for the design. Renewal and release require matching token and unexpired/owned state; expiry is safe to reconcile after restart.

## 9. Notification event, outbox and delivery protocol

Notification has separate transactions for: (1) consuming a committed source event and creating `notification_events`; (2) fanning out one `notification_outbox` row per endpoint; (3) claiming delivery; (4) creating an immutable delivery attempt; (5) invoking an adapter outside the database transaction; (6) committing a definite result; (7) creating a reconciliation row for an ambiguous effect; and (8) retrying only after reconciliation permits it.

`source_effect_fingerprint` prevents duplicate generic events. `(event_id,endpoint_id)` prevents duplicate fan-out. `(outbox_id,attempt_number)` prevents duplicate attempt numbers. One source effect creates one generic effect. Notification owns the delivery lifecycle; Telegram and MAX do not mark generic business success directly. Provider acceptance is not proof of human reading.

Timeout or disconnect after possible transmission is ambiguous. It creates or updates a reconciliation record and cannot be resent until reconciliation explicitly permits resend. Definite rejection is terminal or persistently retryable according to the normalized result contract. There is no database transaction over a provider call. Terminal transitions require the matching lease token and row version. Web presentation cannot bypass Notification ownership.

## 10. Billing external-effect and reconciliation protocol

Payment evidence is separate from entitlement grant. A payment record alone never grants access. Payment operation intent commits before the provider call, which occurs outside the database transaction. A definite response persists normalized evidence only; raw payment payload is not persisted. A timeout or disconnect after possible transmission is an unknown effect and creates or updates `billing_reconciliations`. No retry occurs before reconciliation resolves the effect.

Accepted normalized billing evidence invokes a separate Entitlements command. Entitlements independently evaluates and commits the grant. Recurring billing, trial, grace and proration remain disabled in this scope. Missing credentials disable only the provider (`PROVIDER_DISABLED_CONTINUE`); they do not block core design. Reconciliation owns unknown-effect resolution, records safe provider references/evidence and never converts uncertainty into access without the independent entitlement decision.

## 11. Telegram and MAX adapter transaction protocol

Inbound validation precedes normalization. Deduplication uses provider event/update ID plus fingerprint. Raw payload, token and cookie are not persisted. Normalized event insertion and internal event publication have an explicit commit boundary. Adapters call the Identity public boundary; they cannot directly create or merge an account, and automatic merge is forbidden. Adapter-owned identity mappings reference the Identity link. Delivery mappings reference the generic Notification attempt. Only normalized provider references and bounded evidence persist.

An ambiguous outbound effect returns an explicit ambiguous result to Notification; the adapter does not mark generic Notification success. A MAX nonce is hash-only, one-time and guarded by expiry and consume predicates. A missing credential yields disabled provider readiness, not a core blocker. Provider acceptance remains different from human-read proof.

## 12. Cross-module orchestration and atomicity boundary

Local ACID is limited to one owner boundary plus accepted Platform primitives. There is no distributed transaction and no two-phase commit. No module mutates shared foreign tables. A cross-module flow uses committed public commands, results and events; downstream consumers are idempotent. Compensation is an explicit command owned by the module that owns the compensating state. Partial progress is durable, visible and recoverable.

Event lineage carries correlation and causation IDs plus operation/work/run/attempt identity. Platform and Notification outboxes have different owners and lifecycles. UI and provider adapters are integration boundaries, not domain owners. A successful local commit never implies an atomic downstream commit; the durable event or reconciliation path is the recovery boundary.

## 13. Failure, restart, cancellation and shutdown matrix

| Failure point | Committed durable state | Ambiguous effect | Safe automatic action | Prohibited action | Reconciliation owner | Operator visibility |
|---|---|---|---|---|---|---|
| before transaction begins | none | no | return validation/availability result | claiming success | initiating owner | structured failed operation |
| during validation | none | no | rollback and return normalized validation failure | mutate after failed authorization | owning module | safe reason code |
| owning mutation before commit | none | no | rollback | emit event or retry external effect | owning module | transaction error |
| mutation after changes but before outbox insertion | none after rollback | no | rollback whole local transaction | commit mutation without event | owning module | rollback metric |
| outbox insertion before commit | none after rollback | no | rollback and retry local command if safe | publish uncommitted event | Platform/owner | transaction error |
| commit before response | committed result/event | no | replay committed idempotency result | repeat mutation blindly | owner | correlation-linked result |
| work claim commit before work start | claimed lease/work | no | resume or let lease expire and requeue | duplicate unguarded work | Scan/Egress | work lease age |
| lease expiry during work | prior state only | no | abandon result; expire/requeue safely | commit with expired token | Egress plus Scan | lease-expiry event |
| worker crash after provider request before response | intent/attempt committed | yes | create reconciliation; do not resend | blind retry | Billing or Notification owner | ambiguous-effect alert |
| definite provider rejection | normalized rejection | no | commit terminal/retryable rejection | treat as acceptance | owning integration owner | provider result class |
| provider timeout/disconnect after possible transmission | intent/attempt committed | yes | reconcile before resend | blind retry | Billing/Notification | reconciliation backlog |
| crash after provider acceptance before generic acknowledgement | provider attempt state may be committed | yes | reconcile and query safe reference | mark human read or resend blindly | Notification | attempt/reconciliation state |
| crash after generic acknowledgement | committed generic result | no | idempotently continue downstream | create second generic source effect | Notification | committed lineage |
| scheduler restart | schedules and committed work | no | recreate only missing due work under uniqueness guard | rely on memory queue | Scan | due-work lag |
| worker graceful shutdown | committed claim/lease | no | stop claims; finish or abandon guarded work | start new claims during drain | Scan/Egress | drain/lease metrics |
| DB connection loss | last committed transaction only | no unless provider call was active | reconnect and replay safe command or reconcile | assume commit from client timeout | owning boundary | DB error/correlation |
| stale row version | prior committed row | no | fail closed; re-read and explicit retry | overwrite current state | row owner | conflict counter |
| same key/same fingerprint | stored committed result | no | return stored result | execute mutation again | Platform | idempotency hit |
| same key/different fingerprint | original result unchanged | no | return conflict | replace or merge result | Platform | security/audit event |
| duplicate internal event | first consumer effect | no | acknowledge idempotently | duplicate domain mutation | consuming owner | duplicate metric |
| duplicate listing observation | existing observation/state | no | no-op under unique identity | emit second new-listing effect | Scan | dedup metric |
| duplicate notification fan-out | existing endpoint outbox | no | unique guard/no-op | create second endpoint row | Notification | fan-out dedup metric |
| reconciliation retry | durable unknown/reconciliation row | yes until definite | retry only when reconciliation permits | blind resend | Billing/Notification | aged ambiguity alert |

## 14. Security, privacy, retention and observability

No secret, raw provider payload, HTML, cookie, token or populated environment value is persisted. Persist only bounded normalized JSON and safe normalized evidence. Synthetic data is the acceptance dataset. Authorization is checked before mutation. Admin changes carry actor, reason and audit evidence. Logs are structured and redacted: environment, source SHA, module, operation, correlation ID, causation ID, run/work/attempt IDs, normalized result and latency are allowed; raw idempotency keys and provider payloads are not. Hashes/fingerprints are logged only when accepted and non-sensitive.

Retention follows owner decisions for audit, events, attempts, reconciliation, observations and normalized evidence. Telemetry failure does not alter the business commit. Provider acceptance is not a human-read proof. Reconciliation backlog, lease age, stale-version conflicts, retry age and duplicate rates are observable without exposing credentials or personal data.

## 15. Migration and runtime implementation handoff

This design records future ownership without implementation:

- RF-09: tables, constraints and SQLAlchemy/Alembic transaction foundations.
- RF-10: Platform unit-of-work, idempotency and outbox primitives.
- RF-12: billing reconciliation.
- RF-15: scheduler and Scan leases.
- RF-16: Egress leases.
- RF-17: Notification delivery and reconciliation.
- RF-18/RF-19: channel adapter boundaries.
- RF-23: API/application command wiring.
- RF-24: end-to-end proof.
- RF-26: restart and recovery proof.
- RF-28: final failure drills.

No migration, runtime package, schema, dependency, service or provider implementation is created by this artifact.

## 16. Explicit non-goals

No code; no SQL/DDL; no ORM/Alembic; no dependency change; no CI; no Docker/Compose; no database/container; no server mutation; no service/port; no provider call; no credential; no public ingress; no production data; no production-ready claim; no additional table; no ownership rewrite; no distributed transaction; no broker.

## 17. Remaining RF-04 work

Only the following RF-04 work remains after this artifact:

- runtime process/package layout;
- migration plan;
- runtime topology;
- configuration schema;
- secrets boundary;
- environment-record candidate;
- consistency audit;
- RF-04 closure/status transition.

## 18. Acceptance checklist

- RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`.
- This is the RF-04 second artifact.
- Modules 01–13 are covered exactly once in the catalogue.
- Module 12 owns zero authoritative tables and browser/client state is never authority.
- No new tables are introduced; accepted table names and ownership are unchanged.
- Exact transaction, idempotency, outbox, lease and reconciliation protocols are defined.
- Cross-module atomicity is rejected; local owner transactions and public boundaries are explicit.
- Ambiguous effects reconcile before retry.
- Runtime mutation is none.
- RF-04 remains active and is not closed.
- RF-05 is not started.
- Production remains blocked; `PRODUCTION_READY` is not claimed.

RF04_TRANSACTION_AND_OUTBOX_BOUNDARIES_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT ACCEPTANCE

## 19. Final state

This artifact is documentation-only, active under RF-04, ready for independent operator acceptance, and makes no runtime or foreign-resource claim.

RF04_TRANSACTION_AND_OUTBOX_BOUNDARIES_PUBLISHED
