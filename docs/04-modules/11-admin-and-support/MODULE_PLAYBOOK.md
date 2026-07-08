# Маяк Авито — Admin & Support Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 22 of 24
**Дата:** 2026-07-08
**Модуль:** `11-admin-and-support`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Entitlements & Billing Module Playbook v1.0, Beacon Management Module Playbook v1.0, Scan Orchestration & Listing State Module Playbook v1.0, Egress Routing Module Playbook v1.0, Notification Delivery Module Playbook v1.0, Telegram Adapter Module Playbook v1.0, MAX Adapter Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0 and OPEN_DECISIONS.md.
**Не является:** admin panel implementation, support CRM, operator UI, privileged backend service, authorization implementation, impersonation policy, database schema, migration, audit-log storage implementation, product-code, runtime configuration, service, port, credential or permission to implement.

---

## 1. Назначение

Admin & Support владеет безопасной операторской поверхностью для чтения, объяснения и ограниченного выполнения support/admin actions через публичные контракты owning modules.

Модуль отвечает на вопросы:

- какие operator/support use cases допустимы как documentation boundary;
- как admin/support reads получают данные только через read models and public services;
- как protected support commands проходят Identity role/authorization, ownership/scope validation and audit;
- как operator actions do not bypass module ownership or write directly to business tables;
- как support work item, audit trail and explanation records are separated from domain state;
- как PII, secrets, provider payloads and operational details are minimized;
- как manual intervention remains explicit, reversible where policy permits and never hides root cause;
- как open decisions stay blocked rather than resolved by support workflow.

Модуль не создаёт UI, роли, БД, таблицы, сервисы, audit storage, production access or support tooling. Он фиксирует only semantic boundary.

## 2. Границы и владение

Admin & Support owns semantic mutation authority for:

- support case/work-item records;
- operator action request records;
- admin/support audit references;
- safe support notes and redacted diagnostic summaries;
- support escalation state;
- admin explanation/read-model projections;
- manual review/reconciliation coordination records;
- support-visible decision explanations;
- controlled support command envelopes before dispatch to owning modules.

It does not own:

- internal accounts, identities, roles, sessions or credentials;
- tariffs, subscriptions, entitlement grants or payment records;
- Beacon configuration, lifecycle or revisions;
- Parser extraction, provider response classification or listing candidates;
- Scan runs, observations, baseline/difference or listing state;
- Egress routes, agents, leases or transport state;
- generic Notification outbox, delivery attempts or delivery lifecycle;
- Telegram or MAX provider mapping, tokens or payloads;
- Web Cabinet sessions, customer UI state or web presentation state;
- Filter Catalog definitions;
- physical database schema, audit-log implementation or storage retention policy;
- legal/privacy policy or support staffing/permissions beyond documented gates.

Admin & Support never writes directly to another module’s authoritative state. It calls approved public commands/services and records safe support evidence around the action.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted module playbooks for Identity, Entitlements, Beacon, Scan, Egress, Notification, Telegram and MAX.
4. This playbook.
5. Future exact implementation task and accepted evidence.
6. Runtime evidence for one exact release/environment/operator action.

Admin/support report, screenshot, manual note, local server state or operator memory never overrides public GitHub docs or owning module records.

## 4. Confirmed decisions

1. Admin & Support is a boundary over public module services, not a bypass path into tables or internals.
2. Operator role, permission and actor context are owned by Identity & Access.
3. Role assignment is server-authorized and audited; UI flags, provider usernames, chat titles or local config do not authorize admin power.
4. Support reads use approved read models/projections with provenance and freshness indicators.
5. Protected support mutations are command envelopes sent to owning modules after authorization, scope validation, idempotency and audit.
6. Admin & Support does not own Account, Entitlement, Beacon, Scan, Egress, Notification, Telegram, MAX, Web Cabinet or Filter Catalog state.
7. Support notes are not authoritative business state.
8. Manual action must preserve causation, correlation, actor, target, reason and outcome references.
9. Admin tooling cannot close open decisions, invent tariffs, change retention, create provider credentials or approve runtime access.
10. Ambiguous evidence remains ambiguous and may create review/escalation work, not fabricated success.
11. Support correction fixes root cause through owning module contracts rather than editing downstream symptoms.
12. Customer-visible or operator-visible explanation must be redacted, scoped and safe.
13. Admin/support audit trail is append-style in semantics; historical records are not silently rewritten.
14. PII, provider secrets, raw tokens, private keys, passwords, one-time codes, shell history and raw provider payloads are excluded from ordinary support records.
15. Support impersonation, break-glass access, data export, deletion and retention behavior remain unselected until explicit policy.
16. Run 22 creates no admin UI, role implementation, database, migration, audit store, service, port, credential, secret, runtime or product-code.

