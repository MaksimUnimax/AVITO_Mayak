# Маяк Авито — Scan Orchestration & Listing State Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 17 of 24
**Дата:** 2026-07-07
**Модуль:** `06-scan-orchestration-and-listing-state`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Entitlements & Billing Module Playbook v1.0, Beacon Management Module Playbook v1.0, Avito Parser Adapter Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, Avito Reference Foundation, Target Model v0.1 as documented owner-requirement context and OPEN_DECISIONS.md.
**Не является:** scheduler/worker implementation, queue configuration, physical database schema, migration, parser/provider call, route implementation, notification delivery, executable test, fixture data, runtime configuration or permission to implement.

---

## 1. Назначение

Scan Orchestration & Listing State владеет внутренним жизненным циклом мониторингового запуска и authoritative listing state конкретного Маяка.

Модуль отвечает на вопросы:

- когда существует один логический scan intent/run;
- к какому `beacon_id` и immutable configuration revision он относится;
- как принимается explicit Parser outcome;
- какие observations можно зафиксировать;
- когда допустимо установить initial baseline;
- как получить объяснимый difference result;
- когда возникает committed domain event о новом объявлении или новой для Маяка паре identity+price;
- как обрабатывать replay, overlap, interruption, partial and ambiguous outcomes.

Он не извлекает Avito payload, не выбирает Egress route, не меняет Beacon configuration и не доставляет сообщения пользователю.

## 2. Границы и владение

Scan Orchestration & Listing State owns semantic mutation authority for:

- durable scan intent and run identity;
- internal due-work and claim state after implementation approval;
- run lifecycle and attempt/reconciliation evidence;
- exact `beacon_id` + immutable `configuration_revision_id` binding for a run;
- accepted Parser outcome reference and comparison eligibility decision;
- immutable `ListingObservation` records;
- accepted internal `ListingIdentityReference` and normalized price-key references after evidence approval;
- authoritative `BeaconListingState` isolated by `beacon_id`;
- `BaselineReference`;
- explainable `DifferenceResult`;
- committed scan-domain event facts;
- safe scan/listing read models and diagnostics.

It does not own:

- Account, identity, role, session or credential state;
- tariff, subscription, entitlement grant or payment state;
- Beacon source URL, snapshot, overrides, configuration revision creation or lifecycle authority;
- Avito response classification, extraction/normalization mappings or compatibility profiles;
- Egress route, agent, lease, heartbeat, quarantine or fallback;
- notification endpoint, notification outbox, delivery attempt or provider delivery state;
- Telegram/MAX provider mapping;
- supported filter catalog;
- raw provider payload retention while OD-013 remains unresolved.

Only this module may authorize changes to scan/listing authoritative state. Other modules use public contracts and never write its internal records directly.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted Beacon Management and Avito Parser Adapter playbooks.
4. This playbook.
5. Current Avito evidence for any provider-dependent identity/field/price assumption.
6. Future exact implementation task and accepted evidence.
7. Runtime evidence for one exact release/environment/run.

Target Model v0.1 supplies documented owner-requirement context for baseline and ID+price-pair behavior. Run 17 accepts only the explicit comparison semantics in this playbook; it does not promote unrelated DRAFT tariff, provider, route or UI assumptions.

## 4. Confirmed decisions

1. One logical `ScanRun` belongs to exactly one `beacon_id`.
2. Every run is pinned to exactly one immutable `configuration_revision_id`.
3. A newer Beacon revision never silently reinterprets an existing run, observation, baseline or difference.
4. Scan/listing state is isolated by `beacon_id`, even when two Beacons observe the same provider listing identity.
5. Parser output remains external-derived evidence until its explicit outcome is accepted for comparison.
6. Transport success is not Parser success. Parser success is not a committed scan comparison. A committed scan comparison is not notification delivery.
7. Partial, malformed, restricted, CAPTCHA-affected, route-failed, stale-reference, unsupported or ambiguous outcomes never become clean success or “no listings”.
8. Historical `ListingObservation` records are immutable.
9. Comparison state transitions for one Beacon must be serialized or conflict-detected; concurrent commits cannot silently overwrite each other.
10. Only a complete, explicit, comparison-eligible Parser outcome may establish or advance baseline/difference state.
11. The first comparison-eligible complete run establishes initial baseline and emits no new-listing or price-pair domain event for baseline contents.
12. After baseline, a previously unseen accepted listing identity produces one new-listing domain event for that Beacon.
13. After baseline, a known identity with a previously unseen accepted normalized price key produces one new identity+price-pair event for that Beacon.
14. An already known identity+price pair produces no new change event.
15. If price returns to a value already observed for that identity and Beacon, the pair is already known and v1.0 emits no new price-pair event.
16. A listing missing from one result does not prove deletion, removal, sale or inactivity.
17. A failed/partial run does not erase observations, listing state or baseline.
18. Domain events are emitted only after the authoritative scan comparison reaches its defined commit point.
19. Notification Delivery owns outbox/delivery. Scan emits domain facts only and never calls Telegram/MAX directly.
20. Open decisions and provider mappings receive no fabricated defaults.

## 5. Accepted comparison semantics v1.0

Run 17 explicitly accepts the following project-level comparison model once provider-dependent identity and price inputs are validated by an approved Parser compatibility profile.

### 5.1. Initial baseline

For a Beacon without an accepted baseline:

```text
first complete comparison-eligible ScanRun
→ accept immutable observations
→ establish BaselineReference
→ initialize BeaconListingState
→ emit BaselineEstablished fact
→ emit no user-change listing/price event for baseline contents
```

The baseline suppresses initial bulk notification noise. A partial or ambiguous run cannot establish baseline.

### 5.2. Subsequent comparison

For each accepted listing candidate in a later complete comparison-eligible run:

```text
identity unseen in this beacon
→ record observation and state
→ emit ListingFirstSeenAfterBaseline

identity seen, normalized price key unseen for this identity in this beacon
→ record observation and price-pair state
→ emit ListingPricePairFirstSeen

identity and normalized price key already seen in this beacon
→ record allowed observation/provenance
→ emit no new change event
```

### 5.3. Price return semantics

If observed prices for one identity are `A`, then `B`, then `A`:

- the first `A` pair is known;
- `B` is a new pair and may emit `ListingPricePairFirstSeen`;
- returned `A` is not new and emits no price-pair event.

Changing to “notify every transition” would be a breaking data/contract/product change requiring a new approved packet.

### 5.4. Absence semantics

Absence from one scan result does not establish:

- listing deletion;
- sale/completion;
- provider removal;
- temporary unavailability;
- filter exclusion;
- result truncation;
- route/parser failure.

Removal/inactivity semantics require separate evidence, contracts and fixtures and are not selected by Run 17.

## 6. Open decisions and blockers

Run 17 does not resolve:

- `OD-003` — exact allowed intervals and rules for changing them;
- `OD-004` — behavior after access/entitlement expiry;
- `OD-009` — exact supported Avito filters;
- `OD-010` — country-wide/market support;
- `OD-011` — safe and permitted monitoring cadence;
- `OD-013` — retention/deletion of runs, observations, listing state, events, logs and provider evidence;
- exact scheduling clock/time policy;
- exact due-slot identity and duplicate scheduling window;
- exact run state enum and transition codes;
- exact work-claim lease duration and renewal policy;
- exact worker concurrency, priority and fairness;
- exact overlap policy for multiple requested runs of one Beacon;
- exact cancellation semantics after external dispatch;
- exact retry count, delay, backoff and circuit breaker;
- exact route selection/fallback behavior;
- exact accepted listing identity mapping;
- exact normalized price/currency/unit mapping;
- exact required listing field set;
- exact complete-result/pagination coverage criteria;
- exact duplicate candidate handling when provider output repeats an item;
- exact behavior when Beacon is paused/archived or revision changes during a run;
- exact behavior when entitlement changes during a run;
- exact persistence schema, indexes and constraints;
- exact event transport/outbox implementation;
- exact read-model rebuild and compaction policy;
- removal/inactivity detection;
- history retention/compaction/deletion.

Open means blocked. No code, test, scheduler, worker or migration may invent these values.

## 7. Authoritative semantic records

These are logical records, not approved tables, ORM classes or wire schemas.

| Record | Purpose | Required boundary |
|---|---|---|
| `ScanIntent` | Accepted intent to create/consider one logical scan | exact Beacon/revision/purpose and idempotency context |
| `ScanScheduleState` | Future authoritative due-work state | no interval default; owned by this module |
| `ScanWorkClaim` | Bounded worker claim over one internal work item | not an Egress route lease |
| `ScanRun` | One logical run and lifecycle root | one Beacon, one immutable revision |
| `ScanAttempt` | One bounded execution/dispatch attempt under a run | explicit outcome and reconciliation |
| `ParserOutcomeReference` | Accepted explicit Parser result reference | raw provider payload is not authority |
| `ListingIdentityReference` | Internal accepted identity key for comparison | exact provider mapping remains evidence-gated |
| `ListingObservation` | Immutable listing observation in one run/Beacon | never overwritten |
| `BeaconListingState` | Current authoritative seen-identity/price-pair state for one Beacon | isolated by `beacon_id` |
| `BaselineReference` | Identity of initial accepted comparison state | established once under approved policy |
| `DifferenceResult` | Explainable comparison output for one run | references before/after state and rules version |
| `ScanDomainEvent` | Immutable post-commit fact | not notification delivery |
| `ScanReconciliationRecord` | Evidence resolving interrupted/ambiguous run/attempt | no blind retry |
| `ScanReadModel` | Rebuildable run/listing projection | not mutation authority |

## 8. Isolation and identity rules

- `beacon_id` is the authoritative listing-history isolation boundary.
- `configuration_revision_id` is pinned for the whole run.
- `run_id` identifies one logical scan, not one process invocation.
- `attempt_id` identifies one bounded attempt under a logical run when attempts are needed.
- Provider listing identity does not replace internal `ListingIdentityReference` without approved normalization/evidence.
- The same provider listing may have independent state in Beacon A and Beacon B.
- Cross-Beacon deduplication must not suppress authoritative state or events.
- Exact identifier encoding and provider mapping remain future task scope.

## 9. Scan eligibility boundary

Before a new run may produce external work, future implementation must establish:

- valid contract/version and purpose;
- authorized system/client/admin actor category as applicable;
- visible/owned `beacon_id` scope;
- exact immutable Beacon configuration revision;
- lifecycle eligibility from Beacon Management;
- effective entitlement decision where required;
- current Parser compatibility/reference eligibility;
- Egress availability only through Egress contracts;
- idempotency and overlap/conflict checks;
- approved schedule/due condition when scheduler-initiated.

Rules:

- UI or adapter flags are not authority;
- Scan does not mutate Beacon or Entitlement state;
- ambiguous entitlement or lifecycle result blocks effect;
- OD-004 controls exact expiry behavior;
- OD-003/OD-011 control interval/cadence values;
- no numeric timing default is introduced here.

## 10. Conceptual run lifecycle

The following semantic states/classes must be distinguishable; exact persisted enum names remain future task scope:

- `REQUESTED` — intent accepted for evaluation, no external effect;
- `BLOCKED` — known precondition failed;
- `PLANNED` — durable work accepted under approved policy;
- `CLAIMED` — one worker holds a bounded internal claim;
- `DISPATCH_PENDING` — Parser/Egress work prepared, send not confirmed;
- `IN_PROGRESS` — bounded attempt is active;
- `PARSER_OUTCOME_RECEIVED` — explicit Parser outcome recorded for evaluation;
- `COMPARISON_PENDING` — usable result awaits serialized commit;
- `SUCCEEDED_BASELINE` — baseline committed;
- `SUCCEEDED_DIFFERENCE` — subsequent comparison committed;
- `PARTIAL` — per-unit mixed outcome; no baseline/difference advancement unless separately proven under future policy;
- `FAILED` — explicit terminal failure;
- `AMBIGUOUS` — effect/outcome cannot be classified safely;
- `RECONCILIATION_REQUIRED` — no retry/terminal claim until reconciled;
- `CANCELLED` — cancelled under an approved boundary;
- `SUPERSEDED_BEFORE_EFFECT` — future safe pre-effect replacement only; exact policy deferred.

An alive worker, active claim or successful Egress transport does not prove run success.

## 11. Durable work and claim semantics

Technical Baseline requires durable module-owned work; process-local memory is not authoritative.

Future required properties:

- accepted work exists only after a defined commit point;
- worker claim is bounded and identified;
- one claim does not transfer Beacon, Parser, Egress or Notification ownership;
- claim replay/expiry does not silently create a second logical run;
- worker restart does not erase authoritative run state;
- claim expiry after possible external send requires reconciliation before another attempt;
- claimed work carries exact run/revision/purpose identity;
- completed/failed/ambiguous state is preserved;
- exact claim duration, heartbeat, polling, priority and concurrency remain unselected;
- no external broker is introduced by this playbook.

`ScanWorkClaim` is distinct from Egress `RouteLease`.

## 12. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `RequestScanCommand` | Request one logical run for a Beacon/revision under actor/purpose scope |
| `ScheduleDueScanCommand` | Future scheduler-owned intent to materialize due work without choosing interval values here |
| `ClaimScanWorkCommand` | Internal protected bounded claim over one durable work item |
| `RecordParserOutcomeCommand` | Attach an explicit Parser outcome to one run/attempt |
| `CommitBaselineCommand` | Establish first baseline from a complete comparison-eligible outcome |
| `CommitDifferenceCommand` | Commit subsequent observations/state/difference/events atomically in semantic terms |
| `CancelScanCommand` | Request cancellation under explicit effect/commit boundaries |
| `ReconcileScanRunCommand` | Resolve interrupted/ambiguous attempt/run using approved evidence |
| `GetScanRunQuery` | Read one authorized run with provenance and outcome |
| `ListBeaconScanRunsQuery` | Read authorized Beacon-scoped run summaries |
| `GetBeaconListingStateQuery` | Read current state/provenance for one Beacon |
| `ExplainDifferenceQuery` | Explain why one run produced baseline/no-event/new-listing/new-price-pair outcome |

Mutation-capable inputs require mandatory contract metadata, scope, idempotency key and normalized fingerprint.

## 13. Public output families

| Output family | Meaning |
|---|---|
| `ScanRequestOutcome` | planned, replayed, blocked, conflict or rejected |
| `ScanWorkClaimOutcome` | claimed, replayed, unavailable, expired, conflict or blocked |
| `ScanRunOutcome` | baseline success, difference success, failed, partial, ambiguous, cancelled or blocked |
| `ParserOutcomeAcceptanceResult` | accepted for comparison, recorded-only, rejected, incomplete, stale, unsupported or ambiguous |
| `BaselineEstablishmentOutcome` | established, replayed, blocked, conflict or failed |
| `DifferenceCommitOutcome` | committed, replayed, no change events, new listing events, new price-pair events, conflict or blocked |
| `ScanReconciliationOutcome` | resolved-success, resolved-failure, remains-ambiguous or manual-review-required |
| `ScanRunReadResult` | authorized run projection with revision/parser/route/difference provenance |
| `BeaconListingStateReadResult` | authorized Beacon-scoped current seen-state projection |
| `DifferenceExplanationResult` | rules version, inputs, accepted observations and event/no-event reasons |

Outputs remain transport, framework, ORM and provider neutral.

## 14. Parser Adapter dependency

Scan creates a request bound to one `beacon_id` and immutable `configuration_revision_id`. Parser returns explicit page/batch outcomes with compatibility/reference and provenance evidence.

Scan must preserve:

- Parser contract/version;
- compatibility/reference profile identity;
- page/unit scope and counts;
- normalized listing candidates;
- field-level warnings/uncertainty;
- complete/partial classification;
- restriction/CAPTCHA/failure/ambiguity;
- safe evidence fingerprint/references;
- route/attempt correlation where provided.

Scan must not:

- reinterpret `NOT_SENT`, transport unavailable/ambiguous, rejection, restriction, CAPTCHA, malformed, incomplete, unsupported, stale or disputed as empty success;
- infer omitted provider fields;
- accept raw payload as authoritative listing state;
- change Parser mappings;
- silently discard page/unit failures from a partial batch.

## 15. Comparison eligibility gate

A Parser outcome is comparison-eligible only when future accepted profile/task proves:

- exact intended Beacon revision and request scope;
- explicit usable response classification;
- required complete-result/pagination coverage;
- current reference/compatibility profile;
- accepted listing identity and price candidates;
- no restriction/CAPTCHA/malformed/incomplete/ambiguous signal;
- bounded and internally consistent unit counts;
- safe provenance/fingerprint;
- no unresolved conflict with run cancellation/revision/lifecycle state.

If any required fact is missing, the outcome may be recorded for diagnostics but does not establish or advance baseline/difference state.

## 16. Listing observation model

Each accepted observation must preserve or reference:

- `observation_id`;
- `run_id`;
- `beacon_id`;
- `configuration_revision_id`;
- accepted `ListingIdentityReference`;
- normalized price-key reference when available and required;
- safe normalized listing fields allowed by current profile;
- Parser/profile/reference provenance;
- observation time semantics after approval;
- completeness/quality/warning classification;
- correlation/causation references.

Rules:

- historical observation is immutable;
- a new observation does not overwrite an earlier observation;
- duplicate candidates in one run cannot produce duplicate domain effects;
- raw provider payload, phone, seller details, full description, views, cookies and secrets are excluded by default;
- exact physical uniqueness and storage remain future schema/migration scope.

## 17. Beacon listing state model

For each `beacon_id`, authoritative state conceptually tracks:

- accepted listing identities seen after/baseline initialization;
- accepted normalized price keys observed per identity;
- first/last accepted observation references where approved;
- baseline/version and last committed comparison references;
- rules/profile versions used;
- safe provenance and warning state;
- no inferred removal from absence.

This is not global provider history. State for one Beacon cannot suppress another Beacon’s event.

## 18. Baseline commit semantics

Baseline commit requires:

- no existing accepted baseline for that Beacon under current versioning policy;
- complete comparison-eligible Parser outcome;
- serialized/conflict-free Beacon state transition;
- immutable observations accepted;
- state initialized from accepted observations;
- explicit `BaselineReference` and `DifferenceResult` equivalent of “baseline established”;
- no new-listing or price-pair event for baseline contents;
- post-commit `BeaconBaselineEstablished` fact only;
- idempotent replay returns original baseline outcome.

An empty baseline is accepted only when Parser’s active profile proves genuine empty under its strict gate. Otherwise it remains blocked/ambiguous.

## 19. Difference commit semantics

A subsequent comparison commit requires:

- accepted baseline exists;
- complete comparison-eligible Parser outcome;
- exact previous state/version;
- serialized or conflict-detected transition;
- deterministic application of v1.0 comparison rules;
- immutable observation additions;
- explainable per-candidate classification;
- state and domain events committed under one logical commit boundary;
- idempotent replay with no duplicate state/event effect.

Per candidate classifications include:

- `NEW_IDENTITY_AFTER_BASELINE`;
- `KNOWN_IDENTITY_NEW_PRICE_PAIR`;
- `KNOWN_IDENTITY_KNOWN_PRICE_PAIR`;
- `DUPLICATE_WITHIN_RUN`;
- `UNSUPPORTED_OR_UNCERTAIN`;
- `BLOCKED_BY_INCOMPLETE_CONTEXT`.

Exact persisted codes remain future task scope.

## 20. Domain event families

Events are immutable post-commit facts, not commands and not notification delivery attempts.

- `ScanRunPlanned`;
- `ScanRunStarted`;
- `ScanRunCompleted`;
- `ScanRunFailed`;
- `ScanRunAmbiguous`;
- `BeaconBaselineEstablished`;
- `ListingFirstSeenAfterBaseline`;
- `ListingPricePairFirstSeen`;
- future reconciliation/cancellation facts after exact contract approval.

A listing-change event contains only safe normalized facts/references required by downstream consumers:

- event/contract version;
- event identity;
- `account_id` where required;
- `beacon_id`;
- `configuration_revision_id`;
- `run_id` and difference reference;
- listing identity reference;
- normalized price key/value representation after approval;
- safe client-card field references/provenance;
- correlation/causation;
- event reason/class;
- no raw provider payload or secret.

## 21. Notification Delivery handoff

Notification Delivery may consume committed `ListingFirstSeenAfterBaseline` and `ListingPricePairFirstSeen` events.

Scan does not:

- select notification endpoints;
- render provider-specific messages;
- create delivery attempts;
- manage delivery retries;
- claim Telegram/MAX success;
- send directly to providers;
- own delivery outbox/history.

Baseline contents generate no listing-change event and therefore no delivery intent.

Notification failure never rolls back committed listing observations/state. Delivery semantics belong to Run 19.

## 22. Beacon Management dependency

Scan consumes:

- authorized `beacon_id` reference;
- exact immutable configuration revision;
- lifecycle/eligibility result;
- account ownership scope;
- safe configuration/read model required for Parser request.

Rules:

- Scan never rewrites source URL, extracted snapshot, overrides or revision;
- a run never silently changes to a newer revision;
- historical runs retain their original revision reference;
- exact behavior if revision/lifecycle changes mid-run remains policy-gated;
- paused/archived/expired or ambiguous state cannot be guessed;
- Scan may report outcome but cannot activate/pause/archive a Beacon.

## 23. Entitlements dependency

Where product access affects execution, Scan consumes an explicit effective entitlement decision/reference.

Potential scope includes:

- whether scanning is currently allowed;
- interval class eligibility;
- geography/filter capability relevant to the pinned revision.

Scan does not own tariff values, payment state or grants.

Rules:

- no numeric interval/default introduced here;
- entitlement denial/ambiguity blocks external effect;
- behavior after expiry remains OD-004;
- exact re-evaluation timing during a run remains open;
- entitlement changes do not rewrite historical run evidence.

## 24. Egress Routing dependency

Egress Routing owns route/agent/lease/health/fallback. Parser Adapter consumes transport contracts.

Scan may preserve safe route/lease/outcome references as run provenance but does not:

- select route independently;
- mutate route health/quarantine;
- extend/revoke route lease;
- treat heartbeat as scan success;
- configure Windows/server/network resources;
- retry an ambiguous external dispatch blindly.

Run 18 must define exact Egress contracts. Until accepted, route-dependent implementation remains blocked.

## 25. Idempotency rules

Idempotency is required for scan request creation, due-work materialization, protected cancellation/reconciliation and any retryable command.

Required semantics:

