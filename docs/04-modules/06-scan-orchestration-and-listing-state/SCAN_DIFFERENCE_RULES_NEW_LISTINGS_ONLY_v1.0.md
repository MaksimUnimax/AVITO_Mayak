# Маяк Авито — Scan Difference Rules: New Listings Only v1.0

## Metadata
- status: approved semantic documentation for SOLS-06;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic difference rules for the current owner scope: new listings only.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define the current owner-approved difference scope as new listings after baseline, not price-change notification;
- keep baseline and rolling-anchor comparison semantics explicit and replayable;
- separate safe scan-domain facts from notification delivery and UI rendering;
- preserve anchors and baseline across partial, ambiguous, external-unavailable and malformed outcomes;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no full user-visible listing archive;
- no raw provider payload retention;
- no hard-coded interval, retry, backoff, claim lease, heartbeat or anchor-window default.

## 2. Current owner scope: new listings only

- Current owner-approved difference scope is new listings after baseline, not price-change notification.
- Price may remain display/parser candidate data only.
- Known identity with changed price does not create user notification in this current scope.
- Price-change tracking and price-pair event/notification remain deferred/disabled until separately approved.
- The difference result for this module is about comparison of accepted listing identity against rolling anchors, not about user-visible price transition semantics.
- Notification Delivery and UI/channel modules own rendering and delivery.

## 3. Difference input requirements

A difference comparison may proceed only when all of the following are explicit and accepted for the same Beacon scope:

- an existing accepted baseline;
- rolling anchor state for that Beacon;
- a complete comparison-eligible Parser outcome reference;
- accepted listing identity references for the current ordered candidates;
- proven newest-first/sort context;
- a comparison-eligible completeness signal for the current result set;
- the same beacon/revision scope that the baseline and anchors belong to.

If any required input is missing, ambiguous, unproven or externally unavailable, difference must block or remain pending recovery and must not fabricate a no-new conclusion.

## 4. Rolling-anchor comparison model

- Scan compares current ordered top-window candidates against rolling anchors.
- The parser-provided order, publication/sort signals and listing identity references are used only as comparison evidence.
- Candidates before or above matched anchors may be new listing candidates if identity and sort evidence are accepted.
- Anchors are compact memory, not a full archive and not a price-history store.
- The comparison model is Beacon-scoped and must not bleed across Beacons.
- Replay uses the same accepted anchors and the same committed comparison outcome.

## 5. New-listing candidate rules

- A candidate that is accepted as previously unseen relative to the current rolling anchors may become a new-listing fact.
- A candidate before or above the matched anchor window may be new only when identity, order and comparison eligibility are accepted.
- A new accepted listing identity after baseline may create a new-listing fact.
- A candidate already accepted in the current anchors is not new.
- A candidate that is already anchored by the current Beacon state is not new even if it appears again in the current scan.
- Candidate order alone is not enough; sort context must be proven.

## 6. Known anchor and already-seen rules

- Previously anchored candidate is not new.
- Candidate already accepted in current anchors is not new.
- Known identity with changed price remains known in this current scope.
- Known identity with changed price does not become a user notification here.
- Already-seen identity may still be recorded as safe comparison evidence, but it does not create a new-listing fact.
- The state effect for a known candidate is preservation of baseline/anchors and replayable comparison facts, not reclassification as new.

## 7. Duplicate-within-run rules

- Duplicate candidate within one run does not create duplicate facts.
- Repeated appearance of the same accepted listing identity in the same run is a duplicate candidate, not multiple new listings.
- Duplicate candidate handling must preserve one semantic fact per unique accepted listing identity and run scope.
- Duplicate candidates do not advance anchors twice.
- Duplicate candidates do not create duplicate user-visible outputs.

## 8. No-new-listings rules

