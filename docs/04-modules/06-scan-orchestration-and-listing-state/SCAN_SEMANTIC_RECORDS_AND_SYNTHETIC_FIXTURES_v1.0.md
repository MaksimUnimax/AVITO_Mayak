# Маяк Авито — Scan Semantic Records and Synthetic Fixtures v1.0

status: approved semantic documentation for SOLS-02
date: 2026-07-09
module: 06-scan-orchestration-and-listing-state
prerequisite: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04
not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization

This document is docs-only and transport/provider/framework/ORM neutral.
It defines logical semantic records and synthetic fixture definitions only.
It does not authorize implementation, runtime behavior, schema changes, or live provider traffic.

## Scope and boundary rules

- Scan does not parse Avito.
- Scan does not choose Egress route.
- Scan does not mutate Beacon lifecycle/configuration/revision.
- Scan does not mutate entitlement/payment/grant state.
- Scan does not render or send Notification.
- Scan does not own the full listing archive.
- Scan does not store raw provider payloads.
- Price may remain display/parser candidate data only.
- Price-change tracking and price-pair notification remain deferred/disabled.
- Anchor window size is policy/config reference and future Admin-configurable, not hard-coded.

## Semantic record families

### ScanIntent
- Purpose: capture the intent to perform a scan for a specific Beacon and listing-state scope.
- Required references: Beacon identity, revision/provenance reference, policy/config reference, run correlation reference.
- Mutation authority / owner boundary: Scan may create and read this intent; Scan does not own Beacon lifecycle or configuration.
- Forbidden assumptions: not a provider payload, not a parser outcome, not a final status.
- Replay/idempotency note: duplicate replay of the same intent must not create a second independent run claim.
- Privacy/minimization note: keep only identifiers needed for correlation and scope.

### ScanRun
- Purpose: represent one logical scan execution instance.
- Required references: ScanIntent, Beacon reference, revision/reference snapshot, comparison scope reference.
- Mutation authority / owner boundary: Scan owns the run state for its own work only.
- Forbidden assumptions: not a listing archive, not an entitlement decision, not an egress choice.
- Replay/idempotency note: repeated processing of the same run identity must converge on one run record.
- Privacy/minimization note: store only run identifiers and outcome facts necessary for audit.

### ScanAttempt
- Purpose: represent one attempt within a run, including retry or recovery attempts.
- Required references: ScanRun, attempt index, failure/recovery reason reference, time/order reference.
- Mutation authority / owner boundary: Scan owns attempt bookkeeping; no other module may rewrite attempt semantics.
- Forbidden assumptions: attempt count is not evidence of provider success, parser success, or lifecycle authority.
- Replay/idempotency note: an already-recorded attempt must not be duplicated by replay.
- Privacy/minimization note: minimize transport details; do not retain raw payloads.

### ParserOutcomeReference
- Purpose: reference a parser outcome needed by Scan without making Scan the parser.
- Required references: Parser Adapter module 05 outcome reference, listing identity reference, parser confidence/ambiguity reference.
- Mutation authority / owner boundary: Parser Adapter owns parsing semantics; Scan only consumes the reference.
- Forbidden assumptions: Scan must not derive parser truth beyond the reference.
- Replay/idempotency note: identical parser references should resolve to the same semantic meaning across replays.
- Privacy/minimization note: exclude raw provider payloads and any extraneous personal data.

### BeaconScanEligibility
- Purpose: state whether a Beacon is eligible for Scan consideration at the time of evaluation.
- Required references: Beacon lifecycle reference, entitlement/grant reference, policy reference.
- Mutation authority / owner boundary: Scan may evaluate; Scan does not mutate eligibility source records.
- Forbidden assumptions: eligibility does not imply new listings, baseline success, or notification authority.
- Replay/idempotency note: eligibility evaluation should be repeatable against the same facts.
- Privacy/minimization note: keep only the minimum lifecycle and entitlement facts required.

