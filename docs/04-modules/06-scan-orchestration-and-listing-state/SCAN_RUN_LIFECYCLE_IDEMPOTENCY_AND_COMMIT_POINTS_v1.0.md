# Маяк Авито — Scan Run Lifecycle, Idempotency and Commit Points v1.0

## Metadata
- status: approved semantic documentation for SOLS-04;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic lifecycle, idempotency and commit-point boundaries for one logical scan run.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define the semantic run lifecycle after a scan intent has been accepted for evaluation;
- keep idempotency, replay and commit points explicit for the same logical run;
- separate durable work from process-local memory;
- separate parser outcome recording from comparison commit;
- separate comparison commit from status exposure and notification delivery;
- preserve baseline and anchors across partial, failed, ambiguous or interrupted outcomes;
- document synthetic examples only.

Non-goals:

- no code, test, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no numeric default for interval, retry, backoff, claim lease, heartbeat, window or TTL;
- no live Avito/provider traffic;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no production persistence design or physical uniqueness design.

## 2. Lifecycle model overview

The run lifecycle is a semantic progression, not an implementation contract.

Canonical direction:

- `REQUESTED` accepts the semantic request for evaluation;
- `BLOCKED`, `PLANNED` or `SUPERSEDED_BEFORE_EFFECT` may follow depending on eligibility and overlap facts;
- `PLANNED` may become `CLAIMED` when durable work is accepted;
- `CLAIMED` may become `DISPATCH_PENDING` or `IN_PROGRESS` when a bounded attempt begins;
- `IN_PROGRESS` may produce `PARSER_OUTCOME_RECEIVED`, `PARTIAL`, `FAILED`, `AMBIGUOUS`, `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` or `RECONCILIATION_REQUIRED`;
- `PARSER_OUTCOME_RECEIVED` may advance only to `COMPARISON_PENDING`;
- `COMPARISON_PENDING` may advance to one of the committed success classes or to a recovery/ambiguity class;
- terminal or visible facts may then be reflected as `STATUS_FACT_COMMITTED` and, only after the visibility recheck, `USER_VISIBLE_RESULT_ELIGIBLE_COMMIT`.

The same logical run is replayed, not duplicated.
A later replay can reference the original outcome, pending state or reconciliation obligation.
A replay must not create a second logical run, second baseline, duplicate anchor update or duplicate user-visible fact.

## 3. Lifecycle classes