- No-new-listings is an explicit successful comparison result, not a fallback for uncertainty.
- No-new-listings means the current ordered comparison against the accepted anchors found no new accepted listing identities in scope.
- No-new-listings preserves baseline and anchors.
- No-new-listings may only be emitted when sort context is proven and comparison eligibility is complete.
- Missing, ambiguous or unproven sort context blocks difference and must not become a false no-new.
- External failure is not no-new and must preserve baseline/anchors.

## 9. Price field and price-change non-notification boundary

- Price may remain display/parser candidate data only.
- Price-change tracking and price-pair notification remain deferred/disabled until separately approved.
- Known identity with changed price does not create user notification in the current scope.
- A price delta does not turn a known listing into a new listing.
- Price fields may support future display or parser-candidate use, but they do not authorise notification delivery in SOLS-06.
- Price-change semantics are outside this document's current owner scope.

## 10. Sort context and newest-first proof boundary

- Difference requires proven newest-first/sort context.
- The parser Adapter module 05 is referenced only as documentation/placeholder contract boundary for ordered candidates, listing identity reference, sort context and publication/sort evidence.
- Scan does not parse Avito, create parser mappings or infer sort truth from transport success.
- Missing, ambiguous or unproven sort context blocks difference and must not become a false no-new result.
- Proven newest-first context is comparison evidence, not a provider archive.
- Current ordered top-window candidates are compared only after sort context proof is accepted.

## 11. Incomplete, partial, ambiguous and external-failure boundaries

- Incomplete, partial, CAPTCHA, external-unavailable, malformed or ambiguous outcome does not advance anchors and does not create new-listing facts.
- External failure is not no-new and must preserve baseline/anchors.
- A partial or ambiguous result is not a successful comparison result.
- A malformed or ambiguous parser outcome remains blocked or pending recovery until resolved by accepted facts.
- No baseline or anchor mutation may be inferred from incomplete context.
- Safe scan-domain facts may be recorded, but comparison advancement must stop.

## 12. Lost anchors and window overflow delegation

- Lost anchors are classified for handoff to SOLS-07 and must not be treated as confirmed new here.
- Lost anchors are a distinct recovery boundary, not a new-listing conclusion.
- Window overflow remains future design and must not become false new or false no-new.
- Window overflow does not authorise archive reconstruction, baseline replacement or silent anchor invention.
- This document delegates lost-anchor recovery and overflow handling semantics to future approved documentation.

## 13. Domain facts and status boundary

- Difference result emits safe scan-domain facts/status only.
- Scan does not emit provider payloads, delivery actions or UI render instructions as part of this scope.
- Notification Delivery and UI/channel modules own rendering and delivery.
- Replay after committed difference returns original difference/anchor outcome and does not duplicate facts.
- A committed difference may be surfaced as a stable internal status fact, but the status fact is not itself notification delivery.
- The difference record must remain replayable and non-destructive to baseline and anchors.

## 14. Forbidden assumptions

- Price-change tracking is not active in this current owner scope.
- Known identity with changed price does not imply notification delivery.
- Missing listing from one scan does not prove deleted, sold or inactive.
- Missing, ambiguous or unproven sort context must not be treated as no-new.
- External failure must not be converted into no-new.
- Window overflow must not be converted into false new or false no-new.
- Lost anchors must not be treated as confirmed new.
- One run must not create duplicate facts for duplicate candidates.
- Scan must not infer parser mappings, live Avito truth, egress routing, notification delivery or UI rendering.