### RollingAnchorState
- Purpose: hold the current rolling anchor set used for comparison continuity.
- Required references: anchor membership reference, order/reference window reference, Beacon reference.
- Mutation authority / owner boundary: Scan maintains rolling anchor state for comparison only.
- Forbidden assumptions: anchors are not the full listing archive and not a price-history store.
- Replay/idempotency note: reprocessing the same accepted state must not reorder or duplicate anchors.
- Privacy/minimization note: store only anchor identifiers and minimal comparison metadata.

### AnchorWindowPolicyReference
- Purpose: point to the policy/config reference that defines anchor window size and selection behavior.
- Required references: policy/config reference, future Admin-configurable boundary, version/reference time.
- Mutation authority / owner boundary: policy owner or future Admin surface owns the value; Scan only consumes it.
- Forbidden assumptions: anchor window size is not hard-coded in Scan.
- Replay/idempotency note: policy references should be stable for the run snapshot.
- Privacy/minimization note: no privacy-sensitive data is needed beyond the policy reference.

### AnchorMatchResult
- Purpose: capture whether an observed item matches the rolling anchors.
- Required references: observed listing identity reference, anchor reference, match rationale reference.
- Mutation authority / owner boundary: Scan owns the comparison result only.
- Forbidden assumptions: a match is not a provider truth claim beyond the observed comparison.
- Replay/idempotency note: same observation and same anchors must yield the same semantic result.
- Privacy/minimization note: keep only identifiers and minimal match rationale.

### BaselineReference
- Purpose: record the first complete baseline anchor/reference set for a Beacon.
- Required references: ScanRun, completeness reference, anchor set reference, revision snapshot.
- Mutation authority / owner boundary: Scan owns the baseline fact; it does not own the upstream source data.
- Forbidden assumptions: baseline is not a notification trigger and not a lifecycle mutation.
- Replay/idempotency note: first complete baseline is a one-time semantic fact for the same Beacon/revision context.
- Privacy/minimization note: baseline should retain only the minimal identifiers needed for later comparison.

### DifferenceResult
- Purpose: capture semantic difference between observed listings and the current baseline/anchors.
- Required references: BaselineReference, observed listing reference, comparison scope reference.
- Mutation authority / owner boundary: Scan owns the difference fact.
- Forbidden assumptions: difference alone does not authorize Egress, Notification, or lifecycle changes.
- Replay/idempotency note: identical inputs should lead to the same difference classification.
- Privacy/minimization note: avoid storing raw payloads or non-essential item fields.

### ListingCandidateReference
- Purpose: reference a listing candidate produced for Scan comparison or later display/parser use.
- Required references: listing identity reference, parser/display candidate reference, price candidate reference when present.
- Mutation authority / owner boundary: Scan references the candidate; Parser Adapter owns parser-side derivation.
- Forbidden assumptions: candidate is not confirmed new, not confirmed lost, and not a user-visible notification by itself.
- Replay/idempotency note: repeated observation of the same candidate should not multiply candidate identities.
- Privacy/minimization note: retain only fields required for semantic comparison.

### ListingFirstSeenResult
- Purpose: mark the first-seen semantic result for a new listing relative to the baseline window.
- Required references: ListingCandidateReference, baseline/anchor reference, observation order reference.
- Mutation authority / owner boundary: Scan owns the first-seen semantic result.
- Forbidden assumptions: first-seen does not imply price-pair or price-change notification.
- Replay/idempotency note: once first-seen is established, replay should not convert it into a different class for the same facts.
- Privacy/minimization note: do not retain unnecessary history beyond the first-seen fact.

### ScanStatusFact
- Purpose: record the final scan status or stable status fact for the run.
- Required references: ScanRun, outcome classification reference, reason/fact reference.
- Mutation authority / owner boundary: Scan owns its status fact.
- Forbidden assumptions: status fact is not a provider outcome and not a lifecycle grant.
- Replay/idempotency note: stable statuses must remain stable under replay of the same authoritative inputs.
- Privacy/minimization note: keep status facts concise and non-sensitive.

