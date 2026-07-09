# Маяк Авито — Scan Eligibility and Intent Boundary v1.0

- status: approved semantic documentation for SOLS-03
- date: 2026-07-09
- module: 06-scan-orchestration-and-listing-state
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization

This document is docs-only and transport/provider/framework/ORM neutral.
It defines the semantic boundary for when a ScanIntent may become a valid logical run for exactly one Beacon and one immutable configuration revision.

## 1. Purpose and non-goals

Purpose:

- define when a scan intent is eligible to become a logical run candidate;
- keep the Beacon/revision binding explicit and immutable;
- separate scan eligibility from lifecycle ownership, entitlement ownership, parser compatibility, egress availability, idempotency, overlap, and recovery handling;
- provide semantic outcome classes for documentation, not runtime use.

Non-goals:

- no code, tests, runtime, schema, parser, egress, notification, UI, or deploy authorization;
- no transport/provider/framework/ORM decision;
- no mutation authority over Beacon state, entitlement state, parser state, egress routing, or delivery state;
- no numeric interval, retry, backoff, due-slot, claim lease, or anchor-window default;
- no implementation of Avito parsing or live Avito/provider calls.

## 2. Input references required before intent acceptance

Before a ScanIntent is accepted as eligible, the following references MUST be explicit and unambiguous:

- one explicit `beacon_id`;
- one explicit immutable `configuration_revision_id`;
- one explicit intent purpose that matches an allowed scan purpose;
- one explicit actor/account/authorization context for the requesting side;
- one explicit entitlement decision reference when entitlement gates apply;
- one explicit parser compatibility/outcome reference when comparison or sort evidence is required;
- one explicit egress availability reference when effectful work depends on route availability;
- one explicit idempotency key and one semantic fingerprint;
- one explicit overlap/conflict context for the same Beacon/revision scope.

If any required reference is missing, ambiguous, or unproven, intent acceptance MUST stop with a blocked or ambiguous semantic outcome and MUST NOT create external effect.

## 3. Actor/account/authorization boundary

- Scan eligibility is gated by explicit actor/account/authorization context, not by UI state, channel flags, or implied permissions.
- UI/channel flags are not authority for scan eligibility.
- A user, operator, service account, or admin path MAY be recognized only through explicit contract context.
- Scan must not infer authorization from presentation-layer controls, channel routing, or client-side flags.
- Scan does not mutate account, credential, role, session, or entitlement records.

## 4. Beacon lifecycle and immutable configuration revision boundary

- Beacon Management owns Beacon lifecycle, source URL, effective configuration, and immutable configuration revision creation/management.
- Scan consumes explicit Beacon references only.
- A ScanIntent is only eligible for one explicit `beacon_id` and one immutable `configuration_revision_id`.
- A newer Beacon revision MUST NOT silently replace or reinterpret an accepted run.
- Once accepted, a run remains pinned to its explicit Beacon revision even if a newer revision appears later.
- Paused, archived, deleted, or frozen normal lifecycle state blocks normal scan effect unless the one recovery grace exception applies.

## 5. Entitlement decision boundary

- Entitlements & Billing owns effective entitlement decision semantics.
- Scan consumes an explicit entitlement decision only.
- Ambiguous, denied, expired, or unsupported entitlement blocks normal external effect.
- The entitlement decision may be referenced, not recalculated, by Scan.
- Scan must not mutate tariff, payment, subscription, or grant state.
- Paused, archived, deleted, frozen, denied, ambiguous, or expired normal state blocks normal result, except for the one recovery grace case described below.

## 6. Parser compatibility and sort-context boundary

- Avito Parser Adapter owns parser compatibility, parser outcome, and sort evidence.
- Scan must not parse Avito.
- Missing, ambiguous, or unproven sort context blocks normal newest-first comparison and MUST NOT become a false no-new result.
- When sort context is absent or not proven, Scan must treat newest-first comparison as blocked or ambiguous, not as success.
- Parser compatibility evidence is a reference boundary, not a Scan-owned inference.

## 7. Egress availability reference boundary

- Egress availability is a reference and gate only.
- Scan does not choose routes, heal routes, or invent fallback paths.
- A missing or unavailable egress reference blocks external effect.
- A route decision remains owned by Egress contracts and their approved implementation boundary, not by Scan.
- Scan may consume an explicit availability reference, but it must not transform that reference into routing logic.
- Scan emits safe facts/status only; Notification Delivery/UI/channel modules own delivery/rendering.