The following are semantic docs-only classes. They are not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Allowed source facts / references | What it does not prove | Allowed next semantic direction | Forbidden transition |
|---|---|---|---|---|---|
| `REQUESTED` | The semantic request has been accepted for evaluation, but no durable work is yet authoritative. | Explicit `ScanIntent`, idempotency key, semantic fingerprint, Beacon/revision scope, contract and eligibility references. | Does not prove durable work, worker claim, parser outcome, comparison success, user-visible exposure or notification delivery. | May move to `BLOCKED`, `PLANNED` or `SUPERSEDED_BEFORE_EFFECT` for the same logical request. | Must not jump directly to any `SUCCEEDED_*` class or to user-visible commit. |
| `BLOCKED` | A known precondition or idempotency rule prevents effect. | Blocked eligibility, entitlement, lifecycle, overlap, contract or idempotency mismatch facts. | Does not prove a failed provider call, a completed parser outcome or a committed comparison. | May remain blocked, move to `RECONCILIATION_REQUIRED`, or later re-enter `REQUESTED` only through a new eligible semantic request. | Must not silently become success or create a new logical run. |
| `PLANNED` | Durable work has been accepted under the approved semantic path. | `REQUESTED` plus durable-work acceptance facts and the same run identity. | Does not prove claim ownership, dispatch, parser success or comparison success. | May move to `CLAIMED`, `CANCELLED` or `RECONCILIATION_REQUIRED`. | Must not become any `SUCCEEDED_*` class without later comparison commit. |
| `CLAIMED` | One bounded internal claim exists for the logical run. | `PLANNED` plus claim evidence and the same run identity. | Does not prove external dispatch, provider success, parser success or final comparison. | May move to `DISPATCH_PENDING`, `IN_PROGRESS`, `CANCELLED` or `RECONCILIATION_REQUIRED`. | Must not be treated as scan success. |
| `DISPATCH_PENDING` | Work is prepared for external send or parser/effectful attempt, but send is not confirmed as the semantic truth. | `CLAIMED` plus dispatch preparation facts. | Does not prove external send success, parser success or comparison success. | May move to `IN_PROGRESS`, `PARSER_OUTCOME_RECEIVED`, `AMBIGUOUS`, `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` or `RECONCILIATION_REQUIRED`. | Must not advance to any `SUCCEEDED_*` class before comparison commit. |
| `IN_PROGRESS` | A bounded attempt is active. | `CLAIMED` or `DISPATCH_PENDING` plus live attempt facts. | Does not prove process-local memory is durable, or that parser/comparison/visibility has succeeded. | May move to `PARSER_OUTCOME_RECEIVED`, `PARTIAL`, `FAILED`, `AMBIGUOUS`, `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` or `RECONCILIATION_REQUIRED`. | Must not be used as proof of success. |
| `PARSER_OUTCOME_RECEIVED` | An explicit parser outcome reference has been recorded for evaluation. | Accepted `ParserOutcomeReference`, attempt/run identity, and comparison-eligibility facts. | Does not prove baseline, difference, anchor update or user-visible result. | May move to `COMPARISON_PENDING`. | Must not skip comparison commit. |
| `COMPARISON_PENDING` | Usable parser outcome exists, but serialized comparison commit has not yet happened. | `PARSER_OUTCOME_RECEIVED` plus baseline/anchor snapshot facts and serialization evidence. | Does not prove committed baseline, difference, anchor update or status exposure. | May move to one of the `SUCCEEDED_*` classes, `PARTIAL`, `FAILED`, `AMBIGUOUS` or `RECONCILIATION_REQUIRED`. | Must not emit a success or change event before comparison commit. |
| `SUCCEEDED_BASELINE` | The first complete baseline for the Beacon/revision context has been committed. | First complete comparison-eligible run, baseline eligibility facts and serialized comparison commit. | Does not prove notification delivery or archive creation. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not create a second baseline for the same logical run or replay. |
| `SUCCEEDED_DIFFERENCE` | A committed comparison established a difference and updated anchors accordingly. | Existing baseline, comparison commit facts and accepted difference evidence. | Does not prove notification delivery or duplicate observation advancement. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not duplicate anchor update or observation state transition. |
| `SUCCEEDED_NO_NEW` | A committed comparison produced the stable no-new semantic outcome for the current run. | Existing baseline, comparison commit facts and no-new evidence. | Does not prove notification delivery or baseline replacement. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not spam identical status facts or create a new baseline. |
| `SUCCEEDED_LOST_ANCHORS_RECOVERY` | The run committed a defined recovery result for lost anchors. | Lost-anchor recovery facts, recovery policy reference and serialized recovery commit. | Does not prove a brand-new baseline or archive reconstruction. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not be duplicated by replay or converted into baseline establishment. |
| `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` | The run encountered external failure, CAPTCHA, route failure, parser ambiguity or comparable blocker and retains one pending recovery obligation. | External-failure or ambiguity facts plus recovery eligibility references. | Does not prove no-new, final failure of comparison semantics or state erasure. | May move to `RECONCILIATION_REQUIRED` or, if the one grace case applies, to recovery handling under the same logical run. | Must not accumulate multiple missed scans or erase baseline and anchors. |
| `PARTIAL` | Only some semantic units have trustworthy outcome facts, so the run remains incomplete. | Partial outcome facts, per-unit evidence and preserved prior run state. | Does not prove baseline advance, anchor update, complete success or no-new. | May move to `RECONCILIATION_REQUIRED`, `FAILED` or a later completion path for the same logical run. | Must not advance baseline or anchors. |
| `FAILED` | The run ended in a terminal failure state with no success commit. | Terminal failure facts, preserved prior state and run identity. | Does not prove success, no-new or baseline/anchor mutation. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not erase prior baseline or anchors. |
| `AMBIGUOUS` | The exact semantic outcome cannot be safely classified as success or no-new. | Ambiguity facts, missing proof facts and the same run identity. | Does not prove success, no-new or user-visible change. | May move to `RECONCILIATION_REQUIRED` or a later exact-result class when evidence is restored. | Must not be converted into false no-new. |
| `RECONCILIATION_REQUIRED` | A reconciliation step is required before the run may be considered settled. | Lost response, unknown dispatch state, overlap conflict, ambiguous proof or post-commit loss facts. | Does not prove a fresh run, a second baseline or a second comparison. | May move to a final replayed outcome, a recovery class, `FAILED`, or remain pending until reconciliation facts arrive. | Must not trigger blind retry that duplicates effect. |
| `CANCELLED` | The run was intentionally stopped before a further semantic effect was allowed. | Explicit cancellation facts and the same logical run identity. | Does not prove success, comparison result or delivery. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not be rewritten into success by replay. |
| `SUPERSEDED_BEFORE_EFFECT` | A later accepted semantic request made the current request obsolete before any durable effect. | Newer accepted request, identical scope overlap and pre-effect supersession facts. | Does not prove success, baseline, anchor update or external dispatch. | The run itself is terminal; later logical runs may start again at `REQUESTED`. | Must not create parallel committed comparison work. |

