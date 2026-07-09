# Маяк Авито — Scan Privacy, Observability and Retention Boundary v1.0

## Metadata
- status: approved semantic documentation for SOLS-12;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f, SOLS-08 accepted at 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6, SOLS-09 accepted at dbfa556c1e6b78091b76005cd7f68cb2bca2565f, SOLS-10 accepted at ab8959cc1134b5c00973ef69814ec4c97a33bb1e, SOLS-11 accepted at 7d20eaffadaa2373eb3ea409251b119d8e6479bc;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization;
- physical retention/compaction/deletion remains gated by OD-013 and future DB/persistence decisions.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines the safe privacy, observability and retention boundary for Scan.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define the minimal safe technical and semantic state Scan may keep for lifecycle, idempotency, replay, comparison, recovery and safe diagnostics;
- keep privacy minimization explicit for success, failure, ambiguous, pending recovery, lost anchors, overlap and reconciliation states;
- separate safe observability from raw provider evidence, provider secrets and full archive behavior;
- keep retention, compaction and deletion policy decisions outside Scan-owned semantic state;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no full listing archive, raw provider payload retention, unbounded observation history, views/analytics history, phone/seller/full-description Scan storage or secret retention;
- no retention duration, deletion cadence, compaction algorithm, storage table, index, transaction, lock or rebuild job choice;
- no live Avito/provider traffic;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no assumption that OD-013 is closed.

## 2. Privacy boundary

- Scan may keep only minimal safe technical and semantic state needed for scan lifecycle, idempotency, replay, comparison, recovery and safe diagnostics.
- Scan does not create a full user-visible listing archive.
- Privacy minimization applies to success, failure, ambiguous, pending recovery, lost anchors, overlap and reconciliation states.
- Safe state is reference-minimal, not archive-shaped.
- Any state that can be represented as identifiers, bounded classes or safe references must not be expanded into raw evidence.

## 3. Observability boundary

- Safe diagnostics may identify the run, attempt, claim, Beacon and revision references, but not raw provider payloads or provider secrets.
- Safe observability may include `run_id`, `attempt_id`, `claim_id`, `beacon_id`, revision reference, lifecycle class, parser outcome class/profile/reference identity, counts, anchor match result, baseline/difference classification, status class, overlap/conflict/replay/reconciliation state, safe failure reason, latency/freshness, correlation/causation IDs and rules version.
- Observability is semantic, not transport, provider or delivery evidence.
- Repeated replay must reuse the same safe reference set rather than multiplying facts.
- Safe observability does not authorize new retained content.

## 4. Retention boundary

- Scan retains only compact semantic memory and safe diagnostics.
- Rolling anchors are compact memory, not an archive.
- Scan must not retain raw provider payloads, full HTML, full JSON, cookies, tokens, session values, private route details, foreign-account data, phone, seller, full description, full listing-card archive, unbounded observation history, views/analytics history or secrets.
- Retention applies equally to success and failure paths.
- Retention is bounded by OD-013 and future DB/persistence decisions.

## 5. Safe diagnostics/read-model signals

The following signal families are allowed safe semantic families for Scan. They are docs-only families, not persisted enum names, not wire schema values and not DB values.

