# Маяк Авито — Notification Delivery Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 19 of 24
**Дата:** 2026-07-08
**Модуль:** `08-notification-delivery`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Entitlements & Billing Module Playbook v1.0, Beacon Management Module Playbook v1.0, Scan Orchestration & Listing State Module Playbook v1.0, Egress Routing Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, Telegram/MAX Reference Foundation and OPEN_DECISIONS.md.
**Не является:** queue/worker implementation, message broker selection, provider adapter implementation, Telegram/MAX bot, webhook, Mini App, physical database schema, migration, live delivery, runtime configuration, message-template catalog, provider credential policy or permission to implement.

---

## 1. Назначение

Notification Delivery владеет безопасной серверной семантикой превращения committed scan-domain facts в generic notification work, delivery attempts and delivery history.

Модуль отвечает на вопросы:

- какие committed domain events можно принять как notification source;
- когда создаётся один outbox item;
- как исключаются дубли пользовательского эффекта;
- как отделяются notification intent, provider-specific adapter call и actual provider delivery;
- какие delivery attempt outcomes допустимы;
- когда retry условно допустим, а когда требуется reconciliation;
- почему notification failure не меняет Scan/listing state;
- какие безопасные read models нужны пользователю, администратору и downstream adapters.

Модуль не создаёт Scan facts, не рассчитывает differences, не выбирает Egress route, не маппит Telegram/MAX provider payloads и не доставляет сообщения напрямую в этом playbook.

## 2. Границы и владение

Notification Delivery owns semantic mutation authority for:

- accepted notification-source event intake records;
- generic notification event classification;
- durable notification outbox items;
- recipient/channel target references after approved identity and preference rules;
- notification deduplication state;
- delivery plan/status at the generic module boundary;
- delivery attempt lifecycle and attempt outcome records;
- delivery logs and safe diagnostic records;
- retry/reconciliation state for delivery attempts;
- safe notification read models and delivery history projections.

It does not own:

- Account, identity, authentication, role, session or contact-link challenge state;
- tariff, subscription, entitlement grant or payment state;
- Beacon source URL, configuration, revision or lifecycle authority;
- Parser extraction, provider response classification or normalized listing candidates;
- Scan intent, work claim, run, observations, baseline, difference or listing state;
- Egress route, agent, lease, heartbeat, assignment or transport outcome state;
- Telegram-specific chat, bot command, webhook, callback, Mini App or message formatting rules;
- MAX-specific chat, bot command, webhook, callback, Mini App or message formatting rules;
- Web Cabinet screens or analytics;
- supported Avito filter catalog;
- raw provider payload retention while OD-013 remains unresolved;
- provider credentials, tokens, secrets or runtime infrastructure.

Only Notification Delivery may authorize changes to notification outbox, delivery attempts and delivery history. Provider adapters, Web Cabinet and Admin/Support use public contracts and never edit notification-owned records directly.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted Scan Orchestration & Listing State and Egress Routing playbooks.
4. Accepted Telegram/MAX reference policies.
5. This playbook.
6. Future Telegram Adapter and MAX Adapter playbooks for provider-specific behavior.
7. Current official/primary provider evidence for destination-specific claims.
8. Future exact implementation task and accepted evidence.
9. Runtime evidence for one exact release/environment/delivery operation.

Target Model v0.1 supplies documented owner-requirement context for Telegram/MAX as initial user channels. Run 19 accepts only generic notification-delivery semantics and does not promote unrelated DRAFT tariff, route, provider, UI or retention assumptions.

## 4. Confirmed decisions

