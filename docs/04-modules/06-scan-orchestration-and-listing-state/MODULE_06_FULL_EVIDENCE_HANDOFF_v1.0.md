# Маяк Авито — Module 06 Full Evidence and Handoff v1.0

## Metadata
- status: final evidence/handoff for accepted semantic documentation scope;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- latest accepted module SHA: 89f343ddd69411f6ff0c32de517045d5c5356deb;
- not code/test/runtime/schema/parser/egress/notification/UI/deploy authorization;
- module 06 remains semantic/docs-only until future exact implementation gates.

This document is docs-only and transport/provider/framework/ORM neutral.
It summarizes accepted SOLS-01 through SOLS-13 evidence for module 06 and records the current handoff boundary only.

## 1. Executive summary

- Module 06 accepted scope is semantic documentation and evidence/handoff only.
- Module 06 does not yet implement runtime or product code.
- Module 06 owns scan intent boundary, logical `ScanRun` semantics, baseline semantics, rolling anchors, difference/new-listing semantics, lost-anchor recovery semantics, external-failure and pending-recovery semantics, overlap and mid-run semantics, parser outcome consumption semantics, safe scan-domain facts/status handoff, privacy/observability/retention boundary and implementation gates.
- Module 06 does not parse Avito, call Avito, choose Egress routes, own Parser mappings, mutate Beacon, mutate Entitlements, render or send notifications, own Notification outbox, own Web/Admin/Telegram/MAX UI, create DB schema, run scheduler/worker runtime or deploy services.
- The current product scope is new listings only.
- Price-change semantics remain deferred/disabled in current owner scope.
- Baseline and anchor state remain compact semantic memory, not a full archive.
- OD-013 remains open.

## 2. Accepted SHA chain

```text
SOLS-01 governance capture: 2521acb59520878d38755a3014ae758b79dabc04
SOLS-02 semantic records and synthetic fixtures: 4ffb367a473d27ffe904d8f0efcc3393060dbe52
SOLS-03 scan eligibility and intent boundary: 7d8325cfed0ed0891fc5954dcb9d354a3549fa0b
SOLS-04 run lifecycle, idempotency and commit points: 3b10367b30e76b7cbac3231f185e04cc92ba1757
SOLS-05 baseline and rolling anchor state: 62855988335c4863690ce782f6bab02c990d5787
SOLS-06 difference rules: new listings only: 16127f3429fcf075e77d76c3ad854751af1fd24f
SOLS-07 lost anchors recovery: 11efe89cac25f6e22e64e015e19bf3edd9fc266f
SOLS-08 external failure and pending recovery scan: 87993be0f08f95c4ed6b02c821f7626e4bf5c2e6
SOLS-09 overlap, concurrency and mid-run changes: dbfa556c1e6b78091b76005cd7f68cb2bca2565f
SOLS-10 parser outcome, partial results and reconciliation: ab8959cc1134b5c00973ef69814ec4c97a33bb1e
SOLS-11 notification/status handoff: 7d20eaffadaa2373eb3ea409251b119d8e6479bc
SOLS-12 privacy, observability and retention boundary: 8b013d5124b565be014f80dfcdc7d2e5e925dc28
SOLS-13 persistence, scheduler and worker gates: 89f343ddd69411f6ff0c32de517045d5c5356deb
```

## 3. Accepted artifact inventory

