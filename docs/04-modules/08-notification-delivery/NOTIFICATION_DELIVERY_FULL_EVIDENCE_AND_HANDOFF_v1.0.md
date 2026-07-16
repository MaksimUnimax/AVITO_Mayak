# Маяк Авито — Module 08 Full Evidence and Handoff v1.0

- `status`: final evidence/handoff for accepted semantic contracts and tests scope
- `date`: 2026-07-16
- `module`: 08-notification-delivery
- `roadmap step`: ND-15
- `technical task`: MAYAK-ND-15-FULL-EVIDENCE-HANDOFF-20260716-011
- `latest accepted module SHA`: d02b2ac0bf3845394f4c1b0677cf438e41b9818f
- `source-of-truth playbook`: docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md
- `owner decision capture`: docs/04-modules/08-notification-delivery/OWNER_NOTIFICATION_DECISIONS_CAPTURE_v1.0.md

## 1. Executive summary

Module 08 is complete only inside the current accepted semantic contracts/tests/evidence scope.

The main user-visible event is new listings after a committed Scan fact.

Baseline does not notify.

Price-change notification is disabled/deferred in the current product scope.

One committed Scan result is represented as one generic notification effect with all safe listing references preserved.

All enabled and verified channels are planned by default until the user disables a channel.

Provider-specific mapping, rendering and delivery remain adapter scope.

Unknown provider send is reconciliation-first and does not use blind retry.

Safe delivery history is minimal and is not a full listing archive.

Read/click/open tracking is deferred.

Quiet hours, digest and time batching are deferred.

Runtime, schema, queue, provider and deploy gates are blocked.

This module is not production-ready.

Physical persistence and live delivery remain blocked.

OD-013 remains open.

## 2. Accepted SHA chain

- ND-01 governance capture:
  - `31f7db5455f64915ddd76b0a5544900219e79472`
  - `nd-01: correct notification owner capture`
- ND-02 source intake:
  - `38322db2b5facc31f54cb9183f4fb672b053bef5`
  - `nd-02: add notification source intake semantics`
- ND-03 eligibility/preferences:
  - `e6e1973cd3a20a96fffd24be1e6e72583a1925d0`
  - `nd-03: correct exports and eligibility precedence`
- ND-04 generic outbox:
  - `5e5940e0b5916c7f936a01b0e4a5072353a7074c`
  - `nd-04: add generic notification outbox semantics`
- ND-05 multi-channel plan:
  - `0b3c661f8f1f4bf9c984e28927bb8c6b2f807726`
  - `nd-05: add multi-channel delivery plan semantics`
- ND-06 attempt/provider outcome:
  - `35b35245ea70929b401290f6876e1e1ca190a487`
  - `nd-06: enforce provider outcome start state gate`
- ND-07 idempotency/dedup/replay:
  - `d220c0c525c1a071652b81b5af47239daf05cf50`
  - `nd-07: enforce exact channel class type`
- ND-08 no-new policy:
  - `4d8fdc2b6649115e50baf1729cc7933058df2820`
  - `nd-08: remove static boundary evasion`
- ND-09 external unavailable/recovery:
  - `e49f3c850a35eb083af9361c0e2cc9dffbf2c575`
  - `nd-09: correct same-problem replay status`
- ND-10 listing-card boundary:
  - `ab6050844cb850d781ae6993082d70c48c71085f`
  - `nd-10: enforce listing card output invariants`
- ND-11 batch/partial outcomes:
  - `15207864e0d304f43ac50602f77f57143b89aed6`
  - `nd-11: satisfy batch static type gate`
- ND-12 read models/history:
  - `a05b71818fde3a43066714098e1b9eed43fdf9dd`
  - `nd-12: export notification read model semantics`
- ND-13 security/privacy/suppression:
  - `16ec547eef68b800d17afd95e2a33274c5e68d5c`
  - `nd-13: add security privacy suppression semantics`
- ND-14 deferred runtime gates:
  - `d02b2ac0bf3845394f4c1b0677cf438e41b9818f`
  - `nd-14: add deferred runtime gate semantics`

## 3. Parallel-main and correction evidence

ND-12 implementation commit was `69fd43905550c9dd94f6be45965ba67e72418882` with subject `nd-12: add notification read model semantics`.

Parallel-main commit `0178d5661b7bd1b81e65676491ae6fce46ab00a9` with subject `er-13a: establish canonical test package layout` changed only canonical test package `__init__.py` paths and was not the ND-12 implementation.

