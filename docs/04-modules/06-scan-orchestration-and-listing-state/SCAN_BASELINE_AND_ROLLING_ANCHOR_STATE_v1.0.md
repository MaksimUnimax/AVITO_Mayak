# Маяк Авито — Scan Baseline and Rolling Anchor State v1.0

## Metadata
- status: approved semantic documentation for SOLS-05;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic baseline and rolling anchor state boundaries for one Beacon-scoped comparison flow.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define the semantic boundary for initial baseline establishment and rolling anchor continuity;
- keep Beacon-scoped comparison memory compact and replayable without turning it into a full archive;
- keep parser sort evidence, comparison eligibility and anchor advancement explicit;
- preserve state on failed, partial, ambiguous, CAPTCHA, blocked or external-unavailable outcomes;
- document synthetic examples only.

Non-goals:

- no code, test, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no hard-coded anchor window size or interval default;
- no live Avito/provider traffic;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no production persistence design or physical uniqueness design.

## 2. Baseline definition

- A baseline is the first complete comparison-eligible accepted state for one `beacon_id` under one explicit Beacon configuration revision/provenance context.
- The first complete comparison-eligible scan establishes the initial baseline.
- Baseline establishment emits no user new-listing result for the baseline contents.
- Baseline initialization also initializes rolling anchor state.
- Baseline contents are authoritative comparison starting memory, not a user-visible listing archive.
- A baseline is not a Parser truth claim, not a Notification trigger and not a Beacon or Entitlement mutation.

## 3. Rolling anchor state definition

- Rolling anchor state belongs to one explicit `beacon_id`.
- Rolling anchor state is isolated per Beacon even if two Beacons see the same provider listing identity.
- Rolling anchor state is tied to explicit Beacon configuration revision/provenance references.
- Rolling anchors are compact memory, not a full user-visible listing archive.
- Scan does not store all old listing cards, descriptions, phones, sellers, full history or raw provider payloads.
- Anchor state stores only enough accepted listing references to compare a future top-window.
- Anchor state updates after every successful comparison-eligible scan.
- Anchor state may remain semantically unchanged when a successful scan confirms no new listing, but the replayed commit must still remain idempotent.

## 4. Parser ordered candidate and sort evidence boundary

- Parser Adapter module 05 owns ordered candidates, listing identity reference, sort context and publication/sort evidence as documentation/placeholder contract boundary only.
- Scan consumes explicit parser references only.
- Scan must not parse Avito, infer parser truth or create parser mappings.
- Missing, ambiguous or unproven sort context blocks baseline and anchor advancement.
- Missing, ambiguous or unproven sort context must not become a false no-new result.
- Sort evidence is a comparison-eligibility reference, not a provider-side archive.

## 5. First complete baseline rules

- First complete comparison-eligible scan establishes the initial baseline.
- The baseline is established only once per explicit Beacon/revision scope.
- Baseline establishment requires serialized, conflict-free comparison commit.
- Baseline establishment accepts immutable observations only.
- Baseline establishment initializes rolling anchors from the accepted comparison scope.
- A partial, ambiguous, CAPTCHA, blocked or external-unavailable outcome cannot establish baseline.

## 6. Baseline non-notification rule

- Baseline establishment emits no user new-listing result for baseline contents.
- Baseline establishment emits no price-change notification, no new-listing spam and no notification delivery side effect.
- Baseline establishment may emit only safe semantic facts/status after the comparison commit boundary.
- Replay of the baseline commit must return the original baseline outcome without duplicating user-visible change output.

## 7. Anchor update rules after successful comparison-eligible scan

- Anchor state updates after every successful comparison-eligible scan.
- Successful comparison-eligible scan means the comparison commit completed under the accepted eligibility boundary.
- The anchor update may be semantically `ANCHOR_STATE_UPDATED` or `ANCHOR_STATE_UNCHANGED_NO_NEW` depending on the accepted comparison outcome.
- Failed, partial, ambiguous, CAPTCHA, blocked or external-unavailable outcomes do not advance anchors.
- Missing listing from one scan does not prove deleted, sold or inactive.
- Anchor update replay must not duplicate observations or anchor membership.

## 8. Anchor window policy reference