| Artifact | Role | Accepted step | Key boundary | Remaining gate if any |
|---|---|---|---|---|
| `OWNER_SCAN_DECISIONS_CAPTURE_v1.0.md` | Owner decision capture | SOLS-01 | Current scope is new listings only; price-change semantics are deferred/disabled; newest-first monitoring is required; anchors are compact memory. | OD-011 and OD-013 remain open; no runtime authorization. |
| `SCAN_SEMANTIC_RECORDS_AND_SYNTHETIC_FIXTURES_v1.0.md` | Semantic records and synthetic fixtures | SOLS-02 | Docs-only semantic records and markdown-only synthetic fixtures; no executable behavior. | Real runtime, schema and fixtures remain gated. |
| `SCAN_ELIGIBILITY_AND_INTENT_BOUNDARY_v1.0.md` | Intent acceptance boundary | SOLS-03 | Explicit beacon/revision, actor/auth, entitlement, parser-compatibility, egress-availability, idempotency and overlap references are required. | No numeric defaults or runtime effect. |
| `SCAN_RUN_LIFECYCLE_IDEMPOTENCY_AND_COMMIT_POINTS_v1.0.md` | Run lifecycle and commit-point rules | SOLS-04 | One logical run, explicit replay/idempotency, and serialized commit points. | No DB/runtime/transaction/queue implementation. |
| `SCAN_BASELINE_AND_ROLLING_ANCHOR_STATE_v1.0.md` | Baseline and anchor memory | SOLS-05 | First complete comparison-eligible scan establishes baseline; anchors remain compact memory. | Anchor window size and physical storage remain gated. |
| `SCAN_DIFFERENCE_RULES_NEW_LISTINGS_ONLY_v1.0.md` | Difference rules | SOLS-06 | Current scope is new listings only; price-change notification is deferred/disabled. | No price-pair implementation or notification flow. |
| `SCAN_LOST_ANCHORS_RECOVERY_v1.0.md` | Lost-anchor recovery | SOLS-07 | Lost anchors are distinct from window overflow and confirmed new; latest 3 fresh items are state-restored/latest-fresh. | Window overflow remains future design. |
| `SCAN_EXTERNAL_FAILURE_AND_PENDING_RECOVERY_v1.0.md` | External failure and pending recovery | SOLS-08 | External failure is not no-new and preserves baseline/anchors; one pending recovery scan is kept. | Route self-healing, blind retry and provider traffic remain gated. |
| `SCAN_OVERLAP_CONCURRENCY_AND_MID_RUN_CHANGES_v1.0.md` | Overlap and mid-run change rules | SOLS-09 | One Beacon comparison state is serialized/conflict-detected; lifecycle and entitlement are rechecked before commit. | Physical lock/lease/transaction/worker runtime remain gated. |
| `SCAN_PARSER_OUTCOME_PARTIAL_AND_RECONCILIATION_v1.0.md` | Parser outcome and reconciliation | SOLS-10 | Parser outcome recording is separate from comparison commit; partial/ambiguous/incomplete outcomes do not advance state. | Parser implementation and live provider traffic remain gated. |
| `SCAN_NOTIFICATION_STATUS_HANDOFF_v1.0.md` | Notification/status handoff | SOLS-11 | Scan emits safe facts/status only; Notification Delivery owns delivery, outbox and retries. | Channel rendering and delivery remain gated. |
| `SCAN_PRIVACY_OBSERVABILITY_AND_RETENTION_BOUNDARY_v1.0.md` | Privacy/observability/retention boundary | SOLS-12 | Minimal safe semantic state only; no raw payloads or full archive; OD-013 stays open. | Physical retention, compaction and deletion remain gated. |
| `SCAN_PERSISTENCE_SCHEDULER_AND_WORKER_GATES_v1.0.md` | Persistence/scheduler/worker gates | SOLS-13 | DB/schema/ORM, scheduler, worker, claim, queue, retry and runtime families remain blocked. | Explicit future gates still required. |
| `MODULE_PLAYBOOK.md` | Source-of-truth playbook | Governance source | Accepted module playbook for module 06; append-only history only for new accepted handoff notes. | Open decisions remain open; no implicit implementation approval. |

## 4. Owner decisions captured

- Current product scope is new listings only, not price-change notifications.
- Price may remain display/parser candidate data.
- Price-change tracking and price-pair notification/event are deferred/disabled until separately approved.
- Newest-first monitoring is required.
- Missing, ambiguous or unproven sort must block or remain ambiguous, not false no-new.
- Rolling anchors are compact memory, not full user-visible listing history.
- Anchor state updates after every successful comparison-eligible scan.
- Anchor window size is future Admin-configurable and not hard-coded now.
- Lost anchors and window overflow are different states.
- Lost anchors show latest 3 fresh listings as state-restored/latest-fresh, not confirmed-new.
- Window overflow remains future design.
- External failures do not erase baseline or anchors and are not no-new listings.
- One pending recovery scan is kept, not accumulated missed scans.
- One recovery result may be reported after entitlement expiry only if failure began while access was active.
- One Beacon cannot have parallel comparison commits.
- Beacon lifecycle and entitlement must be re-checked before user-visible commit.
- Scan emits facts/status only; Notification Delivery owns delivery.

## 5. Current module 06 semantic state

- Module 06 is complete only in accepted semantic documentation and evidence scope.
- Module 06 does not implement product runtime behavior yet.
- The semantic state owned by module 06 is the scan intent boundary, logical run semantics, baseline and rolling-anchor memory, new-listing-only difference logic, lost-anchor recovery, external-failure and pending-recovery handling, overlap and mid-run conflict handling, parser-outcome consumption semantics, safe scan-domain facts/status handoff, and privacy/retention boundaries.
- Module 06 consumes contracts and references from other modules; it does not mutate foreign module state.
- Module 06 does not own parser mappings, egress routes, notification rendering/delivery, Beacon lifecycle, entitlement decisions, DB schema, scheduler runtime, worker runtime or deploy runtime.

