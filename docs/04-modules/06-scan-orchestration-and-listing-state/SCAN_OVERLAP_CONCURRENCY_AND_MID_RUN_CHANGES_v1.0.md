# Маяк Авито — Scan Overlap, Concurrency and Mid-Run Changes v1.0

## Metadata
- status: approved semantic documentation for SOLS-09;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f, SOLS-08 accepted at 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic overlap, concurrency and mid-run change boundaries for one Beacon-scoped scan comparison flow.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define how one Beacon-scoped comparison state remains serialized or conflict-detected under overlap;
- keep active scan, claim and pending-recovery semantics explicit when a new due interval arrives during an active scan;
- preserve safe scan facts when Beacon lifecycle, revision or entitlement changes mid-run;
- re-check lifecycle and entitlement before any user-visible commit;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no hard-coded interval, anchor-window size, retry, backoff, claim lease or heartbeat default;
- no live Avito/provider traffic;
- no parser implementation, parser mapping, route self-healing, CAPTCHA bypass, proxy/cookie/session workaround or provider-call implementation;
- no physical lock, claim lease, transaction or DB implementation;
- no silent last-write-wins scan-state behavior;
- no duplicate parser dispatch or duplicate comparison commit behavior.

## 2. Overlap definition

- Overlap means a second semantic scan request, due tick or replayable request arrives for the same Beacon/revision scope while an active comparison boundary already exists.
- One Beacon comparison state must be serialized or conflict-detected.
- Two workers cannot both create baseline for the same Beacon scope.
- Two active scans cannot silently advance the same Beacon anchors.
- Overlap does not authorize parallel committed comparisons.
- Overlap may resolve to pending, claimed, blocked, conflict or reconciliation semantics, but not to silent duplication.
- Overlap must not duplicate parser calls because of overlap.
- Overlap must not duplicate comparison commit facts.
- Overlap must not duplicate user-facing facts.

## 3. Single-Beacon comparison serialization boundary

- The comparison boundary is single-Beacon scoped.
- The same Beacon cannot have two concurrent committed comparison writers for the same authoritative scan state.
- Comparison serialization protects baseline creation, anchor advancement and committed difference facts.
- A second active comparison for the same Beacon scope must observe the existing active semantics rather than invent a second authoritative path.
- No silent last-write-wins behavior is allowed for scan state.
- A serialized comparison boundary may still allow replay, but replay must reuse or reference the original outcome rather than create a new effect.
- Physical locks, transactions, claim leases, worker concurrency and DB implementation remain gated.

## 4. Active scan / claim / pending state boundary

- Active scan means a logical run or attempt is already in progress for the same Beacon scope.
- Claim means one bounded internal holder is associated with that active work, but claim ownership is not the same as final comparison authority.
- Pending means overlap, recovery or reconciliation facts already exist and the run must not be duplicated.
- If a second due tick arrives while a scan is active, Scan must record overlap, pending or claimed state rather than dispatch a blind duplicate parser request.
- New due interval while active scan exists must return or record overlap, pending or claimed state.
- Pending recovery and overlap are distinct, but both block blind duplicate work.
- Scan may preserve a safe diagnostic state only if allowed by already accepted retention/privacy boundaries.

## 5. New due interval while scan is active

- A new due interval arriving during an active scan is a coalescing or conflict boundary, not an automatic second dispatch.
- Scan must not blindly dispatch another parser request because a new due interval arrived.
- The new due interval must be represented as overlap, pending or claimed state until the active scan resolves.
- If the same Beacon scope already has active comparison work, the due interval does not create a second comparison writer.
- The due interval may replay the existing logical run or refer to the same pending obligation, but it must not create duplicate parser work.
- No duplicate comparison commit is allowed.

## 6. Stale concurrent commit and no-effect rules

- A stale concurrent commit is a commit attempt that no longer matches the current authoritative comparison state version.
- Stale concurrent commit returns conflict or no effect.
- Stale concurrent commit must not silently overwrite newer scan state.
- There is no silent last-write-wins for scan state.
- Stale concurrent commit must not create duplicate comparison facts, anchor advances or user-visible facts.
- If the authoritative state has already moved on, the stale attempt must be treated as conflict/no effect and replayed only as the original no-effect fact.

