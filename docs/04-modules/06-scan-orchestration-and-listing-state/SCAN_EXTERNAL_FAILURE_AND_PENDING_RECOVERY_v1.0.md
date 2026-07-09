# Маяк Авито — Scan External Failure and Pending Recovery v1.0

## Metadata
- status: approved semantic documentation for SOLS-08;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic boundaries for external failure handling and the single pending recovery scan obligation.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define what Scan may treat as an external failure boundary in the scan domain;
- keep baseline, rolling anchors, pending recovery and recovery-result obligation explicit across replay;
- keep external failure distinct from no-new-listings, new-listing confirmation, parser truth, route healing and delivery behavior;
- preserve safe scan-domain facts while leaving Parser, Egress and Notification ownership boundaries intact;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no live Avito/provider traffic;
- no parser implementation, parser mapping, route self-healing, CAPTCHA bypass, proxy/cookie/session workaround or provider-call implementation;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no full user-visible listing archive and no raw provider payload retention;
- no numeric interval, retry, backoff, claim lease, heartbeat or anchor-window default.

## 2. External failure definition

- External failure is any safe semantic blocker where the scan cannot prove a comparison result because the provider, route, parser-response classification, reference boundary or comparable upstream dependency is unavailable, rejected, ambiguous, malformed or incomplete.
- External failure is not a no-new-listings conclusion.
- External failure does not erase the baseline.
- External failure does not erase anchors.
- External failure does not advance anchors.
- External failure does not create new-listing facts.
- External failure may create a safe status fact: `Avito сейчас недоступен или мешает проверке. Я продолжаю сканирование.`
- External failure may keep one pending recovery scan obligation alive while the same problem continues.

## 3. External failure categories

These are semantic docs-only categories, not persisted enum names, not Python constants, not wire schema and not DB values.

| Category | Meaning | Owning upstream module boundary | Allowed Scan state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `EXTERNAL_UNAVAILABLE` | The upstream external dependency is unavailable or cannot be reached in a usable way. | Provider/external boundary referenced by Scan only. | Preserve baseline and anchors; register or preserve the one pending recovery obligation; allow a safe status fact. | Treating unavailability as no-new-listings or as new-listing confirmation. |
| `EXTERNAL_REJECTED` | The upstream side rejects the scan path or outcome in a way that prevents a safe comparison result. | Provider response classification owned by Parser Adapter; Scan consumes the reference only. | Preserve baseline and anchors; keep the scan unsettled; allow pending recovery. | Converting rejection into a success, no-new-listings or anchor advancement. |
| `EXTERNAL_AMBIGUOUS` | The upstream or reference state is not safe enough to classify as a comparison result. | Parser Adapter classification boundary. | Preserve baseline and anchors; keep pending recovery or blocked status. | Guessing no-new or new-listing outcome. |
| `CAPTCHA_OR_CHALLENGE` | A CAPTCHA or equivalent challenge blocks normal comparison semantics. | Provider-facing classification boundary referenced through Parser Adapter. | Preserve baseline and anchors; keep one pending recovery obligation; allow safe status fact. | Saying no-new on CAPTCHA or bypassing the challenge. |
| `RATE_OR_ACCESS_RESTRICTED` | Rate limiting or access restriction prevents a safe comparison result. | Provider/external access boundary referenced by Scan only. | Preserve baseline and anchors; keep pending recovery or blocked status. | Treating restricted access as a successful comparison or a false no-new. |
| `ROUTE_FAILURE` | Route, fallback, quarantine or agent mechanics fail before a safe comparison result can be established. | Egress owns route/fallback/quarantine/agent mechanics. | Preserve baseline and anchors; keep pending recovery; allow safe status fact. | Allowing Scan to heal the route or infer no-new. |
| `PARSER_MALFORMED` | The parser outcome reference is malformed and cannot support safe comparison semantics. | Parser Adapter owns provider response classification and parser outcome details. | Preserve baseline and anchors; keep the run unsettled; stop state advance. | Turning malformed parser evidence into no-new or new-listing truth. |
| `PARSER_INCOMPLETE` | The parser outcome reference is incomplete and cannot support safe comparison semantics. | Parser Adapter owns provider response classification and parser outcome details. | Preserve baseline and anchors; keep the run unsettled; stop state advance. | Filling gaps by assumption or claiming no-new. |
| `REFERENCE_STALE_OR_MISSING` | A required semantic reference is stale, missing or unproven for this comparison boundary. | The module that owns the missing reference; Scan only consumes it. | Preserve baseline and anchors; block comparison; keep recovery obligation explicit if applicable. | Guessing the missing reference or creating a false no-new. |
| `TEMPORARY_FAILURE` | A transient failure prevents a safe comparison result but does not change the owner boundaries. | Upstream provider, parser, route or reference boundary referenced by Scan only. | Preserve baseline and anchors; keep or restore the single pending recovery scan. | Treating a temporary failure as durable success or as no-new. |

