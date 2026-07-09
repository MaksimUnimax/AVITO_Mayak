# Маяк Авито — Scan Lost Anchors Recovery v1.0

## Metadata
- status: approved semantic documentation for SOLS-07;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines lost-anchor recovery semantics only.
It does not authorize implementation, runtime behavior, schema changes, DB work, parser/provider traffic, egress routing, notification delivery, UI rendering or deployment.

## 1. Purpose and non-goals

Purpose:

- define the semantic boundary for lost-anchor recovery when the previous anchor window exists but none of the previous anchors are found in a usable current top-window;
- keep recovery, reseed and replay semantics explicit without turning them into a full archive or a parser implementation;
- preserve safe scan facts/status while deferring delivery/rendering to Notification Delivery and UI/channel modules;
- distinguish lost anchors from external failure, ambiguity, partial outcomes and window overflow;
- document synthetic examples only.

Non-goals:

- no code, tests, runtime, schema, DB, migration, transaction, lock, queue, scheduler, worker, parser, egress, notification, UI or deploy authorization;
- no transport/provider/framework/ORM decision;
- no hard-coded interval, claim lease, heartbeat, retry/backoff, anchor-window size or scan cadence default;
- no live Avito/provider traffic;
- no mutation authority over Beacon, Entitlement, Parser, Egress or Notification modules;
- no full user-visible listing archive;
- no raw provider payload retention.

## 2. Lost anchors definition

- Lost anchors means a previous anchor window/state exists, the current observed top-window is usable enough for recovery handling, and none of the previous anchors are found in that observed top-window.
- Lost anchors is a recovery state, not a confirmed new-listing state and not a clean no-new state.
- Lost anchors and window overflow are different states.
- Lost anchors does not mean the provider returned a complete listing archive.
- Lost anchors does not mean the scan may invent anchors, parser mappings or delivery behavior.

## 3. Lost anchors preconditions

Lost anchors may be classified only when all of the following are true:

- a previous anchor window/state exists for the same Beacon scope;
- the current Parser outcome is complete enough for recovery handling;
- the observed newest-first/top-window evidence is usable enough;
- the sort context is not missing, ambiguous or unproven;
- the outcome is not external failure, CAPTCHA, malformed, incomplete, partial or ambiguous;
- the current observed top-window can be compared against prior anchors without guessing parser truth.

If any of these facts is missing or unproven, lost anchors must not be classified.

## 4. Distinction from external failure, ambiguity and partial outcomes

- External failure is not lost anchors.
- CAPTCHA is not lost anchors.
- Malformed, incomplete, partial or ambiguous outcome is not lost anchors.
- These outcomes preserve prior anchor state and block recovery classification.
- These outcomes do not erase prior anchors and do not authorize a no-new conclusion.

## 5. Distinction from window overflow

- Window overflow remains future design and must not be converted into lost anchors by assumption.
- Window overflow is not the same state as lost anchors.
- A comparison that exceeds the current window handling boundary is not evidence that previous anchors were lost.
- Future overflow handling may have its own approved semantics; this document does not define them.

## 6. Distinction from confirmed new listings

- Lost anchors must not be treated as confirmed new listings.
- None of the previous anchors found in the observed top-window does not by itself authorize a new-listing conclusion.
- Lost-anchor recovery may expose latest fresh items, but those items are state-restored/latest-fresh, not confirmed new.
- The recovery boundary is different from new-listing classification.

## 7. Owner-approved recovery behavior

- Owner-approved behavior is to show/report the latest 3 fresh listings as `последние свежие объявления / состояние восстановлено`.
- The recovery output is safe scan facts/status only.
- The latest 3 are reported as state-restored/latest-fresh, not as confirmed new listings.
- Recovery behavior does not authorize full archive reconstruction, raw payload retention or provider-call behavior.
- Notification Delivery and UI/channel modules own exact delivery/rendering.

## 8. Latest 3 fresh listings / state-restored boundary

- The latest 3 fresh listings are the current top-window items selected by the recovery boundary.
- They are the current state-restored/latest-fresh representation, not a full listing archive.
- They are not a “new listings” promise and not a provider archive reconstruction.
- They are the safe recovery output that may be handed off as facts/status.
- They are not sufficient to imply that the older anchor window is still valid without reseed/update.

## 9. Anchor reseed/update after recovery commit