### PendingRecoveryScan
- Purpose: represent a scan that must be retried after an external or transient blocker.
- Required references: ScanRun, blocker reason reference, retry/recovery eligibility reference.
- Mutation authority / owner boundary: Scan owns the pending-recovery fact only.
- Forbidden assumptions: pending recovery is not no-new-listings and not a final failure of comparison semantics.
- Replay/idempotency note: repeated evaluation should not flip pending recovery into a false baseline.
- Privacy/minimization note: no raw blocker payloads.

### LostAnchorsRecoveryResult
- Purpose: capture recovery after anchors are lost, expired, or restored by a defined recovery rule.
- Required references: RollingAnchorState, recovery window/policy reference, recovered item reference.
- Mutation authority / owner boundary: Scan owns the recovery result; policy owner owns recovery rules.
- Forbidden assumptions: recovery is not a full archive reconstruction.
- Replay/idempotency note: same recovery inputs must produce the same recovery result.
- Privacy/minimization note: retain only the minimal anchor and recovery identifiers.

### ScanDomainFact
- Purpose: store stable domain facts that Scan is allowed to own.
- Required references: Beacon reference, listing-state reference, comparison/reference snapshot.
- Mutation authority / owner boundary: Scan owns only safe domain facts in its bounded scope.
- Forbidden assumptions: not a parser truth, not entitlement truth, not a lifecycle command.
- Replay/idempotency note: safe facts should remain stable for the same authoritative source state.
- Privacy/minimization note: minimize to the required non-sensitive domain facts.

### OverlapState
- Purpose: describe whether concurrent or overlapping scan work exists for the same Beacon scope.
- Required references: ScanRun, active-work reference, overlap/conflict reference.
- Mutation authority / owner boundary: Scan may detect overlap; it does not resolve ownership outside its run boundary.
- Forbidden assumptions: overlap is not a listing event and not a success signal.
- Replay/idempotency note: overlapping facts must not be duplicated by replay.
- Privacy/minimization note: keep only run and overlap identifiers.

### LifecycleEntitlementRecheck
- Purpose: represent a late-stage recheck of lifecycle and entitlement conditions before commit.
- Required references: lifecycle fact, entitlement/grant fact, run snapshot.
- Mutation authority / owner boundary: Scan may request or record the recheck result; it does not mutate the sources.
- Forbidden assumptions: recheck does not authorize Scan to change lifecycle or grant state.
- Replay/idempotency note: with unchanged source facts, the recheck result should remain unchanged.
- Privacy/minimization note: retain only the minimum state necessary for the check.

### RecoveryGraceEligibility
- Purpose: represent whether a recovery attempt qualifies for grace handling after expiry or interruption.
- Required references: recovery blocker reference, grace window/policy reference, entitlement/lifecycle reference.
- Mutation authority / owner boundary: policy and source owners define the grace rule; Scan records the eligibility result.
- Forbidden assumptions: grace eligibility is not a general override for blocked runs.
- Replay/idempotency note: same facts and policy snapshot should yield the same eligibility result.
- Privacy/minimization note: no sensitive authorization data beyond what is needed to classify the grace state.

### SortContextAssessment
- Purpose: record whether the sort/publication context is sufficiently proven for semantic comparison.
- Required references: sort context reference, parser/display provenance reference, confidence/ambiguity reference.
- Mutation authority / owner boundary: Parser Adapter module 05 provides documentation/placeholder boundary context; Scan only assesses sufficiency.
- Forbidden assumptions: unproven sort context must not be treated as proven.
- Replay/idempotency note: assessment should be stable for the same evidence set.
- Privacy/minimization note: store only the proof status and minimal supporting reference.

## Synthetic fixture definitions

These fixtures are markdown-only, synthetic, and non-executable.
They define semantic setup and expected outcomes only.