- same key + same semantic request + known terminal outcome returns/references original outcome;
- same key + same request + pending/ambiguous outcome returns pending/reconciliation state;
- same key + different fingerprint returns `IDEMPOTENCY_MISMATCH` with no effect;
- missing required key is rejected before effect;
- replay never creates a second logical run, baseline, observation state transition or domain event;
- retry attempts remain under the same logical run unless an approved policy explicitly creates a new run;
- per-unit partial retry identifies exact page/candidate units and preserves prior outcomes;
- exact storage/TTL remains open.

## 26. Commit-point rules

Before implementation, each mutation must define its logical commit point.

### 26.1. Scan request/work commit

Success means durable intent/work exists and can survive process restart. Process-local scheduling is not success.

### 26.2. Parser outcome recording commit

Success means the explicit outcome/reference is durably associated with the run/attempt. It does not mean comparison success.

### 26.3. Baseline/difference commit

Success means, as one semantic unit:

- required observations are committed;
- Beacon listing state/version is committed;
- baseline or difference result is committed;
- allowed scan-domain event facts are committed;
- outcome is replayable without duplicate effects.

No success/change event is emitted before this commit point.

## 27. Interruption and reconciliation

### Before durable run/work commit

- no logical run success;
- replay may create work only under idempotency rules.

### After run commit but before external dispatch

- run remains planned/claimed/pending;
- safe reclaim/retry requires claim policy.

### Dispatch/send state unknown

- run/attempt becomes ambiguous or reconciliation-required;
- do not issue blind retry;
- preserve correlation, idempotency and Parser/Egress evidence.

### Parser outcome recorded but comparison commit absent

- no baseline/difference/change-event success;
- re-evaluate/replay comparison under exact state-version/idempotency checks.

### Comparison commit succeeded but response/report lost

- replay returns original outcome/references;
- no duplicate observation state transition or event.

Exact reconciliation sources and timeouts remain future task scope.

## 28. Partial and batch outcomes

- Every page/unit/candidate outcome remains explicit.
- Generic whole-run success is prohibited when units differ.
- Partial Parser success cannot erase failed/restricted/ambiguous units.
- Run-level status exposes accepted, failed, blocked, pending and ambiguous counts.
- Under v1.0 safety boundary, partial outcomes do not establish or advance baseline/difference state.
- Partial normalized candidates may be retained only as approved diagnostic evidence under OD-013 policy; they are not authoritative listing state by default.
- Exact future partial-acceptance policy would be a contract/data change requiring fixtures and acceptance review.

## 29. Concurrency and conflict handling

For one Beacon, authoritative comparison commits must be ordered.

Required properties:

- each commit checks expected previous state/baseline/version;
- stale concurrent commit returns conflict and does not overwrite newer state;
- two workers cannot both create the first baseline;
- duplicate candidate/event effects are prevented;
- newer Beacon revision does not silently absorb an older run;
- exact locking, optimistic versioning or transaction mechanism is not selected;
- overlap scheduling policy remains open, but silent last-write-wins is prohibited.

## 30. Error semantics