- After a lost-anchor recovery commit, anchor state is updated/reseeded from the current observed top-window.
- The reseed source is the current observed top-window, not an invented archive and not stale anchors.
- The reseed/update makes the current top-window authoritative for the next scan boundary.
- After recovery commit, the same latest 3 must not repeat on the next scan if they remain in anchors.
- This reseed/update is a state fact, not a parser implementation, DB schema or delivery mechanism.

## 10. Replay and idempotency behavior

- Replay after a committed lost-anchor recovery returns the original recovery outcome.
- Replay must not duplicate state-restored facts.
- Replay must not create a second recovery commit for the same logical outcome.
- Replay must not duplicate the anchor reseed/update fact.
- Same logical recovery input and same committed boundary must converge on the same recovery result.

## 11. Safe diagnostic/status facts

Scan may expose only safe diagnostic/status facts such as:

- anchors were lost;
- recovery is eligible;
- recovery has been committed;
- latest fresh state was restored;
- anchor state was reseeded from the current observed top-window;
- recovery is blocked by incomplete context;
- recovery is blocked by external failure;
- recovery is blocked by sort context;
- the outcome is not confirmed new;
- the outcome is not clean no-new;
- the outcome is not window overflow;
- replayed recovery produced no duplicate state-restored fact.

These facts are safe because they do not expose raw provider payloads, delivery actions or a full archive.

## 12. Notification/UI handoff boundary

- Notification Delivery/UI/channel modules own exact rendering and delivery.
- Scan emits safe facts/status only.
- Scan does not decide final channel text, UI composition or delivery mechanics.
- The handoff boundary may carry the recovery fact that anchors were lost and restored, but it does not transfer delivery authority.
- Exact presentation remains outside this document.

## 13. Forbidden assumptions

- Lost anchors do not authorize a full user-visible listing archive.
- Lost anchors do not authorize raw provider payload retention.
- Lost anchors do not authorize parser implementation.
- Lost anchors do not authorize live Avito calls.
- Lost anchors do not authorize egress implementation.
- Lost anchors do not authorize notification delivery.
- Lost anchors do not authorize UI rendering.
- Lost anchors do not authorize DB/schema/migration work.
- Lost anchors do not authorize scheduler/worker/runtime implementation.
- Lost anchors do not authorize any hard-coded interval, anchor-window size, retry/backoff or claim-lease default.
- Lost anchors do not authorize a new-listing conclusion.
- Lost anchors do not authorize a clean no-new conclusion.
- Lost anchors do not collapse into window overflow by assumption.
- Lost anchors do not become confirmed new listings because the top-window changed.
- Lost anchors do not become a replacement for the previous anchor state unless recovery commits it.
- Lost anchors do not imply a provider archive or user archive.
- Lost anchors do not imply a delivery decision.
- Lost anchors do not imply a parser mapping.
- Lost anchors do not imply any beacon, entitlement or lifecycle mutation.

### Required semantic rules

1. Lost anchors and window overflow are different states.
2. Lost anchors requires a previous anchor window/state to exist.
3. Lost anchors requires the current Parser outcome to be complete enough for recovery handling.
4. Lost anchors requires observed newest-first/top-window evidence to be usable enough.
5. Lost anchors condition means none of the previous anchors are found in the observed top-window.
6. Lost anchors must not be classified when the outcome is external failure, CAPTCHA, malformed, incomplete, partial or ambiguous.
7. Lost anchors must not be classified when sort context is missing, ambiguous or unproven.
8. Lost anchors must not be treated as confirmed new listings.
9. Lost anchors must not be treated as clean no-new-listings.
10. Owner-approved behavior: show/report latest 3 fresh listings as “последние свежие объявления / состояние восстановлено”.
11. The latest 3 are state-restored/latest-fresh, not “новые объявления”.
12. After lost-anchor recovery commit, update/reseed anchor state from the current observed top-window.
13. After recovery commit, the same latest 3 must not repeat on the next scan if they remain in anchors.
14. Lost-anchor recovery must expose safe diagnostic/status that anchors were lost and restored.
15. Replay after committed lost-anchor recovery returns the original recovery outcome and must not duplicate state-restored facts.
16. Lost-anchor recovery does not authorize full listing archive.
17. Lost-anchor recovery does not authorize raw provider payload retention.
18. Lost-anchor recovery does not authorize parser implementation, live Avito calls, egress implementation, notification delivery, UI rendering, DB/schema/migration, scheduler/worker/runtime.
19. Window overflow remains future design and must not be converted into lost anchors by assumption.
20. Notification Delivery/UI/channel modules own exact rendering/delivery. Scan emits safe facts/status only.