## 4. State transition boundaries

The following are semantic boundaries, not implementation mandates.

- `REQUESTED` may become `BLOCKED`, `PLANNED` or `SUPERSEDED_BEFORE_EFFECT`;
- `BLOCKED` may remain blocked, move to `RECONCILIATION_REQUIRED`, or be replaced only by a new eligible semantic request;
- `PLANNED` may become `CLAIMED`, `CANCELLED` or `RECONCILIATION_REQUIRED`;
- `CLAIMED` may become `DISPATCH_PENDING`, `IN_PROGRESS`, `CANCELLED` or `RECONCILIATION_REQUIRED`;
- `DISPATCH_PENDING` may become `IN_PROGRESS`, `PARSER_OUTCOME_RECEIVED`, `AMBIGUOUS`, `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` or `RECONCILIATION_REQUIRED`;
- `IN_PROGRESS` may become `PARSER_OUTCOME_RECEIVED`, `PARTIAL`, `FAILED`, `AMBIGUOUS`, `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` or `RECONCILIATION_REQUIRED`;
- `PARSER_OUTCOME_RECEIVED` may become only `COMPARISON_PENDING`;
- `COMPARISON_PENDING` may become one of the committed success classes, `PARTIAL`, `FAILED`, `AMBIGUOUS` or `RECONCILIATION_REQUIRED`;
- any `SUCCEEDED_*` class is terminal for that logical run;
- `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`, `PARTIAL`, `FAILED`, `AMBIGUOUS` and `RECONCILIATION_REQUIRED` preserve the same logical run unless a later exact replay or recovery fact settles them;
- `CANCELLED` and `SUPERSEDED_BEFORE_EFFECT` are terminal for that logical run.

Forbidden direct transitions:

- `REQUESTED` to any `SUCCEEDED_*` class without durable work, parser outcome and comparison commit;
- `CLAIMED` or `IN_PROGRESS` to any `SUCCEEDED_*` class by process-local memory alone;
- `PARSER_OUTCOME_RECEIVED` to any committed comparison class without `COMPARISON_PENDING` and serialized comparison;
- any replay that creates a second logical run, second baseline or second anchor update;
- any transition that erases baseline or anchors because a run was partial, failed or ambiguous.

## 5. Idempotency rules

1. Idempotency is required for scan request creation, due-work materialization, protected cancellation/reconciliation and retryable commands.
2. Same key plus same semantic request plus known terminal outcome returns or references the original outcome.
3. Same key plus same semantic request plus pending or ambiguous outcome returns a pending or reconciliation state.
4. Same key plus different semantic fingerprint returns `IDEMPOTENCY_MISMATCH` with no effect.
5. Missing required key is rejected before effect.
6. Replay never creates a second logical run.
7. Replay never creates a second baseline.
8. Replay never duplicates anchor update.
9. Replay never duplicates observation state transition.
10. Replay never duplicates scan-domain fact or user-visible status fact.
11. Retry attempts remain under the same logical run unless an approved future policy explicitly creates a new run.
12. Per-unit partial retry must preserve prior outcomes and identify exact page/candidate units.
13. Exact idempotency storage, TTL and physical uniqueness remain future DB/persistence scope.

