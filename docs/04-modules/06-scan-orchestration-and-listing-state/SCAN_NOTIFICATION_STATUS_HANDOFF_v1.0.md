# Маяк Авито — Scan Notification and Status Handoff v1.0

## Metadata
- status: approved semantic documentation for SOLS-11;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- prerequisites: SOLS-01 accepted at 2521acb59520878d38755a3014ae758b79dabc04, SOLS-02 accepted at 4ffb367a473d27ffe904d8f0efcc3393060dbe52, SOLS-03 accepted at 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b, SOLS-04 accepted at 3b10367b30e76b7cbac3231f185e04cc92ba1757, SOLS-05 accepted at 62855988335c4863690ce782f6bab02c990d5787, SOLS-06 accepted at 16127f3429fcf075e77d76c3ad854751af1fd24f, SOLS-07 accepted at 11efe89cac25f6e22e64e015e19bf3edd9fc266f, SOLS-08 accepted at 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6, SOLS-09 accepted at dbfa556c1e6b78091b76005cd7f68cb2bca2565f, SOLS-10 accepted at ab8959cc1134b5c00973ef69814ec4c97a33bb1e;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization.

This document is docs-only and transport/provider/framework/ORM neutral.
It defines the semantic boundary for handoff of scan-domain facts and safe status facts from Scan Orchestration to Notification Delivery and to future read-model or channel consumers.
It does not authorize implementation, runtime behavior, schema changes, or live provider traffic.

## 1. Purpose and non-goals

Purpose:

- define how Scan emits committed scan-domain facts and safe status facts only;
- keep the handoff boundary between Scan, Notification Delivery, and channel/UI consumers explicit;
- preserve the rule that Scan owns scan facts and state, while Notification Delivery owns delivery semantics after its own gate;
- document semantic-only status families for Beacon status/read models and future explicit status channels;
- preserve replay safety, deduplication safety, and no-rollback behavior for committed Scan state.

Non-goals:

- no code, tests, runtime, schema, parser, egress, notification, UI, or deploy authorization;
- no transport/provider/framework/ORM decision;
- no delivery implementation, outbox implementation, attempt creation, retry policy, provider success claim, or channel formatting;
- no scheduler, worker, queue, cache, claim lease, heartbeat, or backoff behavior;
- no live Avito/provider call, no parser implementation, no egress implementation, and no direct Telegram/MAX/Web call.

## 2. Scan-domain fact handoff boundary

Scan creates scan-domain facts and safe status facts only.

Scan must not:

- select notification endpoint or provider;
- render Telegram/MAX/Web message text;
- create delivery attempt;
- create or own Notification outbox;
- retry provider delivery;
- claim Telegram/MAX/Web delivery success;
- suppress or roll back committed Scan state because Notification delivery failed.

Safe handoff means:

- the fact is committed by Scan before any downstream consumer sees it;
- the fact remains scan-owned even when Notification Delivery later consumes it;
- the fact is safe for replay and deduplication without duplicating Scan ownership.

## 3. Notification Delivery ownership boundary

Notification Delivery owns:

- delivery intent after its own gate;
- outbox and delivery records;
- delivery attempts;
- retry and provider-success semantics;
- delivery deduplication;
- provider-facing success/failure classification after Scan has already committed its facts.

Scan may expose only handoff-ready facts and references.
Scan does not own provider retries, does not own the outbox, and does not own the meaning of delivery success.

Notification failure never rolls back committed Scan state.

## 4. Channel/UI ownership boundary

Telegram/MAX/Web/UI modules own:

- channel rendering;
- message presentation;
- channel-specific formatting;
- final consumer-facing display after their own gates.

Scan does not render channel text and does not select the presentation strategy.
Scan only supplies safe facts or status references that are already committed.

## 5. Allowed scan fact/status families

The following are docs-only semantic families. They are not persisted enum names, not Python constants, not wire schema values, and not DB values.