- Anchor window size is a policy/config reference and future Admin-configurable.
- No hard-coded anchor window size is introduced here.
- Window overflow is future design and must not be converted into false new or false no-new.
- The anchor window policy reference is a stable semantic reference, not a numeric default.
- Lost anchors are related but not fully handled here; SOLS-07 will define lost-anchor recovery behavior.

## 9. Beacon/revision isolation rules

- Anchor state belongs to one explicit `beacon_id`.
- Anchor state is isolated per Beacon even if provider listing identity is identical.
- Anchor state is tied to explicit Beacon configuration revision/provenance references.
- Scan must not silently reinterpret an old baseline under a newer Beacon revision.
- A newer revision requires its own explicit baseline scope and cannot inherit old baseline meaning by assumption.
- Physical storage, compaction, retention and deletion remain gated by OD-013 and DB/persistence decisions.

## 10. Comparison eligibility rules

- Comparison eligibility requires explicit Beacon/revision scope, accepted parser outcome reference, sort evidence sufficiency and comparison-eligible completeness.
- Comparison eligibility requires that missing, ambiguous or unproven sort context is not present.
- Comparison eligibility requires that external failure, CAPTCHA, blocked, partial or ambiguous signals do not remain unresolved.
- Comparison eligibility requires that Scan can compare accepted top-window references without guessing parser truth.
- If any required fact is missing, baseline and anchor advancement stay blocked.
- Missing, ambiguous or unproven sort context blocks advancement and must not become a false no-new conclusion.

## 11. Empty result and genuine-empty boundary

- Empty baseline is allowed only if Parser proves genuine empty under a strict future/placeholder evidence boundary.
- A returned empty-looking result is not enough by itself.
- Genuine empty proof must be explicit, accepted and comparison-eligible.
- `GENUINE_EMPTY_BASELINE_ACCEPTED` means the empty result was proven under the accepted boundary.
- `GENUINE_EMPTY_NOT_PROVEN` means the result remains blocked or ambiguous.
- Scan must not infer empty truth from omission, truncation or lack of evidence.

## 12. Revision changes and baseline interpretation

- A baseline is revision-scoped and cannot be silently reinterpreted under a newer Beacon revision.
- Old baseline state remains attached to its original explicit revision/provenance context.
- A new revision may require a new baseline scope even when the provider listing identity looks the same.
- `REVISION_BASELINE_SCOPE_MISMATCH` means the revision context does not match the baseline scope that was accepted previously.
- Scan must not rebind an old baseline to a new revision without explicit new acceptance.

## 13. Privacy and minimization boundary

- Rolling anchors are compact memory, not full history.
- Scan does not store all old listing cards, descriptions, phones, sellers, full history or raw provider payloads.
- Scan keeps only minimal accepted listing references, provenance and comparison-needed metadata.
- Raw provider payload retention is out of scope here and remains constrained by owner decisions and OD-013.
- Privacy minimization applies to baseline, anchor and comparison references alike.

## 14. Forbidden assumptions

- Missing listing from one scan does not prove deleted, sold or inactive.
- Failed, partial, ambiguous, CAPTCHA, blocked or external-unavailable outcomes do not establish baseline.
- Failed, partial, ambiguous, CAPTCHA, blocked or external-unavailable outcomes do not advance anchors.
- Scan must not parse Avito or infer parser truth.
- Missing, ambiguous or unproven sort context must not become a false no-new.
- Window overflow must not be converted into false new or false no-new.

