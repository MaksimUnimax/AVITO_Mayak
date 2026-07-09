# Маяк Авито — Scan Parser Outcome, Partial Results and Reconciliation v1.0

## Metadata
- status: approved semantic documentation for SOLS-10;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f, SOLS-08 accepted at 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6, SOLS-09 accepted at dbfa556c1e6b78091b76005cd7f68cb2bca2565f;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines semantic boundaries for parser outcome recording, partial results and reconciliation.
Scan receives explicit Parser outcome references only and does not parse Avito.
If accepted module 05 Parser Adapter contracts are absent or incomplete, this document uses placeholder/reference semantics only and real parser mappings remain gated.

## 1. Purpose and non-goals

Purpose:

- define how Scan consumes explicit Parser outcome references without becoming the parser;
- separate parser outcome recording commit from comparison commit;
- keep complete, partial, ambiguous and interrupted outcomes explicit;
- keep transport success, parser success and comparison success distinct;
- preserve baseline, anchors and safe facts across replay and reconciliation;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no live Avito/provider traffic;
- no parser implementation, parser mapping, route fallback, CAPTCHA bypass or proxy/cookie/session workaround;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no raw provider payload retention;
- no phone, seller or full description storage as Scan state.

## 2. Parser outcome reference boundary

- Parser Adapter owns provider response classification and parser outcome details.
- Scan consumes explicit Parser outcome references only and does not parse Avito.
- A parser outcome reference is a semantic input boundary, not a provider archive or delivery artifact.
- Scan may record the reference, assess comparison eligibility and classify the reference boundary, but it must not invent parser mappings.
- Required evidence for comparison eligibility includes proven ordering/sort/context and accepted listing-reference evidence for the same Beacon scope.
- If module 05 evidence is absent, incomplete or gated, the scan boundary remains reference-only and real parser mappings remain unavailable.
- Raw provider payloads, phone numbers, seller identity and full descriptions are forbidden as Scan state.

## 3. Recording commit versus comparison eligibility

- `PARSER_OUTCOME_RECORDING_COMMIT` is the durable receipt of an explicit parser outcome reference.
- `PARSER_OUTCOME_RECORDING_COMMIT` is not the same event as comparison commit.
- A recorded parser outcome may still be blocked from comparison if sort context, ordering evidence, listing-reference evidence or completeness is missing.
- Transport success is not parser success.
- Parser success is not comparison success.
- A complete Parser outcome may become comparison-eligible only when required ordering/sort/context/listing-reference evidence is proven.
- Comparison eligibility is an explicit semantic decision, not a transport signal and not a parser implementation detail.

## 4. Complete, partial, ambiguous and interrupted outcomes

- Complete outcome means the parser outcome reference is complete enough for comparison consideration.
- Partial outcome means only some units/pages/candidates have authoritative outcome facts.
- Ambiguous outcome means the outcome cannot be safely classified from the available facts.
- Interrupted outcome means the recording or comparison path lost authoritative continuity and needs reconciliation.
- Partial, ambiguous and interrupted outcomes are not generic success.
- Partial, ambiguous and interrupted outcomes do not become no-new-listings.
- Partial, ambiguous and interrupted outcomes do not advance baseline or anchors.

## 5. Transport success is not parser success and parser success is not comparison success

- Transport success only means transport completed.
- Transport success does not prove parser classification, parser completeness or comparison eligibility.
- Parser success only means Parser Adapter produced an explicit parser outcome reference.
- Parser success does not prove comparison success, baseline commit or anchor update.
- Comparison success only means the comparison boundary reached a committed semantic result.
- Comparison success does not imply notification/report delivery.
- Notification Delivery and UI/channel remain separate owners of delivery and presentation.

## 6. Unit/page/candidate accepted, failed, partial and ambiguous counts

- Scan may keep semantic counts for accepted, failed, partial and ambiguous units/pages/candidates.
- These counts explain the current comparison boundary; they do not create a generic whole-run success.
- Accepted count means the unit is authoritative enough for the current comparison boundary.
- Failed count means the unit has an explicit blocker or failure fact.
- Partial count means the unit has incomplete authority or incomplete coverage.
- Ambiguous count means the unit cannot be safely classified.
- Mixed counts are allowed and must not collapse into a whole-run success when units differ.