## 5. Open decisions and blockers

Run 22 does not resolve:

- `OD-006` — exact phone+password and recovery policy;
- `OD-007` — when phone is required, if ever;
- `OD-008` — account merge policy;
- `OD-013` — retention/deletion of history, logs and personal data;
- `OD-014` — public site, screens and analytics;
- exact admin role taxonomy beyond server-assigned role boundary;
- exact support staffing and approval workflow;
- break-glass access policy;
- support impersonation or delegated login policy;
- customer data export policy;
- manual entitlement correction policy;
- manual Beacon correction policy;
- manual notification resend/suppression policy;
- manual route/agent intervention policy;
- exact support note visibility to customer;
- exact audit retention and tamper-evidence mechanism;
- exact admin UI surface, Web Cabinet integration or separate operator console;
- exact search/filter capabilities for support;
- exact rate limits and approval thresholds for operator actions;
- exact evidence attachments and file retention.

Open means blocked. No implementation, UI, role, database, audit store, policy default or manual operational action may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, queues, wire schemas or UI screens.

| Record | Purpose | Required boundary |
|---|---|---|
| `SupportCase` | Groups a customer/operator issue or investigation | not business state authority |
| `SupportWorkItem` | Actionable admin/support task | no direct domain write |
| `SupportActorContext` | Verified operator identity, role and scope reference | owned by Identity |
| `SupportSubjectReference` | Target account/Beacon/run/notification/provider object reference | scoped and redacted |
| `SupportEvidenceReference` | Safe pointer to relevant records/logs/reports | no secrets/raw payloads |
| `SupportExplanationRecord` | Human-readable reasoning/provenance for support | not mutation authority |
| `SupportCommandEnvelope` | Protected request to owning module public command | authorized, scoped, idempotent |
| `SupportActionAuditRecord` | Append-style record of attempted/completed operator action | actor/target/reason/outcome |
| `SupportEscalationRecord` | Escalation/manual review/reconciliation state | no fabricated resolution |
| `SupportReadModel` | Safe projection for operator/customer assistance | rebuildable/provenance-aware |

## 7. Semantic identifiers and scope

- `support_case_id` identifies one support case.
- `support_work_item_id` identifies one actionable support unit.
- `support_action_id` identifies one attempted operator action.
- `support_evidence_ref` identifies a safe evidence pointer, not raw material.
- `actor_account_id` references the operator account after Identity verification.
- `target_account_id`, `beacon_id`, `run_id`, `notification_outbox_item_id`, `notification_attempt_id`, `route_id` and provider references are used only through approved owning-module references.
- `correlation_id` and `causation_id` connect support records to owning-module outcomes.

Identifiers do not reveal secrets, private credentials, full provider payloads, raw phone/password/code values or unrelated personal data. Exact encoding remains future task scope.

## 8. Read boundary

Admin/support reads must preserve:

- verified operator actor context;
- role and scope authorization;
- ownership/tenant boundary;
- target object provenance;
- read-model freshness/staleness indicator;
- redaction of secrets and unnecessary personal data;
- safe error semantics for forbidden/foreign targets;
- explicit unknown/ambiguous state instead of guessed values.

Admin & Support may read:

- Identity public account/actor summaries;
- Entitlement effective-decision summaries;
- Beacon lifecycle/configuration summaries;
- Scan run/listing-state summaries;
- Egress readiness/route summary projections;
- Notification outbox/attempt/history summaries;
- Telegram/MAX adapter safe event/outcome projections;
- future Web Cabinet and Filter Catalog projections after their playbooks.

It must not read raw credentials, tokens, `.env`, shell history, private keys, process arguments, raw provider payloads, full personal data or foreign host resources.