## 15. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `NEW_LISTING_AFTER_BASELINE` | A previously unseen accepted listing identity is confirmed after the baseline for the same Beacon scope. | Existing accepted baseline; rolling anchors; complete comparison-eligible Parser outcome reference; proven sort context; accepted listing identity reference. | Create a new-listing fact and update anchors according to the committed comparison outcome. | Treating the candidate as already known, or as a price-change notification. |
| `KNOWN_ANCHOR_OR_ALREADY_SEEN_IN_CURRENT_ANCHORS` | The candidate is already part of the current Beacon anchors or was already accepted in the current anchor set. | Existing anchors; candidate identity reference; current run comparison reference. | Preserve baseline/anchors and record only stable comparison evidence. | Classifying a known anchor as new. |
| `DUPLICATE_WITHIN_RUN` | The same accepted listing identity appears more than once in one run scope. | One run identity; repeated candidate identity references; same comparison-eligible result set. | Keep a single semantic fact for the identity and avoid duplicate anchor or fact creation. | Creating duplicate new-listing facts or duplicate outputs. |
| `NO_NEW_LISTINGS` | The comparison completed successfully and found no new accepted listing identities. | Existing baseline; rolling anchors; proven sort context; complete comparison-eligible Parser outcome reference; ordered top-window comparison. | Preserve baseline and anchors and record an explicit successful no-new result. | Using uncertainty or failure as a substitute for no-new. |
| `KNOWN_LISTING_PRICE_CHANGED_NO_NOTIFICATION` | The listing identity is known, but its price changed and the current scope does not notify on price change. | Known listing identity; accepted price candidate/reference; existing baseline/anchors; current owner scope. | Keep the listing known and retain price only as candidate/display data. | Turning a known price change into a user notification or a new listing. |
| `SORT_CONTEXT_NOT_PROVEN` | Newest-first or ordered comparison cannot be proven from accepted evidence. | Parser sort/publication evidence; order reference; comparison eligibility proof. | Block difference or mark it pending recovery without false no-new. | Guessing order or converting uncertainty into no-new. |
| `UNSUPPORTED_OR_UNCERTAIN` | The comparison cannot be safely classified because required evidence is unsupported or uncertain. | Ambiguous or unsupported parser/comparison references; missing authority facts. | Keep the result blocked or pending and do not advance anchors. | Converting unsupported evidence into new or no-new. |
| `BLOCKED_BY_INCOMPLETE_CONTEXT` | Required comparison context is incomplete. | Missing baseline, missing anchors, missing eligible parser reference, missing sort proof, or incomplete comparison scope. | Keep comparison blocked and preserve prior authoritative state. | Treating incomplete context as a successful comparison. |
| `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY` | External dependency failure or unavailable upstream state prevents a valid comparison. | CAPTCHA, unavailable provider reference, route failure reference, malformed external outcome or equivalent blocker. | Preserve baseline and anchors, and mark pending recovery or stable blocked status. | Treating external failure as no-new or as new listing confirmation. |
| `AMBIGUOUS_NO_STATE_ADVANCE` | The outcome is ambiguous and cannot safely move the comparison state forward. | Ambiguous parser/comparison reference; incomplete evidence; same Beacon scope. | Do not advance anchors or create new-listing facts. | Producing a false success or false no-new. |
| `LOST_ANCHORS_RECOVERY_REQUIRED` | Anchor continuity is lost and a future recovery handoff is required. | Lost-anchor condition; current Beacon scope; recovery handoff reference. | Classify for SOLS-07 handoff without claiming confirmed new listing. | Treating lost anchors as confirmed new or as no-new. |
| `WINDOW_OVERFLOW_FUTURE_DESIGN` | The comparison window exceeded current design handling and remains future scope. | Overflow signal; anchor-window policy reference; current comparison scope. | Preserve existing authoritative state and delegate to future design. | Converting overflow into false new or false no-new. |

## 16. Synthetic examples

### EX-SOLS-06-NEW-LISTINGS-ABOVE-MATCHED-ANCHOR-001
- Synthetic setup: existing baseline and rolling anchors are accepted; the current ordered top-window contains one previously unseen accepted listing identity before the matched anchor boundary; sort context is proven.
- Expected classification: `NEW_LISTING_AFTER_BASELINE`.
- Expected state/fact effect: create a new-listing fact for the unseen identity and update anchors according to the committed comparison outcome.
- Expected replay/commit behavior: replay returns the same difference and anchor outcome without duplicating the new-listing fact.
- Forbidden false outcome: treat the candidate as known, or as a price-change notification.