1. Notification Delivery consumes committed scan-domain events only.
2. Parser success is not notification delivery success.
3. Egress transport success is not notification delivery success.
4. A committed Scan comparison is not notification delivery success.
5. Baseline contents do not create user-visible listing-change delivery under v1.0 semantics.
6. `BeaconBaselineEstablished` may be recorded for diagnostics/read models but does not create a listing-change outbox item by default.
7. `ListingFirstSeenAfterBaseline` may create notification work after all delivery eligibility gates pass.
8. `ListingPricePairFirstSeen` may create notification work after all delivery eligibility gates pass.
9. Notification failure never rolls back committed Scan observations, Beacon listing state, difference result or scan-domain events.
10. Delivery attempts are module-owned generic records until handed to a provider adapter through an approved contract.
11. Telegram Adapter and MAX Adapter own provider-specific mapping and provider outcome interpretation after their playbooks; Notification Delivery owns generic outbox/attempt state.
12. One notification source event must not produce duplicate user-visible deliveries under replay.
13. Idempotency is required for source-event intake, outbox creation, delivery attempt creation and provider-result recording.
14. Unknown provider send/delivery state is reconcile-first and never blindly retried.
15. Retry/backoff/rate values are not selected by this playbook.
16. Channel priority, fallback, quiet hours, batching, grouping and template catalog remain unselected.
17. Notification state is scoped to `account_id` and `beacon_id` where applicable and never suppresses another Beacon’s state.
18. Delivery history must not contain raw secrets, provider tokens, cookies or unnecessary personal data.
19. Open decisions and provider-specific defaults receive no fabricated values.
20. Run 19 creates no queue, worker, database table, migration, provider call, bot or runtime.

## 5. Open decisions and blockers

Run 19 does not resolve:

- `OD-004` — behavior after access/entitlement expiry, including whether pending outbox items are held, cancelled or suppressed;
- `OD-012` — future channels beyond Telegram/MAX;
- `OD-013` — retention/deletion of notification events, outbox items, attempts, logs, provider evidence and personal data;
- exact channel preference model and defaults;
- exact opt-in/opt-out and unsubscribe semantics;
- exact quiet-hours, digest, batching and grouping policy;
- exact message template catalog and localization strategy;
- exact listing-card content for each channel;
- exact provider-specific payload schemas;
- exact provider retry count, delay, backoff and circuit breaker;
- exact provider rate limits and quota model;
- exact channel priority/fallback behavior;
- exact outbox worker, queue, scheduler or polling technology;
- exact delivery attempt state enum and transition codes;
- exact read/ack/click tracking semantics;
- exact notification suppression policy beyond baseline contents;
- exact error-to-user copy;
- exact storage schema, indexes and constraints;
- exact retention, archive, deletion and compaction policy;
- exact admin/support intervention policy;
- exact provider credentials, webhook, bot, Mini App or API setup.

Open means blocked. No implementation, test, fixture, template, provider adapter or runtime task may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, queues, wire schemas or provider payloads.

| Record | Purpose | Required boundary |
|---|---|---|
| `NotificationSourceEvent` | Accepted reference to a committed upstream event | immutable source identity and producer evidence |
| `NotificationEligibilityDecision` | Decision whether source event may produce notification work | no fabricated defaults; references entitlement/channel/preference gates |
| `NotificationOutboxItem` | Durable generic work item for one intended user-visible notification effect | not provider-specific message payload |
| `NotificationDeduplicationRecord` | Prevents duplicate user-visible effect for the same semantic source | scoped by contract/source/account/beacon/channel where approved |
| `NotificationDeliveryPlan` | Generic selected channel/target plan after approved preference rules | no provider runtime selection beyond accepted adapter boundary |
| `NotificationAttempt` | One bounded attempt to deliver an outbox item through a channel adapter | explicit outcome and correlation |
| `ProviderDeliveryOutcomeReference` | Adapter-returned explicit provider outcome reference | not generic success unless accepted by Notification |
| `NotificationReconciliationRecord` | Evidence resolving unknown send/delivery state | no blind retry |
| `NotificationDeliveryLog` | Safe immutable audit/diagnostic record | no secrets/raw provider payload |
| `NotificationReadModel` | Rebuildable projection for user/admin/support views | not mutation authority |