## 9. Mutation boundary

Admin/support mutations are only protected command envelopes to owning modules.

Required gates:

1. verified support actor;
2. server-assigned role and explicit scope;
3. target ownership/scope validation;
4. policy gate for action family;
5. explicit reason and support case reference;
6. idempotency key and normalized fingerprint;
7. safe evidence references;
8. owning-module public command;
9. owning-module outcome;
10. append-style support audit record.

Rules:

- no direct table write;
- no direct provider call;
- no direct route/agent/service manipulation;
- no direct credential or secret access;
- no hidden correction without audit;
- no manual close of open decision;
- no mutation if policy is unresolved.

## 10. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `OpenSupportCaseCommand` | Create or replay a support case |
| `AddSupportEvidenceCommand` | Attach safe evidence reference to a case |
| `RecordSupportNoteCommand` | Add a redacted operator note |
| `RequestSupportReadCommand` | Read authorized support projection |
| `ExplainAccountStateQuery` | Explain account/identity summary via public Identity views |
| `ExplainBeaconStateQuery` | Explain Beacon lifecycle/configuration via public Beacon views |
| `ExplainScanStateQuery` | Explain scan/listing outcome via public Scan views |
| `ExplainNotificationStateQuery` | Explain outbox/attempt history via Notification views |
| `ExplainProviderAdapterStateQuery` | Explain Telegram/MAX adapter outcomes via safe projections |
| `CreateSupportActionRequestCommand` | Prepare protected action request to an owning module |
| `DispatchSupportCommandCommand` | Dispatch approved support command to owning module |
| `RecordSupportActionOutcomeCommand` | Record owning-module outcome and audit result |
| `EscalateSupportCaseCommand` | Escalate unresolved/ambiguous case |
| `CloseSupportCaseCommand` | Close case only with explicit outcome and evidence |

Mutation-capable inputs require common contract metadata, verified actor context, authorization, idempotency key and safe fingerprint.

## 11. Public output families

| Output family | Meaning |
|---|---|
| `SupportCaseOutcome` | created, replayed, updated, closed, rejected or ambiguous |
| `SupportReadOutcome` | authorized projection, redacted projection, forbidden, not-found-safe, stale or ambiguous |
| `SupportExplanationOutcome` | explained, partially-explained, blocked, stale, ambiguous or unsupported |
| `SupportCommandPreparationOutcome` | prepared, policy-blocked, unauthorized, target-forbidden, unsupported or ambiguous |
| `SupportCommandDispatchOutcome` | dispatched, replayed, rejected, failed, ambiguous or reconciliation-required |
| `SupportActionAuditOutcome` | recorded, replayed, conflict, rejected or manual-review-required |
| `SupportEscalationOutcome` | escalated, already-escalated, blocked, resolved or ambiguous |

Outputs remain framework, UI, database, provider and transport neutral.

## 12. Mandatory outcome classes

At minimum:

- `ACTOR_UNAUTHENTICATED`;
- `ACTOR_FORBIDDEN`;
- `TARGET_FORBIDDEN`;
- `READMODEL_STALE`;
- `EVIDENCE_REDACTED`;
- `SUPPORT_CASE_OPENED`;
- `SUPPORT_NOTE_RECORDED`;
- `SUPPORT_COMMAND_PREPARED`;
- `SUPPORT_COMMAND_POLICY_BLOCKED`;
- `SUPPORT_COMMAND_DISPATCHED`;
- `OWNING_MODULE_REJECTED`;
- `OWNING_MODULE_AMBIGUOUS`;
- `AUDIT_RECORDED`;
- `ESCALATION_REQUIRED`;
- `CASE_CLOSED_WITH_EVIDENCE`.

Exact wire codes and UI labels are not selected.

## 13. False-success prohibition

None of the following may become clean admin/support success:

- UI-visible admin button without server-side authorization;
- provider username, phone, chat title or display name as admin authority;
- stale read model treated as current authority;
- support note treated as domain mutation;
- manual note used to close open decision;
- direct table edit;
- direct credential/secret access;
- direct provider/bot/API request outside owning adapter;
- direct Egress route/service change;
- ambiguous owning-module outcome treated as completed;
- idempotency mismatch hidden as replay;
- failure masked by closing support case;
- personal data or raw provider payload stored as ordinary note;
- support action without audit evidence.