| Family | Meaning | Source step/facts | Allowed downstream consumer | Allowed user/status meaning | Forbidden Scan behavior |
|---|---|---|---|---|---|
| `ScanRunPlanned` | One logical scan run has been accepted for planning. | Accepted intent, scope, eligibility, idempotency and plan references. | Scan read model, diagnostics, later handoff gate. | Planned / pending scan. | Do not emit delivery attempt or user success. |
| `ScanRunStarted` | A bounded scan attempt has started. | Claimed work, attempt start, correlation and run references. | Scan read model and diagnostics only. | Scan in progress. | Do not claim success or provider delivery. |
| `ScanRunCompleted` | The run reached a committed terminal scan conclusion. | Committed run result, comparison result, recovery result, or blocked result. | Scan read model and safe status consumers. | Run completed with a class-specific meaning. | Do not render channel text or create delivery intent directly. |
| `ScanRunFailed` | The run ended in explicit failure without success commit. | Failure commit and preserved prior state. | Scan read model and diagnostics. | Run failed. | Do not erase baseline or anchors. |
| `ScanRunAmbiguous` | The outcome cannot be safely classified. | Ambiguous evidence, unresolved run state, or conflicting references. | Scan read model and reconciliation consumers. | Ambiguous / needs review. | Do not turn ambiguity into false no-new or false new. |
| `BeaconBaselineEstablished` | The first complete baseline is committed. | First complete comparison-eligible run and baseline reference. | Scan read model and downstream suppression logic. | Baseline established. | Do not produce a new-listing user result for baseline contents. |
| `NewListingsFound` | One or more new listings were found after baseline. | Baseline reference plus committed difference result with unseen listing identity. | Notification Delivery later after its gate. | New listings found. | Do not create delivery attempt or channel text. |
| `NoNewListingsStatus` | Stable no-new semantic status. | Complete comparison with no unseen listing identity. | Beacon status/read model or future explicit status channel. | No new listings. | Do not spam every interval by default. |
| `ExternalUnavailableStatus` | External dependency or provider is unavailable or blocks verification. | External failure, CAPTCHA, route failure, parser ambiguity, or equivalent blocker. | Beacon status/read model and one clear user message when appropriate. | External unavailable / scan continues. | Do not convert it into false no-new. |
| `PendingRecoveryScanRegistered` | One pending recovery obligation is registered. | External failure with recovery eligibility and preserved prior state. | Scan status/read model and reconciliation. | Recovery pending. | Do not accumulate missed scans into a backlog. |
| `RecoveryScanCompleted` | Recovery obligation is satisfied. | Recovery resolved and committed recovery result. | Scan read model and downstream consumers after their gates. | Recovery completed. | Do not duplicate recovery results on replay. |
| `LostAnchorsRecovered` | Lost anchors are restored to state-restored/latest-fresh semantics. | Lost-anchor condition plus recovery policy/reference. | Scan read model and safe status consumers. | Anchors restored / latest fresh. | Do not classify the restored items as confirmed new. |
| `OverlapSkippedOrPending` | Overlap exists but duplicate dispatch is prevented. | Overlap/conflict detection, active-work references, serialization check. | Scan read model and reconciliation. | Overlap / pending / conflict. | Do not dispatch duplicate parser work or duplicate user-facing facts. |
| `LifecycleBlocked` | Beacon lifecycle blocks normal effect. | Paused/archived/deleted/frozen lifecycle facts and recheck references. | Scan read model and diagnostics. | Lifecycle blocked. | Do not mutate Beacon lifecycle state. |
| `EntitlementBlocked` | Entitlement blocks normal effect. | Denied/expired/unsupported entitlement references and recheck facts. | Scan read model and diagnostics. | Entitlement blocked. | Do not mutate entitlement state. |
| `ParserOutcomeBlocked` | Parser outcome is not comparison-eligible. | Incomplete, malformed, ambiguous, restricted, or unsupported parser outcome references. | Scan read model and reconciliation. | Parser blocked. | Do not turn blocked parser outcome into comparison success. |
| `ReconciliationRequired` | The run needs reconciliation before settlement. | Unknown dispatch, lost response, post-commit loss, or unresolved ambiguity. | Scan read model and operational reconciliation. | Reconciliation required. | Do not blind retry into duplicate effect. |
| `SortContextNotProven` | Sort/publication context is not sufficiently proven. | Missing or unproven sort evidence from parser/display provenance. | Scan read model and blocked-status consumers. | Sort not proven. | Do not treat unproven sort context as success or no-new. |