## 7. Semantic identifiers and scope

- `notification_source_event_id` identifies one accepted upstream source fact.
- `notification_outbox_item_id` identifies one generic delivery work item.
- `notification_attempt_id` identifies one bounded delivery attempt.
- `notification_deduplication_key` identifies one protected duplicate-effect boundary.
- `delivery_target_ref` identifies an approved target reference, not raw provider secret or unverified chat identity.
- `channel_id` identifies a logical channel class after approval, not provider runtime credentials.
- `correlation_id` and `causation_id` connect Scan, Notification and adapter evidence.

Identifiers do not reveal private account details, full phone numbers, provider tokens, chat secrets, route details or foreign infrastructure values. Exact encoding remains future task scope.

## 8. Source event intake boundary

Notification Delivery may intake only committed post-Scan facts that have reached their Scan commit point.

Allowed v1.0 source families:

- `ListingFirstSeenAfterBaseline`;
- `ListingPricePairFirstSeen`;
- future listing-change facts only after approved contract change.

Non-delivery source families by default:

- `BeaconBaselineEstablished`;
- `ScanRunPlanned`;
- `ScanRunStarted`;
- `ScanRunFailed`;
- `ScanRunAmbiguous`;
- Parser-only outcomes;
- Egress transport outcomes;
- provider-specific adapter outcomes not tied to a notification attempt.

Rules:

- source identity must be stable and replayable;
- source producer and contract version must be known;
- `account_id`, `beacon_id`, `run_id` and safe listing references must be present where required;
- unsafe/raw provider payload is not copied into notification state;
- a source event rejected or ambiguous at intake does not create outbox work;
- replay with the same source identity cannot create duplicate outbox effects.

## 9. Eligibility gate

Before creating an outbox item, future implementation must establish:

- valid contract/version and source event family;
- authorized internal producer or ingestion identity;
- visible/owned `account_id` and `beacon_id` scope;
- accepted Scan event provenance and commit evidence;
- Beacon lifecycle eligibility where required;
- effective entitlement decision where product access affects notification delivery;
- channel availability/preference decision after approval;
- safe delivery target reference after Identity/Adapter approval;
- idempotency key and normalized fingerprint;
- no suppression/blocking condition under approved policy;
- no unresolved provider/reference/evidence conflict.

Rules:

- UI flags are not authority;
- adapter-visible chat names are not account identity;
- ambiguous entitlement, lifecycle or target state blocks effect;
- OD-004 controls exact expiry behavior;
- OD-012 controls future channels;
- OD-013 controls retention and deletion;
- no default channel, retry schedule or template is introduced here.

## 10. Outbox semantics

A `NotificationOutboxItem` exists only after the eligibility decision reaches its defined commit point.

Required semantic fields/references:

- outbox item identity and contract/version;
- source event identity, producer, contract and version;
- account and Beacon scope where applicable;
- event reason/class;
- safe listing/card fact references;
- intended channel class or unresolved-channel state under approved policy;
- target reference class, never raw secret;
- deduplication key/fingerprint;
- lifecycle state;
- attempt summary references;
- retry/reconciliation state;
- safe correlation/causation;
- created/updated time semantics after approved time policy.

Outbox item creation does not prove provider delivery, provider acceptance, user receipt, user read, click or acknowledgement.

## 11. Conceptual outbox lifecycle

The following semantic states/classes must be distinguishable; exact persisted enum names remain future task scope:

- `INTAKE_REJECTED` — source cannot create notification work;
- `ELIGIBILITY_BLOCKED` — required known state is absent or denied;
- `PLANNED` — durable outbox item exists; no attempt yet;
- `SUPPRESSED` — explicit approved suppression, no attempt;
- `READY_FOR_ATTEMPT` — may be claimed for delivery under approved policy;
- `ATTEMPT_IN_PROGRESS` — one bounded attempt is active;
- `DELIVERED` — provider adapter outcome accepted as successful delivery boundary;
- `FAILED_RETRYABLE` — failed under a policy that permits bounded retry;
- `FAILED_NON_RETRYABLE` — terminal failure;
- `AMBIGUOUS` — effect cannot be safely classified;
- `RECONCILIATION_REQUIRED` — no blind retry until resolved;
- `CANCELLED` — protected cancellation under approved boundary;
- `EXPIRED` — future time-bound expiry only after policy approval.

A queued item, alive worker, provider HTTP success, Egress transport success or adapter callback does not alone prove delivery success.

## 12. Delivery attempt lifecycle

Required semantic sequence:

```text
committed Scan domain event
→ Notification source intake
→ eligibility decision
→ outbox item commit
→ delivery attempt planned
→ provider adapter request prepared
→ provider adapter dispatch attempted
→ provider outcome received | unknown
→ Notification accepts explicit attempt outcome
→ outbox status updated or reconciliation required
```

Each transition preserves exact outbox item, attempt, adapter, channel, correlation and idempotency identity. No later stage may be inferred from an earlier one.

## 13. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `IngestNotificationSourceEventCommand` | Accept/reject a committed upstream event for notification processing |
| `EvaluateNotificationEligibilityCommand` | Decide whether source event may create outbox work |
| `CreateNotificationOutboxItemCommand` | Create or replay one generic outbox item |
| `ClaimNotificationOutboxItemCommand` | Future protected bounded claim over one delivery item |
| `CreateNotificationAttemptCommand` | Create one bounded delivery attempt under an outbox item |
| `RecordProviderDeliveryOutcomeCommand` | Attach explicit adapter/provider outcome to one attempt |
| `ReconcileNotificationAttemptCommand` | Resolve interrupted/ambiguous delivery attempt |
| `CancelNotificationCommand` | Protected cancellation under explicit effect boundary |
| `SuppressNotificationCommand` | Protected policy-based suppression where approved |
| `GetNotificationOutboxItemQuery` | Read authorized outbox item projection |
| `ListBeaconNotificationsQuery` | Read authorized Beacon-scoped notification history |
| `ListAccountNotificationsQuery` | Read authorized account-scoped notification history |
| `ExplainNotificationDecisionQuery` | Explain intake/eligibility/dedup/attempt outcome |

Mutation-capable inputs require mandatory common contract metadata, authorization scope, idempotency key and normalized fingerprint.

## 14. Public output families

| Output family | Meaning |
|---|---|
| `NotificationSourceIntakeOutcome` | accepted, replayed, rejected, unsupported, ambiguous or blocked |
| `NotificationEligibilityOutcome` | eligible, suppressed, blocked, no-channel, no-target, entitlement-denied or ambiguous |
| `NotificationOutboxOutcome` | created, replayed, suppressed, blocked, conflict or rejected |
| `NotificationAttemptOutcome` | planned, dispatched, delivered, failed-retryable, failed-non-retryable, ambiguous or reconciliation-required |
| `ProviderOutcomeAcceptanceResult` | accepted-success, accepted-failure, accepted-ambiguous, rejected, stale or mismatched |
| `NotificationReconciliationOutcome` | resolved-delivered, resolved-failed, remains-ambiguous or manual-review-required |
| `NotificationReadResult` | authorized safe outbox/attempt/history projection |
| `NotificationExplanationResult` | source, rules, eligibility, dedup and attempt reasoning without secrets |

Outputs remain framework, persistence, queue, transport and provider neutral.

## 15. Mandatory delivery outcome classes

At minimum:

- `NOT_ATTEMPTED`;
- `ATTEMPT_PLANNED`;
- `DISPATCH_AMBIGUOUS`;
- `PROVIDER_ACCEPTED`;
- `PROVIDER_REJECTED`;
- `PROVIDER_UNAVAILABLE`;
- `RATE_OR_ACCESS_RESTRICTED`;
- `MALFORMED_OR_UNUSABLE_PROVIDER_RESPONSE`;
- `DELIVERY_FAILURE`;
- `DELIVERY_AMBIGUOUS`;
- `SUPPRESSED_OR_CANCELLED`;
- `TARGET_UNAVAILABLE_OR_UNVERIFIED`.

Exact wire codes, provider payload fields and HTTP mappings are not selected.

## 16. False-success prohibition

None of the following may become clean notification delivery success:

- source event absent or not committed;
- baseline content without listing-change event;
- eligibility not evaluated;
- entitlement or Beacon lifecycle ambiguous;
- target/channel unresolved;
- provider adapter unavailable;
- provider credentials missing or expired;
- provider dispatch not attempted;
- provider dispatch unknown;
- provider explicit rejection;
- provider rate/access restriction;
- malformed provider response;
- callback/webhook identity mismatch;
- transport failure;
- Egress transport success without accepted provider outcome;
- duplicate source replay without dedup proof;
- reconciliation incomplete.

A provider response with status/bytes/message id is not automatically a user-visible delivery. Notification owns acceptance of adapter outcome into generic delivery state.

## 17. Scan dependency and handoff

Scan Orchestration emits committed domain event facts. Notification Delivery consumes only those facts after Scan commit.

Notification may consume:

- source event contract/version;
- `account_id` where required;
- `beacon_id`;
- `configuration_revision_id`;
- `run_id` and difference reference;
- listing identity reference;
- normalized price key/value representation after approval;
- safe client-card field references/provenance;
- event reason/class;
- correlation/causation;
- safe producer evidence.

Notification must not:

- create or modify `ScanRun`, observation, baseline, difference or listing state;
- infer new listing/price-pair facts directly from Parser or Egress evidence;
- treat Scan success as delivery success;
- roll back Scan state after delivery failure;
- create notifications for baseline contents without a future approved change;
- change comparison semantics.

## 18. Egress dependency

Egress Routing owns route/agent/lease/transport state. Notification Delivery may receive adapter/provider outcomes that internally used Egress, but it does not own Egress state.

Rules:

- Notification does not choose route independently;
- Notification does not create, extend or revoke route leases;
- Notification does not mutate route health/quarantine;
- Egress transport success is not provider delivery success;
- Egress ambiguity remains explicit in attempt state;
- provider adapter must preserve safe Egress correlation where relevant;
- Notification retry cannot bypass Egress reconciliation requirements;
- exact route/transport technology remains Egress/operations scope.

## 19. Telegram and MAX adapter dependency

Telegram Adapter and MAX Adapter are future provider-specific modules.

They may later own:

- provider-specific chat/recipient mapping;
- provider request/response mapping;
- message rendering constraints;
- webhook/callback/ingress mapping;
- provider error interpretation;
- provider-specific delivery proof references;
- provider UI affordances such as buttons/Mini App links after evidence.

Notification Delivery owns:

- generic notification source intake;
- outbox item identity;
- generic delivery attempt identity;
- generic deduplication and retry/reconciliation state;
- acceptance or rejection of adapter outcome into notification state.

Adapters do not own generic outbox state, Scan events, Beacon configuration, account identity, entitlement state or Egress route state.

## 20. Identity, Beacon and Entitlements dependency

Identity & Access supplies approved account/contact/channel target references after its own policies and future adapter playbooks. Notification does not create account identity or weak-merge contacts.

Beacon Management supplies Beacon/account/lifecycle context where required. Notification does not activate, pause, archive or rewrite a Beacon.

Entitlements & Billing supplies effective entitlement decision references where product access affects notification delivery. Notification does not own tariff, payment, subscription or grant state.

Rules:

- ambiguous identity, target, Beacon lifecycle or entitlement decision blocks effect;
- OD-004 controls delivery behavior after access expiry;
- OD-007/OD-008 remain Identity concerns where target linking/merge matters;
- historical notification records do not rewrite historical entitlement or Beacon evidence.

## 21. Idempotency and deduplication rules

Idempotency is required for:

- source event intake;
- eligibility-to-outbox transition;
- outbox item creation;
- attempt creation;
- provider outcome recording;
- cancellation/suppression;
- reconciliation;
- any retryable delivery command.

Required semantics:

- same key + same semantic request + known terminal outcome returns/references original outcome;
- same key + same request + pending/ambiguous outcome returns pending/reconciliation state;
- same key + different fingerprint returns `IDEMPOTENCY_MISMATCH` with no effect;
- missing required key is rejected before effect;
- replay of a source event does not create a second outbox item;
- replay of an attempt outcome does not duplicate state transition;
- duplicate provider callbacks without stable identity preserve ambiguity;
- exact storage/TTL remains open.

Deduplication protects user-visible effect. It cannot be used to hide upstream data conflict or provider ambiguity.

## 22. Commit-point rules

Before implementation, each mutation must define its logical commit point.

### 22.1. Source intake commit

Success means Notification has accepted or explicitly rejected one upstream source event reference. It does not mean outbox work exists.

### 22.2. Outbox commit

Success means one durable generic notification work item exists and is replayable without duplicate effect. It does not mean a provider attempt has started.

### 22.3. Attempt commit

Success means one bounded attempt exists under an outbox item. It does not mean provider dispatch, provider acceptance or user receipt.

### 22.4. Provider outcome commit

Success means Notification has accepted an explicit provider adapter outcome into generic attempt/outbox state. Ambiguous provider outcomes remain ambiguous until reconciled.

No success delivery event is emitted before its defined commit point.

## 23. Interruption and reconciliation

### Before outbox commit

- no delivery work exists;
- replay may create work only under idempotency rules.

### After outbox commit but before provider dispatch

- outbox remains planned/ready;
- safe claim/retry requires exact future policy.

### Dispatch/send state unknown

- attempt becomes ambiguous or reconciliation-required;
- do not issue blind retry;
- preserve adapter, Egress, provider and idempotency evidence.

### Provider outcome recorded but outbox status not updated

- replay/reconciliation must apply the same outcome without duplicate attempt effect;
- do not infer user-visible delivery until commit state is accepted.

### Delivery success committed but response/report lost

- replay returns original outcome/references;
- no duplicate user-visible message attempt is created.

Exact reconciliation sources and timeouts remain future task scope.

## 24. Retry, backoff and rate boundary

Run 19 does not select retry count, delay, backoff, jitter, batch size, rate limit or circuit breaker values.

Future retry requires:

- idempotent attempt boundary;
- duplicate user-visible effect prevention;
- provider-specific permission/evidence;
- Egress ambiguity resolution where applicable;
- channel-specific adapter rules;
- approved rate boundary;
- explicit terminal/non-terminal classification.

Automatic retry is prohibited for unauthorized target, invalid channel, explicit provider rejection that policy marks non-retryable, idempotency mismatch, user opt-out, protected cancellation, unapproved provider permission or ambiguous effect requiring reconciliation.

## 25. Partial and batch outcomes

Batch notification processing must not use one generic success result when individual items differ.

It must expose:

- accepted item count;
- created/replayed/suppressed/blocked item identities or safe references;
- failed item identities or safe references;
- per-item error category;
- retry/reconciliation state per item;
- no raw provider payload or secret.

Batching, digesting and grouping of user-visible messages remain unselected. A future digest policy would be a contract/product change requiring fixtures and acceptance review.

## 26. Security, privacy and retention