## 14. Semantic classification classes

These are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema and not DB values.

| Class | Meaning | Required source facts / references | Allowed state/fact effect | Forbidden false outcome |
|---|---|---|---|---|
| `LOST_ANCHORS_DETECTED` | Previous anchors exist, none of them are found in the usable current top-window, and recovery handling may begin. | Previous anchor window/state; usable current top-window evidence; none of the previous anchors found; complete enough Parser outcome; usable sort context. | Emit a safe lost-anchors diagnostic/status fact and move to recovery eligibility assessment. | Confirmed new listing or clean no-new. |
| `LOST_ANCHORS_RECOVERY_ELIGIBLE` | Lost anchors are detected and the recovery boundary is allowed to proceed. | `LOST_ANCHORS_DETECTED`; recovery policy reference; current observed top-window; complete enough Parser outcome; usable sort context. | Authorize recovery handling in docs-only semantic terms. | External failure, partial outcome, ambiguous outcome or window overflow. |
| `LOST_ANCHORS_RECOVERY_COMMITTED` | Recovery handling has been committed and the current top-window now reseeds anchor state. | Recovery eligibility; commit boundary; current observed top-window; same Beacon/revision scope. | Commit the recovery fact and update anchor state from the current top-window. | Duplicate recovery or archive reconstruction. |
| `LATEST_FRESH_STATE_RESTORED` | The latest 3 fresh listings are reported as state-restored/latest-fresh, not as confirmed new listings. | Recovery commit; current top-window; owner-approved latest 3 boundary. | Expose the latest 3 as safe state-restored/latest-fresh facts. | Confirmed new listing or full listing archive. |
| `ANCHOR_STATE_RESEEDED_FROM_CURRENT_TOP_WINDOW` | Anchor state has been updated from the current observed top-window after recovery. | Recovery commit; current observed top-window; Beacon-scoped anchor state. | Replace stale anchor memory with the current top-window anchor state. | Preserving stale anchors or treating reseed as archive creation. |
| `LOST_ANCHORS_BLOCKED_BY_INCOMPLETE_CONTEXT` | The available context is incomplete, partial or insufficient to classify lost anchors safely. | Missing prior anchor state; incomplete Parser outcome; partial coverage; insufficient recovery context. | Preserve prior anchors and stop recovery classification. | Lost anchors detected or clean no-new. |
| `LOST_ANCHORS_BLOCKED_BY_EXTERNAL_FAILURE` | External failure or CAPTCHA blocks recovery classification. | External failure; CAPTCHA; unavailable upstream evidence. | Preserve prior anchors and block recovery semantics. | Lost anchors detected or no-new. |
| `LOST_ANCHORS_BLOCKED_BY_SORT_CONTEXT` | Sort context is missing, ambiguous or unproven. | Missing newest-first proof; ambiguous sort evidence; unproven publication/order context. | Keep recovery blocked and preserve current anchor state. | Treating sort uncertainty as usable lost anchors. |
| `LOST_ANCHORS_NOT_CONFIRMED_NEW` | Lost-anchor recovery must not be promoted to confirmed new-listing status. | Lost-anchor candidate context; prior anchor window/state; current top-window evidence. | Prevent new-listing classification for the recovery boundary. | Confirmed new listing. |
| `LOST_ANCHORS_NOT_NO_NEW` | Lost-anchor recovery must not be collapsed into a clean no-new conclusion. | Lost-anchor candidate context; recovery or detection evidence; same Beacon scope. | Prevent a false clean no-new status. | Clean no-new conclusion. |
| `LOST_ANCHORS_NOT_WINDOW_OVERFLOW` | Lost anchors are not window overflow and must not be interpreted as overflow. | Lost-anchor detection context; overflow future-design reference if any. | Prevent overflow assumptions from replacing the lost-anchor boundary. | Window overflow classification or overflow-based recovery assumption. |
| `LOST_ANCHORS_REPLAYED_NO_DUPLICATE` | Replay of committed lost-anchor recovery returns the original recovery outcome without repeating state-restored facts. | Committed recovery; replay of the same logical outcome; same Beacon/revision scope. | Return the original recovery result and suppress duplicate state-restored facts. | Duplicate recovery fact or duplicate reseed fact. |
| `WINDOW_OVERFLOW_FUTURE_DESIGN` | Window overflow remains future design only. | Overflow signal; anchor-window policy reference; current comparison scope. | Preserve current state and defer overflow handling to future approval. | Treating overflow as lost anchors or as recovered anchors. |