## 6. SOLS-01 governance capture evidence

- Evidence source: `OWNER_SCAN_DECISIONS_CAPTURE_v1.0.md`.
- Governing facts captured the current product scope, the new-listings-only boundary, the price-change deferral, newest-first monitoring, rolling-anchor compact memory, lost-anchor separation, external-failure handling, single pending recovery obligation, one-Beacon serialization, lifecycle/entitlement recheck and safe-facts-only handoff.
- Governance capture also kept OD-011 and OD-013 open and did not close any decision by assumption.
- No runtime, schema or deployment authorization was created by this step.

## 7. SOLS-02 semantic records and synthetic fixtures evidence

- Evidence source: `SCAN_SEMANTIC_RECORDS_AND_SYNTHETIC_FIXTURES_v1.0.md`.
- The step defined docs-only semantic record families and markdown-only synthetic fixture definitions.
- It kept Scan transport/provider/framework/ORM neutral and explicitly excluded raw provider payloads, full archive behavior and executable fixture behavior.
- The synthetic cases are semantic documentation only and do not authorize runtime, tests or fixtures.

## 8. SOLS-03 scan eligibility and intent boundary evidence

- Evidence source: `SCAN_ELIGIBILITY_AND_INTENT_BOUNDARY_v1.0.md`.
- A scan intent requires explicit `beacon_id`, immutable `configuration_revision_id`, allowed purpose, actor/auth context, entitlement reference, parser compatibility reference when needed, egress availability reference when needed, idempotency key, semantic fingerprint and overlap context.
- Missing, ambiguous or unproven facts block intent acceptance and do not create external effect.
- The document does not choose intervals, due slots, claim leases or other runtime defaults.

## 9. SOLS-04 run lifecycle, idempotency and commit points evidence

- Evidence source: `SCAN_RUN_LIFECYCLE_IDEMPOTENCY_AND_COMMIT_POINTS_v1.0.md`.
- The run lifecycle remains semantic, not implementation-specific.
- Replay never creates a second logical run, baseline or anchor update.
- Transport success is not parser success, parser success is not comparison success and comparison success is not notification delivery.
- Comparison commit remains separate from status exposure and user-visible commit.
- No numeric defaults or runtime mechanics were introduced.

## 10. SOLS-05 baseline and rolling anchor state evidence

- Evidence source: `SCAN_BASELINE_AND_ROLLING_ANCHOR_STATE_v1.0.md`.
- The first complete comparison-eligible scan establishes the initial baseline.
- Rolling anchors are compact memory, not a user-visible archive or price-history store.
- Anchor state updates after every successful comparison-eligible scan.
- Proven sort evidence is required; missing, ambiguous or unproven sort context blocks baseline and anchor advancement.
- Anchor window size is future Admin-configurable and not hard-coded here.

## 11. SOLS-06 difference rules: new listings only evidence

- Evidence source: `SCAN_DIFFERENCE_RULES_NEW_LISTINGS_ONLY_v1.0.md`.
- The current owner scope is new listings only, not price-change notification.
- Known identity with changed price remains known in this scope and does not create a notification.
- New-listing difference requires an existing baseline, rolling anchors, complete comparison-eligible parser outcome and proven newest-first context.
- External failure is not no-new and does not preserve a false no-new conclusion.

## 12. SOLS-07 lost anchors recovery evidence

- Evidence source: `SCAN_LOST_ANCHORS_RECOVERY_v1.0.md`.
- Lost anchors are a recovery state, not confirmed new and not clean no-new.
- Lost anchors and window overflow are different states.
- Owner-approved recovery output is the latest 3 fresh listings as state-restored/latest-fresh.
- Recovery reseeds anchor state from the current observed top-window and does not create archive reconstruction.

## 13. SOLS-08 external failure and pending recovery evidence

- Evidence source: `SCAN_EXTERNAL_FAILURE_AND_PENDING_RECOVERY_v1.0.md`.
- External failure is not no-new and does not erase baseline or anchors.
- One pending recovery scan obligation is kept while the same problem continues.
- Missed due intervals coalesce into the one pending recovery obligation rather than accumulating backlog scans.
- Recovery grace is narrow and one-time if the failure began while access was active.
- Scan does not own route healing, provider calls or delivery behavior.

## 14. SOLS-09 overlap, concurrency and mid-run changes evidence