### EX-SOLS-06-KNOWN-ANCHOR-NOT-NEW-001
- Synthetic setup: existing anchors already contain the candidate identity; the same listing appears again in the current comparison scope.
- Expected classification: `KNOWN_ANCHOR_OR_ALREADY_SEEN_IN_CURRENT_ANCHORS`.
- Expected state/fact effect: preserve baseline and anchors and record stable comparison evidence only.
- Expected replay/commit behavior: replay returns the original known-anchor outcome without creating a new fact.
- Forbidden false outcome: classify the known anchor as new.

### EX-SOLS-06-DUPLICATE-CANDIDATE-WITHIN-RUN-001
- Synthetic setup: the same accepted listing identity appears twice in one run's ordered candidate set.
- Expected classification: `DUPLICATE_WITHIN_RUN`.
- Expected state/fact effect: create one semantic fact for the identity and suppress duplicate fact creation.
- Expected replay/commit behavior: replay preserves the single fact and does not multiply anchors or outputs.
- Forbidden false outcome: duplicate new-listing facts or duplicate user-visible output.

### EX-SOLS-06-NO-NEW-LISTINGS-EXPLICIT-SUCCESS-001
- Synthetic setup: existing baseline and anchors are present; all accepted candidates are already known; sort context is proven; comparison eligibility is complete.
- Expected classification: `NO_NEW_LISTINGS`.
- Expected state/fact effect: preserve baseline and anchors and record an explicit successful no-new result.
- Expected replay/commit behavior: replay returns the same no-new comparison outcome without duplicating facts.
- Forbidden false outcome: use uncertainty as a fallback to no-new or treat the scan as failed.

### EX-SOLS-06-PRICE-CHANGED-KNOWN-LISTING-NO-NOTIFICATION-001
- Synthetic setup: a known listing identity appears with a different price candidate than the last accepted price, but the current scope is new listings only.
- Expected classification: `KNOWN_LISTING_PRICE_CHANGED_NO_NOTIFICATION`.
- Expected state/fact effect: keep the listing known, retain price only as candidate/display data, and do not emit a notification.
- Expected replay/commit behavior: replay preserves the same known-listing outcome and does not create delivery facts.
- Forbidden false outcome: new listing classification or user notification.

### EX-SOLS-06-SORT-CONTEXT-NOT-PROVEN-NO-FALSE-NO-NEW-001
- Synthetic setup: ordered candidates exist but newest-first proof is missing, ambiguous or unproven.
- Expected classification: `SORT_CONTEXT_NOT_PROVEN`.
- Expected state/fact effect: block difference and preserve baseline/anchors without false no-new.
- Expected replay/commit behavior: replay remains blocked until sort proof is accepted.
- Forbidden false outcome: treat the uncertainty as no-new.

### EX-SOLS-06-PARTIAL-OUTCOME-NO-STATE-ADVANCE-001
- Synthetic setup: the scan result is partial and does not cover the complete comparison-eligible candidate set.
- Expected classification: `BLOCKED_BY_INCOMPLETE_CONTEXT`.
- Expected state/fact effect: do not advance anchors and do not create new-listing facts.
- Expected replay/commit behavior: replay preserves the blocked status until complete evidence exists.
- Forbidden false outcome: baseline or anchor advancement from partial evidence.

### EX-SOLS-06-CAPTCHA-EXTERNAL-FAILURE-PENDING-RECOVERY-001
- Synthetic setup: the external provider or upstream dependency is unavailable because access is restricted by CAPTCHA.
- Expected classification: `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`.
- Expected state/fact effect: preserve baseline and anchors and register pending recovery or blocked status.
- Expected replay/commit behavior: replay returns the same external-unavailable state without converting it to no-new.
- Forbidden false outcome: no-new result or erased anchor state.