- Authorization and ownership checks precede protected read/mutation.
- Cross-account/Beacon existence details follow safe error semantics.
- Notification history is scoped by account and Beacon where applicable.
- Delivery targets are references, not raw secret material.
- Raw provider tokens, bot tokens, cookies, private keys and one-time codes never appear in contracts, logs, fixtures or reports.
- Message content includes only approved safe listing/card facts.
- Full phone, seller private data, full provider payload and unrelated personal data are excluded by default.
- Logs use safe IDs, counts, state classes, channel class, adapter class, reason codes and latency.
- External strings never become shell commands.
- Read models have provenance/freshness and are not authority.
- Retention, deletion, archive and compaction remain OD-013.
- A deletion/retention implementation cannot be invented by agents.

## 27. Observability semantics

Future minimum safe signals:

- source event/outbox/attempt IDs;
- `account_id` and `beacon_id` under authorization;
- source event family and producer version;
- eligibility outcome class;
- outbox lifecycle class;
- channel/adapter class, not raw credentials;
- attempt outcome class;
- retry/reconciliation state;
- dedup replay/conflict counts;
- provider-safe reason class;
- latency and bounded attempt count after policy approval;
- no raw token, cookie, private message overcollection or provider secret.

A green worker, queued item, Egress success, provider response or adapter callback does not prove generic Notification delivery success until accepted by Notification state.

## 28. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity & Access accepted public contracts;
- Entitlements effective-decision contracts;
- Beacon Management lifecycle/read contracts;
- Scan domain event contracts accepted in Run 17;
- Egress/adapter transport evidence after applicable contracts;
- future Telegram Adapter contracts after Run 20 acceptance;
- future MAX Adapter contracts after Run 21 acceptance;
- PostgreSQL/SQLAlchemy/Psycopg selected-with-gate for authoritative durable state;
- Alembic only after physical schema/migration approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- OpenTelemetry boundary after applicable instrumentation task.

Deferred/blocked:

- physical tables/indexes/constraints;
- queue/worker implementation;
- broker/cache;
- scheduler/polling values;
- provider adapter runtime;
- Telegram/MAX bot/API calls;
- message templates;
- provider credentials;
- delivery rate limits/retry values;
- retention tooling;
- services/deploy/runtime.

No Redis, RabbitMQ, Celery, external queue or provider runtime is introduced by this playbook.

## 29. Fake dependencies and test doubles

Future approved fakes may model:

- `ScanDomainEventSource`;
- `NotificationSourceIntakeRepository`;
- `NotificationOutboxRepository`;
- `NotificationAttemptRepository`;
- `NotificationDeduplicationStore`;
- `IdentityChannelTargetGateway`;
- `BeaconEligibilityGateway`;
- `EntitlementDecisionGateway`;
- `ProviderAdapterGateway`;
- `EgressCorrelationReader`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic accounts, Beacons, source events, listing references, channels, targets and provider outcomes only. They do not prove Telegram/MAX behavior, provider permission, user receipt or production durability.