## 6. Baseline handoff rule

Baseline emits no new-listing user result.

- Scan may emit `BeaconBaselineEstablished` as a safe fact.
- Scan may expose baseline-related diagnostics in read models.
- Notification Delivery does not receive a baseline as a new-listing intent.
- Baseline suppression is a scan semantic rule, not a notification retry rule.

## 7. NewListingsFound handoff rule

`NewListingsFound` is a handoff-ready fact, not a delivery action.

- Notification Delivery may consume it later after its own gate.
- Scan commits the fact and its safe references first.
- Scan does not render the message text and does not own delivery success.

## 8. NoNewListingsStatus anti-spam boundary

`NoNewListingsStatus` is anti-spam and read-model oriented.

- It should not spam every interval by default.
- It is safe for Beacon status/read model or for a future explicit status channel.
- Repeated identical intervals may be coalesced or suppressed by downstream policy, but Scan does not invent that delivery behavior.

## 9. ExternalUnavailableStatus handoff rule

`ExternalUnavailableStatus` may produce one clear user-facing message when the problem begins or materially changes.

The text direction remains:

> Avito сейчас недоступен или мешает проверке. Я продолжаю сканирование.

- Scan may commit the safe status fact.
- Notification Delivery or a future explicit status channel may present the message after its own gate.
- Identical repeated blocker intervals should not be treated as a default spam trigger.

## 10. PendingRecoveryScanRegistered handoff rule

`PendingRecoveryScanRegistered` represents one pending recovery obligation, not accumulated missed scans.

- The obligation is singular while the same blocker continues.
- It is a safe status and read-model fact.
- It does not become backlog accumulation by repeated intervals.

## 11. RecoveryScanCompleted handoff rule

`RecoveryScanCompleted` may produce one result after recovery.

- The result belongs to the recovery obligation, not to a fresh normal scan classification.
- Replay must not create duplicate recovery results.
- Delivery or channel consumers may use the fact only after their own gates.

## 12. LostAnchorsRecovered handoff rule

`LostAnchorsRecovered` is state-restored/latest-fresh, not confirmed-new.

- It restores the comparison state semantics without claiming a new listing.
- It may support safe status/read-model output.
- It must not be converted into a confirmed-new user result.

## 13. Overlap/Lifecycle/Entitlement blocked status handoff

`OverlapSkippedOrPending` means no duplicate parser dispatch and no duplicate user-facing facts.

- `LifecycleBlocked` and `EntitlementBlocked` may be exposed safely.
- These blocked facts do not mutate Beacon or Entitlement state.
- They remain scan-owned safe facts and do not become delivery actions.

## 14. Notification failure does not roll back Scan state

Notification failure never rolls back committed Scan state.

- Committed scan facts remain committed.
- Safe status facts remain committed.
- Baseline, anchors, and other scan-owned facts are not suppressed retroactively because delivery failed.
- Downstream failure belongs to Notification Delivery, not to Scan rollback.

## 15. Replay, deduplication and duplicate-handoff safety

- Replay of the same semantic scan request must not create duplicate Scan facts.
- Replay of the same committed handoff must not create duplicate scan-domain facts or duplicate safe status facts.
- Delivery deduplication belongs to Notification Delivery.
- Scan handoff replay is safe only when it preserves one logical fact set and one logical scan ownership boundary.

## 16. Safe diagnostics/read-model fields

Safe diagnostics/read-model fields may include:

- `scan_run_id`;
- `beacon_id`;
- `configuration_revision_id`;
- `status_class`;
- `fact_class`;
- `reason_code`;
- `source_step`;
- `correlation_id`;
- `causation_id`;
- `rules_version`;
- `freshness_class`;
- `counts`;
- `handoff_eligibility`;
- `replay_reference`.

Forbidden in safe diagnostics/read-model fields:

- raw provider payloads;
- phone numbers;
- seller details;
- full descriptions;
- cookies;
- secrets;
- endpoint selection;
- delivery attempts;
- delivery success claims.

## 17. Forbidden assumptions

The following assumptions are forbidden in this document:

- Scan selects notification endpoint or provider;
- Scan renders Telegram/MAX/Web message text;
- Scan creates delivery attempts or outbox entries;
- Scan retries provider delivery;
- Scan claims Telegram/MAX/Web delivery success;
- Scan suppresses or rolls back committed Scan state because Notification delivery failed;
- `NoNewListingsStatus` means default every-interval spam;
- `LostAnchorsRecovered` means confirmed-new listing;
- `PendingRecoveryScanRegistered` means accumulated missed-scan backlog;
- `ExternalUnavailableStatus` must always be repeated as a notification on every interval;
- `ScanRunCompleted` means delivery success;
- `NewListingsFound` means the user message was already sent;
- `ScanRunPlanned` means a provider call already happened;
- `ScanRunStarted` means success already happened;
- exact event names are semantic placeholder names, not persisted enum names, not Python constants, not wire schema, and not DB values;
- this document authorizes DB/schema/migration/transaction/lock implementation;
- this document authorizes Beacon lifecycle mutation or Entitlement mutation.

## 18. Semantic classification classes

The following are semantic docs-only classes, not persisted enum names, not Python constants, not wire schema values, and not DB values.

| Class | Meaning | Required source facts/references | Allowed handoff/status effect | Forbidden false outcome |
|---|---|---|---|---|
| `SCAN_FACT_HANDOFF_READY` | Committed scan facts are safe to hand off downstream. | Committed scan-domain facts, safe status facts, correlation references. | Handoff-ready reference for Notification Delivery or read-model consumers after their gates. | Do not imply delivery success or endpoint selection. |
| `BASELINE_ESTABLISHED_NO_USER_NEW_LISTING` | Baseline is committed and produces no new-listing user result. | First complete baseline reference and committed baseline fact. | Suppress new-listing user output for baseline contents. | Do not treat baseline as a notification event. |
| `NEW_LISTINGS_FOUND_HANDOFF_READY` | New listing facts are ready for downstream consumption. | Baseline reference, difference result, unseen listing references. | Notification Delivery may consume later after its gate. | Do not imply Scan already sent the message. |
| `NO_NEW_LISTINGS_STATUS_READ_MODEL_ONLY` | Stable no-new status is safe for read model only. | Baseline plus committed comparison with no unseen listing identity. | Safe status/read-model fact. | Do not imply delivery or spam. |
| `NO_NEW_LISTINGS_STATUS_NO_INTERVAL_SPAM` | No-new status must not be emitted every interval by default. | Same facts as no-new status plus anti-spam policy reference. | Coalesced/suppressed read-model status. | Do not turn interval repetition into default notification spam. |
| `EXTERNAL_UNAVAILABLE_STATUS_HANDOFF_READY` | External blocker is ready for a clear status handoff. | External failure, CAPTCHA, route failure, parser ambiguity, or recovery-grace references. | One clear status when the problem begins or materially changes. | Do not convert blocker into false no-new. |
| `PENDING_RECOVERY_SCAN_REGISTERED_HANDOFF_READY` | One pending recovery obligation is registered. | External unavailable facts and recovery eligibility references. | Pending recovery status/read-model fact. | Do not accumulate missed scans. |
| `RECOVERY_SCAN_COMPLETED_HANDOFF_READY` | Recovery result is ready for downstream use. | Recovery resolution and committed recovery result references. | One recovery result may be surfaced after recovery. | Do not duplicate the recovery result. |
| `LOST_ANCHORS_RECOVERED_STATE_RESTORED` | State is restored to latest-fresh semantics. | Lost-anchor condition, recovery policy reference, restored anchor references. | Safe state-restored status. | Do not mark the restored state as confirmed-new. |
| `OVERLAP_SKIPPED_OR_PENDING_HANDOFF_READY` | Overlap is recognized without duplicate dispatch. | Overlap/conflict facts and serialized comparison references. | Safe overlap/pending status without duplicate facts. | Do not allow duplicate parser dispatch or silent last-write-wins. |
| `LIFECYCLE_BLOCKED_STATUS_HANDOFF_READY` | Lifecycle blocks normal effect but can be exposed safely. | Lifecycle block facts and recheck references. | Safe blocked status only. | Do not mutate Beacon lifecycle state. |
| `ENTITLEMENT_BLOCKED_STATUS_HANDOFF_READY` | Entitlement blocks normal effect but can be exposed safely. | Entitlement block facts and recheck references. | Safe blocked status only. | Do not mutate entitlement state. |
| `PARSER_OUTCOME_BLOCKED_STATUS_HANDOFF_READY` | Parser outcome is blocked from comparison success. | Incomplete, malformed, ambiguous, restricted, or unsupported parser outcome references. | Safe blocked status and reconciliation path. | Do not call it comparison success. |
| `RECONCILIATION_REQUIRED_STATUS_HANDOFF_READY` | The run requires reconciliation before settlement. | Unknown dispatch, lost response, post-commit loss, or unresolved ambiguity. | Safe reconciliation-required status. | Do not trigger blind retry or duplicate commit. |
| `SORT_CONTEXT_NOT_PROVEN_STATUS_HANDOFF_READY` | Sort context is not sufficiently proven. | Missing or unproven sort evidence references. | Safe blocked/diagnostic status. | Do not treat unproven sort as proven newest-first comparison. |
| `NOTIFICATION_DELIVERY_NOT_OWNED_BY_SCAN` | Notification delivery ownership is outside Scan. | Committed scan facts and notification-contract boundary references. | Ownership boundary only. | Do not imply Scan-owned outbox or attempts. |
| `NOTIFICATION_FAILURE_NO_SCAN_ROLLBACK` | Notification failure never rewinds committed Scan state. | Committed scan facts and downstream delivery failure references. | Scan state stays committed. | Do not roll back or suppress committed Scan facts. |
| `CHANNEL_RENDERING_NOT_OWNED_BY_SCAN` | Channel rendering belongs to channel modules. | Scan facts and channel gate references. | Rendering occurs later in Telegram/MAX/Web/UI ownership. | Do not imply Scan-produced channel text. |
| `HANDOFF_REPLAY_NO_DUPLICATE_SCAN_FACT` | Replay does not duplicate scan facts at the handoff boundary. | Same scan facts, same semantic request, same run references. | Replay returns the same fact set only. | Do not create a second scan fact or duplicate handoff. |