## 8. Idempotency and intent fingerprint boundary

- Idempotency key and semantic fingerprint are required before accepting retryable or effectful intent.
- Same key plus same semantic request replays the original outcome or pending state.
- Same key plus different fingerprint returns idempotency mismatch with no effect.
- The fingerprint must capture the semantic request boundary that matters for eligibility, not transport noise.
- Idempotency handling must be explicit before any accepted retry or claim path.

## 9. Overlap/conflict boundary

- One Beacon must not have parallel active comparison commits.
- Overlap produces pending, claimed, or conflict semantics, not duplicate parser calls and not duplicate events.
- A second intent for the same Beacon/revision scope MUST observe the existing active semantics and choose a blocked, pending, or conflict outcome.
- Conflict handling protects the serialized comparison boundary and does not authorize parallel duplicate work.
- Scan must not duplicate parser work merely because a second intent arrived.

## 10. Schedule/due/manual/recovery intent boundary

- Scheduler/due condition may be represented only as a semantic placeholder.
- No numeric interval or default is allowed in this document.
- Manual/check-now may be represented only as a future placeholder if separately approved.
- Recovery intent may exist only as one pending recovery obligation, not as accumulated missed scans.
- A due condition is a boundary signal, not a guarantee of work execution.
- This document does not authorize any concrete scheduler cadence, slot window, or retry timer.

## 11. Eligibility outcome classes

The following are semantic docs-only classes for eligibility documentation only. They are not persisted enum names, not Python constants, not wire schema, and not database values.

- `SCAN_INTENT_ACCEPTED`
- `SCAN_INTENT_REPLAYED`
- `SCAN_INTENT_BLOCKED_BY_CONTRACT`
- `SCAN_INTENT_BLOCKED_BY_AUTHORIZATION`
- `SCAN_INTENT_BLOCKED_BY_BEACON_LIFECYCLE`
- `SCAN_INTENT_BLOCKED_BY_ENTITLEMENT`
- `SCAN_INTENT_BLOCKED_BY_PARSER_COMPATIBILITY`
- `SCAN_INTENT_BLOCKED_BY_SORT_CONTEXT`
- `SCAN_INTENT_BLOCKED_BY_EGRESS_UNAVAILABLE`
- `SCAN_INTENT_BLOCKED_BY_OVERLAP`
- `SCAN_INTENT_IDEMPOTENCY_MISMATCH`
- `SCAN_INTENT_PENDING_RECOVERY`
- `SCAN_INTENT_RECOVERY_GRACE_ALLOWED`
- `SCAN_INTENT_REJECTED_UNSUPPORTED_PURPOSE`
- `SCAN_INTENT_AMBIGUOUS_NO_EFFECT`

Interpretation rules:

- `SCAN_INTENT_ACCEPTED` means the intent is eligible as a logical run candidate for one explicit Beacon/revision.
- `SCAN_INTENT_REPLAYED` means the same semantic request and key replay the original outcome or pending state.
- `SCAN_INTENT_BLOCKED_BY_CONTRACT` means the request fails the semantic contract boundary.
- `SCAN_INTENT_BLOCKED_BY_AUTHORIZATION` means actor/account/authorization context is insufficient or not explicit.
- `SCAN_INTENT_BLOCKED_BY_BEACON_LIFECYCLE` means Beacon lifecycle state blocks normal effect.
- `SCAN_INTENT_BLOCKED_BY_ENTITLEMENT` means the explicit entitlement decision blocks normal external effect.
- `SCAN_INTENT_BLOCKED_BY_PARSER_COMPATIBILITY` means parser compatibility evidence is missing or unsupported.
- `SCAN_INTENT_BLOCKED_BY_SORT_CONTEXT` means newest-first comparison cannot be proven.
- `SCAN_INTENT_BLOCKED_BY_EGRESS_UNAVAILABLE` means the route/egress reference is unavailable.
- `SCAN_INTENT_BLOCKED_BY_OVERLAP` means an active equivalent scope already exists.
- `SCAN_INTENT_IDEMPOTENCY_MISMATCH` means same key but different semantic fingerprint.
- `SCAN_INTENT_PENDING_RECOVERY` means one pending recovery obligation exists and has not yet been resolved.
- `SCAN_INTENT_RECOVERY_GRACE_ALLOWED` means the one recovery grace exception applies.
- `SCAN_INTENT_REJECTED_UNSUPPORTED_PURPOSE` means the intent purpose is outside the allowed scan purpose set.
- `SCAN_INTENT_AMBIGUOUS_NO_EFFECT` means the input cannot be safely converted into external effect.