## 7. Strict no-success-from-partial rule

- Partial Parser outcome is not generic success.
- Partial Parser outcome cannot become baseline-established success.
- Partial Parser outcome cannot become no-new-listings success.
- Partial Parser outcome cannot become comparison success by assumption.
- Partial Parser outcome cannot erase failed, restricted or ambiguous units.
- Partial Parser outcome cannot advance anchors.
- Partial Parser outcome cannot advance baseline.

## 8. Partial and ambiguous outcomes do not advance baseline or anchors

- Partial and ambiguous outcomes stay within the blocked or pending boundary.
- Baseline advancement requires a complete comparison-eligible outcome and serialized comparison commit.
- Anchor advancement requires the same complete comparison boundary.
- Partial and ambiguous outcomes preserve existing baseline and anchors.
- Partial and ambiguous outcomes may record safe counts and status facts, but they do not change authoritative comparison memory.

## 9. Reconciliation-required state for unknown dispatch/outcome

- Unknown dispatch means Scan cannot safely confirm whether the dispatch/comparison path reached the expected boundary.
- Unknown parser outcome means the parser result boundary is not authoritative enough to settle the scan.
- Unknown dispatch or unknown parser outcome requires `RECONCILIATION_REQUIRED`.
- `RECONCILIATION_REQUIRED` is a safe diagnostic state, not success and not no-new-listings.
- `RECONCILIATION_REQUIRED` must not trigger blind retry, duplicate parser outcome recording or duplicate comparison effect.
- `PARSER_OUTCOME_INTERRUPTED_RECONCILIATION_REQUIRED` covers interrupted continuity that cannot be safely settled yet.

## 10. Replay after parser outcome recorded but comparison not committed

- If the parser outcome recording commit exists but comparison commit does not, replay reuses the recorded parser outcome reference.
- Replay must not duplicate parser outcome records.
- Replay must not create comparison effects before the comparison commit boundary exists.
- Replay must not advance baseline or anchors from the recording commit alone.
- `RECORDED_OUTCOME_REPLAY_BEFORE_COMPARISON_NO_EFFECT` is the safe replay class for this boundary.

## 11. Replay after comparison committed but response/report lost

- If comparison was committed but the response/report was lost, replay returns the committed outcome.
- Replay must not duplicate anchor updates or duplicate comparison facts.
- Replay must not roll back committed comparison state because a report was lost.
- Notification Delivery/UI/channel ownership remains separate from Scan commit ownership.
- `COMMITTED_COMPARISON_REPLAY_AFTER_RESPONSE_LOSS` is the safe replay class for this boundary.

## 12. External failure and pending recovery linkage

- External failure, CAPTCHA, malformed, incomplete, partial and ambiguous outcomes are not no-new-listings.
- External failure preserves baseline and anchors.
- External failure does not advance baseline or anchors.
- One pending recovery obligation may remain alive while the same problem continues.
- Parser Adapter owns provider response classification details, Egress owns route mechanics, and Notification Delivery owns delivery.
- If recovery begins while access was active, the one narrow recovery-result grace remains governed by SOLS-08, not by this document.

## 13. Lifecycle, entitlement and overlap re-check linkage

- Before normal user-visible commit, lifecycle and entitlement must be re-checked.
- One Beacon comparison state must be serialized or conflict-detected.
- Overlap, stale commit, lifecycle change or entitlement change before commit must not silently become success.
- Unknown dispatch/outcome may also require reconciliation before the run can settle.
- Safe status facts may say that lifecycle re-check, entitlement re-check or overlap reconciliation is required.

## 14. Safe diagnostics/status facts

Scan may expose only safe diagnostics/status facts such as:

- parser outcome reference received;
- parser outcome recording committed;
- comparison eligibility proven or blocked;
- sort context proven or not proven;
- partial count, failed count, ambiguous count or accepted count;
- baseline preserved;
- anchors preserved;
- baseline or anchor advance blocked;
- reconciliation required;
- replay returned original recorded outcome;
- replay returned committed comparison outcome without duplication;
- lifecycle re-check required;
- entitlement re-check required;
- overlap reconciliation required;
- response/report was lost after commit.

These facts are safe because they do not expose raw provider payloads, delivery actions, phone numbers, seller identity or full descriptions.