## 7. Beacon lifecycle changes mid-run

- Beacon lifecycle is owned by Beacon Management.
- Scan must not activate, pause, archive, delete or freeze Beacon.
- If Beacon becomes paused, archived, deleted or frozen before normal external work, the scan is safely cancelled or blocked.
- If Beacon lifecycle changes before normal user-visible commit, normal user-visible new-listing result is blocked.
- Scan may preserve safe diagnostic state only if already accepted retention/privacy boundaries allow it.
- Lifecycle change mid-run does not authorize a silent success conversion.
- The scan must re-check lifecycle before the normal commit boundary if the lifecycle may have changed.

## 8. Beacon revision changes mid-run

- Scan intent and run remain bound to the exact immutable Beacon configuration revision that started them.
- Scan must not silently follow the latest Beacon revision.
- Scan must not rewrite a run to a newer revision.
- A newer revision appearing mid-run does not rebind the active run by assumption.
- If the run is replayed, the same revision binding must remain explicit.
- Beacon revision changes mid-run require conflict, block or safe no-effect semantics; they do not authorize hidden rebinding.
- Beacon revision mismatch produces no effect for the old run scope rather than silent reinterpretation.

## 9. Entitlement changes mid-run

- Entitlement decisions are owned by Entitlements & Billing.
- Scan must not mutate entitlement/payment/subscription/grant state.
- Before normal external work, denied or ambiguous entitlement blocks effect.
- Before normal commit, denied, expired or ambiguous entitlement blocks the normal user-visible result.
- Entitlement changes mid-run do not authorize silent reuse of an earlier permissive outcome.
- The scan must re-check entitlement before the normal commit boundary if entitlement may have changed.
- The same run may retain safe diagnostic state only if already accepted retention/privacy boundaries allow it.

## 10. Parser outcome received after lifecycle or entitlement change

- Parser outcome may arrive after a lifecycle or entitlement change has already occurred.
- Before comparison commit, Beacon lifecycle must be re-checked.
- Before comparison commit, entitlement must be re-checked.
- If Beacon is paused, archived, deleted or frozen before normal commit, normal user-visible new-listing result is blocked.
- If entitlement is denied, expired or ambiguous before normal commit, normal user-visible result is blocked except for the already accepted one-time recovery grace.
- Parser outcome received earlier does not override later lifecycle or entitlement block facts.
- The comparison commit must use the current eligible state, not stale eligibility assumptions.

## 11. Recovery grace exception boundary

- Pending recovery grace may allow one recovery result only if the failure started while access was active.
- Recovery grace is narrow and one-time for the already pending recovery scan only.
- After recovery grace is consumed, current entitlement rules apply again.
- Recovery grace does not mutate entitlement state.
- Recovery grace does not create a general bypass for later scans or later runs.
- Recovery grace does not authorize duplicate recovery facts or duplicate comparison commits.

## 12. Replay and idempotency behavior

- Replay of the same semantic request with the same scope must return or reference the original outcome, pending state or conflict result.
- Replay must not create a second logical run for the same active comparison scope.
- Replay must not create duplicate parser dispatch because of overlap.
- Replay must not create duplicate comparison commit.
- Replay must not create duplicate user-facing facts.
- Same key plus same semantic request replays the original overlap/pending/conflict/no-effect outcome.
- Same key plus different semantic fingerprint returns mismatch or blocked conflict with no effect.
- Overlap replayed no duplicate effect is the safe boundary for same-scope retries or redeliveries.

## 13. Safe diagnostic/status facts

Scan may expose only safe diagnostic/status facts such as:

- a Beacon comparison state is already active;
- overlap was detected for the same Beacon scope;
- the new due interval was coalesced during an active scan;
- pending or claimed state already exists;
- a stale concurrent commit had conflict or no effect;
- baseline creation conflicted for the same Beacon scope;
- anchor advance conflicted for the same Beacon scope;
- lifecycle re-check is required before commit;
- entitlement re-check is required before commit;
- normal commit is blocked by lifecycle;
- normal commit is blocked by entitlement;
- the run is bound to the original immutable Beacon revision;
- replay produced no duplicate effect.