### FX-SOLS-FIRST-COMPLETE-BASELINE-OWNER-001
- Synthetic setup: one Beacon, first complete observed listing set, no prior baseline, complete anchor coverage, stable sort context proven.
- Expected classification: `SUCCEEDED_BASELINE`.
- Expected state effect: create the initial baseline and rolling anchors; mark no change event for baseline establishment itself.
- Expected status/fact: `BaselineReference`, `RollingAnchorState`, `ScanStatusFact`.
- Forbidden false outcome: no-new-listings, lost-anchors recovery, or notification-triggering change.

### FX-SOLS-NEW-LISTINGS-AFTER-BASELINE-OWNER-001
- Synthetic setup: existing baseline, one or more previously unseen listings observed in the next scan.
- Expected classification: `NEW_LISTING_AFTER_BASELINE`.
- Expected state effect: preserve baseline, record difference result, mark new listing references.
- Expected status/fact: `DifferenceResult`, `ListingFirstSeenResult`, `ScanStatusFact`.
- Forbidden false outcome: baseline reset, full archive replacement, or price-change notification.

### FX-SOLS-NO-NEW-LISTINGS-STATUS-OWNER-001
- Synthetic setup: existing baseline, all observed listings already known, no new identities appear.
- Expected classification: `NO_NEW_LISTINGS`.
- Expected state effect: preserve baseline and anchors, record stable no-new semantic fact.
- Expected status/fact: `ScanStatusFact`, `DifferenceResult`.
- Forbidden false outcome: lost anchors, pending recovery, or false new-listing classification.

### FX-SOLS-LOST-ANCHORS-STATE-RESTORED-OWNER-001
- Synthetic setup: anchor continuity is broken by the rolling window, then the defined recovery rule restores valid state.
- Expected classification: `LOST_ANCHORS_RECOVERY`.
- Expected state effect: update rolling anchor state through recovery without claiming a brand-new baseline.
- Expected status/fact: `LostAnchorsRecoveryResult`, `RollingAnchorState`, `ScanStatusFact`.
- Forbidden false outcome: no-new-listings, entitlement mutation, or archive reconstruction claim.

### FX-SOLS-EXTERNAL-UNAVAILABLE-PENDING-RECOVERY-OWNER-001
- Synthetic setup: external provider or upstream dependency is unavailable while the scan intent is otherwise valid.
- Expected classification: `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`.
- Expected state effect: preserve existing state; mark pending recovery without erasing baseline or anchors.
- Expected status/fact: `PendingRecoveryScan`, `ScanStatusFact`.
- Forbidden false outcome: no-new-listings, baseline reinitialization, or final failure of semantic state.

### FX-SOLS-CAPTCHA-RESTRICTED-NOT-NO-NEW-OWNER-001
- Synthetic setup: provider access is restricted by CAPTCHA or comparable anti-automation barrier.
- Expected classification: `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`.
- Expected state effect: keep current comparison state intact; do not advance to no-new.
- Expected status/fact: `PendingRecoveryScan`, `ScanStatusFact`.
- Forbidden false outcome: `NO_NEW_LISTINGS`, lost state, or notification emission.

### FX-SOLS-AMBIGUOUS-PARSER-NO-STATE-ADVANCE-OWNER-001
- Synthetic setup: parser outcome exists only as ambiguous or insufficiently proven reference.
- Expected classification: `AMBIGUOUS_NO_STATE_ADVANCE`.
- Expected state effect: do not advance baseline, anchors, or lifecycle facts.
- Expected status/fact: `ParserOutcomeReference`, `SortContextAssessment`, `ScanStatusFact`.
- Forbidden false outcome: confirmed new listing, confirmed no-new, or lifecycle mutation.