## 4. Difference from no-new-listings

- External failure is not no-new-listings.
- No-new-listings requires a successful comparison result with proven comparison semantics; external failure lacks that proof.
- External failure must not be used as a fallback label for uncertainty.
- External failure must not say `no new listings` on CAPTCHA, blocked, ambiguous or failure states.
- External failure preserves baseline and anchors instead of closing the comparison as successful.
- A no-new-listings result may exist only after the external failure boundary is no longer active and the comparison result is explicit.

## 5. Baseline and anchor preservation

- External failure does not erase baseline.
- External failure does not erase anchors.
- External failure does not advance anchors.
- External failure does not create a new baseline.
- External failure does not create a new-listing fact.
- External failure does not convert compact anchor memory into a full archive.
- The prior baseline and anchors remain authoritative until a later committed scan changes them under the approved rules.

## 6. Pending recovery scan rule

- One pending recovery scan is kept while the same problem continues.
- Scan tracks pending recovery state and recovery-result obligation only.
- The scan domain does not create blind retry loops or route-healing work.
- The same continuing problem does not authorize multiple distinct pending recovery scans.
- The same continuing problem does not authorize multiple provider calls by Scan.
- The pending recovery obligation stays visible as a safe scan-domain fact until the problem resolves or is superseded by later approved facts.

## 7. Missed due interval coalescing

- Missed due intervals during the same problem are not accumulated into multiple scans.
- Do not create 10 overdue scans after 10 missed intervals.
- Repeated due ticks coalesce into the one pending recovery scan state while the same problem continues.
- A due interval is a semantic trigger boundary, not a backlog accumulator.
- This document does not authorize any numeric cadence, claim lease, retry timer or backlog implementation.

## 8. Recovery scan resolution behavior

- When the problem resolves, one actual recovery scan is executed and reported.
- If the recovery scan finds new listings, the recovery result may report or show them through safe facts/status handoff.
- If the recovery scan finds no new listings, the recovery result may report or show recovered/no-new status.
- If the recovery scan hits lost anchors, apply SOLS-07 lost-anchor recovery behavior.
- Recovery resolution does not authorize blind retry loops or route self-healing.
- Recovery resolution does not change ownership boundaries: Parser classifies provider response, Egress owns route mechanics and Notification Delivery owns delivery.

## 9. Entitlement grace for recovery result

- If the external problem began while entitlement or access was active, one pending recovery scan result may be sent or reported even if access expired before recovery completed.
- After that one recovery result, current entitlement rules apply again.
- The grace is narrow and one-time for the already pending recovery scan only.
- The grace does not mutate entitlement state.
- The grace does not create a general bypass for future scans.

## 10. User-facing status boundary

- External failure status is a safe scan-domain fact/status only, not direct Telegram/MAX/Web delivery.
- Notification Delivery and UI/channel modules own delivery and rendering.
- Scan may expose safe internal status facts, including the explicit safe message `Avito сейчас недоступен или мешает проверке. Я продолжаю сканирование.`
- Repeated identical user-facing error spam every interval is not authorized by Scan; future Notification/channel policy owns delivery cadence.
- Scan must not ignore the Beacon forever after CAPTCHA or external failure.
- Scan must not turn a safe internal status fact into a delivery implementation.