| Family | Meaning | Allowed fields/references | Privacy/minimization rule | Forbidden retained data |
|---|---|---|---|---|
| `RunIdentitySignal` | Safe identity of one logical run. | `run_id`, Beacon/revision scope, run lifecycle class, correlation reference. | Keep only the identifiers needed to link lifecycle and replay. | Raw provider payloads, provider secrets, full card history. |
| `AttemptIdentitySignal` | Safe identity of one bounded attempt under a run. | `attempt_id`, `run_id`, attempt class, reconciliation reference. | Keep attempt identity only as a bounded run reference. | Transport traces, cookies, tokens, session values. |
| `ClaimIdentitySignal` | Safe identity of the current claim over internal work. | `claim_id`, `run_id`, claim class, overlap/conflict reference. | Keep claim identity only as a bounded concurrency reference. | Lease internals, lock details, queue internals. |
| `BeaconRevisionReferenceSignal` | Safe reference to the Beacon and immutable revision scope. | `beacon_id`, revision reference, lifecycle class, rules version. | Keep only scope references needed for comparison and replay. | Beacon source editing details, private route details. |
| `RunLifecycleClassSignal` | Safe lifecycle class for the logical run. | Run lifecycle class, `run_id`, `attempt_id`, correlation reference. | Record class only, not transport or payload details. | Full provider archive, raw HTML/JSON. |
| `ParserOutcomeReferenceSignal` | Safe reference to explicit parser outcome evidence. | Parser outcome class/profile/reference identity, `run_id`, `attempt_id`. | Keep the reference, not the raw parser evidence. | Raw provider payloads, full parser dumps, secrets. |
| `ParserOutcomeClassSignal` | Safe parser-outcome classification. | Parser outcome class, counts, reconciliation reference. | Keep class-level outcome only. | Full HTML, full JSON, session values. |
| `ParserProfileReferenceSignal` | Safe reference to parser compatibility/profile identity. | Parser profile reference, parser outcome reference, Beacon/revision scope. | Keep profile reference only as compatibility evidence. | Parser implementation internals, mapping tables. |
| `AcceptedFailedPartialAmbiguousCountsSignal` | Safe counts for accepted, failed, partial and ambiguous units. | Counts, parser outcome class, lifecycle class. | Keep bounded counts, not per-item archive history. | Unbounded observation history, full card archive. |
| `AnchorMatchResultSignal` | Safe result of anchor comparison. | Anchor match result, anchor reference, baseline reference. | Keep compact match result only. | Full listing archive, raw provider payloads. |
| `BaselineClassificationSignal` | Safe baseline classification. | Baseline class, baseline reference, revision reference. | Keep baseline class only. | Archive reconstruction, unbounded history. |
| `DifferenceClassificationSignal` | Safe difference classification. | Difference class, comparison scope, anchor match result. | Keep difference class only. | Raw payloads, full history, secret data. |
| `NewListingStatusSignal` | Safe signal that new listings were found after baseline. | New-listing status class, counts, run reference. | Keep only minimal status and counts. | Full listing-card archive, delivery history. |
| `NoNewStatusSignal` | Safe no-new status. | No-new status class, counts, run reference. | Keep stable no-new semantics only. | Interval spam history, full archive. |
| `LostAnchorStatusSignal` | Safe lost-anchor status. | Lost-anchor status class, recovery reference, top-window reference. | Keep state-restored/latest-fresh semantics only. | Confirmed new-listing archive, raw provider evidence. |
| `RecoveryStatusSignal` | Safe recovery status. | Recovery class, pending/committed recovery reference. | Keep only one recovery obligation and its settlement state. | Accumulated missed-scan backlog, raw payloads. |
| `OverlapConflictSignal` | Safe overlap/conflict signal. | Overlap class, claim reference, run reference. | Keep overlap as a bounded concurrency fact only. | Duplicate parser work, duplicate facts. |
| `ReplayIdempotencySignal` | Safe replay/idempotency reference. | Replay reference, request fingerprint, original outcome reference. | Keep one replay reference, not multiplied outcomes. | Duplicate observation history, duplicate archive. |
| `ReconciliationStateSignal` | Safe reconciliation state. | Reconciliation class, missing-dispatch or lost-response reference. | Keep unresolved state minimal and bounded. | Blind retry traces, raw payloads, secrets. |
| `SafeFailureReasonSignal` | Safe failure reason category. | Safe failure reason, lifecycle/recovery reference, counts. | Keep minimized reason category only. | Route secrets, provider secrets, private route details. |
| `LatencyFreshnessSignal` | Safe latency/freshness observation. | Latency/freshness class, run reference, attempt reference. | Keep derived freshness only, not raw timing traces. | Detailed timing traces, transport payloads. |
| `CorrelationCausationSignal` | Safe correlation and causation linkage. | Correlation ID, causation ID, run/attempt/claim references. | Keep linkage identifiers only. | Sensitive source text, payload contents. |
| `RulesVersionSignal` | Safe reference to the semantic rules version in force. | Rules version, revision scope, run reference. | Keep version reference only. | Runtime config dumps, secrets, schema internals. |

## 6. Excluded by default

The following data families are excluded by default from Scan. They may belong to another module or to a future gate, but they are not Scan-owned state.