- Evidence source: `SCAN_OVERLAP_CONCURRENCY_AND_MID_RUN_CHANGES_v1.0.md`.
- One Beacon comparison state must be serialized or conflict-detected.
- Overlap does not authorize parallel committed comparisons or duplicate parser dispatch.
- Lifecycle, revision and entitlement changes mid-run do not become silent success conversions.
- Lifecycle and entitlement must be rechecked before normal user-visible commit.
- Recovery grace remains narrow and one-time.

## 15. SOLS-10 parser outcome, partial results and reconciliation evidence

- Evidence source: `SCAN_PARSER_OUTCOME_PARTIAL_AND_RECONCILIATION_v1.0.md`.
- Scan consumes explicit parser outcome references only and does not parse Avito.
- Parser outcome recording commit is separate from comparison commit.
- Partial, ambiguous, malformed, incomplete, CAPTCHA or restricted outcomes do not become no-new and do not advance baseline or anchors.
- Unknown dispatch or unknown parser outcome requires reconciliation.
- Replay must not duplicate parser records or committed comparison effects.

## 16. SOLS-11 notification/status handoff evidence

- Evidence source: `SCAN_NOTIFICATION_STATUS_HANDOFF_v1.0.md`.
- Scan emits committed scan-domain facts and safe status facts only.
- Notification Delivery owns delivery intent, outbox, delivery attempts, retries, provider-success semantics and delivery deduplication.
- Baseline emits no new-listing user result.
- No-new status is anti-spam and should not be pushed every interval by default.
- Scan does not render channel text or choose presentation strategy.

## 17. SOLS-12 privacy, observability and retention boundary evidence

- Evidence source: `SCAN_PRIVACY_OBSERVABILITY_AND_RETENTION_BOUNDARY_v1.0.md`.
- Scan retains only minimal safe technical and semantic state needed for lifecycle, idempotency, replay, comparison, recovery and diagnostics.
- Rolling anchors remain compact memory.
- Raw provider payloads, full HTML/JSON, cookies, tokens, session values, private route details, phone, seller, full descriptions, full archive and secrets are excluded by default.
- Physical retention, compaction and deletion remain gated by OD-013 and future DB/persistence decisions.
- OD-013 remains open.

## 18. SOLS-13 persistence, scheduler and worker gates evidence

- Evidence source: `SCAN_PERSISTENCE_SCHEDULER_AND_WORKER_GATES_v1.0.md`.
- PostgreSQL tables, SQLAlchemy models, Psycopg usage and Alembic migrations remain blocked.
- Scheduler runtime, polling loop, due-slot identity, interval values and missed-scan mechanics remain blocked.
- Worker runtime, worker concurrency/fairness and worker dispatch mechanics remain blocked.
- Claim lease, heartbeat, renewal, physical locks, transactions, stale-claim handling, retry/backoff/circuit-breaker policy and queue/broker/cache infrastructure remain blocked.
- Parser calls, live Avito calls, Egress route calls and notification delivery remain owned by their own modules and gates.

## 19. Known divergences from original playbook v1.0

- The original playbook v1.0 included price-pair and new-price semantics.
- Current owner decision supersedes that behavior for module 06.
- Current module 06 behavior is new listings only.
- `ListingPricePairFirstSeen` and price-change notification are deferred/disabled.
- Price remains display/parser candidate data only.
- No permanent price history is introduced here.
- No price-change notification flow is introduced here.
- The original playbook remains historical source-of-truth context, not deleted or rewritten by this handoff.

## 20. Cross-module dependencies and ownership

| Module boundary | Owner responsibility | Scan consumption | Scan limitation |
|---|---|---|---|
| Platform & Contracts | Primitives and shared governance. | Public contracts and governance references. | Does not mutate shared primitives or governance. |
| Identity & Access | Actor/account authorization primitives. | Explicit actor/auth context. | Does not infer authorization from UI or channel state. |
| Entitlements & Billing | Effective entitlement decisions and billing gates. | Explicit entitlement decisions. | Does not mutate entitlement/payment/subscription/grant state. |
| Beacon Management | Beacon lifecycle, source URL, extracted snapshot, overrides, configuration revision and lifecycle authority. | Explicit Beacon and revision references. | Does not mutate Beacon lifecycle or configuration. |
| Avito Parser Adapter | Parser outcome, compatibility profile, observed order, sort context, provider classification and normalized candidates. | Explicit parser outcome references and sort evidence. | Does not parse Avito or own parser mappings. |
| Egress Routing | Route and transport mechanics, route availability and route self-healing. | Explicit egress availability references. | Does not choose or heal routes. |
| Notification Delivery | Facts consumption, outbox, delivery attempts, retries, rendering delegation and provider success. | Handoff-ready scan facts and status facts. | Does not live inside Scan and does not roll back Scan state on delivery failure. |
| Admin/Web/Telegram/MAX/UI | Presentation and user action surfaces. | Safe status/fact references only. | Does not become Scan-owned delivery logic. |
| Persistence/runtime owners | DB/schema/migrations/scheduler/worker/deploy gates. | Semantic gate references only. | Does not become implementation authorization from this handoff. |