## 11. Parser, Egress and Notification ownership boundaries

- Parser Adapter owns provider response classification and parser outcome details.
- Egress owns route/fallback/quarantine/agent mechanics.
- Notification Delivery owns delivery.
- Scan tracks safe scan-domain status, pending recovery state and recovery-result obligation only.
- Scan must not parse Avito.
- Scan must not call Avito.
- Scan must not probe endpoints.
- Scan must not create parser mappings.
- Scan must not create Egress fallback.
- Scan must not bypass CAPTCHA.
- Scan must not implement route healing.
- Scan must not send notifications.
- Scan must not retain raw provider payloads.

## 12. Replay and idempotency behavior

- Replay of the same external-failure semantic input must return the same safe outcome or the same pending recovery obligation.
- Replay must not create duplicate status facts.
- Replay must not create a second pending recovery scan for the same continuing problem.
- Replay must not convert external failure into no-new-listings.
- Replay must not advance anchors or baseline.
- Replay must not duplicate the recovery-result obligation once it has been consumed.
- `EXTERNAL_FAILURE_REPLAYED_NO_DUPLICATE_STATUS` is the replay rule that the same external-failure state is re-emitted without duplicate safe status facts.

## 13. Forbidden assumptions

- External failure is not no-new-listings.
- External failure does not erase baseline, erase anchors, advance anchors or create new-listing facts.
- External failure does not authorize blind retry loops, route self-healing, CAPTCHA bypass, proxy/cookie/session workaround or provider traffic.
- External failure does not authorize a false no-new label on CAPTCHA, blocked, ambiguous or failure states.
- External failure does not authorize repeated identical error spam every interval.
- External failure does not authorize a full user-visible listing archive.
- External failure does not authorize raw provider payload retention.
- External failure does not authorize Parser implementation, Egress implementation, Notification delivery, DB/schema/migration work or scheduler/worker/runtime work.
- External failure does not authorize hard-coded numeric defaults for interval, window, retry, claim lease or heartbeat.
- External failure does not ignore the Beacon forever; it preserves a single pending recovery obligation until resolution or later approved facts.