### FX-SOLS-OVERLAP-CONFLICT-OWNER-001
- Synthetic setup: two overlapping scan claims or conflicting active work units exist for the same Beacon scope.
- Expected classification: `OVERLAP_CONFLICT`.
- Expected state effect: record overlap state and block conflicting advancement.
- Expected status/fact: `OverlapState`, `ScanStatusFact`.
- Forbidden false outcome: duplicate committed baseline or silently merged work.

### FX-SOLS-PAUSED-ARCHIVED-FROZEN-BLOCKED-OWNER-001
- Synthetic setup: Beacon is paused, archived, or otherwise frozen according to lifecycle facts.
- Expected classification: `LIFECYCLE_BLOCKED`.
- Expected state effect: record blocked status only; no scan advancement or recovery claim.
- Expected status/fact: `BeaconScanEligibility`, `LifecycleEntitlementRecheck`, `ScanStatusFact`.
- Forbidden false outcome: pending recovery, baseline creation, or entitlement mutation.

### FX-SOLS-ENTITLEMENT-DENIED-AMBIGUOUS-BLOCKED-OWNER-001
- Synthetic setup: entitlement or grant is denied and the observation context is ambiguous.
- Expected classification: `ENTITLEMENT_BLOCKED`.
- Expected state effect: record blocked eligibility and keep safe facts only.
- Expected status/fact: `BeaconScanEligibility`, `LifecycleEntitlementRecheck`, `ScanStatusFact`.
- Forbidden false outcome: no-new-listings, recovery grace success, or lifecycle override.

### FX-SOLS-PENDING-RECOVERY-SINGLE-OWNER-001
- Synthetic setup: a single pending recovery condition exists for one Beacon and one run snapshot.
- Expected classification: `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`.
- Expected state effect: preserve current state and annotate the one pending recovery fact.
- Expected status/fact: `PendingRecoveryScan`, `ScanStatusFact`.
- Forbidden false outcome: duplicate pending records or state advance to confirmed scan completion.

### FX-SOLS-RECOVERY-SUCCESS-NEW-LISTINGS-OWNER-001
- Synthetic setup: after a pending recovery, the next valid scan observes previously unseen listings.
- Expected classification: `LOST_ANCHORS_RECOVERY`.
- Expected state effect: recover comparison continuity and record new listing semantics if present.
- Expected status/fact: `LostAnchorsRecoveryResult`, `ListingFirstSeenResult`, `ScanStatusFact`.
- Forbidden false outcome: treating recovery as plain no-new or as a lifecycle event.

### FX-SOLS-RECOVERY-SUCCESS-NO-NEW-OWNER-001
- Synthetic setup: after a pending recovery, the next valid scan observes only known listings.
- Expected classification: `LOST_ANCHORS_RECOVERY`.
- Expected state effect: recover anchors and preserve baseline without inventing new identities.
- Expected status/fact: `LostAnchorsRecoveryResult`, `ScanStatusFact`.
- Forbidden false outcome: false new listing or false failure due to the prior pending state.

### FX-SOLS-RECOVERY-AFTER-ENTITLEMENT-EXPIRY-GRACE-OWNER-001
- Synthetic setup: entitlement has expired, but the configured grace rule permits recovery handling.
- Expected classification: `RECOVERY_GRACE_RESULT`.
- Expected state effect: record grace eligibility and recovery result without mutating entitlement.
- Expected status/fact: `RecoveryGraceEligibility`, `LifecycleEntitlementRecheck`, `ScanStatusFact`.
- Forbidden false outcome: entitlement restoration, lifecycle change, or automatic no-new classification.

### FX-SOLS-DUPLICATE-CANDIDATE-WITHIN-RUN-OWNER-001
- Synthetic setup: the same listing candidate appears twice within one scan run.
- Expected classification: `DUPLICATE_WITHIN_RUN`.
- Expected state effect: collapse the duplicate into one semantic candidate within the run.
- Expected status/fact: `ListingCandidateReference`, `ScanRun`, `ScanStatusFact`.
- Forbidden false outcome: two independent first-seen facts for the same run observation.