Scan consumes references and contracts; it does not mutate foreign module state.

## 21. Remaining gated dependencies

- product/runtime code
- executable tests
- real fixture files
- physical DB schema
- migrations
- ORM models
- SQLAlchemy
- Psycopg
- Alembic
- scheduler runtime
- worker runtime
- polling loop
- queue/broker/cache
- claim lease duration
- claim heartbeat
- retry/backoff/circuit breaker
- Egress route calls
- Parser calls
- live Avito/provider calls
- Notification outbox
- delivery attempts
- provider retries
- Telegram/MAX/Web/Admin UI
- retention/deletion/compaction/read-model rebuild jobs
- OD-013 retention resolution
- Docker/CI/CD/deploy/runtime service
- secrets/.env/runtime configuration

## 22. Explicit non-implementation statement

- No source code was introduced by SOLS-01 through SOLS-13.
- No tests were introduced by SOLS-01 through SOLS-13.
- No executable fixtures were introduced.
- No DB/schema/migration artifacts were introduced.
- No scheduler, worker, queue, cache or runtime implementation was introduced.
- No parser/provider/live Avito call was introduced.
- No Egress route implementation was introduced.
- No Notification delivery or outbox implementation was introduced.
- No UI, Admin, Web, Telegram or MAX implementation was introduced.
- No deployment or runtime service was introduced.
- No secrets, tokens, `.env` content or private key content were introduced.

## 23. No live provider traffic statement

No live Avito/provider traffic was introduced by SOLS-01 through SOLS-13, and this handoff does not authorize any live provider traffic.

## 24. No DB/runtime/deploy statement

No DB schema, migration, ORM, scheduler runtime, worker runtime or deploy artifact was introduced by SOLS-01 through SOLS-13, and this handoff does not authorize any such implementation.

## 25. Parallel-work and source-of-truth notes

- This handoff is derived only from `MODULE_PLAYBOOK.md` and the accepted SOLS-01 through SOLS-13 documents in `docs/04-modules/06-scan-orchestration-and-listing-state/`.
- It does not supersede those accepted documents.
- It does not close any open decision by assumption.
- Future implementation must start from explicit future gates and ChatGPT verification.
- The accepted documents remain the source of truth for their own scopes until a future accepted task changes them.

## 26. Future implementation prerequisites

- Explicit future gates are required before any runtime implementation begins.
- Explicit future gates are required for physical schema, migrations, ORM mapping, scheduler runtime, worker runtime, claim/concurrency strategy, retry policy, queue/broker/cache choice, parser execution, egress route execution, notification delivery, UI surfaces and retention/deletion/compaction policy.
- OD-013 must remain explicitly resolved before any retention or deletion implementation.
- No gate value, default interval, claim lease, heartbeat, retry/backoff or worker concurrency is chosen in this handoff.
- ChatGPT verification must precede any future implementation scope.

## 27. Final acceptance checklist

- [ ] GitHub main verified at SOLS-14 base.
- [ ] SOLS-01 through SOLS-13 artifacts present.
- [ ] Owner decisions captured.
- [ ] New-listings-only scope confirmed.
- [ ] Price-change notification deferred/disabled.
- [ ] Rolling anchors compact-memory boundary confirmed.
- [ ] Lost anchors not confirmed-new.
- [ ] External failure not no-new and does not erase anchors.
- [ ] Pending recovery single-obligation rule captured.
- [ ] Overlap/mid-run/lifecycle/entitlement recheck captured.
- [ ] Parser partial/ambiguous/reconciliation boundary captured.
- [ ] Notification/status handoff captured without delivery.
- [ ] Privacy/retention boundary captured without full archive/raw payload.
- [ ] Persistence/scheduler/worker gates captured without implementation.
- [ ] OD-013 remains open.
- [ ] No live provider traffic.
- [ ] No DB/runtime/deploy artifacts.
- [ ] No out-of-scope paths.
- [ ] Module 06 semantic documentation scope ready for ChatGPT final acceptance.