## 6. Semantic fingerprints

The semantic fingerprint is a docs-only identity summary for request equivalence.

It must represent the request boundary that changes semantics, not transport noise.

Required fingerprint inputs are limited to stable semantic facts such as:

- explicit `beacon_id`;
- explicit immutable `configuration_revision_id`;
- explicit intent purpose;
- explicit comparison or recovery scope;
- explicit lifecycle and entitlement references that affect effectfulness;
- explicit parser compatibility or sort-context proof references when they affect comparison eligibility;
- explicit overlap/conflict context for the same Beacon scope;
- explicit idempotency key boundary.

The fingerprint must not depend on:

- process id;
- worker id;
- queue path;
- retry counter;
- transport attempt count;
- request timestamps that do not change the semantic request;
- provider payload noise;
- runtime memory state.

Fingerprint rules:

- same key plus same semantic request must produce the same semantic fingerprint;
- same key plus different semantic request must produce a different fingerprint and therefore an `IDEMPOTENCY_MISMATCH`;
- the fingerprint is a semantic comparison aid, not a physical uniqueness contract;
- exact storage, TTL, hashing and collision policy remain future persistence scope.

## 7. Commit-point taxonomy

The following are semantic commit points only.
They are not DB transactions, SQL statements, locks, tables, migrations or worker code.

| Commit point | Semantic role |
|---|---|
| `SCAN_INTENT_ACCEPTED_COMMIT` | The intent has been accepted as a logical run candidate. |
| `DURABLE_WORK_ACCEPTED_COMMIT` | Durable work now exists for the logical run. |
| `PARSER_OUTCOME_RECORDED_COMMIT` | An explicit parser outcome has been durably recorded. |
| `BASELINE_ESTABLISHED_COMMIT` | The first complete baseline has been committed. |
| `DIFFERENCE_AND_ANCHORS_UPDATED_COMMIT` | A comparison difference and anchor update have been committed. |
| `PENDING_RECOVERY_REGISTERED_COMMIT` | One pending recovery obligation has been registered. |
| `LOST_ANCHORS_RECOVERY_COMMIT` | Lost-anchor recovery has been committed. |
| `STATUS_FACT_COMMITTED` | A stable internal status fact has been committed. |
| `USER_VISIBLE_RESULT_ELIGIBLE_COMMIT` | The run is eligible to be surfaced only after the visibility recheck. |
| `CANCELLED_OR_BLOCKED_COMMIT` | The run has been intentionally stopped or blocked without further effect. |
| `RECONCILIATION_REQUIRED_COMMIT` | Reconciliation is required before the run may be considered settled. |

Common rules:

- process-local memory is not authoritative durable work;
- a live worker or claim does not prove scan success;
- transport success is not parser success;
- parser success is not comparison success;
- comparison success is not notification delivery;
- no success or change event may appear before the comparison commit;
- user-visible commit must re-check lifecycle and entitlement;
- recovery grace is narrow and one-time;
- external failure, CAPTCHA, route failure and parser ambiguity are not no-new;
- a failed, partial or ambiguous run does not erase baseline or anchors.

## 8. Scan request/work commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| Explicit semantic request, explicit key, explicit fingerprint, explicit Beacon/revision scope, explicit eligibility boundary and no mismatch. | One logical run candidate exists and may be referenced as the accepted request. | No external effect, no worker claim, no parser outcome, no notification delivery and no user-visible success may be assumed. | Same key plus same semantic request returns the original accepted candidate; same key plus different request returns mismatch with no effect. | No second logical run, no live provider traffic, no Beacon or Entitlement mutation, no status spam. |

## 9. Parser outcome recording commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| Accepted logical run, explicit parser outcome reference, comparison eligibility context and the same run identity. | The parser outcome becomes an authoritative input for comparison. | No baseline, difference, anchor update or user-visible success may be claimed yet. | The same parser outcome reference is reused for exact comparison re-evaluation under the same state version and idempotency checks. | No duplicate parser outcome recording, no transport-success inference, no notification delivery claim. |