| Family | Why excluded from Scan | Owner module or future gate | Forbidden Scan assumption |
|---|---|---|---|
| `RawProviderPayload` | It is parser/provider evidence, not Scan-owned retained state. | Parser Adapter / Provider evidence boundary, OD-013 gate. | Scan may store raw provider payloads as its own state. |
| `FullProviderHTML` | It is raw evidence and can expose private content. | Parser Adapter / Provider boundary, OD-013 gate. | Scan may keep full HTML as an observability record. |
| `FullProviderJSON` | It is raw evidence and can expose full item history. | Parser Adapter / Provider boundary, OD-013 gate. | Scan may store full JSON as retained history. |
| `CookieTokenSessionValue` | It is authentication material and must not be Scan-owned. | Auth/session owner, security boundary, future runtime gate. | Scan may retain cookies, tokens or session values. |
| `PrivateRouteDetails` | It belongs to route/egress mechanics, not Scan state. | Egress / route ownership, future gate. | Scan may store private route details. |
| `ForeignAccountData` | It is foreign account evidence, not Scan lifecycle state. | Provider boundary, Parser Adapter evidence gate. | Scan may retain foreign-account data. |
| `PhoneNumberData` | It is personal contact data and not required for Scan lifecycle. | Notification Delivery / future presentation gates. | Scan may store phone numbers as Scan state. |
| `SellerIdentityData` | It is seller identity evidence, not Scan state. | Parser/Provider evidence boundary. | Scan may store seller identity as retained history. |
| `FullListingDescriptionData` | It is full content evidence and exceeds minimal Scan need. | Parser/Provider boundary, future display gate. | Scan may store full descriptions. |
| `FullListingCardArchive` | It would turn Scan into a user-visible archive. | Future read-model/archive gate, OD-013 boundary. | Scan may own a full listing archive. |
| `UnboundedObservationHistory` | It violates compact-memory retention. | OD-013 and future DB/persistence decisions. | Scan may keep unbounded observation history. |
| `ViewsAnalyticsHistory` | It belongs to future product analytics, not Scan. | Future Admin/Web modules. | Scan may own views/analytics history. |
| `NotificationDeliveryAttemptHistory` | It belongs to delivery ownership, not Scan. | Notification Delivery. | Scan may own outbox/delivery history. |
| `PaymentEntitlementHistory` | It belongs to billing/entitlement ownership, not Scan. | Entitlements & Billing. | Scan may mutate or retain payment history. |
| `AdminAuditHistory` | It belongs to future Admin ownership, not Scan. | Future Admin module gate. | Scan may own admin audit history. |
| `SecretCredentialMaterial` | It is secret material and must stay outside Scan. | Security/secrets boundary, future runtime gate. | Scan may retain secrets because they are useful for diagnostics. |

## 7. Rolling anchors versus full archive

- Rolling anchors are compact memory, not full history.
- Rolling anchors support comparison continuity, idempotency, replay and recovery.
- Rolling anchors are not a user-visible listing archive and not a complete account history.
- Rolling anchors must not expand into full listing-card archives, full descriptions, phones, sellers or raw provider payloads.
- The safe comparison memory can be sufficient even when archive-shaped state is forbidden.

## 8. Raw provider payload boundary

- Raw provider payload is Parser/Provider/Egress evidence boundary, not Scan-owned state.
- Scan may reference parser outcome identity, parser outcome class and safe comparison references, but not raw payload contents.
- Raw payload retention is excluded by default and remains constrained by OD-013 and future DB/persistence decisions.
- Scan must not infer that raw payload retention is required for lifecycle, replay or safe diagnostics.

## 9. Personal/provider-sensitive data boundary

- Scan must not retain phone, seller, full description, cookie, token, session, private route or secret material.
- Personal/provider-sensitive data is excluded even when it would be convenient for debugging or replay.
- Minimization applies to both successful and failed states.
- No Scan-owned state may depend on hidden personal data to remain meaningful.

## 10. Correlation and causation boundary

- Safe correlation and causation identifiers are allowed for replay, diagnostics and idempotency.
- Correlation does not authorize causal inference beyond the committed semantic boundary.
- Causation references must stay bounded to run/attempt/claim/reconciliation identities.
- Correlation/causation IDs are references, not evidence payloads.