## 14. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `EXTERNAL_FAILURE_DETECTED` | A safe external-failure boundary has been recognized for the current scan domain. | External blocker reference; provider/route/parser/reference boundary evidence; same Beacon/revision scope. | Preserve baseline and anchors, and move the run into pending recovery or blocked handling. | No-new-listings or new-listing confirmation. |
| `EXTERNAL_UNAVAILABLE_STATUS_FACT` | A safe status fact reports the external unavailability without exposing delivery mechanics. | External-unavailable reference; safe status boundary; same scan identity. | Emit a safe internal status fact only. | Direct notification delivery or a false no-new. |
| `ANCHORS_PRESERVED_ON_EXTERNAL_FAILURE` | Anchors remain authoritative when external failure occurs. | Existing rolling anchors; external failure reference; same Beacon scope. | Keep anchors unchanged and replayable. | Anchor erasure, anchor advancement or archive creation. |
| `BASELINE_PRESERVED_ON_EXTERNAL_FAILURE` | Baseline remains authoritative when external failure occurs. | Existing baseline; external failure reference; same Beacon/revision scope. | Keep baseline unchanged and replayable. | Baseline erasure or silent baseline replacement. |
| `NO_NEW_FORBIDDEN_ON_EXTERNAL_FAILURE` | External failure cannot be relabeled as no-new-listings. | External failure or CAPTCHA or ambiguous blocker reference; comparison boundary. | Prevent the false no-new outcome. | False no-new-listings on failure. |
| `NO_STATE_ADVANCE_ON_EXTERNAL_FAILURE` | External failure does not move comparison state forward. | External failure reference; existing baseline/anchors; same run identity. | Preserve current state without advancing anchors, baseline or new-listing facts. | Any state advance that depends on a failed comparison. |
| `PENDING_RECOVERY_SCAN_REGISTERED` | One pending recovery scan obligation has been registered. | External failure reference; recovery obligation boundary; same Beacon scope. | Keep one pending recovery obligation visible as a safe fact. | Multiple pending recovery scans for the same continuing problem. |
| `PENDING_RECOVERY_SCAN_ALREADY_EXISTS` | The same continuing problem already has one pending recovery scan. | Existing pending recovery obligation; same blocker reference; same Beacon/revision scope. | Preserve the existing single pending recovery scan. | Creating a second pending recovery scan or a backlog of scans. |
| `MISSED_DUE_INTERVAL_COALESCED` | Missed due intervals collapse into the one pending recovery obligation. | Repeated due ticks; same continuing problem; pending recovery reference. | Coalesce missed intervals without backlog growth. | Ten overdue scans after ten missed intervals. |
| `RECOVERY_SCAN_ELIGIBLE` | The problem has resolved enough for one actual recovery scan to run. | Recovery readiness reference; preserved baseline/anchors; same Beacon/revision scope. | Allow one actual recovery scan and reported recovery outcome. | Blind retry loops or route self-healing. |
| `RECOVERY_SCAN_COMPLETED_WITH_NEW_LISTINGS` | The recovery scan completed and found new listings. | Eligible recovery scan; comparison result; safe report/handoff reference. | Report or show the safe new-listings recovery result through the approved handoff boundary. | Treating the recovery result as blocked or as no-new when it found new listings. |
| `RECOVERY_SCAN_COMPLETED_WITH_NO_NEW_LISTINGS` | The recovery scan completed and found no new listings. | Eligible recovery scan; explicit no-new recovery result; safe report/handoff reference. | Report or show the recovered/no-new status through the approved handoff boundary. | Treating the recovery result as a false failure or as new listings. |
| `RECOVERY_SCAN_COMPLETED_WITH_LOST_ANCHORS` | The recovery scan completed and encountered lost anchors. | Eligible recovery scan; lost-anchors reference; SOLS-07 handoff reference. | Delegate to SOLS-07 lost-anchor recovery behavior. | Treating lost anchors as no-new or as confirmed new. |
| `RECOVERY_GRACE_ELIGIBLE_AFTER_ENTITLEMENT_EXPIRY` | One pending recovery result may still be reported after entitlement expiry because the problem started while access was active. | External failure start time reference; active-access reference at problem start; expiry-before-completion reference. | Allow one pending recovery result to be reported or sent. | General entitlement bypass or repeated grace use. |
| `RECOVERY_GRACE_CONSUMED` | The one allowed recovery result under grace has been used. | Grace-eligible recovery result; one-time consumption boundary. | Allow exactly one grace-consumed recovery outcome and then stop using grace. | Reusing grace for later scans. |
| `RECOVERY_BLOCKED_BY_ENTITLEMENT_AFTER_GRACE` | After the grace result, current entitlement rules apply again. | Grace consumed reference; current entitlement reference; same scan scope. | Block further effect when current entitlement does not allow it. | Continued delivery after grace has already been consumed. |
| `EXTERNAL_FAILURE_REPLAYED_NO_DUPLICATE_STATUS` | Replay returns the same external-failure status without duplicating safe status facts. | Replayed external-failure input; same blocker reference; same run identity. | Re-emit the same safe status or pending recovery state without duplication. | Duplicate status spam or a second recovery obligation. |

## 15. Synthetic examples

The following examples are markdown-only synthetic examples. They are non-executable and docs-only.

### EX-SOLS-08-CAPTCHA-NOT-NO-NEW-001

- Synthetic setup: the current scan hits CAPTCHA or an equivalent challenge before a safe comparison result exists; baseline and anchors are already present.
- Expected classification: `NO_NEW_FORBIDDEN_ON_EXTERNAL_FAILURE`.
- Expected state/fact effect: preserve baseline and anchors, keep the run unsettled and do not emit no-new-listings.
- Expected replay/commit behavior: replay returns the same CAPTCHA-blocked external-failure state without turning it into a successful comparison.
- Forbidden false outcome: `no new listings` on CAPTCHA.

### EX-SOLS-08-AVITO-UNAVAILABLE-PRESERVE-ANCHORS-001