## 14. Identity & Access dependency

Identity & Access owns operator accounts, roles, sessions, actor validation and account-linking rules.

Admin & Support consumes:

- verified actor context;
- role and scope decisions;
- safe account summaries;
- identity-linking/support-safe explanations.

Rules:

- operator role is never client-supplied;
- admin rights are not derived from Telegram/MAX username or Web Cabinet UI;
- support cannot merge accounts until OD-008 is resolved;
- support cannot make phone required until OD-007 is resolved;
- break-glass/impersonation remains blocked until explicit policy.

## 15. Entitlements dependency

Entitlements & Billing owns tariffs, subscription, grants, manual access and future payment authority.

Admin & Support may later request controlled support action only through public entitlement commands after policy approval.

Rules:

- support cannot invent tariff period/price or payment behavior;
- support cannot silently grant access without approved manual-grant policy and audit;
- payment provider evidence is not entitlement authority until converted by Entitlements;
- OD-001–OD-005 remain open where applicable.

## 16. Beacon, Scan, Egress and Notification dependencies

Admin & Support may explain and coordinate:

- Beacon lifecycle/configuration evidence;
- Scan run/listing-state evidence;
- Egress route/agent readiness and ambiguity summaries;
- Notification outbox/attempt/delivery history summaries.

Rules:

- support does not edit Beacon configuration directly;
- support does not rewrite Scan observations, baseline or listing state;
- support does not create, revoke or extend Egress route leases;
- support does not resend notifications outside Notification Delivery contracts;
- failure in one module is fixed through owning-module root cause, not support-table override.

## 17. Telegram and MAX dependencies

Admin & Support may read safe provider adapter projections and explain adapter outcomes.

Rules:

- support does not access bot tokens or webhook secrets;
- support does not call Telegram/MAX APIs directly;
- support does not treat provider IDs as account IDs;
- provider ambiguity remains explicit;
- legal/partner/moderation evidence for MAX is not stored as public raw documents;
- provider-specific support action is routed through owning adapter contracts after approval.

## 18. Security, privacy and retention

- Support records contain minimum necessary data.
- Raw passwords, one-time codes, bot tokens, webhook secrets, private keys, `.env`, shell history and process arguments are forbidden.
- Raw provider payloads and full private-message archives are excluded from ordinary support notes.
- Personal data is redacted unless a future policy explicitly approves limited processing.
- Support evidence uses safe references, hashes/classes or redacted summaries.
- Audit records include actor, target, reason, policy reference, command, outcome and correlation.
- Retention/deletion/archive/compaction remain OD-013.
- Support cannot implement deletion/export/retention behavior by assumption.

## 19. Observability semantics

Future minimum safe signals:

- support case/work item/action IDs;
- operator actor reference and role/scope class;
- target type and safe reference;
- action family and policy gate;
- read model freshness;
- owning module called;
- outcome class;
- idempotency replay/conflict;
- escalation/reconciliation state;
- latency and safe reason code;
- no raw credentials, secrets, private payloads or unnecessary personal data.

A green admin UI, successful read model fetch or support case closure does not prove domain mutation success.

## 20. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity actor/role contracts;
- owning-module public read and command contracts;
- Notification, Telegram and MAX safe diagnostic projections;
- PostgreSQL/SQLAlchemy/Psycopg after physical schema approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- OpenTelemetry boundary after applicable instrumentation task.

Deferred/blocked:

- admin UI technology;
- operator console versus Web Cabinet integration;
- role taxonomy beyond approved boundary;
- audit storage implementation;
- support attachments storage;
- break-glass/impersonation;
- data export/deletion tooling;
- persistence schema/migrations;
- services/deploy/runtime.

No admin runtime is introduced by this playbook.

## 21. Fake dependencies and test doubles

Future approved fakes may model:

- `SupportActorVerifier`;
- `SupportAuthorizationPolicy`;
- `SupportCaseRepository`;
- `SupportAuditSink`;
- `IdentityReadGateway`;
- `EntitlementReadGateway`;
- `BeaconReadGateway`;
- `ScanReadGateway`;
- `EgressReadGateway`;
- `NotificationReadGateway`;
- `TelegramAdapterReadGateway`;
- `MaxAdapterReadGateway`;
- `OwningModuleCommandGateway`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic actors, accounts, Beacons, runs, routes, notification attempts, provider events, cases and support actions only. They do not prove production authorization, data retention, real admin UI, real provider behavior or live operations.