## 15. Forbidden assumptions

- Scan parses Avito or invents parser mappings.
- Transport success proves parser success.
- Parser success proves comparison success.
- Partial outcome proves generic whole-run success.
- Partial or ambiguous outcome becomes no-new-listings.
- Partial, ambiguous, malformed, incomplete, CAPTCHA or restricted outcome advances baseline or anchors.
- Partial outcome erases failed, restricted or ambiguous units.
- Generic whole-run success is allowed when units differ.
- Unknown dispatch or unknown parser outcome is settled by guesswork.
- Replay may duplicate parser outcome records or comparison effects.
- Response/report loss rolls back committed comparison or duplicates anchor updates.
- Parser outcome details are owned by Scan.
- Egress route mechanics are owned by Scan.
- Notification delivery or outbox behavior is owned by Scan.
- Raw provider payload retention is allowed in Scan.
- Phone, seller or full description storage is allowed in Scan state.
- Parser implementation, live Avito calls or route fallback are authorized here.
- DB/schema/migration/transaction/lock implementation is authorized here.
- Scheduler/worker/queue/cache implementation is authorized here.
- Beacon lifecycle/revision/source/settings mutation is authorized here.
- Entitlement/payment/subscription/grant mutation is authorized here.
- No baseline or anchor advance from partial or ambiguous outcome.

