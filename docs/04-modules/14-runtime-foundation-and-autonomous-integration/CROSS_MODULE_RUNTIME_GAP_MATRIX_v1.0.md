# Cross-Module Runtime Gap Matrix

**Version:** `1.0`
**Status:** `RF-03_ACTIVE_SECOND_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
**Date:** `2026-07-23`
**Module:** `14-runtime-foundation-and-autonomous-integration`
**Roadmap step:** `RF-03`
**Technical-ID:** `RF-03-02-CROSS-MODULE-RUNTIME-GAP-MATRIX-20260723`
**Source branch:** `main`
**Source base SHA:** `23e73707b14b220da98beade93ee2d13021ba1b9`
**RF-03-01 original publishing SHA:** `c366f1dd6331902fc1a08f54225026f17c1ef4fa`
**RF-03-01 accepted corrective chain head:** `23e73707b14b220da98beade93ee2d13021ba1b9`
**Runtime mutation:** `none`
**Production verdict:** `NOT_CLAIMED`
**Final Module 14 target:** `READY_FOR_OPERATOR_ACCEPTANCE`

## 1. Purpose and authority

This matrix inventories all known automatically executable runtime gaps after accepted semantic work in modules 01–13. GitHub `main`, accepted Module 14 governance, accepted module handoffs/contracts and the current tracked tree are the authority. This artifact performs no runtime mutation, does not transfer domain ownership, and does not authorize RF-04 or later work before prerequisite acceptance.

## 2. Evidence method

Gaps are derived from the accepted completion matrix and module handoffs, then checked against current tracked source, tests and fixtures. Accepted semantic implementation is distinguished from absent physical runtime. Every automatically correctable gap is assigned to one primary RF step; cross-cutting proof is assigned to applicable later RF steps. External operator-only actions are separated from automatic implementation. Missing provider credentials are treated as `PROVIDER_DISABLED_CONTINUE`. No unsupported provider capability is inferred.

## 3. Controlled vocabulary

- `GAP_OPEN_AUTOMATABLE` — required automatic work not yet accepted and assigned to an exact RF step.
- `GAP_EXTERNAL_OPERATOR_ONLY` — external account, credential, eligibility, host installation or live proof that cannot be fabricated.
- `GAP_NOT_APPLICABLE` — no owned runtime gap for that category.
- `GAP_DEFERRED_POST_ACCEPTANCE` — explicitly future production/scaling/legal scope outside Module 14 acceptance completion.
- `PROVIDER_DISABLED_CONTINUE` — optional provider credential unavailable; provider disabled while core automatic work continues.
- `GAP_ACCEPTED_SEMANTIC_ONLY` — semantic/contracts/tests accepted but physical runtime proof remains pending.

## 4. Roadmap runtime-gap coverage

| RF step | Required outcome | Primary owning scope | Current evidence state | Automatically executable gap | Prerequisites | Required acceptance proof | External residual | Gap status |
|---|---|---|---|---|---|---|---|---|
| RF-04 | Runtime architecture and physical data model | Module 14 runtime foundation | Semantic architecture accepted; physical model absent | Define owned PostgreSQL aggregates, boundaries and runtime topology | RF-03 closure | Approved physical model and architecture gate | NONE | GAP_OPEN_AUTOMATABLE |
| RF-05 | Existing-server environment record | Module 14 operations | Server boundary documented; current record absent | Record safe environment, toolchain and ownership facts | RF-04 | Reproducible redacted environment evidence | NONE | GAP_OPEN_AUTOMATABLE |
| RF-06 | Toolchain and dependency proof | Module 14 toolchain | Dependency intent tracked; proof absent | Verify pinned toolchain and lock without changing dependencies | RF-05 | Clean deterministic toolchain and lock verification | NONE | GAP_OPEN_AUTOMATABLE |
| RF-07 | CI quality gates | Module 14 CI | CI gates specified; no accepted runtime gates | Implement static, architecture, test, security and migration gates | RF-06 | GitHub Actions checks pass from clean checkout | NONE | GAP_OPEN_AUTOMATABLE |
| RF-08 | Container and Compose foundation | Module 14 runtime assembly | Compose runtime absent | Build local-only API/worker/scheduler/PostgreSQL Compose foundation | RF-07 | Build and Compose validation with no public ingress | NONE | GAP_OPEN_AUTOMATABLE |
| RF-09 | PostgreSQL and Alembic foundation | Module 14 persistence | No physical schema or migration chain accepted | Create project-owned schema and deterministic migration from zero | RF-08 | Migration zero-to-head and current-head proof | NONE | GAP_OPEN_AUTOMATABLE |
| RF-10 | Platform & Contracts runtime | Module 01 | Semantic contracts accepted; physical runtime absent | Add DB-backed idempotency, transactions, configuration, health and assembly primitives | RF-09 | Unit/contract/integration proof and readiness evidence | NONE | GAP_OPEN_AUTOMATABLE |
| RF-11 | Identity & Access runtime | Module 02 | Semantic identity rules accepted; persistence absent | Persist accounts, links, sessions and roles; add acceptance-only synthetic login | RF-09, RF-10 | Account/link/session/role and authorization tests | External provider identity proof where applicable | GAP_OPEN_AUTOMATABLE |
| RF-12 | Entitlements & Billing runtime | Module 03 | Semantic tariff and payment rules accepted; persistence absent | Persist tariff/access/usage/payment/reconciliation and sandbox-ready adapter | RF-09, RF-10, RF-11 | Entitlement, cadence, reconciliation and disabled-provider tests | YooKassa credentials/live sandbox proof | GAP_OPEN_AUTOMATABLE |
| RF-13 | Beacon Management runtime | Module 04 | Semantic lifecycle and revision rules accepted; persistence absent | Persist Beacon aggregate/history/idempotency and lifecycle commands | RF-09, RF-10, RF-11, RF-12 | Stale-revision, authorization and lifecycle integration proof | NONE | GAP_OPEN_AUTOMATABLE |
| RF-14 | Avito Parser Adapter runtime | Module 05 | Synthetic parser semantics accepted; live process absent | Assemble synthetic parser and disabled-by-default HTTPX/egress boundary | RF-09, RF-10, RF-13 | Explicit parser outcomes, malformed/partial and route-boundary tests | Live Avito access and proof | GAP_OPEN_AUTOMATABLE |
| RF-15 | Scan Orchestration & Listing State runtime | Module 06 | Scan rules documented; durable state absent | Persist schedules, ScanRun, leases, baselines, anchors and listings with restart recovery | RF-09, RF-10, RF-13, RF-14 | Baseline/new-listing, failure, lease and restart tests | NONE | GAP_OPEN_AUTOMATABLE |
| RF-16 | Egress Routing runtime | Module 07 | Semantic gates accepted; durable route runtime absent | Persist route registry/health/leases and implement agent protocol, simulator and recovery | RF-09, RF-10, RF-14 | Lease, fail-closed, replay and recovery proof | Windows installation/live route proof | GAP_OPEN_AUTOMATABLE |
| RF-17 | Notification Delivery runtime | Module 08 | Outbox semantics accepted; delivery persistence absent | Persist outbox, attempts, retry/reconciliation and read history | RF-09, RF-10, RF-15 | Newly-observed event, lifecycle and ambiguous-effect tests | NONE | GAP_OPEN_AUTOMATABLE |
| RF-18 | Telegram Adapter runtime | Module 09 | Provider-boundary semantics accepted; bot runtime absent | Persist updates/mappings, deduplicate, assemble fake and disabled outbound adapters | RF-09, RF-10, RF-11, RF-17 | Update deduplication, mapping, fake provider and readiness tests | Telegram token/live bot proof | GAP_OPEN_AUTOMATABLE |
| RF-19 | MAX Adapter runtime | Module 10 | Secondary provider semantics accepted; runtime absent | Implement webhook model, optional dev polling boundary, Mini App validation and fake adapter | RF-09, RF-10, RF-11, RF-17 | Webhook, validation, fake provider and disabled readiness tests | MAX eligibility/token/live proof | GAP_OPEN_AUTOMATABLE |
| RF-20 | Admin & Support runtime | Module 11 | Workflow semantics accepted; operator runtime absent | Persist cases/notes/audit, safe projections and authorized command API/UI | RF-09, RF-10, RF-11, RF-12, RF-13, RF-15, RF-17 | Actor/authorization/reason/target/idempotency/audit tests | Operator Admin UAT | GAP_OPEN_AUTOMATABLE |
| RF-21 | Web Cabinet runtime | Module 12 | Projection semantics accepted; UI/runtime absent | Assemble FastAPI/Jinja2 server-rendered cabinet, sessions, projections and command boundary | RF-09, RF-10, RF-11, RF-12, RF-13, RF-15, RF-17, RF-20 | UAT-ready synthetic cabinet and no-direct-write tests | Operator Web Cabinet UAT | GAP_OPEN_AUTOMATABLE |
| RF-22 | Filter Catalog & Builder runtime | Module 13 | FC-08 semantic evidence accepted; persistence/UI absent | Persist immutable catalog versions, validate server-side and wire candidate to Beacon | RF-09, RF-10, RF-13, RF-14, RF-21 | FC-08 plus catalog, validation and Beacon integration proof | Exact live catalog evidence | GAP_OPEN_AUTOMATABLE |
| RF-23 | Cross-module API and command wiring | Module 14 public boundaries | Public contracts accepted; wiring absent | Wire services through public contracts and transport DTOs | RF-10–RF-22 applicable gates | Contract and integration edge tests | NONE | GAP_OPEN_AUTOMATABLE |
| RF-24 | Synthetic end-to-end vertical slices | Module 14 acceptance runtime | Semantic slices accepted; E2E absent | Execute synthetic identity-to-scan-to-notification and cabinet/admin slices | RF-23 | Deterministic deployed E2E with synthetic data | NONE | GAP_OPEN_AUTOMATABLE |
| RF-25 | Security, privacy and supply-chain verification | Module 14 security | Policies accepted; closure proof absent | Run secret, vulnerability, license, privacy and authorization gates | RF-23, RF-24 | Clean security and supply-chain evidence | NONE | GAP_OPEN_AUTOMATABLE |
| RF-26 | Observability, backup and recovery | Module 14 operations | Requirements documented; implementation absent | Add telemetry, redaction, backup, restore and failure recovery proof | RF-23, RF-24, RF-25 | Liveness/readiness, restore and recovery drills | NONE | GAP_OPEN_AUTOMATABLE |
| RF-27 | Deployment on existing server | Module 14 deployment | Server boundary known; deployment absent | Deploy isolated project runtime with rollback-safe evidence | RF-26 | Deployment, source SHA and isolation evidence | NONE | GAP_OPEN_AUTOMATABLE |
| RF-28 | Automated final regression and failure drills | Module 14 quality | Tests are semantic; final runtime suite absent | Run full regression, migrations, restart, failure and reconciliation drills | RF-27 | Complete automated acceptance report | NONE | GAP_OPEN_AUTOMATABLE |
| RF-29 | Operator acceptance pack | Module 14 operator boundary | Operator evidence not collected | Produce runbook, evidence pack and PASS/FAIL/NOT_AVAILABLE record | RF-28 | Operator acceptance pack and recorded outcome | Operator checks and live proofs | GAP_EXTERNAL_OPERATOR_ONLY |
| RF-30 | Final evidence handoff | Module 14 closure | Final handoff absent | Assemble final evidence and `READY_FOR_OPERATOR_ACCEPTANCE` handoff | RF-29 | Final handoff accepted; no `PRODUCTION_READY` claim | NONE | GAP_OPEN_AUTOMATABLE |

## 5. Module-specific runtime gaps

### 01 — Platform & Contracts

- **Primary RF step:** RF-10.
- **Accepted semantic baseline:** Common contracts/platform primitives only; business state remains foreign.
- **Current tracked implementation contour:** Contract and platform primitives with semantic tests; no assembled physical runtime.
- **Persistence gap:** DB-backed idempotency and transaction/configuration state are not implemented.
- **Process/runtime gap:** Runtime assembly, health and readiness process are absent.
- **API/command gap:** Public transport and application-service assembly are absent.
- **Integration gap:** Shared primitives are not wired to every owning module.
- **Provider gap:** NONE.
- **Observability/recovery gap:** Structured telemetry, redaction and restart/recovery proof are absent.
- **Security/privacy gap:** Runtime authorization/configuration and secret-safe diagnostics are not proven.
- **Automated acceptance proof:** RF-10 unit, contract, integration, health and idempotency tests.
- **Operator-only residual:** NONE.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 02 — Identity & Access

- **Primary RF step:** RF-11.
- **Accepted semantic baseline:** `account_id` is authoritative; phone is not mandatory; no standalone password login; no automatic merge.
- **Current tracked implementation contour:** Identity/link contracts and synthetic semantic fixtures; no physical identity runtime.
- **Persistence gap:** Account, link, session and role persistence are absent.
- **Process/runtime gap:** Identity/session runtime assembly is absent.
- **API/command gap:** Acceptance-only synthetic login and authorization boundary are absent.
- **Integration gap:** Verified account context is not wired to Entitlements, Telegram, MAX, Web and Admin.
- **Provider gap:** External provider identity proof remains operator-only where applicable.
- **Observability/recovery gap:** Session expiry, relinking recovery and audit telemetry are not proven.
- **Security/privacy gap:** Runtime authorization, account recovery and privacy controls are not proven.
- **Automated acceptance proof:** Synthetic login, account identity, role, link, session, authorization and no-merge tests.
- **Operator-only residual:** External provider identity proof where applicable.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 03 — Entitlements & Billing

- **Primary RF step:** RF-12.
- **Accepted semantic baseline:** Payment evidence cannot grant entitlement; Free/Basic and accepted cadence are preserved.
- **Current tracked implementation contour:** Tariff, entitlement, usage, payment and reconciliation semantics/tests; no authoritative store.
- **Persistence gap:** Tariff, access, usage, payment and reconciliation records are absent.
- **Process/runtime gap:** Entitlement evaluation and reconciliation workers are absent.
- **API/command gap:** Grant, renew, revoke, refund and tariff command boundary is absent.
- **Integration gap:** Authorization is not wired to Beacon lifecycle/cadence.
- **Provider gap:** YooKassa sandbox-ready adapter is disabled without credentials; missing payment credentials = PROVIDER_DISABLED_CONTINUE.
- **Observability/recovery gap:** Payment unknown-effect reconciliation and entitlement audit proof are absent.
- **Security/privacy gap:** Payment evidence isolation and privileged access controls are not runtime-proven.
- **Automated acceptance proof:** Free/Basic cadence, payment non-grant, reconciliation, refund and disabled-provider tests.
- **Operator-only residual:** YooKassa sandbox credentials and live sandbox proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 04 — Beacon Management

- **Primary RF step:** RF-13.
- **Accepted semantic baseline:** Beacon owns configuration and lifecycle; stale patch must not overwrite current revision; Filter Catalog candidates cannot mutate Beacon directly.
- **Current tracked implementation contour:** Beacon contracts, fixtures and revision/lifecycle semantics; no durable aggregate.
- **Persistence gap:** Beacon aggregate/history/idempotency persistence is absent.
- **Process/runtime gap:** Lifecycle and scheduled Beacon execution are absent.
- **API/command gap:** Authorized create/update/archive/restore commands are absent.
- **Integration gap:** Entitlement authorization and catalog candidate acceptance are not wired.
- **Provider gap:** NONE.
- **Observability/recovery gap:** Revision conflicts, lifecycle audit and restart recovery are not proven.
- **Security/privacy gap:** Account-scoped authorization and safe configuration handling are not runtime-proven.
- **Automated acceptance proof:** Stale-patch, idempotency, lifecycle, authorization and candidate-boundary tests.
- **Operator-only residual:** NONE.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 05 — Avito Parser Adapter

- **Primary RF step:** RF-14.
- **Accepted semantic baseline:** Synthetic parser required; live HTTPX adapter disabled by default; CAPTCHA/restriction is not empty; partial/malformed is not success; route failure is not parser success; no raw payload persistence.
- **Current tracked implementation contour:** Provider-neutral parser contracts, fixtures and semantic tests; no live process.
- **Persistence gap:** No raw provider payload persistence is allowed; normalized result persistence belongs to Scan.
- **Process/runtime gap:** Synthetic parser and disabled-by-default HTTPX/egress runtime are absent.
- **API/command gap:** Parser invocation and explicit result-class boundary are absent.
- **Integration gap:** Egress route/session and Scan result wiring are absent.
- **Provider gap:** Live Avito proof is operator-only; unsupported capability is not inferred.
- **Observability/recovery gap:** Redacted parser outcomes, restriction diagnostics and retry/recovery proof are absent.
- **Security/privacy gap:** Provider secret handling and payload redaction are not runtime-proven.
- **Automated acceptance proof:** Synthetic parser, malformed/partial/restricted, route-failure and no-raw-payload tests.
- **Operator-only residual:** Live Avito access and live parser proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: process/runtime, API/command, integration, observability/recovery and security/privacy.

### 06 — Scan Orchestration & Listing State

- **Primary RF step:** RF-15.
- **Accepted semantic baseline:** First baseline emits no notification; only newly observed listings create notification events; no price-change notifications.
- **Current tracked implementation contour:** Documentation-only semantic evidence and scan package marker; no executable scan path.
- **Persistence gap:** Schedules, ScanRun, leases, baseline/anchor/listing state are absent.
- **Process/runtime gap:** Durable scheduler, worker, claim, lease and restart recovery are absent.
- **API/command gap:** Scan lifecycle and anchor commands are absent.
- **Integration gap:** Beacon, Parser, Egress and Notification boundaries are not wired.
- **Provider gap:** Synthetic parser is required; live provider remains disabled.
- **Observability/recovery gap:** Incomplete-run, lost-anchor, overlap and reconciliation proof are absent.
- **Security/privacy gap:** Retention, account scoping and safe listing handling are not runtime-proven.
- **Automated acceptance proof:** Baseline, newly-observed-only, partial/failure, lease, anchor and restart tests.
- **Operator-only residual:** NONE.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 07 — Egress Routing

- **Primary RF step:** RF-16.
- **Accepted semantic baseline:** Route registry, health, leases, Windows Agent protocol/simulator and recovery are required; no foreign proxy reuse.
- **Current tracked implementation contour:** Semantic routing functions, gates, fixtures and tests; no durable route runtime.
- **Persistence gap:** Route registry, health and lease persistence are absent.
- **Process/runtime gap:** Dispatch, agent protocol, simulator and recovery worker are absent.
- **API/command gap:** Registration, route selection and diagnostic command boundary is absent.
- **Integration gap:** Parser route/session boundary is not wired.
- **Provider gap:** Live Windows installation/proof is operator-only; missing Windows host does not block automatic scope.
- **Observability/recovery gap:** Fail-closed, replay, lease expiry and reconcile-first operational proof are absent.
- **Security/privacy gap:** Session-secret and route isolation are not runtime-proven.
- **Automated acceptance proof:** Simulator/protocol, leases, restrictions, replay, recovery and secret-safety tests.
- **Operator-only residual:** Windows Egress Agent installation and live route proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 08 — Notification Delivery

- **Primary RF step:** RF-17.
- **Accepted semantic baseline:** Generic notification outbox/delivery lifecycle owner; provider acceptance is not human reading; ambiguous effect is reconcile-first.
- **Current tracked implementation contour:** Outbox, attempts, plans, deduplication and recovery semantics/tests; no durable delivery runtime.
- **Persistence gap:** Outbox, attempts, retry/reconciliation and read-history persistence are absent.
- **Process/runtime gap:** Durable delivery worker and reconciliation process are absent.
- **API/command gap:** Generic notification intake and read-history boundary are absent.
- **Integration gap:** Scan event to Telegram/MAX/Web delivery projections are not wired.
- **Provider gap:** Synthetic providers are required; optional providers remain disabled without credentials.
- **Observability/recovery gap:** Delivery lifecycle, retry, unknown-effect and reconciliation proof are absent.
- **Security/privacy gap:** Redaction, retention and account-scoped history are not runtime-proven.
- **Automated acceptance proof:** Outbox, deduplication, attempts, retry, reconcile-first and read-projection tests.
- **Operator-only residual:** NONE.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 09 — Telegram Adapter

- **Primary RF step:** RF-18.
- **Accepted semantic baseline:** Telegram is the primary practical channel but not account owner; provider acceptance is not human reading.
- **Current tracked implementation contour:** Update, identity, callback, Mini App, display and outbound semantic contracts/tests; no bot process.
- **Persistence gap:** Update deduplication and identity mapping persistence are absent.
- **Process/runtime gap:** Bot intake and outbound adapter runtime are absent.
- **API/command gap:** Webhook/update and outbound command boundary is absent.
- **Integration gap:** Verified account context and generic notification delivery are not wired.
- **Provider gap:** Fake provider and disabled readiness are required; missing token = PROVIDER_DISABLED_CONTINUE.
- **Observability/recovery gap:** Update replay, delivery outcome and unknown-effect reconciliation proof are absent.
- **Security/privacy gap:** Token isolation, identity validation and redacted diagnostics are not runtime-proven.
- **Automated acceptance proof:** Update deduplication, mapping, validation, fake provider, outbound and readiness tests.
- **Operator-only residual:** Telegram token and live bot proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 10 — MAX Adapter

- **Primary RF step:** RF-19.
- **Accepted semantic baseline:** MAX is a secondary/future channel; no provider identity replaces `account_id`.
- **Current tracked implementation contour:** Webhook, Mini App, outbound and provider-outcome semantics/tests; no provider runtime.
- **Persistence gap:** Webhook intake, identity mapping and delivery state are absent.
- **Process/runtime gap:** Webhook runtime and optional development polling boundary are absent.
- **API/command gap:** Validation and outbound command boundaries are absent.
- **Integration gap:** Verified account context and Notification Delivery are not wired.
- **Provider gap:** Missing eligibility/token = PROVIDER_DISABLED_CONTINUE; live proof is operator-only.
- **Observability/recovery gap:** Delivery reconciliation, replay and moderation outcome proof are absent.
- **Security/privacy gap:** Mini App validation and secret-safe provider handling are not runtime-proven.
- **Automated acceptance proof:** Webhook, optional polling boundary, Mini App, fake provider and disabled-readiness tests.
- **Operator-only residual:** MAX eligibility, token and live provider proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 11 — Admin & Support

- **Primary RF step:** RF-20.
- **Accepted semantic baseline:** Admin owns support/admin workflow, not foreign state; every mutation requires actor, authorization, reason, target, idempotency and audit.
- **Current tracked implementation contour:** Safe reads, actions, contracts and synthetic tests; no operator runtime.
- **Persistence gap:** Case, note and audit persistence are absent.
- **Process/runtime gap:** Operator authorization and safe projection runtime are absent.
- **API/command gap:** Audited command API/UI is absent.
- **Integration gap:** All foreign mutations must flow through owning services; wiring is absent.
- **Provider gap:** NONE.
- **Observability/recovery gap:** Audit completeness, command idempotency and recovery proof are absent.
- **Security/privacy gap:** Actor authorization, reason/target checks and privacy-safe projections are not runtime-proven.
- **Automated acceptance proof:** Authorization, command boundary, idempotency, audit and safe-read tests.
- **Operator-only residual:** Operator Admin UAT.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 12 — Web Cabinet

- **Primary RF step:** RF-21.
- **Accepted semantic baseline:** Web Cabinet owns presentation/projection only; no direct foreign writes.
- **Current tracked implementation contour:** Semantic read models, auth context, commands and deterministic tests; no UI runtime.
- **Persistence gap:** Session, projection and notification-history persistence are absent.
- **Process/runtime gap:** Server-rendered FastAPI/Jinja2 UI runtime is absent.
- **API/command gap:** Safe command boundary and projections are absent.
- **Integration gap:** Owning-module reads/commands and session integration are not wired.
- **Provider gap:** NONE.
- **Observability/recovery gap:** Safe diagnostics, session recovery and UI operation proof are absent.
- **Security/privacy gap:** No-direct-write, session, authorization and tracking-free runtime proof is absent.
- **Automated acceptance proof:** Synthetic server-rendered cabinet, session, projections and command-boundary tests.
- **Operator-only residual:** Operator Web Cabinet UAT.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

### 13 — Filter Catalog & Builder

- **Primary RF step:** RF-22.
- **Accepted semantic baseline:** Immutable evidence-bound catalog versions; unsupported/stale/ambiguous fields blocked; candidate only; Beacon owns actual configuration.
- **Current tracked implementation contour:** Provider-neutral catalog, evidence, builder validation and FC-08 tests; no publication runtime.
- **Persistence gap:** Immutable catalog versions and evidence metadata are absent.
- **Process/runtime gap:** Catalog publication and validation runtime are absent.
- **API/command gap:** Server validation and catalog UI/API are absent.
- **Integration gap:** Candidate-to-Beacon acceptance boundary is not wired.
- **Provider gap:** Missing optional credentials disable provider; exact live catalog evidence remains operator-only.
- **Observability/recovery gap:** Version traceability, stale evidence and rollback proof are absent.
- **Security/privacy gap:** Evidence provenance, safe metadata and unsupported-field blocking are not runtime-proven.
- **Automated acceptance proof:** FC-08 plus catalog persistence, server validation, UI/API and Beacon-integration tests.
- **Operator-only residual:** Exact live catalog evidence and eligibility proof.
- **Gap status:** GAP_ACCEPTED_SEMANTIC_ONLY; GAP_OPEN_AUTOMATABLE categories: persistence, process/runtime, API/command, integration, observability/recovery and security/privacy.

## 6. Cross-module dependency and wiring gaps

| Edge ID | Producer/owner | Consumer | Public boundary | Current gap | Primary RF step | Cross-cutting RF proof | Forbidden shortcut | Status |
|---|---|---|---|---|---|---|---|---|
| E01 | Platform contracts | All modules | Public contracts/primitives | Runtime assembly and shared persistence wiring absent | RF-10 | RF-23 | Private implementation imports | GAP_OPEN_AUTOMATABLE |
| E02 | Identity | Entitlements | Verified `account_id` context | Account context runtime wiring absent | RF-11 | RF-23 | UI state as authority | GAP_OPEN_AUTOMATABLE |
| E03 | Identity | Telegram/MAX/Web/Admin | Verified account context | Provider/UI context adapters absent | RF-11 | RF-23 | Provider identity as account authority | GAP_OPEN_AUTOMATABLE |
| E04 | Entitlements | Beacon lifecycle/cadence | Authorization and cadence service | Entitlement authorization wiring absent | RF-12 | RF-23 | Payment evidence as entitlement | GAP_OPEN_AUTOMATABLE |
| E05 | Beacon | Parser scan input | Owned Beacon scan intent | Durable intent handoff absent | RF-13 | RF-23, RF-24 | Direct foreign-table writes | GAP_OPEN_AUTOMATABLE |
| E06 | Filter Catalog | Beacon override candidate only | Validated candidate contract | Candidate acceptance wiring absent | RF-22 | RF-23 | Candidate mutates Beacon directly | GAP_OPEN_AUTOMATABLE |
| E07 | Egress | Parser route/session boundary | Route lease/session contract | Route dispatch wiring absent | RF-16 | RF-23, RF-24 | Foreign proxy reuse | GAP_OPEN_AUTOMATABLE |
| E08 | Parser | Scan explicit result classes | Parser outcome contract | Explicit result-class handoff absent | RF-14 | RF-23, RF-24 | Route failure as parser success | GAP_OPEN_AUTOMATABLE |
| E09 | Scan | Notification generic newly-observed-listing event | Notification intent contract | Event emission/outbox handoff absent | RF-15 | RF-23, RF-24 | Incomplete scan advancing anchor | GAP_OPEN_AUTOMATABLE |
| E10 | Notification | Telegram/MAX/Web delivery/read projections | Generic outbox/delivery contract | Channel adapters and projections absent | RF-17 | RF-23, RF-24 | Provider acceptance as human read | GAP_OPEN_AUTOMATABLE |
| E11 | Admin | Owning module commands only | Authorized command contracts | Safe command routing absent | RF-20 | RF-23, RF-25 | Direct foreign-table writes | GAP_OPEN_AUTOMATABLE |
| E12 | Web | Owning module commands/read projections only | Cabinet projection/command contracts | UI wiring absent | RF-21 | RF-23, RF-24 | UI state as authority | GAP_OPEN_AUTOMATABLE |
| E13 | API transport | Application services | Transport DTO/public service boundary | API assembly and DTO mapping absent | RF-23 | RF-24 | Transport becoming authority | GAP_OPEN_AUTOMATABLE |
| E14 | Scheduler | Durable Scan due work | Durable work claim contract | Due-work scheduler absent | RF-15 | RF-23, RF-24 | Framework background task as durable queue | GAP_OPEN_AUTOMATABLE |
| E15 | Worker | PostgreSQL-backed leases/work/outbox | Lease/work/outbox services | Durable worker absent | RF-09 | RF-23, RF-24, RF-26 | In-memory durable queue | GAP_OPEN_AUTOMATABLE |
| E16 | Observability | Non-authoritative telemetry | Redacted telemetry boundary | Telemetry assembly absent | RF-26 | RF-25, RF-28 | Telemetry becoming domain authority | GAP_OPEN_AUTOMATABLE |
| E17 | Backup/recovery | Project-owned PostgreSQL/runtime only | Backup/restore and recovery runbook | Backup and restore proof absent | RF-26 | RF-27, RF-28 | Foreign resource reuse | GAP_OPEN_AUTOMATABLE |

## 7. External operator-only residuals

| Residual ID | External requirement | Automatic work that still proceeds | Disabled/readiness state | Operator evidence | Roadmap location | Status |
|---|---|---|---|---|---|---|
| R01 | Telegram token and live bot proof | Synthetic identity, fake provider, persistence and core delivery work | Provider disabled; core continues | Token presence and live bot acceptance | RF-18, RF-29 | PROVIDER_DISABLED_CONTINUE |
| R02 | MAX eligibility, token and live provider proof | Webhook model, validation, fake provider and core delivery work | Provider disabled; core continues | Eligibility, token and live provider record | RF-19, RF-29 | PROVIDER_DISABLED_CONTINUE |
| R03 | Avito live access and live parser proof | Synthetic parser, explicit outcomes and core scan wiring | Live traffic disabled until proof | Access and live parser result evidence | RF-14, RF-29 | GAP_EXTERNAL_OPERATOR_ONLY |
| R04 | Windows Egress Agent installation and live route proof | Simulator, protocol, packaging and route semantics | Host optional; automatic scope continues | Installation and live route record | RF-16, RF-29 | GAP_EXTERNAL_OPERATOR_ONLY |
| R05 | YooKassa sandbox credentials and live sandbox proof | Tariff, entitlement, reconciliation and disabled adapter work | Provider disabled; core continues | Sandbox credential availability and proof | RF-12, RF-29 | PROVIDER_DISABLED_CONTINUE |
| R06 | Operator Web Cabinet UAT | Automated UI/runtime and synthetic E2E work | UAT not yet recorded | Operator UAT record | RF-21, RF-29 | GAP_EXTERNAL_OPERATOR_ONLY |
| R07 | Operator Admin UAT | Automated command, audit and synthetic E2E work | UAT not yet recorded | Operator UAT record | RF-20, RF-29 | GAP_EXTERNAL_OPERATOR_ONLY |
| R08 | Final operator PASS/FAIL/NOT_AVAILABLE record | All automated final regression and evidence assembly | Record not yet created | Final operator record | RF-29, RF-30 | GAP_EXTERNAL_OPERATOR_ONLY |
| R09 | Production public ingress/DNS/TLS/legal launch gate | Local acceptance runtime and all Module 14 proof | Outside acceptance scope | Separate future launch evidence | Post-acceptance | GAP_DEFERRED_POST_ACCEPTANCE |

## 8. Unassigned-gap audit

The canonical modules inventoried are exactly 13. Primary module runtime mappings are exactly RF-10–RF-22. Later roadmap coverage rows are exactly RF-04–RF-30. Cross-module wiring records total exactly 17. External residual records total exactly 9. Automatically correctable gaps without an RF assignment: `0`. Known external residuals without an operator acceptance location: `0`. Direct foreign-module mutation authorizations: `0`. Live-provider calls authorized by this artifact: `0`. Production personal-data use authorized: `0`. Runtime mutations performed by RF-03-02: `0`. Unknown auto-work gaps discovered but unassigned: `0`.

Later RF work is not complete and no row is evidence of completion.

## 9. Evidence limitations

This artifact does not prove the final physical data model, PostgreSQL implementation, migrations from zero, API/worker/scheduler assembly, CI, Docker Compose, deployed E2E, security closure, backup/restore, server deployment, operator acceptance or production readiness. RF-03-03 consistency audit remains pending. RF-03 remains incomplete. RF-04 must not start before RF-03 closure and independent acceptance.

## 10. Remaining RF-03 artifacts

- RF-03-03: `CROSS_MODULE_CONSISTENCY_AUDIT_v1.0.md` — pending.
- RF-03 closure evidence/status transition — pending.

## 11. Current verdict

`RF-03_ACTIVE — CROSS_MODULE_RUNTIME_GAP_MATRIX_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`

RF-03-01 was accepted through corrective SHA `23e73707b14b220da98beade93ee2d13021ba1b9`. RF-03-03 is pending. RF-03 closure is pending. RF-04 is not started. No runtime mutation was performed. No `PRODUCTION_READY` claim is made.