- Synthetic setup: the upstream provider is unavailable while the same Beacon scope still has baseline and rolling anchors.
- Expected classification: `ANCHORS_PRESERVED_ON_EXTERNAL_FAILURE`.
- Expected state/fact effect: keep anchors unchanged and register or preserve the single pending recovery obligation.
- Expected replay/commit behavior: replay preserves the same anchors and does not create anchor advancement or duplicate recovery state.
- Forbidden false outcome: anchor erasure or anchor advancement.

### EX-SOLS-08-ROUTE-FAILURE-PENDING-RECOVERY-001

- Synthetic setup: route or fallback mechanics fail and the scan cannot complete a safe comparison result.
- Expected classification: `PENDING_RECOVERY_SCAN_REGISTERED`.
- Expected state/fact effect: register one pending recovery scan and keep baseline and anchors intact.
- Expected replay/commit behavior: replay returns the same pending recovery obligation and does not introduce route-healing behavior.
- Forbidden false outcome: second pending recovery scan or blind retry loop.

### EX-SOLS-08-PARSER-MALFORMED-NO-STATE-ADVANCE-001

- Synthetic setup: Parser Adapter returns a malformed provider-response classification reference for the current scan.
- Expected classification: `NO_STATE_ADVANCE_ON_EXTERNAL_FAILURE`.
- Expected state/fact effect: preserve the previous baseline and anchors without advancing state.
- Expected replay/commit behavior: replay keeps the malformed parser boundary stable and does not fabricate comparison results.
- Forbidden false outcome: new-listing fact or no-new-listings.

### EX-SOLS-08-PARSER-INCOMPLETE-NO-STATE-ADVANCE-001

- Synthetic setup: the parser outcome reference is incomplete and cannot support safe comparison semantics.
- Expected classification: `NO_STATE_ADVANCE_ON_EXTERNAL_FAILURE`.
- Expected state/fact effect: keep the run unsettled, preserve baseline and anchors and do not advance state.
- Expected replay/commit behavior: replay preserves the same incomplete parser boundary without guessing missing data.
- Forbidden false outcome: false no-new or false new-listing confirmation.

### EX-SOLS-08-AMBIGUOUS-EXTERNAL-NO-FALSE-NO-NEW-001

- Synthetic setup: the upstream state is ambiguous and cannot be safely classified as no-new or new.
- Expected classification: `NO_NEW_FORBIDDEN_ON_EXTERNAL_FAILURE`.
- Expected state/fact effect: keep the scan on a safe blocker path and preserve baseline/anchors.
- Expected replay/commit behavior: replay remains ambiguous and does not convert uncertainty into no-new.
- Forbidden false outcome: silent no-new classification.

### EX-SOLS-08-ONE-PENDING-RECOVERY-NOT-TEN-OVERDUE-001

- Synthetic setup: the same external problem continues across many due ticks and one pending recovery scan already exists.
- Expected classification: `PENDING_RECOVERY_SCAN_ALREADY_EXISTS`.
- Expected state/fact effect: preserve the single pending recovery obligation rather than creating additional overdue scans.
- Expected replay/commit behavior: replay returns the same single pending recovery state.
- Forbidden false outcome: ten overdue scans or backlog multiplication.

### EX-SOLS-08-MISSED-DUE-INTERVALS-COALESCED-001

- Synthetic setup: multiple due intervals are missed while the same provider problem continues.
- Expected classification: `MISSED_DUE_INTERVAL_COALESCED`.
- Expected state/fact effect: coalesce the missed intervals into the one pending recovery obligation.
- Expected replay/commit behavior: replay does not accumulate a backlog of distinct scans.
- Forbidden false outcome: one overdue scan per missed interval.

### EX-SOLS-08-RECOVERY-RESOLVES-WITH-NEW-LISTINGS-001

- Synthetic setup: the external problem resolves and one actual recovery scan finds new listings.
- Expected classification: `RECOVERY_SCAN_COMPLETED_WITH_NEW_LISTINGS`.
- Expected state/fact effect: report the recovery result through safe facts/status handoff and keep ownership boundaries intact.
- Expected replay/commit behavior: replay returns the same recovery result without duplicating the status fact.
- Forbidden false outcome: suppressing the new-listings recovery result as no-new.