## 16. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `PARSER_OUTCOME_REFERENCE_RECEIVED` | An explicit parser outcome reference has been received for Scan. | Explicit Parser outcome reference; same Beacon scope; comparison context reference. | Record the reference boundary and keep comparison eligibility separate. | Treating receipt as comparison success. |
| `PARSER_OUTCOME_RECORDING_COMMIT` | The parser outcome reference has been durably recorded. | Accepted parser reference; recording commit boundary; same run identity. | Make the parser reference authoritative for later comparison evaluation. | Treating recording as comparison commit. |
| `PARSER_OUTCOME_COMPLETE_COMPARISON_ELIGIBLE` | The complete parser outcome may be compared because required ordering/sort/context/listing-reference evidence is proven. | Complete parser reference; proven ordering/sort/context; accepted listing-reference evidence. | Allow comparison commit evaluation. | Assuming success without the comparison boundary. |
| `PARSER_OUTCOME_COMPLETE_BUT_SORT_NOT_PROVEN` | The parser outcome is complete, but sort context is not proven. | Complete parser reference; missing or unproven sort context; same Beacon scope. | Block comparison and preserve prior baseline/anchors. | False no-new-listings or anchor advance. |
| `PARSER_OUTCOME_PARTIAL_COMPARISON_BLOCKED` | Only some units/pages/candidates are authoritative, so comparison is blocked. | Partial outcome; unit/page/candidate counts; incomplete coverage facts. | Keep the run partial and prevent comparison advancement. | Generic success or no-new-listings. |
| `PARSER_OUTCOME_AMBIGUOUS_NO_STATE_ADVANCE` | The parser outcome cannot be safely classified and must not advance state. | Ambiguous reference; insufficient proof; same Beacon scope. | Preserve baseline and anchors without advance. | Treating ambiguity as success or no-new. |
| `PARSER_OUTCOME_INTERRUPTED_RECONCILIATION_REQUIRED` | The outcome path lost authoritative continuity and requires reconciliation. | Interrupted recording/comparison boundary; missing continuity facts; same run identity. | Move to reconciliation-required handling. | Silent success, silent failure or duplicate commit. |
| `TRANSPORT_SUCCESS_PARSER_NOT_PROVEN` | Transport completed, but parser success is not established. | Transport completion fact; no parser success proof. | Keep parser success unresolved. | Treating transport as parser truth. |
| `PARSER_SUCCESS_COMPARISON_NOT_PROVEN` | Parser produced an explicit outcome reference, but comparison success is not established. | Parser outcome recording; no comparison commit proof. | Keep comparison pending or blocked. | Treating parser success as comparison success. |
| `UNIT_MIXED_OUTCOME_NO_GENERIC_SUCCESS` | Different units in one run have mixed accepted, failed, partial or ambiguous counts. | Mixed unit/page/candidate counts; same run identity. | Preserve per-unit facts without collapsing into whole-run success. | Generic whole-run success when units differ. |
| `PARSER_MALFORMED_NO_STATE_ADVANCE` | The parser outcome reference is malformed and cannot support state advance. | Malformed parser reference; same Beacon scope. | Keep the run blocked and preserve prior state. | No-new or new-listing truth from malformed data. |
| `PARSER_INCOMPLETE_NO_STATE_ADVANCE` | The parser outcome reference is incomplete and cannot support state advance. | Incomplete parser reference; missing coverage facts. | Keep the run blocked and preserve prior state. | Filling gaps by assumption. |
| `CAPTCHA_OR_RESTRICTED_NO_NO_NEW` | CAPTCHA or restricted access blocks a clean no-new conclusion. | CAPTCHA or restriction fact; incomplete comparison proof. | Preserve baseline and anchors; keep recovery or blocked state. | `no new listings` on CAPTCHA or restriction. |
| `UNKNOWN_DISPATCH_RECONCILIATION_REQUIRED` | Dispatch state is unknown and must be reconciled. | Missing dispatch continuity; same run identity. | Move to reconciliation-required handling. | Blind retry or duplicate dispatch effect. |
| `UNKNOWN_PARSER_OUTCOME_RECONCILIATION_REQUIRED` | Parser outcome is unknown and must be reconciled. | Unknown parser outcome; missing authoritative classification. | Move to reconciliation-required handling. | Guessing parser truth or advance. |
| `PARSER_OUTCOME_REPLAYED_NO_DUPLICATE_RECORD` | Replay returns the original parser outcome record without duplicating it. | Replayed parser reference; same run identity; same recording boundary. | Reuse the original recorded outcome. | Duplicate parser outcome records. |
| `RECORDED_OUTCOME_REPLAY_BEFORE_COMPARISON_NO_EFFECT` | Replay after recording but before comparison commit has no comparison effect. | Recorded parser outcome; absent comparison commit; same run identity. | Return the recorded outcome and keep comparison side effects absent. | Baseline or anchor advance from recording alone. |
| `COMMITTED_COMPARISON_REPLAY_AFTER_RESPONSE_LOSS` | Comparison was committed, but response/report loss does not duplicate effect. | Comparison commit fact; lost response/report fact; same Beacon scope. | Return the committed comparison outcome without duplication. | Anchor re-advance or duplicate facts. |
| `PARTIAL_NO_BASELINE_COMMIT` | Partial outcome cannot establish baseline. | Partial outcome; incomplete comparison coverage. | Preserve prior baseline state. | Baseline establishment from partial evidence. |
| `PARTIAL_NO_ANCHOR_ADVANCE` | Partial outcome cannot advance anchors. | Partial outcome; incomplete comparison coverage. | Preserve prior anchors. | Anchor advancement from partial evidence. |
| `AMBIGUOUS_NO_NO_NEW_LISTINGS` | Ambiguous outcome must not be converted into no-new-listings. | Ambiguous parser/comparison reference; same Beacon scope. | Keep the run unsettled or reconciliation-required. | Clean no-new-listings from ambiguity. |

## 17. Synthetic examples

### EX-SOLS-10-COMPLETE-PARSER-OUTCOME-COMPARISON-ELIGIBLE-001

- Synthetic setup: one Beacon scope has a complete explicit Parser outcome reference, proven ordering/sort/context and accepted listing-reference evidence.
- Expected classification: `PARSER_OUTCOME_COMPLETE_COMPARISON_ELIGIBLE`.
- Expected state/fact effect: record the parser outcome and allow comparison evaluation.
- Expected replay/commit behavior: replay returns the same recorded outcome and does not create a duplicate parser record.
- Forbidden false outcome: treat recording as comparison success.

### EX-SOLS-10-COMPLETE-BUT-SORT-NOT-PROVEN-BLOCKED-001

- Synthetic setup: one complete parser outcome exists, but sort context is missing or unproven.
- Expected classification: `PARSER_OUTCOME_COMPLETE_BUT_SORT_NOT_PROVEN`.
- Expected state/fact effect: preserve baseline and anchors and block comparison advancement.
- Expected replay/commit behavior: replay keeps the same blocked boundary until sort proof exists.
- Forbidden false outcome: false no-new-listings.