## Required semantic classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts/references | Allowed state effect | Forbidden false outcome |
|---|---|---|---|---|
| `BASELINE_NOT_ESTABLISHED` | No accepted baseline exists for the current explicit Beacon/revision scope. | Missing or insufficient complete comparison-eligible scan; absent baseline commit; no accepted baseline reference. | Keep baseline unset and keep anchors non-authoritative for that scope. | Silent baseline inference, implicit no-new, or hidden archive creation. |
| `BASELINE_ESTABLISHED` | The first complete comparison-eligible scan has established the initial baseline. | Complete comparison-eligible scan; serialized comparison commit; explicit Beacon/revision scope; accepted baseline reference. | Create the baseline and initialize rolling anchors. | Additional baseline for the same scope, or user new-listing result for baseline contents. |
| `BASELINE_BLOCKED_BY_INCOMPLETE_CONTEXT` | Baseline cannot be established because required context is incomplete. | Missing comparison scope, missing eligible parser reference, missing revision reference, or other incomplete authority facts. | Keep baseline blocked and do not advance anchors. | Treating incomplete context as acceptance or as no-new. |
| `BASELINE_BLOCKED_BY_SORT_CONTEXT` | Baseline cannot be established because sort/publication evidence is missing, ambiguous or unproven. | Parser ordered candidate evidence, sort context proof, publication/sort evidence, comparison eligibility check. | Keep baseline and anchor advancement blocked until sort context is proven. | Silent fallback to guessed order or false no-new. |
| `BASELINE_BLOCKED_BY_EXTERNAL_FAILURE` | Baseline cannot be established because provider/external availability failed. | External-unavailable, blocked, CAPTCHA or equivalent unavailable evidence; no accepted comparison-eligible result. | Preserve existing state and do not create baseline. | Converting external failure into baseline success or no-new. |
| `BASELINE_BLOCKED_BY_PARTIAL_OR_AMBIGUOUS_OUTCOME` | Baseline cannot be established because the outcome is partial or ambiguous. | Partial classification, ambiguous parser reference, incomplete accepted comparison outcome. | Preserve existing state and do not advance anchors. | Converting partial or ambiguous outcome into baseline success. |
| `ANCHOR_STATE_INITIALIZED` | Rolling anchor state has been initialized from the accepted baseline. | `BASELINE_ESTABLISHED` plus accepted comparison references and Beacon/revision scope. | Create compact anchor memory for future top-window comparison. | Full archive initialization or cross-Beacon anchor bleed. |
| `ANCHOR_STATE_UPDATED` | Rolling anchor state has been advanced by a successful comparison-eligible scan. | Successful comparison-eligible scan; accepted comparison references; current anchor window policy reference. | Update anchor membership/references in compact memory form. | Duplicate anchor advancement or replacement with raw history. |
| `ANCHOR_STATE_UNCHANGED_NO_NEW` | Successful comparison-eligible scan confirmed no new semantic effect for the anchor set. | Existing baseline; accepted comparison result; replayable anchor membership facts. | Keep anchors semantically stable while preserving the successful scan outcome. | Reclassifying the result as failure, reset, or false new. |
| `ANCHOR_STATE_NOT_ADVANCED` | Anchors were not advanced because the scan was not eligible or not successful. | Failed, partial, ambiguous, CAPTCHA, blocked or external-unavailable outcome. | Preserve existing anchors without advancement. | Quietly moving anchors forward or pretending a no-new success. |
| `ANCHOR_WINDOW_POLICY_REFERENCE_REQUIRED` | Anchor advancement requires a policy/config reference for the window. | Window policy reference, future Admin-configurable boundary, comparison scope. | Bind anchor comparison to the policy reference rather than to a hard-coded size. | Hard-coded window size or numeric default. |
| `GENUINE_EMPTY_BASELINE_ACCEPTED` | Empty baseline is proven genuine under the accepted strict boundary. | Explicit genuine-empty parser proof; strict future/placeholder evidence boundary; comparison-eligible acceptance. | Establish an empty baseline and initialize empty anchor memory for the scope. | Treating unproven emptiness as accepted empty baseline. |
| `GENUINE_EMPTY_NOT_PROVEN` | Empty-looking result is not proven genuine and therefore cannot establish empty baseline. | Empty-looking or incomplete result without explicit genuine-empty proof. | Keep baseline blocked or ambiguous. | Turning unproven emptiness into accepted empty baseline. |
| `REVISION_BASELINE_SCOPE_MISMATCH` | The baseline scope does not match the explicit Beacon revision context. | Baseline reference; explicit Beacon configuration revision/provenance reference; scope mismatch evidence. | Reject reinterpretation of old baseline under the new revision. | Silent reuse of the old baseline under a different revision. |

## 15. Synthetic examples

### EX-SOLS-05-FIRST-COMPLETE-BASELINE-001
- Synthetic setup: one Beacon, first complete comparison-eligible scan, no prior baseline, sort context proven, explicit revision scope.
- Expected semantic class: `BASELINE_ESTABLISHED`.
- Expected state effect: create the initial baseline and initialize rolling anchors.
- Expected replay/commit behavior: replay returns the same baseline reference and does not create a second baseline or duplicate anchor state.
- Forbidden false outcome: user new-listing output for baseline contents, or false no-new inference from an uninitialized baseline.