## 15. Synthetic examples

### EX-SOLS-07-LOST-ANCHORS-ALL-PREVIOUS-MISSING-001

- Synthetic setup: a previous anchor window exists, the current observed top-window is usable enough, the current Parser outcome is complete enough for recovery handling, and none of the previous anchors are found in the observed top-window.
- Expected classification: `LOST_ANCHORS_DETECTED`.
- Expected state/fact effect: emit the safe lost-anchors diagnostic/status fact and keep the boundary on recovery eligibility, not on confirmed new or clean no-new.
- Expected replay/commit behavior: replay returns the same lost-anchors detection fact and does not duplicate a later state-restored fact.
- Forbidden false outcome: confirmed new listing or clean no-new.

### EX-SOLS-07-LATEST-3-STATE-RESTORED-NOT-NEW-001

- Synthetic setup: lost anchors have been detected, the recovery boundary is eligible, and the owner-approved output selects the latest 3 current top-window listings.
- Expected classification: `LATEST_FRESH_STATE_RESTORED`.
- Expected state/fact effect: report the latest 3 as `последние свежие объявления / состояние восстановлено`, not as `новые объявления` and not as clean no-new.
- Expected replay/commit behavior: replay returns the same state-restored/latest-fresh facts and does not create an additional recovery fact.
- Forbidden false outcome: confirmed new listing or full listing archive.

### EX-SOLS-07-ANCHORS-RESEEDED-AFTER-RECOVERY-001

- Synthetic setup: lost-anchor recovery has been committed and the current observed top-window is the reseed source.
- Expected classification: `ANCHOR_STATE_RESEEDED_FROM_CURRENT_TOP_WINDOW`.
- Expected state/fact effect: reseed anchor state from the current observed top-window so the same top-window becomes the new authoritative anchor memory.
- Expected replay/commit behavior: replay returns the same reseed fact and does not create a second reseed from the same committed recovery boundary.
- Forbidden false outcome: stale anchors preserved or archive reconstruction.

### EX-SOLS-07-NEXT-SCAN-DOES-NOT-REPEAT-LATEST-3-001

- Synthetic setup: a recovery commit already happened, the same latest 3 remain in anchors on the next scan, and the next scan reaches the same current top-window shape.
- Expected classification: `LOST_ANCHORS_REPLAYED_NO_DUPLICATE`.
- Expected state/fact effect: the next scan must not repeat the latest 3 as a new state-restored fact while they remain in anchors.
- Expected replay/commit behavior: replay returns the original recovery outcome and keeps the state-restored fact non-duplicated.
- Forbidden false outcome: duplicate latest-fresh output or a second recovery commit.

### EX-SOLS-07-EXTERNAL-FAILURE-NOT-LOST-ANCHORS-001

- Synthetic setup: previous anchors exist, but the upstream/provider side is unavailable and the run has an external failure instead of usable recovery evidence.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_EXTERNAL_FAILURE`.
- Expected state/fact effect: preserve prior anchors and block lost-anchor recovery classification.
- Expected replay/commit behavior: replay returns the same external-failure block until authoritative facts change.
- Forbidden false outcome: lost anchors detected or clean no-new.

### EX-SOLS-07-CAPTCHA-NOT-LOST-ANCHORS-001

- Synthetic setup: the current run is restricted by CAPTCHA and does not have a usable recovery context.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_EXTERNAL_FAILURE`.
- Expected state/fact effect: keep anchor state intact and block recovery semantics.
- Expected replay/commit behavior: replay keeps the same CAPTCHA-blocked state and does not turn it into recovered state.
- Forbidden false outcome: lost anchors detected or state-restored output.

### EX-SOLS-07-PARTIAL-OUTCOME-NOT-LOST-ANCHORS-001