### EX-SOLS-10-TRANSPORT-200-NOT-PARSER-SUCCESS-001

- Synthetic setup: transport completes successfully, but parser success is not yet proven as a semantic reference.
- Expected classification: `TRANSPORT_SUCCESS_PARSER_NOT_PROVEN`.
- Expected state/fact effect: keep parser success unresolved and do not advance comparison state.
- Expected replay/commit behavior: replay preserves the same transport-only fact without fabricating parser success.
- Forbidden false outcome: transport success equals parser success.

### EX-SOLS-10-PARSER-SUCCESS-NOT-COMPARISON-SUCCESS-001

- Synthetic setup: Parser Adapter returns an explicit parser outcome reference, but comparison commit has not happened.
- Expected classification: `PARSER_SUCCESS_COMPARISON_NOT_PROVEN`.
- Expected state/fact effect: keep comparison pending or blocked and preserve baseline/anchors.
- Expected replay/commit behavior: replay returns the recorded parser outcome without a comparison effect.
- Forbidden false outcome: parser success equals comparison success.

### EX-SOLS-10-PARTIAL-PAGE-FAILURE-NO-BASELINE-001

- Synthetic setup: one or more pages or units are partial and the coverage is incomplete.
- Expected classification: `PARSER_OUTCOME_PARTIAL_COMPARISON_BLOCKED`.
- Expected state/fact effect: block comparison and do not establish baseline.
- Expected replay/commit behavior: replay preserves the partial blocked boundary until complete evidence exists.
- Forbidden false outcome: baseline establishment from partial coverage.

### EX-SOLS-10-PARTIAL-CANDIDATES-NO-ANCHOR-ADVANCE-001

- Synthetic setup: some candidate units are authoritative, but the scan remains partial.
- Expected classification: `PARTIAL_NO_ANCHOR_ADVANCE`.
- Expected state/fact effect: preserve anchors and do not advance them.
- Expected replay/commit behavior: replay keeps the same partial boundary without anchor movement.
- Forbidden false outcome: anchor advance from partial candidates.

### EX-SOLS-10-MIXED-UNIT-OUTCOME-NO-GENERIC-SUCCESS-001

- Synthetic setup: accepted, failed, partial and ambiguous unit counts are mixed in one run.
- Expected classification: `UNIT_MIXED_OUTCOME_NO_GENERIC_SUCCESS`.
- Expected state/fact effect: preserve per-unit facts and do not collapse them into a whole-run success.
- Expected replay/commit behavior: replay preserves the same mixed counts and the same per-unit facts.
- Forbidden false outcome: generic whole-run success when units differ.

### EX-SOLS-10-AMBIGUOUS-PARSER-OUTCOME-NO-NO-NEW-001

- Synthetic setup: parser outcome is present, but the available facts cannot safely classify it.
- Expected classification: `PARSER_OUTCOME_AMBIGUOUS_NO_STATE_ADVANCE`.
- Expected state/fact effect: preserve baseline and anchors without advance.
- Expected replay/commit behavior: replay keeps the same ambiguous boundary until authoritative facts exist.
- Forbidden false outcome: no-new-listings from ambiguity.

### EX-SOLS-10-CAPTCHA-OUTCOME-NO-NO-NEW-001

- Synthetic setup: the current comparison boundary is blocked by CAPTCHA or restricted access.
- Expected classification: `CAPTCHA_OR_RESTRICTED_NO_NO_NEW`.
- Expected state/fact effect: preserve baseline and anchors and keep recovery or blocked state.
- Expected replay/commit behavior: replay preserves the CAPTCHA or restriction boundary.
- Forbidden false outcome: `no new listings` on CAPTCHA or restriction.

### EX-SOLS-10-PARSER-MALFORMED-NO-STATE-ADVANCE-001

- Synthetic setup: parser outcome reference is malformed.
- Expected classification: `PARSER_MALFORMED_NO_STATE_ADVANCE`.
- Expected state/fact effect: keep the run blocked and preserve prior state.
- Expected replay/commit behavior: replay returns the same malformed boundary without inventing comparison truth.
- Forbidden false outcome: state advance from malformed data.

### EX-SOLS-10-PARSER-INCOMPLETE-NO-STATE-ADVANCE-001