### EX-SOLS-08-RECOVERY-RESOLVES-WITH-NO-NEW-001

- Synthetic setup: the external problem resolves and one actual recovery scan finds no new listings.
- Expected classification: `RECOVERY_SCAN_COMPLETED_WITH_NO_NEW_LISTINGS`.
- Expected state/fact effect: report the recovered/no-new status through safe facts/status handoff.
- Expected replay/commit behavior: replay preserves the same no-new recovery result without duplicate delivery facts.
- Forbidden false outcome: converting the recovery result into a failure or into new listings.

### EX-SOLS-08-RECOVERY-HITS-LOST-ANCHORS-DELEGATE-SOLS-07-001

- Synthetic setup: the recovery scan resolves the external blocker but the comparison boundary discovers lost anchors.
- Expected classification: `RECOVERY_SCAN_COMPLETED_WITH_LOST_ANCHORS`.
- Expected state/fact effect: delegate to SOLS-07 lost-anchor recovery behavior instead of classifying the result as confirmed new.
- Expected replay/commit behavior: replay preserves the same lost-anchor handoff and does not invent a second recovery path.
- Forbidden false outcome: treating lost anchors as no-new or as confirmed new.

### EX-SOLS-08-RECOVERY-GRACE-AFTER-ENTITLEMENT-EXPIRY-001

- Synthetic setup: the external problem began while access was active, but entitlement expired before the one pending recovery result completed.
- Expected classification: `RECOVERY_GRACE_ELIGIBLE_AFTER_ENTITLEMENT_EXPIRY`.
- Expected state/fact effect: allow one pending recovery result to be reported even though current entitlement is now expired.
- Expected replay/commit behavior: replay keeps the single grace-eligible result stable and does not extend the grace window.
- Forbidden false outcome: blocking the one allowed recovery result solely because the expiry happened before completion.

### EX-SOLS-08-RECOVERY-GRACE-CONSUMED-THEN-NORMAL-ENTITLEMENT-001

- Synthetic setup: the one recovery grace result has already been reported once and a later scan uses the same scope.
- Expected classification: `RECOVERY_GRACE_CONSUMED`.
- Expected state/fact effect: consume the one-time grace and then return to current entitlement rules.
- Expected replay/commit behavior: replay preserves the consumed-grace fact and does not reopen grace for later scans.
- Forbidden false outcome: repeating grace-based delivery after it was already used.

### EX-SOLS-08-REPLAY-NO-DUPLICATE-STATUS-001

- Synthetic setup: the same external-failure scan outcome is replayed without any new authoritative facts.
- Expected classification: `EXTERNAL_FAILURE_REPLAYED_NO_DUPLICATE_STATUS`.
- Expected state/fact effect: re-emit the same safe status or pending recovery state without creating duplicate status facts.
- Expected replay/commit behavior: replay converges on the same status and does not duplicate recovery obligations.
- Forbidden false outcome: duplicate safe-status spam or state advance.

### EX-SOLS-08-NOTIFICATION-HANDOFF-ONLY-001

- Synthetic setup: the scan needs to surface an external-failure status to downstream presentation logic.
- Expected classification: `EXTERNAL_UNAVAILABLE_STATUS_FACT`.
- Expected state/fact effect: expose only a safe internal status fact for handoff; do not perform direct delivery.
- Expected replay/commit behavior: replay preserves the same safe status fact and leaves delivery to Notification Delivery/UI/channel modules.
- Forbidden false outcome: direct Telegram/MAX/Web delivery from Scan.

### EX-SOLS-08-NO-ROUTE-SELF-HEALING-001

- Synthetic setup: route failure occurs and the scan could be tempted to invent a fallback or self-healing path.
- Expected classification: `EXTERNAL_FAILURE_DETECTED`.
- Expected state/fact effect: preserve baseline and anchors, keep the run on the pending recovery path and do not heal the route.
- Expected replay/commit behavior: replay keeps the same external-failure boundary without introducing route mechanics.
- Forbidden false outcome: route self-healing, CAPTCHA bypass or proxy/cookie/session workaround.