## 11. Latency/freshness/counts boundary

- Scan may expose latency and freshness as safe derived classes, not raw timing traces.
- Scan may expose accepted/failed/partial/ambiguous counts as bounded comparison signals.
- Counts are semantic summaries, not observation archives.
- Freshness and counts must not be inflated into full history or raw provider evidence.

## 12. Failure reason and status visibility

- Safe failure reason is a minimized category, not a raw provider trace.
- Safe status visibility may identify run state, recovery state, overlap state, lifecycle state and reconciliation state.
- Status visibility must not reveal provider secrets, route details, contacts, phone data or seller data.
- Privacy minimization applies equally to external failure, pending recovery and ambiguous states.

## 13. Retention/compaction/deletion gate

- Physical retention, compaction, deletion and rebuild jobs remain gated by OD-013 and future DB/persistence decisions.
- Scan must not choose retention duration, deletion cadence, compaction algorithm, storage table, index, transaction, lock or rebuild job.
- No retention policy choice is authorized here.
- No physical persistence implementation is authorized here.

## 14. OD-013 remains open

- OD-013 remains open.
- Do not close OD-013 by assumption.
- This document only defines safe semantic boundaries while the physical retention question remains unresolved.
- If a future document changes OD-013, it must do so explicitly.

## 15. Cross-module ownership boundary

- Parser/Provider/Egress owns raw evidence, transport classification and route mechanics.
- Notification Delivery owns delivery, outbox and delivery history.
- Web/Admin analytics history belongs to future Admin/Web modules, not Scan.
- Entitlements & Billing owns payment and entitlement history.
- Security owns secret credential material.
- Scan owns only minimal safe semantic state for its lifecycle, replay, comparison and recovery obligations.

## 16. Replay/idempotency observability safety

- Replay must not duplicate scan facts or expand retained data.
- Idempotent replay reuses the same safe references and the same bounded classes.
- Replay must not turn safe summaries into archive-shaped retained history.
- Replay must not create new raw payload retention just because a fact was replayed.
- Replay observability must remain privacy-minimized in success, failure, ambiguous, pending recovery, lost-anchor, overlap and reconciliation states.

## 17. Forbidden assumptions

- Scan may store raw provider payloads, full HTML, full JSON, cookies, tokens, session values or secret material.
- Scan may store phone, seller or full description data as its own lifecycle state.
- Scan may create a full listing-card archive.
- Scan may keep unbounded observation history.
- Scan may keep views/analytics history.
- Scan may own notification delivery history.
- Scan may choose retention duration, deletion cadence, compaction algorithm or rebuild job.
- Scan may close OD-013 by assumption.
- Scan may rely on raw payload retention to justify safe diagnostics.
- Scan may treat replay as permission to expand retained data.
- Scan may use personal/provider-sensitive data as a required Scan dependency.