Applicable categories include:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`;
- `FORBIDDEN`;
- `NOT_FOUND`;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `RATE_LIMITED` where an approved policy exists;
- `EXTERNAL_UNAVAILABLE`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

Error output includes safe contract/run/Beacon/revision/correlation/profile/retry/reconciliation references. It excludes raw provider payloads, credentials, cookies, private route details and foreign-account data.

## 31. Security, privacy and retention

- Authorization and ownership checks precede protected read/mutation.
- Cross-account/Beacon existence details follow safe error semantics.
- Raw provider payloads are not ordinary run/listing state.
- Phone, seller details, full description and views are excluded by default.
- External strings never become shell commands.
- Logs use safe IDs, counts, state classes, rules/profile versions, latency and reason codes.
- No credentials, tokens, cookies, private keys or secrets in contracts, logs, fixtures or reports.
- Read models have provenance/freshness and are not authority.
- Retention, archive, deletion and compaction remain OD-013.
- A deletion/retention task cannot be invented by implementation agents.

## 32. Observability semantics

Future minimum safe signals:

- run/attempt/claim IDs;
- `beacon_id` and revision reference under authorization;
- run lifecycle class;
- Parser outcome class/profile/reference identity;
- page/item accepted/failed/partial/ambiguous counts;
- baseline/difference classification;
- new-listing/new-price-pair/no-event counts;
- overlap/conflict/replay/reconciliation state;
- claim age/freshness after exact time policy;
- safe failure reason and latency;
- no raw payload/secret/personal overcollection.

A green worker, claimed job, route heartbeat or Parser response does not prove committed scan success.

## 33. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Beacon Management accepted public contracts;
- Avito Parser Adapter accepted public contracts;
- Entitlements effective-decision contracts;
- future Egress Routing contracts after Run 18 acceptance;
- future Notification Delivery contracts after Run 19 acceptance;
- PostgreSQL/SQLAlchemy/Psycopg selected-with-gate for authoritative durable state;
- Alembic only after physical schema/migration approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- OpenTelemetry boundary after applicable instrumentation task.

Deferred/blocked:

- physical tables/indexes/constraints;
- scheduler/worker implementation;
- polling/claim/lease values;
- broker/cache;
- external queue;
- parser/provider traffic;
- route implementation;
- notification outbox/delivery;
- retention tooling;
- services/deploy/runtime.

No Redis, RabbitMQ, Celery or other broker is introduced by this playbook.

## 34. Fake dependencies and test doubles

Future approved fakes may model:

- `BeaconRevisionReader`;
- `BeaconEligibilityGateway`;
- `EntitlementDecisionGateway`;
- `ParserAdapterGateway`;
- `EgressOutcomeReferenceReader`;
- `NotificationEventSink` as a domain-event boundary, not provider delivery;
- `ScanRunRepository`;
- `ListingObservationRepository`;
- `BeaconListingStateRepository`;
- `ScanWorkRepository`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic accounts, Beacons, revisions, listing identities, prices, Parser outcomes and routes only. They do not prove Avito behavior or production durability.

## 35. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-OWNER-FOREIGN-BEACON-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-INTERRUPT-PRECOMMIT-001`;
- `FX-INTERRUPT-UNKNOWN-001`;
- `FX-INTERRUPT-POSTCOMMIT-001`;
- `FX-BATCH-PARTIAL-001`;
- `FX-DATA-BEACON-ISOLATION-001`;
- `FX-DATA-HISTORY-IMMUTABLE-001`;
- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-EXT-SUCCESS-001`;
- `FX-EXT-REJECTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-AVITO-CAPTCHA-001`;
- `FX-ROUTE-FAILURE-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-SOLS-FIRST-COMPLETE-BASELINE-001`;
- `FX-SOLS-BASELINE-NO-NOTIFICATION-001`;
- `FX-SOLS-NEW-LISTING-AFTER-BASELINE-001`;
- `FX-SOLS-KNOWN-PAIR-NO-EVENT-001`;
- `FX-SOLS-NEW-PRICE-PAIR-EVENT-001`;
- `FX-SOLS-PRICE-RETURN-KNOWN-PAIR-NO-EVENT-001`;
- `FX-SOLS-CROSS-BEACON-ISOLATION-001`;
- `FX-SOLS-HISTORICAL-OBSERVATION-IMMUTABLE-001`;
- `FX-SOLS-PARTIAL-NO-BASELINE-ADVANCE-001`;
- `FX-SOLS-FAILURE-NOT-EMPTY-001`;
- `FX-SOLS-CAPTCHA-NOT-EMPTY-001`;
- `FX-SOLS-PARSER-AMBIGUOUS-RECONCILE-001`;
- `FX-SOLS-REVISION-PINNED-001`;
- `FX-SOLS-REVISION-CHANGED-MIDRUN-001`;
- `FX-SOLS-PAUSED-BLOCKED-001`;
- `FX-SOLS-ENTITLEMENT-AMBIGUOUS-BLOCKS-001`;
- `FX-SOLS-IDEMPOTENT-RUN-REPLAY-001`;
- `FX-SOLS-IDEMPOTENCY-MISMATCH-001`;
- `FX-SOLS-PRECOMMIT-INTERRUPTION-001`;
- `FX-SOLS-POSTCOMMIT-REPLAY-001`;
- `FX-SOLS-OVERLAP-CONFLICT-001`;
- `FX-SOLS-DUPLICATE-WITHIN-RUN-001`;
- `FX-SOLS-MISSING-LISTING-NO-REMOVAL-001`;
- `FX-SOLS-NOTIFICATION-EVENT-AFTER-COMMIT-001`;
- `FX-SOLS-NO-DIRECT-DELIVERY-001`;
- `FX-SOLS-RAW-PAYLOAD-EXCLUDED-001`;
- `FX-SOLS-RETENTION-OD013-BLOCKED-001`.

Run 17 creates no fixture files and executes no tests.

## 36. Acceptance Matrix coverage

Run 17 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-BATCH-001`;
- `AM-DATA-002`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-003`;
- `AM-EXT-001`–`AM-EXT-004`;
- `AM-AVITO-001`;
- `AM-EGRESS-001`;
- `AM-REF-001`–`AM-REF-004`;
- `AM-MIG-008`–`AM-MIG-009` where applicable;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, scheduler, Parser, Egress and Notification executions remain future gates and are not passed by this documentation run.

## 37. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral scan/run/observation/state/difference/event models;
- implement synthetic deterministic baseline/difference rules;
- prove per-Beacon isolation, immutable history and price-pair semantics;
- implement durable PostgreSQL-owned work/state after physical schema/migration approval;
- integrate accepted Beacon and Parser contracts;
- integrate future Egress and Notification contracts after their playbooks;
- add bounded scheduler/worker behavior after time/claim/cadence decisions;
- add observability, idempotency and reconciliation evidence;
- add approved read models with provenance.

## 38. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create scheduler or worker implementation;
- create queues, broker, cache or services;
- choose intervals, polling, claim lease, concurrency, retry or backoff values;
- guess expiry/lifecycle behavior;
- send Parser/provider requests directly;
- choose or mutate Egress routes;
- classify malformed/restricted/partial/ambiguous as no listings;
- establish baseline from incomplete outcome;
- infer listing removal from absence;
- silently follow latest Beacon revision;
- collapse cross-Beacon state;
- mutate historical observations;
- emit change events before comparison commit;
- call Telegram/MAX or create delivery attempts;
- collect/retain raw provider payloads without OD-013 policy;
- invent listing identity/price mappings;
- create product-code, dependency file, lockfile, executable test, fixture data file, migration, database, Docker/CI/CD, service, container, port, deploy or runtime configuration.

## 39. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `SOLS-01` | Semantic scan/run/observation/difference/event contracts and synthetic fixtures | `NOT_STARTED` | exact implementation task and Platform primitives |
| `SOLS-02` | Schedule and eligibility model | `BLOCKED` | OD-003, OD-004, OD-011 and exact time policy |
| `SOLS-03` | Durable work/claim/run lifecycle | `BLOCKED` | physical state task, claim/concurrency policy and toolchain proof |
| `SOLS-04` | Parser outcome integration and comparison eligibility | `NOT_STARTED` | accepted Parser contracts and exact profile fixtures |
| `SOLS-05` | Baseline and ID+price-pair difference engine | `BLOCKED` | approved identity/price mapping and synthetic contract task |
| `SOLS-06` | Observation/listing-state persistence | `BLOCKED` | physical schema, migration and PostgreSQL proof |
| `SOLS-07` | Scan-domain event handoff | `BLOCKED` | Run 19 Notification Delivery contract and event mechanism |
| `SOLS-08` | Concurrency, idempotency and reconciliation | `NOT_STARTED` | exact task and durable transaction model |
| `SOLS-09` | Privacy, retention, read models and observability | `BLOCKED` | OD-013 and operations/evidence policy |
| `SOLS-10` | Full acceptance evidence and handoff | `NOT_STARTED` | applicable subtasks complete |

## 40. Task packet requirements

A future task must include:

- exact paths and parent SHA;
- stable task/iteration ID;
- accepted run/contract/rules version;
- exact Beacon/revision and actor/purpose scope;
- schedule/eligibility/entitlement assumptions and blocked values;
- Parser profile/outcome classes and comparison eligibility;
- listing identity/price mapping evidence;
- baseline/difference/event semantics;
- durable work/claim/commit/concurrency boundaries;
- idempotency, interruption and reconciliation;
- partial/batch behavior;
- Egress and Notification fake/real contract boundaries;
- privacy/redaction/retention scope;
- physical schema/migration scope if applicable;
- fixtures and Acceptance Matrix rows;
- isolated toolchain/dependency/DB proof;
- no-live-provider requirement unless separately approved;
- evidence/report format and exact final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 41. Report and handoff

A future implementation/proof report must include:

- task/iteration ID and exact commit SHA;
- changed paths and dependency/lock identity;
- run/rules/contract versions;
- Beacon/revision/entitlement/Parser/Egress provenance;
- run lifecycle, work claim and commit-point evidence;
- first-baseline/no-notification evidence;
- new-listing/new-price-pair/known-pair/price-return evidence;
- cross-Beacon isolation and immutable-history evidence;
- partial/failure/CAPTCHA/route/ambiguous no-false-empty evidence;
- overlap/conflict/idempotency/interruption/reconciliation evidence;
- post-commit event and no-direct-delivery evidence;
- privacy/redaction/retention confirmation;
- fixtures, Acceptance Matrix rows and exact results;
- database/migration/runtime statement;
- live provider traffic statement (`NONE` unless separately authorized);
- prohibited-artifact check;
- blockers and next safe task;
- exact final marker for independent review.

## 42. Acceptance criteria

The playbook is acceptable only when:

- scan/run/listing ownership and non-ownership are explicit;
- one run is pinned to one Beacon and immutable revision;
- durable work is authoritative rather than process-local;
- Parser outcome and comparison eligibility remain explicit;
- first complete baseline suppresses listing-change events;
- subsequent new identity and unseen identity+price-pair semantics are explicit;
- returned known price produces no event under v1.0;
- cross-Beacon state isolation and immutable observations are explicit;
- missing listing does not imply removal;
- partial/failure/restricted/ambiguous outcomes cannot establish baseline, erase state or become no listings;
- concurrency/conflict/idempotency/commit/reconciliation boundaries are explicit;
- domain events occur only post-commit and Notification Delivery remains separate;
- exact intervals, expiry, provider mappings, route/retry values and retention are not guessed;
- contracts, fakes, fixtures, matrix rows, roadmap and handoff are present;
- no code, scheduler, worker, queue, database, migration, parser/provider call, notification delivery, dependency, lock, test, fixture file, Docker/CI/CD, deploy/runtime, service, port or sensitive material is created;
- GitHub publication and exact server synchronization are independently verified.

## 43. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### SOLS-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 17 initial Scan Orchestration & Listing State ownership, contracts and roadmap defined.
- One-run/one-Beacon/one-immutable-revision boundary fixed.
- First complete baseline without listing-change events and subsequent new-identity/unseen identity+price-pair semantics accepted as v1.0.
- Cross-Beacon isolation, immutable observations, no-removal-from-absence and false-empty prohibition fixed.
- Durable work, idempotency, concurrency, interruption, reconciliation and post-commit domain-event boundaries defined without implementation.
- OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain unresolved.
- No scheduler, worker, queue, product code, database, migration, provider request, notification delivery, runtime or infrastructure artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.

### SOLS-HISTORY-0002 — 2026-07-09 — Owner Scan decisions captured by ADR-0018

This history entry records the SOLS-01 governance capture now fixed in `OWNER_SCAN_DECISIONS_CAPTURE_v1.0.md`.

The captured owner decisions keep Scan on new listings only, require newest-first monitoring, leave price as candidate data while price-change tracking and price-pair notification remain deferred, assign observed order and sort/publication signals to Parser Adapter, treat missing or unproven sort context as blocked/ambiguous rather than false no-new, use compact rolling anchors with future Admin-configurable size, distinguish lost anchors from window overflow, allow latest 3 lost-anchor items to restore as latest-fresh rather than confirmed-new, keep the current one pending recovery scan model, treat external failure/CAPTCHA/route/parser/ambiguity as not no-new, preserve baseline and anchors on failure, prevent default no-new spam, forbid parallel active comparison commits for one Beacon, require lifecycle and entitlement re-check before user-visible commit, keep safe facts/status only at Scan, and leave scheduler, worker, DB, parser/provider, Egress, Notification, UI, deploy, secrets and raw provider payload retention gated. Older playbook v1.0 price-pair direction is superseded for current owner scope, but history is preserved; OD-011 and OD-013 remain open and no open decision is closed by assumption.

### SOLS-HISTORY-0003 — 2026-07-09 — Scan semantic records and synthetic fixture definitions

SOLS-02 created docs-only semantic records and synthetic fixture definitions.
It uses SOLS-01 owner decisions.
No code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created.
Fixture definitions are markdown-only, synthetic and non-executable.
Parser Adapter module 05 is referenced only as documentation/placeholder contract boundary.
OD-011 and OD-013 remain open.
SOLS-03+ remain gated.

### SOLS-HISTORY-0004 — 2026-07-09 — Scan eligibility and intent boundary

SOLS-03 created docs-only scan eligibility and intent boundary documentation;
it uses SOLS-01 owner decisions and SOLS-02 semantic record families;
Beacon/Entitlements/Parser modules are referenced only as documentation/placeholder contract boundaries;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no numeric intervals, anchor window size, retry/backoff, due-slot or claim lease values were introduced;
scheduler/worker/DB/runtime remain gated;
SOLS-04+ remain gated.

### SOLS-HISTORY-0005 — 2026-07-09 — Scan run lifecycle, idempotency and commit points

SOLS-04 created docs-only lifecycle, idempotency and commit-point documentation;
it uses SOLS-01 owner decisions, SOLS-02 semantic records and SOLS-03 eligibility boundary;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-05+ remain gated.

### SOLS-HISTORY-0006 — 2026-07-09 — Baseline and rolling anchor state

SOLS-05 created docs-only baseline and rolling anchor state documentation;
it uses SOLS-01 owner decisions, SOLS-02 semantic records, SOLS-03 eligibility boundary and SOLS-04 lifecycle/commit-point rules;
first complete comparison-eligible scan establishes baseline and emits no user new-listing result for baseline contents;
rolling anchors are compact memory, not full user-visible listing archive;
anchor window size remains policy/config reference and future Admin-configurable, with no hard-coded value;
failed/partial/ambiguous/CAPTCHA/external-unavailable outcomes do not establish baseline or advance anchors;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-06+ remain gated.

### SOLS-HISTORY-0007 — 2026-07-09 — Difference rules for new listings only

SOLS-06 created docs-only difference rules for current owner scope: new listings only;
it uses SOLS-01 owner decisions, SOLS-02 semantic records, SOLS-03 eligibility boundary, SOLS-04 lifecycle/commit-point rules and SOLS-05 baseline/rolling anchor state;
price may remain display/parser candidate data, but price-change tracking and price-pair notification/event remain deferred/disabled;
no user notification is created solely because an old listing changed price;
no-new-listings is an explicit successful comparison result, not a fallback for uncertainty;
incomplete/partial/ambiguous/CAPTCHA/external-unavailable outcomes do not create new-listing facts and do not advance anchors;
lost anchors are delegated to SOLS-07;
window overflow remains future design;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-07+ remain gated.

### SOLS-HISTORY-0008 — 2026-07-09 — Lost anchors recovery

SOLS-07 created docs-only lost-anchor recovery documentation;
it uses SOLS-01 owner decisions, SOLS-02 semantic records, SOLS-03 eligibility boundary, SOLS-04 lifecycle/commit-point rules, SOLS-05 baseline/rolling anchor state and SOLS-06 difference rules;
lost anchors means previous anchors exist but none are found in a usable current top-window;
lost anchors are not external failure, CAPTCHA, partial, ambiguous, malformed, sort-not-proven or window overflow;
lost-anchor recovery reports latest 3 fresh listings as state-restored/latest-fresh, not confirmed new listings;
after recovery commit, anchor state is updated/reseeded from the current observed top-window to avoid repeated latest-3 output;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-08+ remain gated.

### SOLS-HISTORY-0009 — 2026-07-09 — External failure and pending recovery scan

SOLS-08 created docs-only external-failure and pending-recovery scan documentation;
it uses SOLS-01 owner decisions, SOLS-02 semantic records, SOLS-03 eligibility boundary, SOLS-04 lifecycle/commit-point rules, SOLS-05 baseline/rolling anchor state, SOLS-06 difference rules and SOLS-07 lost-anchor recovery;
external failure/CAPTCHA/route/parser/provider ambiguity is not no-new-listings;
external failure does not erase baseline, erase anchors, advance anchors or create new-listing facts;
one pending recovery scan is kept while the same problem continues; missed due intervals are coalesced and not accumulated into multiple scans;
one recovery result may be sent/reported even after entitlement expiry if the external problem began while access was active; after that, current entitlement rules apply;
Parser owns provider response classification, Egress owns route/fallback/quarantine/agent mechanics, Notification Delivery owns delivery;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-09+ remain gated.

### SOLS-HISTORY-0010 — 2026-07-09 — Overlap, concurrency and mid-run changes

SOLS-09 created docs-only overlap, concurrency and mid-run change documentation;
it uses SOLS-01 owner decisions, SOLS-02 semantic records, SOLS-03 eligibility boundary, SOLS-04 lifecycle/commit-point rules, SOLS-05 baseline/rolling anchor state, SOLS-06 difference rules, SOLS-07 lost-anchor recovery and SOLS-08 pending recovery/external failure rules;
one Beacon comparison state must be serialized or conflict-detected;
new due interval while one scan is active is overlap/pending/claimed, not duplicate parser dispatch or duplicate comparison commit;
stale concurrent commit has conflict/no effect; no silent last-write-wins;
Beacon lifecycle/revision and entitlement must be re-checked before user-visible commit;
paused/archived/deleted/frozen Beacon before normal commit blocks normal user-visible new-listing result;
denied/expired/ambiguous entitlement before normal commit blocks normal user-visible result except the already accepted one-time recovery grace;
no code/tests/runtime/schema/parser/egress/notification/UI/deploy artifacts were created;
no DB transaction/lock/table/index/migration was introduced;
no scheduler/worker/queue/cache/claim lease/heartbeat/retry/backoff implementation or numeric default was introduced;
no live Avito/provider traffic, parser implementation, Egress implementation or Notification delivery was introduced;
SOLS-10+ remain gated.