## 10. Baseline commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| First complete comparison-eligible run, proven comparison scope, serialized comparison commit and no prior baseline for the same Beacon/revision context. | The initial baseline exists and is the authoritative starting comparison state. | No partial or ambiguous run may establish baseline, and no change event may be emitted for baseline contents. | Replay returns the same baseline reference and never creates a second baseline. | No archive reconstruction claim, no second baseline, no duplicate observation state transition, no direct notification delivery. |

## 11. Difference and anchor update commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| Existing baseline, accepted comparison result, comparison serialization and exact state-version check. | The difference fact and anchor update are authoritative. | No success/change event may appear before the comparison commit. | Replay returns the same difference fact and anchor update; it does not duplicate the update. | No duplicate observation state transition, no baseline reset, no notification delivery assumption, no duplicate domain fact. |

## 12. Pending recovery state commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| External failure, CAPTCHA, route failure, parser ambiguity or equivalent blocker, plus recovery eligibility for the same logical run. | One pending recovery obligation is registered and the run remains unsettled. | No no-new conclusion, no final success and no erasure of baseline or anchors may be inferred. | Replay returns the same pending recovery obligation until it is resolved or superseded by exact facts. | No accumulation of missed scans, no duplicate pending recovery record, no baseline or anchor erasure. |

## 13. Lost-anchor recovery commit point

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| Lost-anchor condition, recovery policy reference, recovery eligibility and the same Beacon/revision scope. | The lost-anchor recovery fact and recovered anchor state are authoritative. | No brand-new baseline may be claimed and no no-new conclusion may be fabricated before this commit. | Replay references the original recovery fact and does not rebuild anchors again. | No archive reconstruction claim, no duplicate recovery, no baseline reset. |

## 14. Status fact and user-visible status boundary

| Required preceding facts | What becomes true after the commit | What must not happen before the commit | Replay behavior after the commit | Forbidden side effects |
|---|---|---|---|---|
| A committed internal status fact, a fresh lifecycle and entitlement recheck, and a compatible visibility boundary. | The run has a stable internal status fact and may become eligible for user-visible exposure only if the recheck still passes. | No user-visible result may be exposed before the recheck; no notification delivery may be treated as proven by status alone. | Replay returns the same status fact and the same visibility eligibility decision for the same source facts. | No direct Notification delivery, no bypass of lifecycle/entitlement recheck, no duplicate status spam. |

## 15. Replay after known terminal outcome

When the same key and the same semantic request are replayed after a known terminal outcome:

- the original terminal outcome is returned or referenced;
- no second logical run is created;
- no second baseline is created;
- no second anchor update is created;
- no second observation state transition is created;
- no new scan-domain fact or user-visible status fact is duplicated.

Terminal outcomes include committed `SUCCEEDED_*` classes, `FAILED`, `CANCELLED`, `SUPERSEDED_BEFORE_EFFECT` and any other exact terminal fact already committed for that logical run.

## 16. Replay while pending or ambiguous

When the same key and the same semantic request are replayed while the outcome is pending, ambiguous or under reconciliation:

- the pending or reconciliation state is returned or referenced;
- no blind retry is allowed to create a second dispatch or second comparison commit;
- the same unresolved logical run remains the authority until exact reconciliation facts arrive;
- the run may remain in `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`, `AMBIGUOUS` or `RECONCILIATION_REQUIRED` until the blocker is resolved;
- exact timeout, lease, heartbeat and backoff policy remain future-gated.

## 17. Interruption and reconciliation boundaries

1. Before durable run/work commit there is no logical run success; replay may create work only under idempotency rules.
2. After run commit but before external dispatch, the run remains planned, claimed or pending; safe reclaim or retry requires future claim policy.
3. If dispatch or send state is unknown, the run or attempt becomes ambiguous or reconciliation-required; do not blind retry.
4. If parser outcome is recorded but comparison commit is absent, there is no baseline, difference or change-event success; replay re-evaluates comparison under exact state-version and idempotency checks.
5. If comparison commit succeeded but the response or report was lost, replay returns the original outcome or reference and does not duplicate observation, anchor update or domain fact.
6. Partial outcomes do not establish or advance baseline or anchors under the current safety boundary.
7. Exact reconciliation sources, timeouts, claim lease, heartbeat and retry/backoff remain future-gated decisions.