## 18. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed observability/retention effect | Forbidden false outcome |
|---|---|---|---|---|
| `SAFE_SCAN_DIAGNOSTIC_SIGNAL_ALLOWED` | A diagnostic signal is safe to expose at Scan boundary. | Run/attempt/claim references, safe lifecycle/status class, safe failure/recovery reference. | Keep minimal diagnostic references only. | Exposing raw payloads or provider secrets. |
| `SAFE_READ_MODEL_SIGNAL_ALLOWED` | A safe read-model signal is allowed without archive expansion. | Run identity, status class, counts, correlation references. | Keep safe read-model summaries only. | Turning read-model safety into full archive retention. |
| `ROLLING_ANCHOR_COMPACT_MEMORY_ONLY` | Rolling anchors are compact memory only. | Anchor reference, baseline reference, Beacon/revision scope. | Retain only anchor-comparison memory. | Full listing archive or unbounded history. |
| `FULL_LISTING_ARCHIVE_FORBIDDEN` | A full listing archive is not allowed in Scan. | Full-card/description/phone/seller evidence boundary. | Prevent archive-shaped retention. | Archive creation or archive replay inside Scan. |
| `RAW_PROVIDER_PAYLOAD_RETENTION_FORBIDDEN` | Raw provider payload retention is forbidden in Scan. | Parser/Provider evidence boundary, OD-013 gate. | Keep payloads outside Scan-owned state. | Raw HTML/JSON retained as Scan state. |
| `PHONE_SELLER_DESCRIPTION_RETENTION_FORBIDDEN` | Phone, seller and full-description retention is forbidden. | Personal/provider-sensitive data boundary. | Keep only minimal identifiers. | Full contact/content retention in Scan. |
| `COOKIE_TOKEN_SESSION_RETENTION_FORBIDDEN` | Cookies, tokens and session values are forbidden. | Auth/session boundary, security gate. | Keep credential material outside Scan. | Session material retained for convenience. |
| `PRIVATE_ROUTE_DETAILS_NOT_SCAN_OWNED` | Private route details are not owned by Scan. | Egress/route ownership boundary. | Keep route mechanics outside Scan. | Scan-owned route detail retention. |
| `UNBOUNDED_OBSERVATION_HISTORY_FORBIDDEN` | Unbounded observation history is forbidden. | Compact-memory boundary, OD-013 gate. | Keep only bounded semantic history. | Infinite observation retention. |
| `VIEWS_ANALYTICS_HISTORY_NOT_SCAN_OWNED` | Views and analytics history is not Scan-owned. | Future Admin/Web ownership boundary. | Keep analytics outside Scan. | Scan-owned analytics history. |
| `NOTIFICATION_DELIVERY_HISTORY_NOT_SCAN_OWNED` | Notification delivery history is not Scan-owned. | Notification Delivery boundary. | Keep delivery history outside Scan. | Scan-owned outbox/delivery history. |
| `RETENTION_POLICY_GATED_BY_OD_013` | Retention policy is gated by OD-013. | OD-013 open status, future DB/persistence gate. | Keep policy unresolved in Scan docs. | Retention duration chosen by Scan. |
| `COMPACTION_POLICY_GATED_BY_OD_013` | Compaction policy is gated by OD-013. | OD-013 open status, future DB/persistence gate. | Keep compaction unresolved in Scan docs. | Compaction algorithm chosen by Scan. |
| `DELETION_POLICY_GATED_BY_OD_013` | Deletion policy is gated by OD-013. | OD-013 open status, future DB/persistence gate. | Keep deletion unresolved in Scan docs. | Deletion cadence chosen by Scan. |
| `REBUILD_JOB_GATED_BY_DB_RUNTIME` | Rebuild jobs belong to future DB/runtime decisions. | Future DB/runtime gate, OD-013 open status. | Keep rebuild jobs out of Scan scope. | Rebuild job introduced in Scan documentation as a chosen design. |
| `SAFE_FAILURE_REASON_MINIMIZED` | Failure reason is minimized to a safe category. | Safe failure reason, lifecycle/recovery reference. | Keep only safe reason categories. | Route secrets or payload dumps. |
| `CORRELATION_CAUSATION_SAFE_REFERENCE` | Correlation/causation references are safe. | Correlation ID, causation ID, run/attempt/claim references. | Keep link identifiers only. | Payload contents exposed via linkage fields. |
| `REPLAY_OBSERVABILITY_NO_DATA_EXPANSION` | Replay does not expand retained data. | Replay reference, original outcome reference, safe status class. | Preserve the same bounded observability set. | Replay creating wider retained history. |
| `AMBIGUOUS_STATE_PRIVACY_MINIMIZED` | Ambiguous state must stay privacy-minimized. | Ambiguous status class, reconciliation reference. | Keep ambiguous state bounded. | Ambiguous state leaking raw provider evidence. |
| `RECOVERY_STATE_PRIVACY_MINIMIZED` | Recovery state must stay privacy-minimized. | Recovery class, pending/committed recovery reference. | Keep recovery state minimal. | Recovery state becoming archive-shaped. |
| `LOST_ANCHORS_STATE_PRIVACY_MINIMIZED` | Lost-anchor state must stay privacy-minimized. | Lost-anchor status class, top-window recovery reference. | Keep lost-anchor state minimal and safe. | Lost-anchor state exposing raw payloads or archive history. |

## 19. Synthetic examples