- Synthetic setup: the outcome is partial and does not provide complete enough recovery handling for the current top-window.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_INCOMPLETE_CONTEXT`.
- Expected state/fact effect: preserve prior anchors and stop recovery classification until the outcome is complete enough.
- Expected replay/commit behavior: replay keeps the partial block and does not invent recovery facts.
- Forbidden false outcome: lost anchors detected or clean no-new.

### EX-SOLS-07-AMBIGUOUS-PARSER-NOT-LOST-ANCHORS-001

- Synthetic setup: the Parser outcome is ambiguous and cannot safely support lost-anchor recovery handling.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_INCOMPLETE_CONTEXT`.
- Expected state/fact effect: keep the recovery boundary blocked because the outcome is not complete enough.
- Expected replay/commit behavior: replay preserves the same ambiguous block until authoritative facts exist.
- Forbidden false outcome: lost anchors detected or confirmed new.

### EX-SOLS-07-SORT-CONTEXT-NOT-PROVEN-BLOCKS-RECOVERY-001

- Synthetic setup: the current top-window exists, but newest-first or sort context is missing, ambiguous or unproven.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_SORT_CONTEXT`.
- Expected state/fact effect: block recovery and preserve the current anchor state.
- Expected replay/commit behavior: replay remains blocked until sort context is proven.
- Forbidden false outcome: treating the sort gap as usable lost anchors.

### EX-SOLS-07-WINDOW-OVERFLOW-NOT-LOST-ANCHORS-001

- Synthetic setup: the comparison window exceeds the current boundary, but there is no evidence that prior anchors were lost.
- Expected classification: `WINDOW_OVERFLOW_FUTURE_DESIGN`.
- Expected state/fact effect: preserve current authoritative state and defer overflow handling to future design.
- Expected replay/commit behavior: replay returns the same overflow future-design classification without converting it to lost anchors.
- Forbidden false outcome: lost anchors detected or recovered anchors.

### EX-SOLS-07-NO-PREVIOUS-ANCHORS-NOT-LOST-ANCHORS-001

- Synthetic setup: no previous anchor window/state exists for the Beacon scope.
- Expected classification: `LOST_ANCHORS_BLOCKED_BY_INCOMPLETE_CONTEXT`.
- Expected state/fact effect: keep recovery blocked because the prior anchor prerequisite is missing.
- Expected replay/commit behavior: replay preserves the missing-prerequisite block and does not infer a recovery fact.
- Forbidden false outcome: lost anchors detected or confirmed new.

### EX-SOLS-07-REPLAY-NO-DUPLICATE-STATE-RESTORED-FACT-001

- Synthetic setup: a lost-anchor recovery commit already exists and the same logical recovery outcome is replayed.
- Expected classification: `LOST_ANCHORS_REPLAYED_NO_DUPLICATE`.
- Expected state/fact effect: return the original recovery outcome and do not duplicate state-restored facts.
- Expected replay/commit behavior: replay is idempotent and does not create a second recovery commit.
- Forbidden false outcome: duplicate state-restored fact or duplicate reseed fact.

### EX-SOLS-07-NO-FULL-LISTING-ARCHIVE-001

- Synthetic setup: lost-anchor recovery is eligible, but an implementation request tries to turn the result into a full listing archive.
- Expected classification: `LOST_ANCHORS_NOT_CONFIRMED_NEW`.
- Expected state/fact effect: emit only safe latest-fresh/state-restored facts and keep the boundary away from archive reconstruction.
- Expected replay/commit behavior: replay preserves the same limited recovery result and does not expand it into a full archive.
- Forbidden false outcome: full user-visible listing archive or raw provider payload retention.

### EX-SOLS-07-NOTIFICATION-HANDOFF-ONLY-001

- Synthetic setup: lost-anchor recovery has been committed and the only next step is a safe handoff of facts/status to delivery-owning modules.
- Expected classification: `LOST_ANCHORS_RECOVERY_COMMITTED`.
- Expected state/fact effect: expose safe facts that anchors were lost and restored, and hand off only the semantic facts to Notification Delivery/UI/channel modules.
- Expected replay/commit behavior: replay returns the original committed recovery result without invoking direct delivery or rendering from Scan.
- Forbidden false outcome: direct notification delivery, UI rendering by Scan, or a second recovery commit.
