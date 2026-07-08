# Маяк Авито — Web Cabinet Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 23 of 24
**Дата:** 2026-07-08
**Модуль:** `12-web-cabinet`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Entitlements & Billing Module Playbook v1.0, Beacon Management Module Playbook v1.0, Scan Orchestration & Listing State Module Playbook v1.0, Notification Delivery Module Playbook v1.0, Telegram Adapter Module Playbook v1.0, MAX Adapter Module Playbook v1.0, Admin & Support Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, Target Model v0.1 and OPEN_DECISIONS.md.
**Не является:** web application implementation, frontend design, UI component library choice, session implementation, authentication implementation, public site launch, analytics implementation, database schema, migration, API route implementation, runtime configuration, service, port, credential, secret or permission to implement.

---

## 1. Назначение

Web Cabinet владеет user-facing web presentation boundary поверх уже утверждённых public module services.

Модуль отвечает на вопросы:

- как будущий веб-кабинет показывает клиенту аккаунт, Маяки, тарифные права, состояния сканов, уведомлений и provider channels without owning those records;
- как web session/presentation state remains separate from Identity account/session authority;
- как customer actions become public commands to owning modules;
- как web-specific forms, draft edits and screen-state drafts remain non-authoritative until accepted by owning module;
- как Telegram/MAX and Web Cabinet share the same internal account and public services rather than creating parallel customer databases;
- как read models expose provenance, freshness, redaction and safe error semantics;
- как future analytics/screen composition remains blocked by OD-014 rather than guessed.

Модуль не создаёт website, frontend, API routes, session store, auth mechanism, database, migrations, services, deploy or runtime. Он фиксирует semantic boundary only.

## 2. Границы и владение

Web Cabinet owns semantic mutation authority for:

- web presentation preferences and safe UI state after policy approval;
- draft form state before submission to owning modules;
- web navigation/read-model composition records;
- web display adapters for owning-module projections;
- user-facing explanation views;
- web command envelopes before dispatch to owning modules;
- safe web analytics event intent if later approved;
- session-presentation references that do not replace Identity sessions;
- web error/display state and client-visible support handoff references.

It does not own:

- internal accounts, identities, roles, authentication records or sessions;
- tariffs, subscription, entitlement grant or payment state;
- Beacon source URL, extracted snapshot, overrides, revisions or lifecycle;
- Parser extraction, Avito provider evidence or listing candidates;
- Scan runs, observations, baseline/difference or listing state;
- Egress routes, agents, leases or transport state;
- Notification events, outbox, attempts or delivery lifecycle;
- Telegram or MAX provider identity/update/mapping state;
- Admin & Support cases, audits or escalation records;
- Filter Catalog definitions;
- public marketing site content strategy;
- web analytics policy while OD-014 remains unresolved;
- physical database schema, migrations or deployment topology.

Web Cabinet never writes directly to another module’s authoritative state. It submits validated public commands and reads safe projections.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted module playbooks for Identity, Entitlements, Beacon, Scan, Notification, Telegram, MAX and Admin & Support.
4. Target Model v0.1 where it defines the future website and shared account principle.
5. This playbook.
6. Future exact implementation task and accepted evidence.
7. Runtime evidence for one exact release/environment/UI action.

A web screen, local browser state, support screenshot, provider username or customer statement never overrides owning-module state.

## 4. Confirmed decisions

1. Web Cabinet is a presentation and command boundary over public module services, not a second backend domain.
2. Identity & Access owns account, authentication, authorization, sessions and identity linking.
3. Telegram, MAX and Web Cabinet share the same internal account model; Web Cabinet must not create a parallel user database.
4. Beacon Management owns Beacon configuration/lifecycle; Web Cabinet may display and submit Beacon commands only through public contracts.
5. Entitlements & Billing owns tariff/subscription/grant decisions; Web Cabinet may display effective entitlements and payment/upgrade placeholders only as approved projections.
6. Scan Orchestration & Listing State owns scan/listing facts; Web Cabinet may display read models and explanations only.
7. Notification Delivery owns notification history; Telegram/MAX adapters own provider specifics.
8. Admin & Support owns support cases and operator actions; Web Cabinet may link to customer-facing support state only through approved public views.
9. Draft form state is not authoritative business state.
10. Client-side validation is usability only; server-side module validation remains authoritative.
11. Web UI cannot close open decisions, invent tariff values, choose retention, introduce analytics or define screen composition beyond approved boundaries.
12. Login/recovery, phone requirement and account merge are blocked by OD-006, OD-007 and OD-008 where applicable.
13. Future public-site screens and analytics are blocked by OD-014.
14. Retention, deletion/export and personal-data handling remain OD-013.
15. Run 23 creates no web app, route, component, package, session implementation, database, migration, analytics, service, port, credential, secret, deploy or runtime.