### EX-SOLS-12-SAFE-RUN-ID-DIAGNOSTIC-001
- Synthetic setup: one logical scan run is in a safe diagnostic state and only its run identity is needed for replay and lifecycle tracking.
- Expected classification: `SAFE_SCAN_DIAGNOSTIC_SIGNAL_ALLOWED`.
- Expected safe signal/retention effect: expose `run_id` and bounded lifecycle references only.
- Expected privacy/minimization effect: keep the record compact and reference-only.
- Forbidden false outcome: a raw payload archive or secret-bearing state.

### EX-SOLS-12-SAFE-BEACON-REVISION-REFERENCE-001
- Synthetic setup: a safe diagnostic view needs only the Beacon and immutable revision reference for comparison context.
- Expected classification: `CORRELATION_CAUSATION_SAFE_REFERENCE`.
- Expected safe signal/retention effect: expose `beacon_id`, revision reference and correlation linkage only.
- Expected privacy/minimization effect: do not retain route details, payloads or owner secrets.
- Forbidden false outcome: Scan-owned Beacon source mutation.

### EX-SOLS-12-PARSER-OUTCOME-REFERENCE-NO-RAW-PAYLOAD-001
- Synthetic setup: Scan records an explicit parser outcome reference for comparison eligibility.
- Expected classification: `SAFE_SCAN_DIAGNOSTIC_SIGNAL_ALLOWED`.
- Expected safe signal/retention effect: keep parser outcome class/reference only.
- Expected privacy/minimization effect: no raw HTML, JSON or provider payload retention.
- Forbidden false outcome: a full parser dump in Scan state.

### EX-SOLS-12-COUNTS-ALLOWED-NO-FULL-CARDS-001
- Synthetic setup: one run has accepted, failed, partial and ambiguous counts for comparison summaries.
- Expected classification: `SAFE_READ_MODEL_SIGNAL_ALLOWED`.
- Expected safe signal/retention effect: expose bounded counts only.
- Expected privacy/minimization effect: no card archive, no unbounded history.
- Forbidden false outcome: per-item archive expansion.

### EX-SOLS-12-ROLLING-ANCHORS-NOT-ARCHIVE-001
- Synthetic setup: rolling anchors are used to compare a future top-window.
- Expected classification: `ROLLING_ANCHOR_COMPACT_MEMORY_ONLY`.
- Expected safe signal/retention effect: retain compact anchor memory only.
- Expected privacy/minimization effect: no full listing-card archive, no raw provider evidence.
- Forbidden false outcome: archive-shaped anchor storage.

### EX-SOLS-12-NEW-LISTING-STATUS-NO-FULL-HISTORY-001
- Synthetic setup: a committed comparison finds new listings after baseline and emits a safe status.
- Expected classification: `SAFE_READ_MODEL_SIGNAL_ALLOWED`.
- Expected safe signal/retention effect: expose `NewListingStatusSignal` and counts only.
- Expected privacy/minimization effect: do not retain full listing history or delivery history.
- Forbidden false outcome: user-visible archive retention in Scan.

### EX-SOLS-12-EXTERNAL-FAILURE-SAFE-REASON-NO-ROUTE-SECRET-001
- Synthetic setup: an external failure occurs and only a safe failure reason is needed.
- Expected classification: `SAFE_FAILURE_REASON_MINIMIZED`.
- Expected safe signal/retention effect: expose a minimized failure category only.
- Expected privacy/minimization effect: do not reveal route secrets, cookies or payload contents.
- Forbidden false outcome: route self-healing details inside Scan state.

### EX-SOLS-12-CAPTCHA-STATUS-NO-BYPASS-DATA-001
- Synthetic setup: a CAPTCHA barrier is represented as a safe blocker status.
- Expected classification: `SAFE_FAILURE_REASON_MINIMIZED`.
- Expected safe signal/retention effect: keep the blocker as a minimized safe status only.
- Expected privacy/minimization effect: do not store bypass data, challenge internals or cookies.
- Forbidden false outcome: CAPTCHA bypass state in Scan-owned retention.