ND-12 export correction was `a05b71818fde3a43066714098e1b9eed43fdf9dd` with subject `nd-12: export notification read model semantics`.

Parallel Egress commit before ND-13 was `fa06c5e502910d5fbdd2efe9f168f870726a34b9` with subject `er-14a: add persistence runtime gate`.

Final ND-13 publish was `16ec547eef68b800d17afd95e2a33274c5e68d5c` with subject `nd-13: add security privacy suppression semantics`.

Parallel commits were not rewritten.

Stale worktrees were not published.

Rebase, merge, cherry-pick, reset, amend, squash and force-push were not used.

Each publish was performed only after a new exact-base gate.

GitHub `main` remained the source of truth.

## 4. Accepted artifact inventory

| Artifact | Roadmap step | Role | Accepted boundary | Still blocked |
|---|---|---|---|---|
| `docs/04-modules/08-notification-delivery/OWNER_NOTIFICATION_DECISIONS_CAPTURE_v1.0.md` | ND-01 | Owner decision capture | Semantic scope decisions only | Runtime, schema, queue, provider, deploy |
| `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md` | ND-01 to ND-14 | Source playbook | Approved semantic playbook only | Runtime, physical implementation, deploy |
| `src/mayak/modules/notification_delivery/source_intake.py` | ND-02 | Committed source intake semantics | Only committed upstream facts and safe references | Raw payload, runtime ingestion, provider mapping |
| `src/mayak/modules/notification_delivery/eligibility.py` | ND-03 | Eligibility and preference semantics | Account, beacon, entitlement and channel gates only | UI persistence, runtime scheduling, provider delivery |
| `src/mayak/modules/notification_delivery/outbox.py` | ND-04 | Generic outbox semantics | One intended user-visible effect, provider-neutral | Physical persistence, queue, runtime workers |
| `src/mayak/modules/notification_delivery/delivery_plan.py` | ND-05 | Multi-channel planning semantics | Default plan for enabled verified channels | Provider payload, fallback policy, runtime dispatch |
| `src/mayak/modules/notification_delivery/attempt.py` | ND-06 | Attempt lifecycle semantics | Generic attempt and provider-outcome acceptance | Retry engine, backoff engine, blind retry |
| `src/mayak/modules/notification_delivery/deduplication.py` | ND-07 | Idempotency and replay semantics | Duplicate-effect boundary protection | Storage engine, external dedup cache, runtime retries |
| `src/mayak/modules/notification_delivery/no_new_status.py` | ND-08 | No-new status semantics | Suppressed-by-default status policy | UI storage implementation, scheduler, runtime push |
| `src/mayak/modules/notification_delivery/external_recovery.py` | ND-09 | External unavailable and recovery semantics | One problem-start effect and one recovery result | Route choice, parser behavior, provider execution |
| `src/mayak/modules/notification_delivery/listing_card.py` | ND-10 | Safe listing-card boundary | Safe generic listing facts only | Fetch, parse, enrichment, raw HTML/JSON |
| `src/mayak/modules/notification_delivery/batch.py` | ND-11 | Batch and partial outcome semantics | Per-item/per-channel outcomes preserved | Provider-specific batch format, runtime batch transport |
| `src/mayak/modules/notification_delivery/read_model.py` | ND-12 | Read model and delivery-history semantics | Safe minimal read/history projection only | Full archive, mutation authority, tracking auth |
| `src/mayak/modules/notification_delivery/security_privacy.py` | ND-13 | Security/privacy/suppression semantics | Authorization and safe-public-error boundaries | Provider mapping, read tracking, retention implementation |
| `src/mayak/modules/notification_delivery/deferred_runtime_gate.py` | ND-14 | Deferred runtime gate semantics | Explicit blocked capabilities and allowed pre-runtime work | Schema, queue, provider adapter, deploy, live delivery |
| `src/mayak/modules/notification_delivery/__init__.py` | ND-02 to ND-14 | Package export surface | Direct export ownership for accepted semantic modules | Dynamic import bridge, lazy loading, runtime side effects |
| `tests/contract/test_notification_delivery_*` contracts | ND-02 to ND-14 | Contract evidence | Accepted semantic contracts only | Runtime integration, provider delivery, deploy evidence |
| `tests/unit/test_notification_delivery_*` semantics | ND-02 to ND-14 | Semantic evidence | Deterministic semantic behavior only | Physical persistence, live delivery, provider runtime |
| `tests/architecture/test_notification_delivery_boundaries.py` | ND-14 | Boundary evidence | Static boundary checks only | Runtime implementation, provider adapter code |