## 22. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-OWNER-FOREIGN-BEACON-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-BATCH-PARTIAL-001`;
- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`;
- `FX-EXT-AMBIGUOUS-001`.

Module-specific future semantic fixtures:

- `FX-ADMIN-ACTOR-UNAUTHENTICATED-001`;
- `FX-ADMIN-ACTOR-FORBIDDEN-001`;
- `FX-ADMIN-TARGET-FORBIDDEN-001`;
- `FX-ADMIN-READMODEL-STALE-001`;
- `FX-ADMIN-SUPPORT-CASE-OPENED-001`;
- `FX-ADMIN-SUPPORT-NOTE-REDACTED-001`;
- `FX-ADMIN-COMMAND-PREPARED-001`;
- `FX-ADMIN-COMMAND-POLICY-BLOCKED-001`;
- `FX-ADMIN-OWNING-MODULE-REJECTED-001`;
- `FX-ADMIN-OWNING-MODULE-AMBIGUOUS-001`;
- `FX-ADMIN-AUDIT-REQUIRED-001`;
- `FX-ADMIN-DIRECT-TABLE-WRITE-FORBIDDEN-001`;
- `FX-ADMIN-SECRET-ACCESS-FORBIDDEN-001`;
- `FX-ADMIN-BREAKGLASS-BLOCKED-001`;
- `FX-ADMIN-IMPERSONATION-BLOCKED-001`;
- `FX-ADMIN-RETENTION-OD013-BLOCKED-001`;
- `FX-ADMIN-OPEN-DECISION-NOT-CLOSED-001`.

Run 22 creates no fixture files and executes no tests.

## 23. Acceptance Matrix coverage

Run 22 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-DATA-002`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, admin UI, role implementation, audit store, provider access, support action execution and deployment remain future gates and are not passed by this documentation run.

## 24. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral support case/action/audit records;
- implement synthetic deterministic authorization/read/command boundary tests;
- integrate Identity actor/role contracts;
- integrate owning-module safe read models;
- integrate protected command dispatch after module policies;
- add support audit persistence after schema/migration approval;
- add UI/API only after Web Cabinet/Admin surface decisions;
- add observability, idempotency and redaction evidence.

## 25. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create tables, migrations, ORM models or physical schemas;
- create admin UI, support CRM, services, ports, workers or schedulers;
- install dependencies or create lockfiles;
- create roles, sessions, impersonation, break-glass or privilege escalation;
- read or expose secrets, credentials, `.env`, shell history or process arguments;
- call Telegram/MAX/Avito/provider APIs;
- edit another module’s tables or authoritative state directly;
- grant entitlements or change tariffs outside Entitlements policy;
- merge accounts or require phone by support decision;
- rewrite Scan/Beacon/Notification/Egress state by manual note;
- invent retention/deletion/export policy;
- store raw provider payloads, tokens, cookies, secrets or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 26. Report and handoff requirements

Any future implementation/proof task touching Admin & Support must report:

- exact GitHub SHA and paths;
- module playbook version used;
- created/changed files and hashes;
- whether product-code, migrations, dependency files, database, runtime, admin UI, support service, role implementation, audit store or provider calls were created;
- exact tests and outputs;
- authorization/idempotency/audit/redaction evidence;
- secret and personal-data minimization evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 27. Roadmap after this playbook

1. Synchronize exact Run 22 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Run 23 — Web Cabinet Module Playbook.
4. Run 24 — Filter Catalog & Builder Module Playbook.
5. Final independent documentation audit and explicit owner decision before any product-code track.

This playbook is a prerequisite only and does not authorize implementation.

## 28. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `ADMIN-HISTORY-0001` | 2026-07-08 | Run 22 created Admin & Support Module Playbook v1.0 and fixed support cases, safe reads, protected commands, audit, escalation and redaction boundaries without implementation. | Public GitHub `main`; Run 22 publication commit; no runtime artifacts. |