- Synthetic setup: parser outcome reference is incomplete.
- Expected classification: `PARSER_INCOMPLETE_NO_STATE_ADVANCE`.
- Expected state/fact effect: keep the run blocked and preserve prior state.
- Expected replay/commit behavior: replay preserves the incomplete boundary without guessing missing facts.
- Forbidden false outcome: state advance from incomplete data.

### EX-SOLS-10-UNKNOWN-DISPATCH-RECONCILIATION-001

- Synthetic setup: dispatch continuity is unknown and the run cannot safely settle the dispatch boundary.
- Expected classification: `UNKNOWN_DISPATCH_RECONCILIATION_REQUIRED`.
- Expected state/fact effect: move the run to reconciliation-required handling.
- Expected replay/commit behavior: replay returns the same reconciliation-required boundary without blind retry.
- Forbidden false outcome: settled success or duplicate dispatch effect.

### EX-SOLS-10-UNKNOWN-PARSER-OUTCOME-RECONCILIATION-001

- Synthetic setup: parser outcome cannot be safely classified and the authoritative outcome is unknown.
- Expected classification: `UNKNOWN_PARSER_OUTCOME_RECONCILIATION_REQUIRED`.
- Expected state/fact effect: move the run to reconciliation-required handling.
- Expected replay/commit behavior: replay preserves the same unknown-outcome boundary until facts are restored.
- Forbidden false outcome: guessed parser truth.

### EX-SOLS-10-RECORDED-OUTCOME-REPLAY-BEFORE-COMPARISON-001

- Synthetic setup: parser outcome recording commit exists, but comparison commit has not happened.
- Expected classification: `RECORDED_OUTCOME_REPLAY_BEFORE_COMPARISON_NO_EFFECT`.
- Expected state/fact effect: return the recorded parser outcome and keep comparison side effects absent.
- Expected replay/commit behavior: replay must not duplicate parser records or comparison effects.
- Forbidden false outcome: baseline or anchor advance from the recording commit alone.

### EX-SOLS-10-COMMITTED-COMPARISON-REPLAY-AFTER-RESPONSE-LOSS-001

- Synthetic setup: comparison was committed, then the response/report is lost.
- Expected classification: `COMMITTED_COMPARISON_REPLAY_AFTER_RESPONSE_LOSS`.
- Expected state/fact effect: return the committed comparison outcome without duplication.
- Expected replay/commit behavior: replay must not duplicate anchor updates or facts.
- Forbidden false outcome: rollback or duplicate commit because the report was lost.

### EX-SOLS-10-PARSER-OUTCOME-DETAILS-OWNED-BY-PARSER-001

- Synthetic setup: parser outcome details are needed for comparison, but ownership must remain with Parser Adapter.
- Expected classification: `PARSER_OUTCOME_REFERENCE_RECEIVED`.
- Expected state/fact effect: record the reference boundary only and keep parser details outside Scan ownership.
- Expected replay/commit behavior: replay returns the same reference boundary and does not create parser mappings.
- Forbidden false outcome: Scan-owned parser implementation or parser mapping.

### EX-SOLS-10-NO-RAW-PROVIDER-PAYLOAD-RETENTION-001

- Synthetic setup: a parser outcome reference exists, but raw provider payload retention would be required to make Scan authoritative.
- Expected classification: `PARSER_OUTCOME_REFERENCE_RECEIVED`.
- Expected state/fact effect: keep only the reference boundary and do not retain raw payloads.
- Expected replay/commit behavior: replay preserves the same minimal boundary without storing payloads.
- Forbidden false outcome: raw provider payload retention, phone retention, seller retention or full description retention in Scan.

### EX-SOLS-10-NOTIFICATION-REPORT-LOSS-DOES-NOT-ROLLBACK-SCAN-001

- Synthetic setup: comparison was committed, but the report or delivery surface loses the response after the fact.
- Expected classification: `COMMITTED_COMPARISON_REPLAY_AFTER_RESPONSE_LOSS`.
- Expected state/fact effect: preserve the committed comparison and do not roll back Scan facts.
- Expected replay/commit behavior: replay returns the committed outcome without duplicating anchor updates.
- Forbidden false outcome: notification/report loss causes rollback of Scan comparison state.