### EX-SOLS-06-AMBIGUOUS-PARSER-NO-NEW-FACT-001
- Synthetic setup: the parser outcome exists, but its comparison meaning is ambiguous and not sufficiently proven.
- Expected classification: `AMBIGUOUS_NO_STATE_ADVANCE`.
- Expected state/fact effect: do not advance anchors or create a new-listing fact.
- Expected replay/commit behavior: replay preserves the ambiguity until accepted evidence resolves it.
- Forbidden false outcome: confirmed new listing or confirmed no-new.

### EX-SOLS-06-MISSING-LISTING-DOES-NOT-PROVE-DELETED-001
- Synthetic setup: one previously known listing is absent from the current scan, but there is no independent deletion evidence.
- Expected classification: `NO_NEW_LISTINGS`.
- Expected state/fact effect: preserve the existing comparison state and do not infer deleted, sold or inactive status.
- Expected replay/commit behavior: replay preserves the absence-of-proof boundary without creating deletion facts.
- Forbidden false outcome: deletion, sold or inactive proof from absence alone.

### EX-SOLS-06-LOST-ANCHORS-DELEGATED-TO-SOLS-07-001
- Synthetic setup: anchor continuity is broken and the comparison cannot safely classify the result as a new listing or no-new.
- Expected classification: `LOST_ANCHORS_RECOVERY_REQUIRED`.
- Expected state/fact effect: classify for SOLS-07 handoff and do not treat the outcome as confirmed new.
- Expected replay/commit behavior: replay keeps the same recovery-required classification until future recovery semantics are approved.
- Forbidden false outcome: confirmed new listing or false no-new.

### EX-SOLS-06-WINDOW-OVERFLOW-FUTURE-DESIGN-001
- Synthetic setup: the ordered comparison exceeds the current comparison window handling boundary.
- Expected classification: `WINDOW_OVERFLOW_FUTURE_DESIGN`.
- Expected state/fact effect: preserve current authoritative state and delegate overflow handling to future design.
- Expected replay/commit behavior: replay returns the same overflow classification without inventing a new comparison result.
- Forbidden false outcome: false new or false no-new.

### EX-SOLS-06-POST-COMMIT-REPLAY-NO-DUPLICATE-FACT-001
- Synthetic setup: a difference result was already committed for the same Beacon scope and the same ordered comparison inputs are replayed.
- Expected classification: `NEW_LISTING_AFTER_BASELINE` or `NO_NEW_LISTINGS`, matching the original committed outcome.
- Expected state/fact effect: return the original difference/anchor outcome and do not duplicate facts.
- Expected replay/commit behavior: replay is idempotent and references the original committed result.
- Forbidden false outcome: duplicate new-listing facts or duplicate anchor updates.

### EX-SOLS-06-BASELINE-ABSENT-BLOCKED-001
- Synthetic setup: no accepted baseline exists for the current explicit Beacon/revision scope.
- Expected classification: `BLOCKED_BY_INCOMPLETE_CONTEXT`.
- Expected state/fact effect: keep difference blocked and do not fabricate a no-new result.
- Expected replay/commit behavior: replay remains blocked until a valid baseline exists.
- Forbidden false outcome: implicit no-new or hidden baseline inference.

### EX-SOLS-06-ANCHORS-NOT-ADVANCED-ON-UNCERTAINTY-001
- Synthetic setup: the scan contains ambiguous sort or incomplete comparison evidence, even though some listing identities are present.
- Expected classification: `UNSUPPORTED_OR_UNCERTAIN`.
- Expected state/fact effect: preserve anchors and do not advance comparison state on uncertainty.
- Expected replay/commit behavior: replay keeps the same uncertain classification until accepted evidence resolves it.
- Forbidden false outcome: advancing anchors, claiming new listing, or claiming no-new.