These facts are safe because they do not expose raw provider payloads, delivery actions or a full archive.

## 14. Forbidden assumptions

- One Beacon comparison state may be advanced by two active scans without conflict.
- Two workers may both create baseline for the same Beacon scope.
- Overlap may silently merge into duplicate parser dispatch.
- Overlap may silently merge into duplicate comparison commit.
- Stale concurrent commit may overwrite newer scan state by last-write-wins.
- Scan may silently follow the latest Beacon revision.
- Scan may rewrite a run to a newer revision.
- Scan may activate, pause, archive, delete or freeze Beacon.
- Scan may mutate entitlement/payment/subscription/grant state.
- Lifecycle or entitlement changes mid-run may be ignored before normal commit.
- A denied, expired or ambiguous entitlement may still produce a normal user-visible result.
- Recovery grace may be reused multiple times.
- Physical locks, transactions, claim leases, worker concurrency or DB implementation are defined here.
- Route self-healing, CAPTCHA bypass, proxy/cookie/session workaround or notification delivery mechanics are defined here.
- Duplicate parser calls, duplicate comparison commits or duplicate user-facing facts are allowed.

## 15. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `BEACON_SCAN_ALREADY_ACTIVE` | A comparison-capable scan for the same Beacon scope is already active. | Active run evidence; same Beacon/revision scope; overlap context. | Preserve the active state and prevent a parallel duplicate effect. | Silent second active comparison or silent last-write-wins. |
| `OVERLAP_PENDING_OR_CLAIMED` | The new due interval or request must resolve into pending or claimed overlap semantics. | New due interval; active comparison scope; claim/pending evidence. | Record overlap, pending or claimed state without duplicate parser work. | Duplicate parser dispatch or duplicate comparison commit. |
| `DUE_INTERVAL_COALESCED_DURING_ACTIVE_SCAN` | A due tick arriving during active work is coalesced into the existing logical run. | Active scan; new due interval; same Beacon scope. | Reuse the existing run or pending obligation. | Blind second dispatch or accumulated duplicate backlog. |
| `DUPLICATE_PARSER_DISPATCH_BLOCKED` | A second parser dispatch for the same active scan scope is forbidden. | Active scan; overlap context; dispatch boundary. | Block duplicate dispatch and preserve the original work. | Duplicate parser request because a due tick repeated. |
| `DUPLICATE_COMPARISON_COMMIT_BLOCKED` | A second comparison commit for the same authoritative scan state is forbidden. | Serialized comparison boundary; same Beacon scope; committed or pending state. | Prevent duplicate committed facts and duplicate anchor advancement. | Two committed comparison writers for one Beacon scope. |
| `STALE_CONCURRENT_COMMIT_NO_EFFECT` | A stale commit attempt has no authoritative effect. | Current state-version mismatch; concurrent commit attempt; same Beacon scope. | Return conflict or no effect only. | Silent overwrite of newer scan state. |
| `BASELINE_CREATION_CONFLICT` | Two workers or attempts contend for baseline creation in the same Beacon scope. | No prior baseline or a race to establish baseline; same Beacon scope. | Allow only one serialized baseline creation outcome. | Two baseline facts for one Beacon scope. |
| `ANCHOR_ADVANCE_CONFLICT` | A concurrent attempt would advance the same Beacon anchors without serialization. | Existing baseline/anchors; concurrent comparison attempt. | Block or conflict the second anchor update. | Two active scans silently advancing the same anchors. |
| `NO_SILENT_LAST_WRITE_WINS` | Scan state must not be overwritten silently by a later writer. | Concurrent state version facts; same Beacon comparison scope. | Preserve explicit conflict/no-effect semantics. | Hidden state overwrite by last-write-wins. |
| `BEACON_LIFECYCLE_RECHECK_REQUIRED` | Lifecycle may have changed and must be re-checked before commit. | Mid-run lifecycle-change possibility; Beacon management reference. | Require a fresh lifecycle decision before normal commit. | Committing user-visible success on stale lifecycle facts. |
| `LIFECYCLE_BLOCKED_BEFORE_DISPATCH` | Beacon lifecycle blocks normal external work before dispatch. | Paused, archived, deleted or frozen lifecycle fact. | Cancel or block normal effect before external work. | Dispatching as if the Beacon remained eligible. |
| `LIFECYCLE_BLOCKED_BEFORE_COMMIT` | Beacon lifecycle blocks normal user-visible commit. | Paused, archived, deleted or frozen lifecycle fact before commit. | Prevent normal user-visible new-listing result. | Stale user-visible success after lifecycle change. |
| `BEACON_REVISION_MISMATCH_NO_EFFECT` | The active run no longer matches the exact immutable Beacon revision scope. | Original run revision; newer revision appearance; mismatch evidence. | Keep the original run bound and produce no effect for the newer revision. | Silent follow of latest revision or run rewrite. |
| `ENTITLEMENT_RECHECK_REQUIRED` | Entitlement may have changed and must be re-checked before commit. | Mid-run entitlement-change possibility; entitlement reference. | Require a fresh entitlement decision before normal commit. | Committing on stale entitlement facts. |
| `ENTITLEMENT_BLOCKED_BEFORE_EXTERNAL_WORK` | Denied or ambiguous entitlement blocks normal effect before external work. | Denied, expired or ambiguous entitlement fact. | Block or cancel normal external work. | Blind external dispatch on blocked entitlement. |
| `ENTITLEMENT_BLOCKED_BEFORE_COMMIT` | Denied, expired or ambiguous entitlement blocks normal user-visible commit. | Denied, expired or ambiguous entitlement fact before commit. | Prevent normal user-visible result except the one accepted recovery grace case. | Normal success despite denied or expired entitlement. |
| `RECOVERY_GRACE_EXCEPTION_APPLIED` | One recovery result is allowed under the narrow pending-recovery grace. | External failure began while access was active; one pending recovery scan; grace boundary. | Allow one recovery result only. | Reusing grace for later scans or multiple results. |
| `RECOVERY_GRACE_NOT_AVAILABLE` | The grace case does not apply. | No qualifying active-access start; grace already consumed; current entitlement blocks. | Apply current entitlement rules with no grace bypass. | Silent entitlement bypass. |
| `MID_RUN_CHANGE_SAFE_DIAGNOSTIC_ONLY` | Mid-run change facts may be preserved only as safe diagnostics. | Accepted retention/privacy boundary; lifecycle/revision/entitlement change facts. | Keep safe status facts only; no mutation of external owner state. | Full archive retention or external owner-state mutation. |
| `OVERLAP_REPLAYED_NO_DUPLICATE_EFFECT` | Replay of overlap state returns the same outcome without duplicating effect. | Same semantic request; overlap context; same Beacon scope. | Return the original pending, claimed, blocked or conflict result. | Duplicate parser dispatch, duplicate commit or duplicate user facts. |