### EX-SOLS-12-RECOVERY-PENDING-MINIMAL-STATE-001
- Synthetic setup: a pending recovery obligation exists after an external blocker.
- Expected classification: `RECOVERY_STATE_PRIVACY_MINIMIZED`.
- Expected safe signal/retention effect: keep one pending recovery obligation only.
- Expected privacy/minimization effect: no backlog accumulation or raw blocker payloads.
- Forbidden false outcome: multiple missed-scan records as Scan-owned history.

### EX-SOLS-12-LOST-ANCHORS-MINIMAL-DIAGNOSTIC-001
- Synthetic setup: lost anchors are detected and only the minimal recovery diagnostic is needed.
- Expected classification: `LOST_ANCHORS_STATE_PRIVACY_MINIMIZED`.
- Expected safe signal/retention effect: expose lost-anchor recovery state only.
- Expected privacy/minimization effect: no raw evidence, no archive reconstruction.
- Forbidden false outcome: confirmed new-listing archive from lost anchors.

### EX-SOLS-12-OVERLAP-CONFLICT-SAFE-DIAGNOSTIC-001
- Synthetic setup: two overlapping requests collide for the same Beacon scope.
- Expected classification: `SAFE_SCAN_DIAGNOSTIC_SIGNAL_ALLOWED`.
- Expected safe signal/retention effect: expose overlap/conflict state only.
- Expected privacy/minimization effect: no duplicate parser work, no duplicate facts.
- Forbidden false outcome: silent last-write-wins or expanded history.

### EX-SOLS-12-RECONCILIATION-REQUIRED-NO-BLIND-RAW-PAYLOAD-001
- Synthetic setup: dispatch or outcome continuity is unknown and requires reconciliation.
- Expected classification: `REPLAY_OBSERVABILITY_NO_DATA_EXPANSION`.
- Expected safe signal/retention effect: keep the reconciliation reference only.
- Expected privacy/minimization effect: no blind retry payload retention or raw dumps.
- Forbidden false outcome: reconciliation resolved by guesswork.

### EX-SOLS-12-NOTIFICATION-DELIVERY-HISTORY-OUTSIDE-SCAN-001
- Synthetic setup: a downstream consumer wants delivery history.
- Expected classification: `NOTIFICATION_DELIVERY_HISTORY_NOT_SCAN_OWNED`.
- Expected safe signal/retention effect: keep delivery history out of Scan.
- Expected privacy/minimization effect: do not copy outbox/delivery history into Scan.
- Forbidden false outcome: Scan-owned notification delivery logs.

### EX-SOLS-12-WEB-ANALYTICS-HISTORY-OUTSIDE-SCAN-001
- Synthetic setup: future Web/Admin analytics history is requested from the scan boundary.
- Expected classification: `VIEWS_ANALYTICS_HISTORY_NOT_SCAN_OWNED`.
- Expected safe signal/retention effect: keep analytics history outside Scan.
- Expected privacy/minimization effect: do not retain views analytics history in Scan.
- Forbidden false outcome: Scan-owned analytics archive.

### EX-SOLS-12-RETENTION-DURATION-GATED-OD-013-001
- Synthetic setup: someone asks for a concrete retention duration inside Scan docs.
- Expected classification: `RETENTION_POLICY_GATED_BY_OD_013`.
- Expected safe signal/retention effect: leave duration unspecified in Scan.
- Expected privacy/minimization effect: do not choose a numeric retention default.
- Forbidden false outcome: invented retention cadence or TTL.

### EX-SOLS-12-DELETION-COMPACTION-GATED-OD-013-001
- Synthetic setup: someone asks Scan to define deletion or compaction behavior.
- Expected classification: `DELETION_POLICY_GATED_BY_OD_013`.
- Expected safe signal/retention effect: keep deletion/compaction unresolved and gated.
- Expected privacy/minimization effect: no deletion or compaction algorithm in Scan.
- Forbidden false outcome: a concrete deletion job or compaction job in Scan scope.

### EX-SOLS-12-REPLAY-DOES-NOT-EXPAND-RETENTION-001
- Synthetic setup: a committed safe scan result is replayed for the same logical request.
- Expected classification: `REPLAY_OBSERVABILITY_NO_DATA_EXPANSION`.
- Expected safe signal/retention effect: reuse the same bounded observability set.
- Expected privacy/minimization effect: no new retained data, no widened archive.
- Forbidden false outcome: replay expanding retained history.