## 5. Open decisions and blockers

Run 23 does not resolve:

- `OD-001` — tariff period for Basic 990 ₽;
- `OD-002` — exact price, names and limits of later tariffs;
- `OD-003` — exact list of allowed intervals and change rules;
- `OD-004` — behavior after access expiration;
- `OD-005` — payment provider, refunds, recurring/manual payments;
- `OD-006` — phone+password and recovery policy;
- `OD-007` — when phone is required, if ever;
- `OD-008` — account merge policy;
- `OD-009` — first-stage editable Avito filters by category;
- `OD-013` — retention/deletion of history, logs and personal data;
- `OD-014` — public website screens and analytics depth;
- exact web UI screen map;
- exact frontend framework/package choices beyond Technical Baseline boundaries;
- exact routing/API surface;
- exact session storage mechanism;
- exact email/phone recovery flow;
- exact analytics events, consent, retention and reporting;
- exact public marketing pages;
- exact customer support visibility;
- exact web notification preferences and channel management.

Open means blocked. No implementation, UI, route, schema, analytics, session, payment, tariff display value or screen map may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, frontend components, API routes, ORM classes or wire schemas.

| Record | Purpose | Required boundary |
|---|---|---|
| `WebPresentationState` | Safe UI state for one customer session/context | not Identity session authority |
| `WebDraftFormState` | Unsaved customer edits before owning-module command | not Beacon/Entitlement authority |
| `WebReadModelComposition` | Combined projection for a screen/card | rebuildable from public services |
| `WebCommandEnvelope` | Customer action submitted to owning module | authorized, validated, idempotent |
| `WebNavigationReference` | Stable route/screen reference after UI decisions | no implementation route yet |
| `WebExplanationView` | Customer-facing explanation/provenance | redacted and safe |
| `WebSupportHandoffReference` | Link to support case/public support status | not support mutation authority |
| `WebAnalyticsIntent` | Future analytics event intent if approved | blocked by OD-014 and OD-013 |
| `WebErrorDisplayState` | Safe client-visible error/retry state | no leaked internals |
| `WebAccessibilityState` | Future UI accessibility preference/evidence | no business authority |

## 7. Semantic identifiers and scope

- `web_context_id` identifies one web presentation context.
- `web_draft_id` identifies one unsaved/draft interaction.
- `web_screen_ref` identifies future screen composition only after OD-014 is resolved.
- `account_id`, `beacon_id`, `scan_run_id`, `notification_outbox_item_id`, `notification_attempt_id`, `support_case_id` and provider references belong to owning modules.
- `correlation_id` and `causation_id` connect web actions to owning-module outcomes.

Identifiers do not reveal credentials, cookies, tokens, one-time codes, raw provider payloads or unnecessary personal data. Exact encoding remains future task scope.

## 8. Read boundary

Web Cabinet reads are safe projections, not direct table access.

Required properties:

- verified customer actor context from Identity;
- ownership/tenant scope;
- read-model provenance;
- freshness/staleness indicator;
- redaction and personal-data minimization;
- safe not-found/forbidden semantics;
- explicit unknown/ambiguous state;
- no raw credentials, tokens, provider payloads or support private notes.

Web Cabinet may later read:

- Identity safe account summary;
- Entitlements effective rights summary;
- Beacon list/detail/configuration summary;
- Scan run/listing-state summary;
- Notification history summary;
- Telegram/MAX channel summaries;
- Admin & Support customer-visible case status;
- Filter Catalog definitions after Run 24 acceptance.

## 9. Mutation boundary

Web mutations are customer command envelopes to owning modules.

Required gates:

1. verified customer actor;
2. ownership/scope validation;
3. public command schema;
4. client-side usability checks treated as non-authoritative;
5. server-side validation by owning module;
6. idempotency key and normalized fingerprint;
7. correlation/causation;
8. explicit owning-module outcome;
9. safe web display outcome.

Rules:

- no direct table write;
- no direct provider call;
- no direct entitlement grant/payment mutation;
- no direct Beacon/Scan/Notification mutation outside public commands;
- no hidden customer identity merge;
- no unapproved phone requirement;
- no analytics/event capture beyond future approved policy.

## 10. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `RequestWebCabinetViewQuery` | Fetch one authorized web composition projection |
| `StartWebDraftCommand` | Start or replay a draft customer interaction |
| `UpdateWebDraftCommand` | Update non-authoritative draft state |
| `SubmitWebCommandCommand` | Submit validated command envelope to owning module |
| `ExplainWebViewStateQuery` | Explain provenance/freshness/redaction of displayed state |
| `RequestBeaconWebSummaryQuery` | Read Beacon summary through Beacon public view |
| `SubmitBeaconWebCommandCommand` | Dispatch Beacon command after server validation |
| `RequestNotificationWebHistoryQuery` | Read notification history through Notification public view |
| `RequestChannelWebSummaryQuery` | Read Telegram/MAX channel state through adapter projections |
| `RequestSupportWebHandoffCommand` | Open/link customer-visible support handoff through Admin & Support |
| `RecordWebDisplayOutcomeCommand` | Record safe display/retry/error outcome if later approved |
| `RecordWebAnalyticsIntentCommand` | Future placeholder only after OD-014/OD-013 resolution |

Mutation-capable inputs require common contract metadata, verified actor context, authorization, idempotency key and safe fingerprint.

## 11. Public output families

| Output family | Meaning |
|---|---|
| `WebCabinetViewResult` | authorized projection, redacted projection, forbidden, not-found-safe, stale or ambiguous |
| `WebDraftOutcome` | created, replayed, updated, expired, invalid or discarded |
| `WebCommandSubmitOutcome` | submitted, replayed, rejected, forbidden, stale, ambiguous or reconciliation-required |
| `WebExplanationOutcome` | explained, partially-explained, blocked, stale, ambiguous or unsupported |
| `WebSupportHandoffOutcome` | opened, linked, blocked, unsupported, rejected or ambiguous |
| `WebDisplayOutcome` | displayed, redacted, stale-warning, blocked, retryable-error or safe-error |
| `WebAnalyticsIntentOutcome` | blocked, policy-approved-recorded, rejected or disabled |

Outputs remain framework, frontend, database, route and deployment neutral.

## 12. Mandatory outcome classes

At minimum:

- `WEB_ACTOR_UNAUTHENTICATED`;
- `WEB_ACTOR_FORBIDDEN`;
- `WEB_TARGET_FORBIDDEN`;
- `WEB_READMODEL_STALE`;
- `WEB_DRAFT_CREATED`;
- `WEB_DRAFT_EXPIRED`;
- `WEB_DRAFT_NOT_AUTHORITY`;
- `WEB_COMMAND_SUBMITTED`;
- `WEB_COMMAND_REPLAYED`;
- `OWNING_MODULE_REJECTED`;
- `OWNING_MODULE_AMBIGUOUS`;
- `WEB_DISPLAY_REDACTED`;
- `WEB_SAFE_ERROR`;
- `WEB_SUPPORT_HANDOFF_CREATED`;
- `WEB_ANALYTICS_POLICY_BLOCKED`.

Exact wire codes, route names, UI labels and component states are not selected.

## 13. False-success prohibition

None of the following may become clean web success:

- client-side validation without owning-module acceptance;
- draft state treated as saved Beacon/Entitlement/Notification state;
- browser session/local storage treated as Identity session authority;
- UI role flag treated as authorization;
- stale read model presented as current authority;
- hidden account merge;
- phone requirement invented by UI;
- tariff/payment value invented by UI;
- support case link treated as domain correction;
- analytics event captured without policy;
- provider channel display treated as provider delivery success;
- direct table edit or direct provider call;
- ambiguous owning-module outcome displayed as completed;
- raw secret/personal/provider payload shown in UI.

## 14. Identity & Access dependency

Identity & Access owns account, authentication, sessions, roles and identity linking.

Web Cabinet consumes:

- verified customer actor context;
- safe account summary;
- session/authorization decisions;
- identity-linking challenge results after policy approval.

Rules:

- Web Cabinet does not implement auth by this playbook;
- Web Cabinet cannot require phone until OD-007 resolves;
- Web Cabinet cannot define phone+password/recovery until OD-006 resolves;
- Web Cabinet cannot merge accounts until OD-008 resolves;
- Telegram/MAX provider identity remains adapter evidence, not web login authority by itself.

## 15. Entitlements dependency

Entitlements & Billing owns effective rights, tariffs, grants and payment authority.

Web Cabinet may later display:

- current effective rights;
- limits and upgrade prompts after tariff decisions;
- payment status only after provider/payment policy approval.

Rules:

- Web Cabinet cannot invent tariff names, prices, intervals or limits;
- Web Cabinet cannot grant access;
- Web Cabinet cannot create payments;
- OD-001–OD-005 remain open where applicable.

## 16. Beacon, Scan and Notification dependencies

Web Cabinet may later present and submit commands for:

- Beacon list/detail/configuration through Beacon contracts;
- scan run/listing-state summaries through Scan contracts;
- notification history/preferences through Notification contracts;
- channel summaries through Telegram/MAX adapter projections.

Rules:

- Web Cabinet does not own Beacon state;
- Web Cabinet does not edit extracted snapshot or revisions directly;
- Web Cabinet does not rewrite Scan observations or listing history;
- Web Cabinet does not create notification delivery attempts directly;
- Web Cabinet does not call Telegram/MAX providers.

## 17. Admin & Support dependency

Web Cabinet may expose customer-facing support handoff/status only through Admin & Support public views.

Rules:

- Web Cabinet does not own support cases;
- Web Cabinet does not expose operator notes or private audit records;
- Web Cabinet does not create admin actions;
- customer support visibility remains policy-gated.

## 18. Filter Catalog dependency

Filter Catalog & Builder is Run 24 and remains reserved until accepted.

Rules:

- Web Cabinet cannot invent filter catalog definitions;
- visual filter builder screens are blocked until Run 24 acceptance and later exact task;
- OD-009 remains unresolved;
- Web Cabinet may only state that future builder uses the same Beacon configuration model.

## 19. Security, privacy and retention

- Web Cabinet stores no raw passwords, one-time codes, bot tokens, webhook secrets, private keys, `.env`, provider payloads or unnecessary personal data by this playbook.
- Browser-visible data is minimized and redacted.
- Error messages do not reveal foreign object existence, internals, stack traces, provider payloads or secrets.
- Drafts expire by future approved policy; no value is selected here.
- Analytics, consent, retention, deletion/export and personal-data policy remain OD-013/OD-014.
- Web forms treat all user input as untrusted.
- External strings never become shell commands.

## 20. Observability semantics

Future minimum safe signals:

- web context/draft/action IDs;
- actor/account reference;
- target type and safe reference;
- owning module called;
- read-model freshness;
- command idempotency replay/conflict;
- display outcome class;
- support handoff state;
- analytics policy-blocked/disabled state;
- safe reason code and latency;
- no credentials, tokens, cookies, raw provider payloads or unnecessary personal data.

A rendered screen, green button, successful client validation or browser route does not prove owning-module success.

## 21. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity actor/session/authorization contracts;
- owning-module public read and command contracts;
- Admin & Support customer-visible support projection;
- Filter Catalog definitions after Run 24 acceptance;
- FastAPI/Pydantic/HTTPX only where later exact backend task authorizes;
- PostgreSQL/SQLAlchemy/Psycopg after physical schema approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- OpenTelemetry boundary after applicable instrumentation task.

Deferred/blocked:

- frontend framework and UI component library;
- route map and page composition;
- web auth/session implementation;
- analytics implementation;
- public marketing site;
- payment UI/provider integration;
- persistence schema/migrations;
- services/deploy/runtime.

No web runtime is introduced by this playbook.

## 22. Fake dependencies and test doubles

Future approved fakes may model:

- `WebActorVerifier`;
- `WebAuthorizationPolicy`;
- `WebDraftStore`;
- `WebReadCompositionGateway`;
- `IdentityReadGateway`;
- `EntitlementReadGateway`;
- `BeaconReadGateway`;
- `BeaconCommandGateway`;
- `ScanReadGateway`;
- `NotificationReadGateway`;
- `TelegramAdapterReadGateway`;
- `MaxAdapterReadGateway`;
- `SupportReadGateway`;
- `OwningModuleCommandGateway`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic accounts, Beacons, scans, notifications, provider states, support cases, drafts and display states only. They do not prove real web authentication, browser behavior, analytics, payments, deployment or production security.

## 23. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-OWNER-FOREIGN-BEACON-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`.

Module-specific future semantic fixtures:

- `FX-WEB-ACTOR-UNAUTHENTICATED-001`;
- `FX-WEB-ACTOR-FORBIDDEN-001`;
- `FX-WEB-TARGET-FORBIDDEN-001`;
- `FX-WEB-READMODEL-STALE-001`;
- `FX-WEB-DRAFT-NOT-AUTHORITY-001`;
- `FX-WEB-DRAFT-EXPIRED-001`;
- `FX-WEB-COMMAND-SUBMITTED-001`;
- `FX-WEB-OWNING-MODULE-REJECTED-001`;
- `FX-WEB-OWNING-MODULE-AMBIGUOUS-001`;
- `FX-WEB-HIDDEN-MERGE-FORBIDDEN-001`;
- `FX-WEB-PHONE-REQUIRED-OD007-BLOCKED-001`;
- `FX-WEB-TARIFF-OD001-BLOCKED-001`;
- `FX-WEB-ANALYTICS-OD014-BLOCKED-001`;
- `FX-WEB-RETENTION-OD013-BLOCKED-001`;
- `FX-WEB-FILTER-CATALOG-RUN24-BLOCKED-001`;
- `FX-WEB-SECRET-REDACTION-001`;
- `FX-WEB-SAFE-ERROR-001`;
- `FX-WEB-NO-SECOND-USER-DB-001`.

Run 23 creates no fixture files and executes no tests.

## 24. Acceptance Matrix coverage

Run 23 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-DATA-002`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, frontend, web auth/session, analytics, payment UI, route implementation, API implementation and deployment remain future gates and are not passed by this documentation run.

## 25. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral web read/command/draft records;
- implement synthetic deterministic authorization/read/command boundary tests;
- integrate Identity actor/session contracts;
- integrate owning-module safe read models;
- integrate Beacon command submission through public contracts;
- add web drafts and display-state persistence after schema/migration approval;
- add UI/API routes only after screen and route decisions;
- add analytics only after OD-014/OD-013 resolution;
- add observability, idempotency and redaction evidence.

## 26. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create frontend, pages, routes, API handlers or UI components;
- create tables, migrations, ORM models or physical schemas;
- create sessions, auth, recovery, account merge or phone requirement;
- install dependencies or create lockfiles;
- create analytics, tracking, consent or reporting implementation;
- create payment UI or payment provider calls;
- call Telegram/MAX/Avito/provider APIs;
- edit another module’s tables or authoritative state directly;
- grant entitlements or change tariffs outside Entitlements policy;
- invent public website screen map or analytics depth;
- invent filter catalog definitions or visual builder behavior before Run 24;
- store raw provider payloads, tokens, cookies, secrets or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 27. Report and handoff requirements

Any future implementation/proof task touching Web Cabinet must report:

- exact GitHub SHA and paths;
- module playbook version used;
- created/changed files and hashes;
- whether product-code, frontend, API routes, migrations, dependency files, database, runtime, session/auth implementation, analytics, payment UI or provider calls were created;
- exact tests and outputs;
- authorization/idempotency/redaction/freshness evidence;
- secret and personal-data minimization evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 28. Roadmap after this playbook

1. Synchronize exact Run 23 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Run 24 — Filter Catalog & Builder Module Playbook.
4. Final independent documentation audit and explicit owner decision before any product-code track.

This playbook is a prerequisite only and does not authorize implementation.

## 29. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `WEB-HISTORY-0001` | 2026-07-08 | Run 23 created Web Cabinet Module Playbook v1.0 and fixed web presentation, draft, read-model composition, command envelope, support handoff, analytics-blocking and redaction boundaries without implementation. | Public GitHub `main`; Run 23 publication commit; no runtime artifacts. |