## 19. Synthetic examples

These are markdown-only synthetic examples, not executable fixtures.

| Example | Synthetic setup | Expected classification | Expected handoff/status effect | Expected replay/dedup behavior | Forbidden false outcome |
|---|---|---|---|---|---|
| `EX-SOLS-11-BASELINE-NO-USER-NEW-LISTING-001` | First complete comparison-eligible baseline is committed for one Beacon. | `BASELINE_ESTABLISHED_NO_USER_NEW_LISTING` | Baseline fact only; no new-listing user result. | Replay returns the same baseline fact; no duplicate handoff. | Do not turn baseline into a new-listing notification. |
| `EX-SOLS-11-NEW-LISTINGS-HANDOFF-READY-001` | Existing baseline, then a later comparison commits unseen listing identity facts. | `NEW_LISTINGS_FOUND_HANDOFF_READY` | Handoff-ready new-listings fact for later Notification Delivery gate. | Replay reuses the same fact set; no duplicate scan fact. | Do not imply Scan already sent the user message. |
| `EX-SOLS-11-NO-NEW-READ-MODEL-NO-SPAM-001` | Existing baseline, all observed items are already known, no new identities appear. | `NO_NEW_LISTINGS_STATUS_NO_INTERVAL_SPAM` | Safe read-model no-new status only. | Identical intervals are coalesced; no default spam. | Do not emit one identical notification every interval. |
| `EX-SOLS-11-EXTERNAL-UNAVAILABLE-ONE-CLEAR-STATUS-001` | Provider is unavailable or blocked by CAPTCHA during an otherwise valid scan. | `EXTERNAL_UNAVAILABLE_STATUS_HANDOFF_READY` | One clear status when the problem begins or materially changes. | Replay keeps the same blocker fact; no default interval spam. | Do not call this no-new. |
| `EX-SOLS-11-PENDING-RECOVERY-NOT-MISSED-SCAN-BACKLOG-001` | The same external blocker continues across multiple due intervals. | `PENDING_RECOVERY_SCAN_REGISTERED_HANDOFF_READY` | One pending recovery obligation only. | Repeated intervals do not accumulate into multiple pending scans. | Do not invent a backlog of missed scans. |
| `EX-SOLS-11-RECOVERY-COMPLETED-ONE-RESULT-001` | Recovery succeeds after the pending blocker is resolved. | `RECOVERY_SCAN_COMPLETED_HANDOFF_READY` | One recovery result may be surfaced after recovery. | Replay returns the same recovery result; no duplicate. | Do not duplicate recovery output. |
| `EX-SOLS-11-LOST-ANCHORS-STATE-RESTORED-NOT-CONFIRMED-NEW-001` | Anchor continuity is broken, then the recovery rule restores valid state. | `LOST_ANCHORS_RECOVERED_STATE_RESTORED` | State-restored/latest-fresh semantics only. | Replay preserves the recovered state; no reclassification into new. | Do not mark restored items as confirmed-new. |
| `EX-SOLS-11-OVERLAP-PENDING-NO-DUPLICATE-USER-FACTS-001` | Two overlapping scan claims target the same Beacon scope. | `OVERLAP_SKIPPED_OR_PENDING_HANDOFF_READY` | No duplicate parser dispatch and no duplicate user facts. | Replay keeps the same overlap decision; no silent second dispatch. | Do not silently merge into duplicate work. |
| `EX-SOLS-11-LIFECYCLE-BLOCKED-SAFE-STATUS-001` | Beacon lifecycle is paused or archived before normal commit. | `LIFECYCLE_BLOCKED_STATUS_HANDOFF_READY` | Safe blocked status only. | Replay preserves the same block; no lifecycle mutation. | Do not mutate Beacon lifecycle state. |
| `EX-SOLS-11-ENTITLEMENT-BLOCKED-SAFE-STATUS-001` | Entitlement decision is denied or expired before normal commit. | `ENTITLEMENT_BLOCKED_STATUS_HANDOFF_READY` | Safe blocked status only. | Replay preserves the same block; no entitlement mutation. | Do not mutate entitlement state. |
| `EX-SOLS-11-PARSER-OUTCOME-BLOCKED-SAFE-STATUS-001` | Parser outcome is malformed, incomplete, or ambiguous. | `PARSER_OUTCOME_BLOCKED_STATUS_HANDOFF_READY` | Safe blocked status and reconciliation path. | Replay keeps the same blocked classification. | Do not convert to comparison success. |
| `EX-SOLS-11-RECONCILIATION-REQUIRED-SAFE-STATUS-001` | Dispatch state is unknown or a post-commit response is lost. | `RECONCILIATION_REQUIRED_STATUS_HANDOFF_READY` | Safe reconciliation-required status. | Replay does not blind retry or create duplicate commits. | Do not treat it as settled success. |
| `EX-SOLS-11-SORT-NOT-PROVEN-NO-FALSE-NO-NEW-001` | Sort/publication context is missing or not proven. | `SORT_CONTEXT_NOT_PROVEN_STATUS_HANDOFF_READY` | Safe blocked/diagnostic status. | Replay preserves the same proof gap. | Do not call it proven no-new. |
| `EX-SOLS-11-NOTIFICATION-FAILURE-NO_SCAN_ROLLBACK-001` | Scan facts are committed, then downstream notification delivery fails. | `NOTIFICATION_FAILURE_NO_SCAN_ROLLBACK` | Scan state remains committed; downstream failure stays downstream. | Replay must not roll back committed scan facts. | Do not suppress committed Scan state because delivery failed. |
| `EX-SOLS-11-CHANNEL-RENDERING-NOT-SCAN-OWNERSHIP-001` | Telegram/MAX/Web/UI must render after their gates, not in Scan. | `CHANNEL_RENDERING_NOT_OWNED_BY_SCAN` | Channel rendering stays outside Scan ownership. | Replay does not create channel text from Scan. | Do not imply Scan authored channel formatting. |
| `EX-SOLS-11-HANDOFF-REPLAY-NO-DUPLICATE-FACT-001` | The same committed scan facts are replayed through the handoff boundary. | `HANDOFF_REPLAY_NO_DUPLICATE_SCAN_FACT` | Same fact references only; no second fact set. | Replay dedupes Scan facts and preserves one logical handoff. | Do not create a duplicate scan-domain fact. |