Logical records remain logical records and are not physical tables, queues, wire schemas or provider payloads.

## 5. ND-01 owner decisions captured

- New listings after committed Scan facts are the primary notification effect.
- Price-change notification is disabled/deferred.
- Baseline does not notify.
- No-new push is off/suppressed by default.
- Optional no-new preference exists as future user choice.
- Minimum frequency for no-new is one hour.
- Current no-new status remains available to the read model and UI.
- External problem status is emitted once at start or material change.
- One recovery-result is used for the recovery outcome boundary.
- A narrow entitlement recovery grace is allowed only once where applicable.
- Lost anchors resolve to latest fresh or state restored, not confirmed-new.
- All safe listing references are preserved.
- No Notification-level preview truncation is allowed.
- All enabled verified channels are planned by default.
- Per-channel user opt-out is supported by the semantic boundary.
- Telegram, MAX and Web ownership remain separate.
- Minimal safe history is preserved.
- Unknown send is reconciliation-first.
- Read/click tracking is deferred.
- Quiet hours, digest and time batching are deferred.
- OD-013 remains open.

## 6. ND-02 source intake evidence

- Only committed upstream source facts are accepted.
- Stable source identity, producer and contract/version are required.
- Allowed current source families are limited to the accepted notification families already captured in the module semantics.
- Baseline facts, start-of-scan facts, parser-only facts, egress-only facts and provider-only facts do not create user-visible notification work.
- Price-change trigger remains inactive in the current scope.
- Ambiguous source creates no effect.
- Raw upstream or provider payload is not copied.

## 7. ND-03 eligibility and preference evidence

- Account, Beacon, lifecycle, entitlement, preference and target evidence are required.
- Ambiguous evidence blocks effect.
- Verified enabled channels are allowed.
- Disabled channel is suppressed.
- No-new status preference and frequency gate are enforced.
- Minimum one-hour policy remains the accepted constraint.
- One explicit recovery grace is the only entitlement exception.
- No UI implementation or preference persistence implementation is authorized here.

## 8. ND-04 generic outbox evidence

- One intended user-visible effect is represented.
- The outbox is provider-neutral.
- Stable source, outbox and dedup identities are required.
- Full count and all safe listing references are preserved.
- No preview truncation is allowed.
- Outbox creation is not provider delivery, user receipt, read or click.
- No physical persistence implementation is authorized here.

## 9. ND-05 multi-channel planning evidence

- All enabled and verified channels are planned by default.
- Telegram and MAX targets are safe references, not credentials.
- Web is a read and status projection boundary.
- Per-channel outcomes remain independent.
- One channel success does not erase another channel failure.
- No priority or fallback values are invented.
- No provider-specific payload is defined here.

## 10. ND-06 attempt and provider-outcome evidence

- The attempt lifecycle is generic.
- Provider HTTP success and Egress transport success are not accepted delivery by themselves.
- Provider outcome must be accepted into generic state.
- Unknown or ambiguous send requires reconciliation.
- Blind retry is not allowed.
- Replay does not duplicate a state transition.
- Retry and backoff values remain unselected.

## 11. ND-07 idempotency, deduplication and replay evidence

- Same key plus same request returns or references the original state.
- Pending or ambiguous remains pending or reconciliation-bound.
- Key or fingerprint mismatch produces no effect.
- Source replay does not create a second outbox effect.
- Attempt or provider-result replay does not duplicate the transition.
- Dedup scope includes account, Beacon and channel where applicable.
- Recovery, status and no-new duplicate-effect boundaries remain protected.
- Unrelated Beacon state is not suppressed.

## 12. ND-08 no-new status evidence

- No-new is not the new-listing event.
- No push is emitted after each Scan.
- No five-minute push exists in the accepted scope.
- Default state is suppressed or off.
- Future preference remains optional.
- Minimum one-hour constraint remains.
- Status remains readable independently of push delivery.
- No UI, storage or scheduler implementation is authorized here.

## 13. ND-09 external unavailable and recovery evidence