### FX-SOLS-SORT-CONTEXT-NOT-PROVEN-OWNER-001
- Synthetic setup: parser/display order is not sufficiently proven to establish comparison ordering.
- Expected classification: `SORT_CONTEXT_NOT_PROVEN`.
- Expected state effect: block state advance until sort context is proven.
- Expected status/fact: `SortContextAssessment`, `ScanStatusFact`.
- Forbidden false outcome: no-new-listings, confirmed new listing, or silent fallback to guessed order.

### FX-SOLS-PRICE-CHANGED-OLD-LISTING-NO-NOTIFICATION-OWNER-001
- Synthetic setup: a known listing shows a price change on an old identity while notification is out of scope.
- Expected classification: `KNOWN_LISTING_PRICE_CHANGED_NO_NOTIFICATION`.
- Expected state effect: keep price as candidate/display data only; do not emit price-pair notification.
- Expected status/fact: `DifferenceResult`, `ListingCandidateReference`, `ScanStatusFact`.
- Forbidden false outcome: notification delivery, price-pair escalation, or change of the listing into a new identity.

## Outcome coverage matrix

- `SUCCEEDED_BASELINE`: FX-SOLS-FIRST-COMPLETE-BASELINE-OWNER-001
- `NEW_LISTING_AFTER_BASELINE`: FX-SOLS-NEW-LISTINGS-AFTER-BASELINE-OWNER-001
- `NO_NEW_LISTINGS`: FX-SOLS-NO-NEW-LISTINGS-STATUS-OWNER-001
- `LOST_ANCHORS_RECOVERY`: FX-SOLS-LOST-ANCHORS-STATE-RESTORED-OWNER-001, FX-SOLS-RECOVERY-SUCCESS-NEW-LISTINGS-OWNER-001, FX-SOLS-RECOVERY-SUCCESS-NO-NEW-OWNER-001
- `EXTERNAL_UNAVAILABLE_PENDING_RECOVERY`: FX-SOLS-EXTERNAL-UNAVAILABLE-PENDING-RECOVERY-OWNER-001, FX-SOLS-CAPTCHA-RESTRICTED-NOT-NO-NEW-OWNER-001, FX-SOLS-PENDING-RECOVERY-SINGLE-OWNER-001
- `SORT_CONTEXT_NOT_PROVEN`: FX-SOLS-SORT-CONTEXT-NOT-PROVEN-OWNER-001
- `AMBIGUOUS_NO_STATE_ADVANCE`: FX-SOLS-AMBIGUOUS-PARSER-NO-STATE-ADVANCE-OWNER-001
- `OVERLAP_CONFLICT`: FX-SOLS-OVERLAP-CONFLICT-OWNER-001
- `LIFECYCLE_BLOCKED`: FX-SOLS-PAUSED-ARCHIVED-FROZEN-BLOCKED-OWNER-001
- `ENTITLEMENT_BLOCKED`: FX-SOLS-ENTITLEMENT-DENIED-AMBIGUOUS-BLOCKED-OWNER-001
- `RECOVERY_GRACE_RESULT`: FX-SOLS-RECOVERY-AFTER-ENTITLEMENT-EXPIRY-GRACE-OWNER-001
- `DUPLICATE_WITHIN_RUN`: FX-SOLS-DUPLICATE-CANDIDATE-WITHIN-RUN-OWNER-001
- `KNOWN_LISTING_PRICE_CHANGED_NO_NOTIFICATION`: FX-SOLS-PRICE-CHANGED-OLD-LISTING-NO-NOTIFICATION-OWNER-001

## Non-goals

- No executable fixtures are defined here.
- No source code, tests, schemas, runtime configuration, provider integration, parser implementation, Egress logic, Notification logic, UI logic, deploy logic, secrets, or database artifacts are introduced.
- No raw provider payloads are stored.
- No hard-coded scan interval is introduced.
- No hard-coded anchor window size is introduced.