## 18. Overlap/concurrency boundaries

- one Beacon must not have parallel active comparison commits;
- a second accepted intent for the same Beacon/revision scope must observe the existing active semantics;
- the second intent may resolve only into blocked, pending or reconciliation semantics, not a parallel committed comparison;
- overlap must not duplicate parser calls, duplicate anchor updates or duplicate domain facts;
- claim ownership and logical run identity are not the same thing;
- exact serialization, fairness and lease policy remain future-gated.

## 19. Forbidden assumptions

- process-local memory is authoritative durable work;
- a live worker or claim proves scan success;
- transport success proves parser success;
- parser success proves comparison success;
- comparison success proves notification delivery;
- any success or change event may appear before the comparison commit;
- user-visible commit may skip lifecycle and entitlement recheck;
- recovery grace is broad, reusable or multi-use;
- external failure, CAPTCHA, route failure or parser ambiguity means no-new;
- a failed, partial or ambiguous run erases baseline or anchors;
- a partial result may advance baseline under this safety boundary;
- overlap may silently merge into a parallel committed comparison;
- retry or replay may create a second logical run for the same semantic request;
- any document here authorizes code, schema, migration, runtime or deployment changes.

## 20. Synthetic examples

| Example | Synthetic setup | Expected lifecycle class | Expected commit point | Expected replay behavior | Forbidden false outcome |
|---|---|---|---|---|---|
| `EX-SOLS-04-FIRST-REQUEST-COMMIT-001` | One explicit Beacon/revision scope, one explicit semantic request, one valid key and fingerprint, and the request is accepted for evaluation. | `REQUESTED` | `SCAN_INTENT_ACCEPTED_COMMIT` | Replay with the same key and the same semantic request returns the original accepted run candidate. | A second logical run or any committed success class. |
| `EX-SOLS-04-IDEMPOTENT-REQUEST-REPLAY-001` | The same key and the same semantic request are replayed after a known terminal outcome has already been committed. | `SUCCEEDED_NO_NEW` | `STATUS_FACT_COMMITTED` | Replay returns or references the original terminal outcome and does not create a new run. | A duplicate run, duplicate baseline or duplicate status fact. |
| `EX-SOLS-04-IDEMPOTENCY-MISMATCH-NO-EFFECT-001` | The same key is reused with a different semantic fingerprint, for example a changed Beacon/revision scope or comparison scope. | `BLOCKED` | `CANCELLED_OR_BLOCKED_COMMIT` | Replay reports the mismatch and does not create effect. | Silent reuse of the old run or a second logical run. |
| `EX-SOLS-04-DURABLE-WORK-NOT-PROCESS-MEMORY-001` | Process-local memory suggests work exists, but after restart there is no durable work record to support it. | `REQUESTED` | `SCAN_INTENT_ACCEPTED_COMMIT` | Replay may create durable work only under idempotency rules; memory alone is not authority. | Treating in-memory state as a durable work commit. |
| `EX-SOLS-04-CLAIMED-NOT-SUCCESS-001` | Durable work has been accepted and one bounded claim is held, but no parser outcome or comparison commit exists. | `CLAIMED` | `DURABLE_WORK_ACCEPTED_COMMIT` | Replay references the same logical run and claim boundary, not a success claim. | Any `SUCCEEDED_*` class. |
| `EX-SOLS-04-PARSER-OUTCOME-RECORDED-NOT-COMPARISON-001` | A parser outcome reference is recorded, but comparison has not yet been serialized. | `PARSER_OUTCOME_RECEIVED` | `PARSER_OUTCOME_RECORDED_COMMIT` | Replay reuses the exact parser outcome reference for comparison under the same state-version checks. | A baseline, difference or user-visible success claim. |
| `EX-SOLS-04-FIRST-BASELINE-COMMIT-001` | The first complete comparison-eligible run exists and no prior baseline exists for the same Beacon/revision context. | `SUCCEEDED_BASELINE` | `BASELINE_ESTABLISHED_COMMIT` | Replay returns the same baseline reference and does not create a second baseline. | A second baseline or a change event for baseline contents. |
| `EX-SOLS-04-DIFFERENCE-ANCHORS-UPDATED-001` | Existing baseline and accepted comparison result show a difference that requires anchor update. | `SUCCEEDED_DIFFERENCE` | `DIFFERENCE_AND_ANCHORS_UPDATED_COMMIT` | Replay returns the same difference fact and the same updated anchors without duplicating them. | Duplicate anchor update or duplicated observation state transition. |
| `EX-SOLS-04-NO-NEW-STATUS-NO-SPAM-001` | Existing baseline, stable no-new semantic outcome and a need to surface a status fact once, not repeatedly. | `SUCCEEDED_NO_NEW` | `STATUS_FACT_COMMITTED` | Replay returns the same no-new status fact and does not spam duplicate user-visible status. | Repeated identical status spam or a hidden baseline change. |
| `EX-SOLS-04-EXTERNAL-UNAVAILABLE-PENDING-RECOVERY-001` | Provider access is unavailable, blocked by CAPTCHA or otherwise externally interrupted while the run is otherwise valid. | `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` | `PENDING_RECOVERY_REGISTERED_COMMIT` | Replay retains one pending recovery obligation and does not convert the run into no-new. | Final no-new or erased baseline and anchors. |
| `EX-SOLS-04-RECOVERY-GRACE-ONE-TIME-001` | One pending recovery began while access was active, then entitlement later expired before retry. | `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` | `PENDING_RECOVERY_REGISTERED_COMMIT` | One recovery grace may still be used for the same pending recovery, but only once. | Unlimited retries or an entitlement bypass. |
| `EX-SOLS-04-LOST-ANCHORS-RECOVERY-COMMIT-001` | Anchor continuity is lost and the defined recovery rule restores valid state from the current recovery window. | `SUCCEEDED_LOST_ANCHORS_RECOVERY` | `LOST_ANCHORS_RECOVERY_COMMIT` | Replay returns the original recovery fact and does not rebuild anchors twice. | A brand-new baseline or a no-new false claim. |
| `EX-SOLS-04-PARTIAL-NO-BASELINE-ADVANCE-001` | Only part of the comparison result is trustworthy and the safety boundary forbids using it to advance anchors or baseline. | `PARTIAL` | `RECONCILIATION_REQUIRED_COMMIT` | Replay preserves the prior baseline and identifies the exact missing page or candidate units. | Baseline advance or false no-new. |
| `EX-SOLS-04-DISPATCH-UNKNOWN-RECONCILIATION-001` | Dispatch or send state is unknown after an attempt and the run must not be blindly retried. | `RECONCILIATION_REQUIRED` | `RECONCILIATION_REQUIRED_COMMIT` | Replay keeps the same reconciliation obligation and does not perform a blind duplicate dispatch. | Duplicate dispatch or direct success. |
| `EX-SOLS-04-POST-COMMIT-REPLAY-NO-DUPLICATE-001` | Comparison commit succeeded, but the response or report was lost before it could be observed by the caller. | `SUCCEEDED_DIFFERENCE` | `USER_VISIBLE_RESULT_ELIGIBLE_COMMIT` | Replay returns the original committed outcome or reference and does not duplicate the comparison. | A second observation, anchor update or domain fact. |
| `EX-SOLS-04-OVERLAP-CONFLICT-NO-PARALLEL-COMMIT-001` | A second accepted intent arrives for the same Beacon/revision scope while one comparison commit is already active. | `BLOCKED` | `RECONCILIATION_REQUIRED_COMMIT` | Replay observes the existing active semantics and does not create a parallel committed comparison. | Two parallel comparison commits or silently merged work. |
| `EX-SOLS-04-LIFECYCLE-ENTITLEMENT-RECHECK-BLOCKS-VISIBLE-COMMIT-001` | A committed comparison exists, but lifecycle or entitlement no longer passes the visibility recheck before user exposure. | `BLOCKED` | `CANCELLED_OR_BLOCKED_COMMIT` | Replay keeps the same blocked result and does not surface stale success. | A stale user-visible success or bypass of the recheck. |