## 16. Synthetic examples

### EX-SOLS-09-TWO-DUE-TICKS-ONE-ACTIVE-SCAN-001

- Synthetic setup: one Beacon scope already has an active scan, and a second due interval arrives before the active comparison resolves.
- Expected classification: `DUE_INTERVAL_COALESCED_DURING_ACTIVE_SCAN`.
- Expected state/fact effect: record overlap, pending or claimed state for the existing run instead of dispatching a second parser request.
- Expected replay/commit behavior: replay returns the same coalesced overlap fact and does not create a second parser dispatch.
- Forbidden false outcome: duplicate parser dispatch or duplicate comparison commit.

### EX-SOLS-09-DUPLICATE-PARSER-DISPATCH-BLOCKED-001

- Synthetic setup: one active scan exists and another request tries to send the same parser work for the same Beacon scope.
- Expected classification: `DUPLICATE_PARSER_DISPATCH_BLOCKED`.
- Expected state/fact effect: block the second dispatch and preserve the original work boundary.
- Expected replay/commit behavior: replay returns the same blocked overlap fact without creating a new dispatch.
- Forbidden false outcome: a second parser request because the due tick repeated.

### EX-SOLS-09-TWO-WORKERS-BASELINE-CONFLICT-001

- Synthetic setup: two workers concurrently attempt to create the first baseline for the same Beacon scope.
- Expected classification: `BASELINE_CREATION_CONFLICT`.
- Expected state/fact effect: allow only one serialized baseline creation outcome and treat the other attempt as conflict/no effect.
- Expected replay/commit behavior: replay returns the original baseline or conflict fact without creating a second baseline.
- Forbidden false outcome: two baseline facts for one Beacon scope.