- External problem is not no-new.
- One problem-start or material-change effect is allowed.
- Same problem replay does not create a duplicate effect.
- One recovery result follows recovery.
- Recovery with new, no-new or lost-anchor result remains distinguishable.
- One narrow entitlement grace remains the only exception boundary.
- Notification failure does not erase Scan recovery obligation.
- No Egress route choice or parser behavior is defined here.

## 14. ND-10 listing-card boundary evidence

- Only safe generic listing references and facts are allowed.
- Optional fields are never required.
- Complete order and references are preserved.
- No fetch, parse, enrichment or Avito access is permitted here.
- No raw HTML or JSON is stored here.
- No unapproved seller or private data is included.
- Adapters own presentation, pagination and buttons.

## 15. ND-11 batch and partial outcome evidence

- Per-item and per-channel results are preserved.
- Mixed results never collapse into one generic success.
- Replayed, suppressed, blocked and failed identities remain retained.
- Safe error categories are used.
- Reconciliation and retry state remain per attempt.
- All listing references remain preserved.
- No provider-specific batch format is defined here.

## 16. ND-12 read model and delivery-history evidence

- User, admin and support audiences are separated.
- Authorization scope is explicit.
- Safe outbox, attempt, source, channel, status and reconciliation references are used.
- Minimal history only is retained.
- No full listing archive exists here.
- No full chat or message archive exists here.
- No raw provider payload exists here.
- No credentials or secrets exist here.
- No read/click tracking exists here.
- Projection is not mutation authority.
- Retention, deletion, archive and compaction remain governed by OD-013.

ND-12 implementation and package export correction are one accepted roadmap capability, and the final accepted ND-12 SHA is `a05b71818fde3a43066714098e1b9eed43fdf9dd`.

## 17. ND-13 security/privacy/suppression evidence

- Authorization precedes protected reads and effects.
- Unauthorized, cross-account and cross-Beacon access collapse to safe public errors.
- Ambiguous identity, lifecycle, entitlement, content or target blocks effect.
- Target remains a verified internal reference.
- User opt-out suppresses the matching channel.
- Safe listing references preserve complete ordered content.
- Historical entitlement and Beacon evidence are not rewritten.
- Provider mapping and execution are not authorized here.
- Read/click tracking is not authorized here.
- Retention is not authorized here.
- No external strings are executed as commands.
- No unapproved personal data collection is authorized here.

## 18. ND-14 deferred runtime gate evidence

Required gate classes:

- `PHYSICAL_SCHEMA_AND_MIGRATIONS`
- `QUEUE_WORKER_BROKER`
- `PROVIDER_ADAPTER_PLAYBOOKS`
- `PROVIDER_CREDENTIALS_POLICY`
- `RETRY_RATE_TIME_POLICY`
- `OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY`
- `EXACT_IMPLEMENTATION_TASK`

Satisfied gate classes: none

Status: `BLOCKED_PENDING_EXPLICIT_GATES`

Allowed pre-runtime classes:

- `SEMANTIC_CONTRACTS`
- `SYNTHETIC_DETERMINISTIC_FAKES`
- `ARCHITECTURE_STATIC_CHECKS`
- `DOCS_ONLY_DECISIONS`
- `EVIDENCE_HANDOFF`

Blocked capability families:

- PostgreSQL, SQLAlchemy, Psycopg and Alembic
- queue, worker, broker and cache
- scheduler and polling
- Telegram and MAX provider adapters
- Web push
- webhook and Mini App
- provider API calls
- message templates
- credentials
- retry, backoff and rate limits
- quiet hours and digest
- retention tooling
- runtime services
- Docker, CI/CD and deploy
- live delivery

Runtime execution authorized: false

Persistence implementation authorized: false

Provider adapter implementation authorized: false

Production readiness inferred: false

Provider permission inferred: false

Retention policy resolved: false

OD-013 closed: false

## 19. Package/public contract state

- Package exports cover ND-02 through ND-14.
- Each semantic module owns an exact direct `__all__`.
- Earlier contracts use append-only package-prefix semantics.
- ND-14 owns the exact current package surface.
- Aliases preserve object identity.
- No dynamic `__getattr__`, wildcard package bridge or lazy loading is used.
- Package import creates no runtime effect.
- The package surface is direct and explicit, not runtime-generated.

## 20. Current module ownership

Notification Delivery owns only generic semantic authority for:

- committed source intake;
- eligibility;
- generic outbox effect;
- generic multi-channel plan;
- attempt lifecycle;
- provider outcome acceptance;
- deduplication, idempotency and replay;
- no-new notification policy;
- external unavailable and recovery policy;
- safe listing-card references;
- batch and partial outcomes;
- safe read models and history;
- security, privacy and suppression;
- deferred runtime gate.

Semantic in-memory records are not durable physical records.

## 21. Cross-module dependencies and non-ownership

- Scan owns committed source facts, baseline, anchors, listing state, no-new facts and recovery obligations.
- Parser owns extraction and provider response classification.
- Egress Routing owns routes, agents, leases and transport outcomes.
- Identity owns authentication, account scope and verified target linking.
- Entitlements owns effective access decisions.
- Beacon Management owns configuration and lifecycle.
- Telegram Adapter owns Telegram mapping, rendering and delivery.
- MAX Adapter owns MAX mapping, rendering and delivery.
- Web Cabinet owns UI and read presentation.
- Admin and Support consume safe read models and do not mutate Notification records.
- Platform and Contracts owns shared primitives.
- Notification Delivery does not mutate foreign module state.

## 22. Security and privacy summary

- No raw provider payload is stored or exposed.
- No raw Avito HTML or JSON is stored or exposed.
- No cookies, tokens, sessions, private keys or one-time codes are stored or exposed.
- No provider credentials are present.
- No unsafe target values are accepted.
- No cross-account leakage is allowed.
- No full listing archive exists.
- No full message or chat history exists.
- No read/click/open analytics are authorized.
- Only safe evidence references are used.
- Retention implementation remains blocked by OD-013.

## 23. Validation evidence

| Check | Result | Evidence scope |
|---|---|---|
| `python -m py_compile` | passed | Semantic module Python source |
| `ruff check` | passed | Notification Delivery module and tests |
| `mypy src/mayak/modules/notification_delivery` | passed | Notification Delivery module |
| Targeted ND-14 contract/unit/architecture | passed: 9 + 53 + 32 tests | Deferred runtime gate semantics and boundaries |
| Targeted ND-13 contract/unit | passed: 9 + 20 tests | Security/privacy/suppression semantics |
| Targeted ND-12 contract/unit | passed: 8 + 21 tests | Read model/history semantics |
| `python -m pytest -q` | passed: 3477 tests | Full repository test suite |
| `pytest -q` | passed: 3477 tests | Console test entrypoint |
| `lint-imports` | passed: 3 kept, 0 broken | Import boundary validation |
| Dependency lock status | `UV_LOCK_RESULT: NOT_RUN_TOOL_UNAVAILABLE` | Lockfile state |
| Changed-path check | passed: `docs/04-modules/08-notification-delivery/NOTIFICATION_DELIVERY_FULL_EVIDENCE_AND_HANDOFF_v1.0.md` | Single-file docs-only gate |
| Forbidden-artifact check | passed | Secrets, runtime and physical-artifact absence |

GitHub Actions workflow evidence is not used here unless GitHub provides a run for the exact commit; local checks remain the source of evidence for this handoff.

## 24. Remaining open decisions and gates

- OD-013 retention, deletion, archive and compaction.
- Physical schema, indexes, constraints and migrations.
- Queue, worker, broker and cache.
- Scheduler, polling and runtime topology.
- Provider adapter playbooks.
- Provider credentials policy.
- Telegram and MAX API setup.
- Webhook and Mini App.
- Provider templates and localization.
- Retry count, delay and backoff.
- Provider rate limits.
- Exact preference storage and UI.
- Exact unsubscribe semantics.
- Channel priority and fallback.
- Quiet hours, digest and time batching.
- Read, click and open tracking.
- Production observability and runbooks.
- Operations deploy approval.
- Exact future implementation task.

Open means blocked.

No open decision is resolved by assuming a reasonable default.

## 25. Final handoff state

ND-01 through ND-14 are complete in the accepted semantic contracts/tests scope.

ND-15 provides evidence and handoff only.

Module 08 current semantic scope is complete after acceptance of this document.

No runtime, provider, schema, queue, worker or deploy implementation exists or is authorized.

Telegram, MAX and Web implementation remains in their owning modules and future gates.

Physical persistence remains gated.

OD-013 remains open.

Future work requires a new explicit owner-approved roadmap or gate and fresh GitHub verification.

No automatic next product implementation step is authorized.