### EX-SOLS-05-FIRST-BASELINE-NO-NOTIFICATION-001
- Synthetic setup: first complete comparison-eligible scan contains baseline contents only and no prior accepted baseline exists.
- Expected semantic class: `BASELINE_ESTABLISHED`.
- Expected state effect: establish baseline without emitting user-visible new-listing output for baseline contents.
- Expected replay/commit behavior: idempotent replay preserves the baseline fact and keeps notification output absent for the baseline contents.
- Forbidden false outcome: notification delivery, price-change output, or a baseline that behaves like a new-listing alert.

### EX-SOLS-05-ANCHORS-INITIALIZED-FROM-BASELINE-001
- Synthetic setup: accepted baseline exists for one Beacon and the first comparison-eligible scan completes the baseline commit.
- Expected semantic class: `ANCHOR_STATE_INITIALIZED`.
- Expected state effect: initialize compact rolling anchors from the accepted baseline.
- Expected replay/commit behavior: replay preserves the same anchor initialization without duplicating anchor membership.
- Forbidden false outcome: full archive creation, cross-Beacon anchor reuse, or raw provider payload retention.

### EX-SOLS-05-ANCHORS-UPDATED-AFTER-SUCCESSFUL-SCAN-001
- Synthetic setup: existing baseline, successful comparison-eligible scan, accepted top-window references and proven sort context.
- Expected semantic class: `ANCHOR_STATE_UPDATED`.
- Expected state effect: advance compact rolling anchors after the successful comparison-eligible scan.
- Expected replay/commit behavior: replay returns the same anchor update and does not duplicate observations.
- Forbidden false outcome: baseline reset, duplicate anchor advancement, or notification side effects.

### EX-SOLS-05-ANCHORS-UNCHANGED-NO-NEW-001
- Synthetic setup: existing baseline, successful comparison-eligible scan, all compared references already accepted, no new semantic effect.
- Expected semantic class: `ANCHOR_STATE_UNCHANGED_NO_NEW`.
- Expected state effect: keep anchor membership semantically stable while preserving the successful scan outcome.
- Expected replay/commit behavior: replay preserves the unchanged anchor state and the no-new semantic result.
- Forbidden false outcome: false new-listing classification, hidden baseline reset, or failure conversion.

### EX-SOLS-05-PARTIAL-OUTCOME-NO-BASELINE-001
- Synthetic setup: scan returns a partial outcome with incomplete candidate coverage.
- Expected semantic class: `BASELINE_BLOCKED_BY_PARTIAL_OR_AMBIGUOUS_OUTCOME`.
- Expected state effect: do not establish baseline and do not advance anchors.
- Expected replay/commit behavior: replay preserves the same blocked classification until new authoritative facts exist.
- Forbidden false outcome: baseline establishment, anchor update, or false no-new conclusion.

### EX-SOLS-05-CAPTCHA-NO-ANCHOR-ADVANCE-001
- Synthetic setup: comparison attempt is restricted by CAPTCHA or a comparable external barrier.
- Expected semantic class: `BASELINE_BLOCKED_BY_EXTERNAL_FAILURE`.
- Expected state effect: preserve existing state and do not advance anchors.
- Expected replay/commit behavior: replay keeps the same blocked result and does not turn the outcome into success.
- Forbidden false outcome: baseline establishment, anchor advancement, or notification delivery.

### EX-SOLS-05-SORT-CONTEXT-NOT-PROVEN-BLOCKS-BASELINE-001
- Synthetic setup: ordered candidate evidence exists, but sort/publication context is not proven.
- Expected semantic class: `BASELINE_BLOCKED_BY_SORT_CONTEXT`.
- Expected state effect: block baseline and anchor advancement until sort context is proven.
- Expected replay/commit behavior: replay remains blocked with the same missing sort proof.
- Forbidden false outcome: false no-new result, guessed order acceptance, or silent parser-truth inference.