### EX-SOLS-09-TWO-WORKERS-ANCHOR-ADVANCE-CONFLICT-001

- Synthetic setup: two active comparisons try to advance the same Beacon anchors concurrently.
- Expected classification: `ANCHOR_ADVANCE_CONFLICT`.
- Expected state/fact effect: serialize or conflict-detect the anchor advance and preserve a single authoritative anchor update.
- Expected replay/commit behavior: replay returns the same anchor outcome and does not duplicate anchor advancement.
- Forbidden false outcome: two active scans silently advancing the same anchors.

### EX-SOLS-09-STALE-COMMIT-NO-EFFECT-001

- Synthetic setup: a commit attempt is made against an older comparison state after the authoritative state has already changed.
- Expected classification: `STALE_CONCURRENT_COMMIT_NO_EFFECT`.
- Expected state/fact effect: return conflict or no effect and preserve the newer scan state.
- Expected replay/commit behavior: replay returns the original stale/no-effect result without overwriting newer facts.
- Forbidden false outcome: silent last-write-wins overwrite.

### EX-SOLS-09-NO-SILENT-LAST-WRITE-WINS-001

- Synthetic setup: a later writer attempts to replace earlier scan state without detecting the concurrent version mismatch.
- Expected classification: `NO_SILENT_LAST_WRITE_WINS`.
- Expected state/fact effect: reject hidden overwrite and keep explicit conflict/no-effect semantics.
- Expected replay/commit behavior: replay preserves the same conflict boundary and does not mutate authoritative facts.
- Forbidden false outcome: silent state overwrite by a later writer.

### EX-SOLS-09-BEACON-PAUSED-BEFORE-DISPATCH-001

- Synthetic setup: Beacon lifecycle changes to paused before the scan reaches normal external work.
- Expected classification: `LIFECYCLE_BLOCKED_BEFORE_DISPATCH`.
- Expected state/fact effect: cancel or block normal effect before dispatch and preserve safe diagnostics only if allowed.
- Expected replay/commit behavior: replay returns the same lifecycle block without dispatching work.
- Forbidden false outcome: dispatching as if the Beacon remained eligible.

### EX-SOLS-09-BEACON-ARCHIVED-AFTER-PARSER-BEFORE-COMMIT-001

- Synthetic setup: parser outcome has been received, but Beacon lifecycle becomes archived before normal commit.
- Expected classification: `LIFECYCLE_BLOCKED_BEFORE_COMMIT`.
- Expected state/fact effect: block the normal user-visible new-listing result and keep only safe diagnostic facts.
- Expected replay/commit behavior: replay re-checks lifecycle and preserves the blocked result.
- Forbidden false outcome: a stale user-visible success.

### EX-SOLS-09-BEACON-DELETED-BEFORE-COMMIT-001

- Synthetic setup: Beacon is deleted after run activity begins but before normal commit.
- Expected classification: `LIFECYCLE_BLOCKED_BEFORE_COMMIT`.
- Expected state/fact effect: block the normal user-visible result and avoid treating the old run as still eligible.
- Expected replay/commit behavior: replay returns the same blocked lifecycle fact.
- Forbidden false outcome: normal success on deleted Beacon.

### EX-SOLS-09-BEACON-FROZEN-BLOCKS-NORMAL-COMMIT-001

- Synthetic setup: Beacon lifecycle becomes frozen before the comparison commit boundary.
- Expected classification: `LIFECYCLE_BLOCKED_BEFORE_COMMIT`.
- Expected state/fact effect: prevent normal user-visible new-listing result and preserve safe diagnostics only.
- Expected replay/commit behavior: replay keeps the frozen-block fact stable.
- Forbidden false outcome: user-visible success despite frozen lifecycle.

### EX-SOLS-09-REVISION-CHANGED-NO-SILENT-FOLLOW-001