## 12. Recovery grace exception boundary

- The recovery grace exception MAY apply only to one pending recovery scan.
- That one pending recovery scan must have had its external failure begin while access was active.
- Recovery grace does not create a general entitlement bypass.
- Recovery grace does not accumulate missed scans.
- Recovery grace does not override unresolved ambiguity outside the single pending recovery case.
- Recovery grace is a narrow semantic exception, not a default retry policy.

## 13. Pre-effect and pre-user-visible-commit recheck rule

- Lifecycle and entitlement MUST be re-checked before user-visible commit.
- A pre-effect check guards acceptance; a pre-user-visible-commit recheck guards exposure of committed facts.
- If lifecycle or entitlement changes before the user-visible commit point, the result MUST be re-evaluated against the current explicit references.
- This recheck rule prevents stale acceptance from becoming a user-visible false success.
- The rule applies even when earlier intent evaluation was accepted or pending.

## 14. Forbidden assumptions

The following assumptions are forbidden in this document:

- silent Beacon revision upgrade for an already accepted run;
- UI/channel flag authority for eligibility;
- implicit Beacon lifecycle ownership by Scan;
- implicit entitlement recalculation by Scan;
- normal effect from denied, ambiguous, expired, or unsupported entitlement;
- parser behavior implemented inside Scan;
- sort-order inference from missing or unproven evidence;
- route selection, route healing, or fallback invention by Scan;
- idempotent effect without explicit key and semantic fingerprint;
- duplicate parser calls or duplicate events during overlap;
- numeric interval, anchor size, retry/backoff, due-slot, or claim lease defaults;
- product-code/runtime/schema/parser/egress/notification/UI implementation authority from this document;
- any mutation of Beacon, Entitlement, Parser, Egress, or Notification state by Scan.

## 15. Synthetic examples

### EX-SOLS-03-VALID-SCHEDULED-SCAN-INTENT-001

- Synthetic setup: one explicit `beacon_id`, one explicit immutable `configuration_revision_id`, a supported contract/purpose, explicit actor authorization, explicit entitlement decision, proven parser compatibility reference, proven sort context reference, explicit egress availability reference, and a unique idempotency key with semantic fingerprint.
- Expected eligibility outcome: `SCAN_INTENT_ACCEPTED`.
- State effect: the intent may become a single logical run candidate for that exact Beacon/revision pair.
- Forbidden false outcome: do not treat the intent as blocked merely because it came from a scheduler-driven due condition placeholder.

### EX-SOLS-03-VALID-MANUAL-PLACEHOLDER-BLOCKED-001

- Synthetic setup: a manual/check-now request exists only as an unapproved future placeholder with no separately approved manual intent contract.
- Expected eligibility outcome: `SCAN_INTENT_REJECTED_UNSUPPORTED_PURPOSE`.
- State effect: no external effect, no claim, no parser call, no event.
- Forbidden false outcome: do not call the request accepted just because a UI control suggested a manual action.

### EX-SOLS-03-BEACON-REVISION-PINNED-001

- Synthetic setup: the intent was accepted for `beacon_id` A and configuration revision R1, then a newer revision R2 appears before completion.
- Expected eligibility outcome: `SCAN_INTENT_ACCEPTED` remains pinned to R1 for the accepted run scope.
- State effect: the accepted run stays bound to R1 and must not silently switch to R2.
- Forbidden false outcome: do not reinterpret the accepted run as if it had always targeted R2.

### EX-SOLS-03-BEACON-PAUSED-BLOCKED-001

- Synthetic setup: explicit Beacon lifecycle reference shows the Beacon is paused before intent acceptance.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_BEACON_LIFECYCLE`.
- State effect: no normal external effect and no user-visible commit.
- Forbidden false outcome: do not allow normal success merely because entitlement or UI flags look healthy.

### EX-SOLS-03-ENTITLEMENT-DENIED-BLOCKED-001

- Synthetic setup: explicit entitlement decision says denied for the target Beacon/revision scope.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_ENTITLEMENT`.
- State effect: no normal external effect, no comparison commit, no delivery-visible result.
- Forbidden false outcome: do not convert denied entitlement into a normal accepted run.