### EX-SOLS-05-GENUINE-EMPTY-BASELINE-PROVEN-001
- Synthetic setup: Parser provides explicit genuine-empty proof under the strict future/placeholder evidence boundary.
- Expected semantic class: `GENUINE_EMPTY_BASELINE_ACCEPTED`.
- Expected state effect: establish an empty baseline and initialize empty anchor memory for the scope.
- Expected replay/commit behavior: replay returns the same empty baseline acceptance and does not invent listings.
- Forbidden false outcome: treating the empty result as unproven or as a hidden new-listing event.

### EX-SOLS-05-GENUINE-EMPTY-NOT-PROVEN-BLOCKED-001
- Synthetic setup: scan result looks empty, but genuine-empty proof is missing or ambiguous.
- Expected semantic class: `GENUINE_EMPTY_NOT_PROVEN`.
- Expected state effect: keep baseline blocked or ambiguous and do not accept empty baseline.
- Expected replay/commit behavior: replay preserves the blocked status until explicit genuine-empty proof exists.
- Forbidden false outcome: empty baseline acceptance, false no-new, or silent inference from omission.

### EX-SOLS-05-SAME-PROVIDER-LISTING-DIFFERENT-BEACONS-ISOLATED-001
- Synthetic setup: two Beacons observe the same provider listing identity under different explicit Beacon scopes.
- Expected semantic class: `ANCHOR_STATE_INITIALIZED` for each Beacon scope, with isolated state.
- Expected state effect: keep anchor state isolated per Beacon and avoid cross-Beacon deduplication effects.
- Expected replay/commit behavior: replay for one Beacon does not mutate or suppress the other Beacon’s state.
- Forbidden false outcome: shared baseline, shared anchors or cross-Beacon suppression.

### EX-SOLS-05-NEW-REVISION-DOES-NOT-REINTERPRET-OLD-BASELINE-001
- Synthetic setup: a newer Beacon configuration revision is explicit while an older baseline exists for a previous revision.
- Expected semantic class: `REVISION_BASELINE_SCOPE_MISMATCH`.
- Expected state effect: reject silent reinterpretation of the old baseline under the new revision.
- Expected replay/commit behavior: replay keeps the mismatch until a new explicit baseline scope is accepted.
- Forbidden false outcome: automatic reuse of the old baseline or automatic revision rebinding.

### EX-SOLS-05-MISSING-LISTING-DOES-NOT-PROVE-DELETED-001
- Synthetic setup: one known listing is absent from the current scan, but no independent deletion evidence exists.
- Expected semantic class: `ANCHOR_STATE_UNCHANGED_NO_NEW`.
- Expected state effect: preserve the existing comparison state and do not infer deletion, sale or inactivity.
- Expected replay/commit behavior: replay preserves the same no-deletion inference boundary.
- Forbidden false outcome: deletion proof, sold proof or inactive proof from absence alone.

### EX-SOLS-05-ANCHOR-WINDOW-SIZE-POLICY-REFERENCE-ONLY-001
- Synthetic setup: anchor comparison needs a window reference, but no numeric window size is introduced in the doc.
- Expected semantic class: `ANCHOR_WINDOW_POLICY_REFERENCE_REQUIRED`.
- Expected state effect: bind comparison to a policy/config reference rather than a hard-coded value.
- Expected replay/commit behavior: replay preserves the same policy-reference dependency without inventing a number.
- Forbidden false outcome: hard-coded window size, hidden numeric default or future policy bypass.

### EX-SOLS-05-NO-FULL-LISTING-ARCHIVE-001
- Synthetic setup: accepted baseline and anchors exist, and the next scan only needs comparison continuity.
- Expected semantic class: `ANCHOR_STATE_UPDATED`.
- Expected state effect: keep only compact anchor memory and minimal references, not a full user-visible archive.
- Expected replay/commit behavior: replay preserves the same compact state without expanding into archive retention.
- Forbidden false outcome: storing all old cards, descriptions, phones, sellers or full history.

### EX-SOLS-05-WINDOW-OVERFLOW-FUTURE-DESIGN-001
- Synthetic setup: a future case would exceed the anchor window, but this document does not define overflow handling.
- Expected semantic class: `ANCHOR_WINDOW_POLICY_REFERENCE_REQUIRED`.
- Expected state effect: leave overflow handling to future design and keep current semantics non-committal.
- Expected replay/commit behavior: replay must not transform overflow into false new or false no-new.
- Forbidden false outcome: silent overflow truncation treated as a user-visible change or as a hidden no-new guarantee.