## 30. Required fixtures and test vectors

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
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-ND-SOURCE-LISTING-FIRST-SEEN-001`;
- `FX-ND-SOURCE-PRICE-PAIR-FIRST-SEEN-001`;
- `FX-ND-BASELINE-NO-OUTBOX-001`;
- `FX-ND-SCAN-SUCCESS-NOT-DELIVERY-001`;
- `FX-ND-EGRESS-SUCCESS-NOT-DELIVERY-001`;
- `FX-ND-PARSER-SUCCESS-NOT-DELIVERY-001`;
- `FX-ND-OUTBOX-IDEMPOTENT-REPLAY-001`;
- `FX-ND-DEDUPE-SOURCE-REPLAY-001`;
- `FX-ND-IDEMPOTENCY-MISMATCH-001`;
- `FX-ND-NO-CHANNEL-BLOCKED-001`;
- `FX-ND-TARGET-UNVERIFIED-BLOCKED-001`;
- `FX-ND-ENTITLEMENT-AMBIGUOUS-BLOCKS-001`;
- `FX-ND-OD004-EXPIRY-BLOCKED-001`;
- `FX-ND-PROVIDER-ACCEPTED-001`;
- `FX-ND-PROVIDER-REJECTED-001`;
- `FX-ND-PROVIDER-AMBIGUOUS-RECONCILE-001`;
- `FX-ND-DUPLICATE-CALLBACK-RECONCILE-001`;
- `FX-ND-PRECOMMIT-INTERRUPTION-001`;
- `FX-ND-POSTCOMMIT-REPLAY-001`;
- `FX-ND-BATCH-PARTIAL-001`;
- `FX-ND-RETRY-VALUE-BLOCKED-001`;
- `FX-ND-RETENTION-OD013-BLOCKED-001`;
- `FX-ND-SECRET-REDACTION-001`;
- `FX-ND-CROSS-BEACON-ISOLATION-001`;
- `FX-ND-TELEGRAM-ADAPTER-BOUNDARY-001`;
- `FX-ND-MAX-ADAPTER-BOUNDARY-001`.

Run 19 creates no fixture files and executes no tests.

## 31. Acceptance Matrix coverage

Run 19 documentation coverage:

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
- `AM-EGRESS-001`;
- `AM-REF-001`–`AM-REF-004`;
- `AM-MIG-008`–`AM-MIG-009` where applicable;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, queue, worker, provider adapter, Telegram/MAX and notification executions remain future gates and are not passed by this documentation run.

## 32. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral notification records/contracts;
- implement synthetic deterministic source-intake/outbox/dedup rules;
- prove baseline-no-notification and scan-event-to-outbox semantics;
- implement durable PostgreSQL-owned notification state after physical schema/migration approval;
- integrate accepted Scan event contracts;
- integrate future Telegram/MAX adapter contracts after their playbooks;
- add bounded worker/queue behavior after retry/rate/time decisions;
- add observability, idempotency and reconciliation evidence;
- add approved read models with provenance.

## 33. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create tables, migrations, ORM models or physical schemas;
- create queues, brokers, workers, schedulers or services;
- install dependencies or create lockfiles;
- send Telegram, MAX or other provider requests;
- create bots, webhooks, Mini Apps or provider credentials;
- create provider-specific message templates;
- select retry counts, delays, backoff, rate limits or quiet hours;
- select channel priority, fallback or future channels;
- invent behavior after entitlement expiry;
- invent retention/deletion policy;
- treat Scan, Parser or Egress success as delivery success;
- create notifications for baseline contents;
- retry ambiguous provider send blindly;
- write Scan, Parser, Egress, Beacon, Identity or Entitlement state directly;
- store raw provider payloads, tokens, cookies, secrets or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 34. Report and handoff requirements

Any future implementation/proof task touching Notification Delivery must report:

- exact GitHub SHA and paths;
- module playbook version used;
- exact source events and fixture IDs;
- created/changed files and hashes;
- whether product-code, migrations, dependency files, database, runtime or provider calls were created;
- exact tests and outputs;
- idempotency/dedup/reconciliation evidence;
- secret and personal-data redaction evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 35. Roadmap after this playbook

1. Synchronize exact Run 19 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Run 20 — Telegram Adapter Module Playbook.
4. Run 21 — MAX Adapter Module Playbook.
5. Run 22 — Admin & Support Module Playbook.
6. Run 23 — Web Cabinet Module Playbook.
7. Run 24 — Filter Catalog & Builder Module Playbook.
8. Final independent documentation audit and explicit owner decision before any product-code track.

This playbook is a prerequisite only and does not authorize implementation.

## 36. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `ND-HISTORY-0001` | 2026-07-08 | Run 19 created Notification Delivery Module Playbook v1.0 and fixed generic notification event/outbox/attempt/reconciliation boundaries without implementation. | Public GitHub `main`; Run 19 publication commit; no runtime artifacts. |