### EX-SOLS-03-ENTITLEMENT-AMBIGUOUS-BLOCKED-001

- Synthetic setup: the entitlement decision is present but ambiguous or unsupported.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_ENTITLEMENT`.
- State effect: Scan remains blocked until an explicit, non-ambiguous decision exists.
- Forbidden false outcome: do not guess a permissive entitlement outcome.

### EX-SOLS-03-PARSER-COMPATIBILITY-MISSING-BLOCKED-001

- Synthetic setup: no explicit parser compatibility evidence exists for the intended comparison path.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_PARSER_COMPATIBILITY`.
- State effect: no parser-derived comparison eligibility and no external effect.
- Forbidden false outcome: do not pretend compatibility is proven by a transport success signal.

### EX-SOLS-03-SORT-CONTEXT-NOT-PROVEN-BLOCKED-001

- Synthetic setup: parser sort evidence is missing, ambiguous, or unproven for newest-first comparison.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_SORT_CONTEXT`.
- State effect: no normal newest-first comparison and no false no-new conclusion.
- Forbidden false outcome: do not infer a no-new result from absent sort evidence.

### EX-SOLS-03-EGRESS-UNAVAILABLE-REFERENCE-BLOCKED-001

- Synthetic setup: the explicit egress availability reference is unavailable.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_EGRESS_UNAVAILABLE`.
- State effect: no route is chosen, no route is healed, and no external effect begins.
- Forbidden false outcome: do not claim fallback route selection was performed by Scan.

### EX-SOLS-03-IDEMPOTENT-REPLAY-SAME-001

- Synthetic setup: the same idempotency key and the same semantic fingerprint are repeated for the same Beacon/revision request.
- Expected eligibility outcome: `SCAN_INTENT_REPLAYED`.
- State effect: the original outcome or pending state is replayed without new effect.
- Forbidden false outcome: do not emit a duplicate parser call or duplicate event.

### EX-SOLS-03-IDEMPOTENCY-MISMATCH-001

- Synthetic setup: the same idempotency key is reused, but the semantic fingerprint differs.
- Expected eligibility outcome: `SCAN_INTENT_IDEMPOTENCY_MISMATCH`.
- State effect: no effect and no silent overwrite of the original request.
- Forbidden false outcome: do not merge the changed request into the original accepted intent.

### EX-SOLS-03-OVERLAP-CONFLICT-001

- Synthetic setup: one Beacon/revision already has an active comparable scan commitment and a second intent arrives for the same scope.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_OVERLAP`.
- State effect: pending, claimed, or conflict semantics may be recorded, but not duplicate work.
- Forbidden false outcome: do not launch parallel active comparison commits or duplicate events.

### EX-SOLS-03-PENDING-RECOVERY-SINGLE-001

- Synthetic setup: one recovery scan obligation exists after an external failure that started while access was active.
- Expected eligibility outcome: `SCAN_INTENT_PENDING_RECOVERY`.
- State effect: exactly one pending recovery obligation is tracked.
- Forbidden false outcome: do not accumulate the failure into multiple missed scans.

### EX-SOLS-03-RECOVERY-GRACE-AFTER-EXPIRY-001

- Synthetic setup: the scan failure began while access was active, then access expired before the recovery attempt completed.
- Expected eligibility outcome: `SCAN_INTENT_RECOVERY_GRACE_ALLOWED`.
- State effect: the narrow recovery grace exception may allow the one pending recovery scan to proceed.
- Forbidden false outcome: do not generalize grace into an unlimited expiry bypass.

### EX-SOLS-03-NO-NUMERIC-INTERVAL-DEFAULT-001

- Synthetic setup: a scheduling description asks for a cadence but provides no separately approved numeric interval or default.
- Expected eligibility outcome: `SCAN_INTENT_BLOCKED_BY_CONTRACT`.
- State effect: no numeric schedule is invented and no due-slot is fabricated.
- Forbidden false outcome: do not insert a hidden interval, retry, or anchor-window default.