- Synthetic setup: a newer Beacon revision appears mid-run after the active run already started on an older immutable revision.
- Expected classification: `BEACON_REVISION_MISMATCH_NO_EFFECT`.
- Expected state/fact effect: keep the run bound to the original revision and do not silently follow the newer one.
- Expected replay/commit behavior: replay returns the same revision mismatch boundary without rebinding the run.
- Forbidden false outcome: silent follow of latest revision.

### EX-SOLS-09-ENTITLEMENT-DENIED-BEFORE-WORK-001

- Synthetic setup: entitlement decision is denied before normal external work would begin.
- Expected classification: `ENTITLEMENT_BLOCKED_BEFORE_EXTERNAL_WORK`.
- Expected state/fact effect: block normal external work and preserve only safe diagnostics.
- Expected replay/commit behavior: replay returns the same blocked entitlement fact.
- Forbidden false outcome: blind external dispatch.

### EX-SOLS-09-ENTITLEMENT-EXPIRED-BEFORE-COMMIT-001

- Synthetic setup: entitlement was active earlier, but it has expired before the normal commit boundary.
- Expected classification: `ENTITLEMENT_BLOCKED_BEFORE_COMMIT`.
- Expected state/fact effect: block the normal user-visible result unless the already accepted one-time recovery grace applies.
- Expected replay/commit behavior: replay re-checks entitlement and keeps the blocked result.
- Forbidden false outcome: normal user-visible success despite expiry.

### EX-SOLS-09-ENTITLEMENT-AMBIGUOUS-BLOCKS-COMMIT-001

- Synthetic setup: entitlement state is ambiguous when the scan is ready to commit a user-visible result.
- Expected classification: `ENTITLEMENT_BLOCKED_BEFORE_COMMIT`.
- Expected state/fact effect: block normal user-visible commit and keep the result unsettled.
- Expected replay/commit behavior: replay preserves the same ambiguity block until an explicit entitlement decision exists.
- Forbidden false outcome: normal success on ambiguous entitlement.

### EX-SOLS-09-RECOVERY-GRACE-ALLOWS-ONE-RESULT-001

- Synthetic setup: the external failure began while access was active, one pending recovery scan exists, and the only remaining question is whether the narrow grace applies.
- Expected classification: `RECOVERY_GRACE_EXCEPTION_APPLIED`.
- Expected state/fact effect: allow exactly one recovery result and then return to current entitlement rules.
- Expected replay/commit behavior: replay returns the same one-time grace result and does not reuse grace again.
- Forbidden false outcome: repeated grace use or entitlement bypass.

### EX-SOLS-09-RECOVERY-GRACE-NOT-AVAILABLE-NORMAL-BLOCK-001

- Synthetic setup: the run does not satisfy the one-time recovery grace conditions, or the grace has already been consumed.
- Expected classification: `RECOVERY_GRACE_NOT_AVAILABLE`.
- Expected state/fact effect: apply current entitlement rules with no bypass.
- Expected replay/commit behavior: replay keeps the same no-grace boundary.
- Forbidden false outcome: a silent entitlement bypass.

### EX-SOLS-09-REPLAY-NO-DUPLICATE-COMMIT-001

- Synthetic setup: the same semantic overlap request is replayed after a conflict or pending state has already been established.
- Expected classification: `OVERLAP_REPLAYED_NO_DUPLICATE_EFFECT`.
- Expected state/fact effect: return the original overlap result without duplicate parser dispatch or duplicate commit.
- Expected replay/commit behavior: replay produces the same no-duplicate effect fact.
- Forbidden false outcome: a second logical run or duplicate user-facing facts.

### EX-SOLS-09-MID-RUN-DIAGNOSTIC-ONLY-001

- Synthetic setup: lifecycle, revision or entitlement changes occur mid-run but the already accepted retention/privacy boundary allows only safe diagnostic facts.
- Expected classification: `MID_RUN_CHANGE_SAFE_DIAGNOSTIC_ONLY`.
- Expected state/fact effect: preserve safe status facts only and avoid mutating Beacon, entitlement or other owner state.
- Expected replay/commit behavior: replay returns the same safe diagnostic facts without exposing a full archive.
- Forbidden false outcome: full archive retention or external owner-state mutation.
