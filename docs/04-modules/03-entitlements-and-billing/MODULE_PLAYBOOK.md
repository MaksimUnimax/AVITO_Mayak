# Маяк Авито — Entitlements & Billing Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 14 of 24
**Дата:** 2026-07-07
**Модуль:** `03-entitlements-and-billing`
**Основание:** Architecture Baseline v1.1, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Technical Baseline v1.0, Acceptance Matrix v1.1, Target Model v0.1 as DRAFT context and OPEN_DECISIONS.md.
**Не является:** product-code, tariff approval, payment-provider selection, subscription implementation, billing engine, payment integration, physical database schema, migration, executable test, runtime configuration or permission to implement.

---

## 1. Назначение

Entitlements & Billing владеет серверной политикой доступа к возможностям продукта: tariff definitions, subscriptions, entitlement grants, manual access, future payment records and any later approved usage-consumption records.

Модуль отвечает на вопрос «какие действия и лимиты разрешены конкретному `account_id` в данный момент» и возвращает объяснимое effective entitlement decision. UI, adapters, Beacon Management, scheduler and Admin do not calculate tariff rights independently.

## 2. Границы и non-ownership

Entitlements & Billing owns:

- `TariffDefinition`;
- `Subscription`;
- `EntitlementGrant`;
- `ManualAccessGrant`;
- effective entitlement decision semantics;
- future `PaymentRecord` and `PaymentEvent` after approved provider/policy gates;
- future `UsageCounter` or equivalent only after separate approval;
- audit references for protected entitlement mutations.

It does not own:

- Account, identity, role, session or credential state;
- Beacon configuration, lifecycle or listing history;
- parser, route, scan or notification state;
- provider-specific payment SDK payload mapping before provider approval;
- Telegram/MAX/Web/Admin presentation state;
- refunds, recurrence, tariff period or expiry policy while OD-001–OD-005 are open.

Other modules request an entitlement decision through approved contracts and never mutate owned billing state directly.

## 3. Confirmed decisions

1. Entitlement checks are server-side business rules, not hidden buttons or client-side flags.
2. `account_id` is the ownership scope for account entitlements; provider identities do not replace it.
3. Tariff, subscription, entitlement, manual grant, payment record and payment event remain semantically distinct.
4. A payment-provider response is external evidence and never grants access by itself.
5. Entitlement mutation requires verified actor context, authorization, ownership/scope validation, idempotency, explicit commit point and auditable outcome.
6. Manual access requires actor, reason, scope, effective interval and audit reference.
7. Beacon Management and scheduler consume an effective decision; they do not duplicate tariff tables or independently infer access.
8. A future payment provider is a sub-boundary of this module, not a new business-domain owner.
9. DRAFT product values are not implementation defaults until accepted through governance.

## 4. DRAFT product context — not approved defaults

Target Model v0.1 currently describes candidate product values:

- free: zero price, one active Beacon, city-only, three-hour interval;
- basic: stated price 990 ₽, five active Beacons, supported city/country-wide geography and intervals from five minutes;
- later paid levels: candidate increments of five Beacons.

These values remain DRAFT context because period, later tier prices/names/limits, exact intervals, expiry behavior and payment rules are unresolved. A future implementation task must not hard-code them as accepted defaults without an approved product/decision update.

## 5. Open decisions and blockers

Run 14 does not resolve:

- `OD-001` — period for the stated 990 ₽ Basic price;
- `OD-002` — price, names and limits of later tiers;
- `OD-003` — exact allowed intervals and change rules;
- `OD-004` — behavior after access expiry;
- `OD-005` — provider, refunds, recurrence and manual-payment rules;
- `OD-010` — country-wide availability by market;
- `OD-011` — safe minimum monitoring frequency;
- `OD-013` — retention of billing, audit and personal data;
- exact currency/money representation;
- proration, grace period and trial semantics;
- taxation, receipts, invoices and legal accounting boundary;
- dispute/chargeback handling;
- exact usage-counter semantics;
- exact role taxonomy for entitlement administration.

Open means blocked. No CLI, code, test or UI may fabricate a value.

## 6. Authoritative state

| Record | Purpose | Required boundary |
|---|---|---|
| `TariffDefinition` | Versioned policy definition | no fabricated product values; effective interval explicit |
| `Subscription` | Account relationship to a tariff lifecycle | distinct from payment and effective grant |
| `EntitlementGrant` | Explicit capability/limit grant | scoped to account, capability and effective interval |
| `ManualAccessGrant` | Protected operator-created grant | actor, reason, scope, interval and audit required |
| `PaymentRecord` | Future normalized payment business record | only after provider/policy gates |
| `PaymentEvent` | Future verified normalized provider event | raw provider payload is not authority |
| `UsageCounter` | Future entitlement-consumption evidence | blocked until exact semantics approved |
| `EffectiveEntitlementDecision` | Explainable evaluated decision | derived result, not independent authority |

## 7. Entitlement capability families

Exact capability names and schemas remain future task scope. A tariff or grant may eventually govern:

- active Beacon count;
- allowed scan interval class;
- supported geography class;
- supported filter/edit capability class;
- account-level feature access;
- administrative/manual exception scope.

No capability receives a numeric/default value in this playbook unless separately approved.

## 8. Public input families

| Input family | Purpose |
|---|---|
| `GetEffectiveEntitlementsQuery` | Read effective account capabilities and limits |
| `EvaluateEntitlementRequest` | Decide whether one proposed action is allowed |
| `ListTariffDefinitionsQuery` | Read approved tariff definitions visible to caller |
| `AssignSubscriptionCommand` | Future protected assignment after product policy gates |
| `ChangeSubscriptionCommand` | Future protected transition after compatibility/expiry gates |
| `CancelSubscriptionCommand` | Future transition without guessing post-expiry behavior |
| `CreateManualAccessGrantCommand` | Create protected time/scope-bound grant |
| `RevokeManualAccessGrantCommand` | Revoke or close a protected grant |
| `RecordVerifiedPaymentEventCommand` | Future normalized provider-event ingestion after verification |
| `ReconcilePaymentEffectCommand` | Resolve ambiguous external payment effect before retry |
| `RecordUsageConsumptionCommand` | Future idempotent consumption record after approval |

Mutation-capable inputs require idempotency key, actor context and explicit account/scope metadata.

## 9. Public output families

| Output family | Meaning |
|---|---|
| `EffectiveEntitlementsResult` | Effective capabilities, limits, provenance and evaluation time |
| `EntitlementDecisionOutcome` | allowed, denied, blocked, expired, ambiguous or unsupported |
| `SubscriptionOutcome` | assigned, changed, cancelled, pending, blocked or conflict |
| `ManualAccessGrantOutcome` | created, replayed, revoked, expired, rejected or conflict |
| `PaymentEventOutcome` | verified-recorded, rejected, duplicate, ambiguous or reconcile-required |
| `PaymentReconciliationOutcome` | confirmed, rejected, unresolved or manual-review-required |
| `UsageConsumptionOutcome` | accepted, denied, replayed, conflict or unavailable |

Outputs remain transport, framework, ORM and provider neutral.

## 10. Public event families

Events may be emitted only after the owning mutation reaches its defined commit point:

- `TariffDefinitionPublished`;
- `SubscriptionStateChanged`;
- `EntitlementGrantChanged`;
- `ManualAccessGranted`;
- `ManualAccessRevoked`;
- future `PaymentEventRecorded`;
- future `PaymentReconciliationRequired`.

Events are immutable facts, not commands and not provider payloads.

## 11. Authorization boundary

- A client may read only entitlements visible for its own verified `account_id`.
- Entitlement evaluation for a protected account action requires verified actor/account context.
- Tariff definition, subscription, manual access and payment mutation require approved server-side role/scope.
- Telegram/MAX/Web UI flags, usernames and provider display values are not authorization.
- Admin & Support requests protected actions through public commands and does not write billing state directly.
- System-initiated transition must identify its service actor class and causation.

## 12. Evaluation semantics

An effective entitlement decision must be deterministic for the same authoritative state and evaluation time policy and must expose safe provenance:

1. validate request and contract version;
2. establish actor/account scope;
3. load applicable authoritative tariff/subscription/grant state;
4. reject fabricated or unresolved defaults;
5. evaluate active effective intervals;
6. combine grants only by an approved precedence policy;
7. return explicit allowed/denied/blocked/ambiguous result;
8. include safe reason codes and source references;
9. do not mutate foreign module state.

Exact precedence among tariff, subscription and manual grants remains a future contract/task detail and must be explicit before implementation.

## 13. Payment boundary

No payment integration is authorized by Run 14.

Future payment flow must preserve:

- provider-specific verification before trust;
- normalization into internal semantic records;
- stable provider event identity where officially available;
- idempotency before duplicate internal effect;
- explicit distinction among sent, confirmed, rejected and ambiguous effect;
- reconcile-first behavior for unknown commit state;
- no entitlement grant before server-authorized business transition;
- raw provider payload minimization/redaction;
- refund, recurrence and cancellation behavior only after OD-005 resolution.

## 14. Manual access

A manual access grant requires:

- target `account_id`;
- actor context and authorized role scope;
- safe reason code and optional protected note reference;
- exact capability/scope;
- effective start/end or explicitly approved open interval;
- idempotency key;
- commit point;
- audit outcome;
- revocation/expiry semantics.

A chat message, UI toggle or direct database edit is not a valid grant.

## 15. Idempotency and commit points

Idempotency is mandatory for entitlement/manual-access/subscription/payment mutations.

Required behavior:

- same key + same request + terminal outcome → return original outcome, no second effect;
- same key + different fingerprint → `IDEMPOTENCY_MISMATCH`;
- missing key for required mutation → reject before effect;
- ambiguous provider effect → reconcile first;
- success event only after authoritative state commit.

Each future command must define owner, intended effect, commit point, visible pre-commit state, interruption state, reconciliation and compensation/roll-forward boundary.

## 16. Errors and reconciliation

Applicable error categories include:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`;
- `FORBIDDEN`;
- `NOT_FOUND`;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

A payment failure is not “no entitlement change confirmed” unless that exact outcome is proven. Unknown external effect is explicit and blocks blind retry.

## 17. Dependencies

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity & Access verified actor/account/role context;
- Pydantic v2 at serialization/validation boundaries;
- FastAPI only at entrypoint transport boundary;
- SQLAlchemy/Psycopg/Alembic only after physical database gates;
- PostgreSQL authoritative records after schema approval;
- HTTPX only inside a future approved payment adapter;
- pytest/pytest-asyncio/RESpx for deterministic tests;
- OpenTelemetry instrumentation under approved telemetry boundaries.

Forbidden leakage:

- provider SDK types in public contracts;
- raw payment payload as entitlement state;
- ORM/session objects in public interfaces;
- direct Beacon/UI billing table access;
- credentials, card data or raw payment access material in fixtures/reports.

## 18. Fake dependencies and test doubles

Future fakes may model:

- `IdentityActorContextProvider`;
- `TariffDefinitionRepository`;
- `SubscriptionRepository`;
- `EntitlementGrantRepository`;
- `ManualAccessGrantRepository`;
- `EffectiveEntitlementEvaluator`;
- `PaymentProviderAdapter` only after provider approval;
- `PaymentEventVerifier` only after official evidence;
- `UsageCounterStore` only after semantics approval;
- `AuditSink`;
- `Clock`;
- `IdGenerator`.

Fakes use synthetic accounts/events only and never prove provider production behavior.

## 19. Required fixtures and test vectors

Minimum fixture IDs:

- `FX-EB-OWN-ACCOUNT-DECISION-001`;
- `FX-EB-FOREIGN-ACCOUNT-FORBIDDEN-001`;
- `FX-EB-NO-FABRICATED-TARIFF-001`;
- `FX-EB-PAYMENT-NOT-ENTITLEMENT-001`;
- `FX-EB-MANUAL-GRANT-AUTHORIZED-001`;
- `FX-EB-MANUAL-GRANT-REPLAY-001`;
- `FX-EB-MANUAL-GRANT-MISMATCH-001`;
- `FX-EB-MANUAL-GRANT-EXPIRED-001`;
- `FX-EB-CONFLICTING-GRANTS-001`;
- `FX-EB-LIMIT-ALLOW-001`;
- `FX-EB-LIMIT-DENY-001`;
- `FX-EB-PAYMENT-DUPLICATE-001`;
- `FX-EB-PAYMENT-AMBIGUOUS-RECON-001`;
- `FX-EB-OD001-BLOCKED-001`;
- `FX-EB-OD004-BLOCKED-001`;
- `FX-EB-REDACTION-001`.

Run 14 creates no fixture files.

## 20. Acceptance Matrix coverage

Run 14 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-DATA-001`, `AM-DATA-006`, `AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004` where applicable;
- `AM-EXT-001`–`AM-EXT-004` for future payment adapter;
- `AM-MIG-009`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Rows requiring provider, runtime, state, migration or reconciliation execution remain future gates.

## 21. Allowed future changes

A later exact task may:

- create Entitlements & Billing package skeleton inside approved source layout;
- define transport-neutral semantic contracts and synthetic fixtures;
- implement effective entitlement evaluation using only approved tariff/grant values;
- implement manual grants with authorization/idempotency/audit;
- integrate Beacon Management through an entitlement decision contract;
- add persistence after physical schema/migration gates;
- add payment adapter only after OD-001–OD-005, official provider evidence and a dedicated task.

## 22. Forbidden changes

Without new accepted decisions/tasks, this module must not:

- hard-code DRAFT tariff values as accepted defaults;
- assume 990 ₽ is monthly;
- invent future tier names, prices or limits;
- choose payment provider, refunds, recurrence, manual-payment or expiry behavior;
- grant entitlement directly from provider response;
- let UI/adapters/Beacon Management write billing state;
- store card data, credentials or raw provider access material;
- create product-code, dependency file, lockfile, executable tests, fixture files, migrations, database, payment account, provider call, Docker/CI/CD, service, port, deploy or runtime configuration.

## 23. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `EB-01` | Semantic contracts and synthetic fixtures | `NOT_STARTED` | Platform/Identity primitives and exact task |
| `EB-02` | Effective entitlement evaluation | `BLOCKED` | approved tariff/capability values and precedence |
| `EB-03` | Manual access grants | `NOT_STARTED` | exact authorization scope and task |
| `EB-04` | Subscription lifecycle | `BLOCKED` | OD-001, OD-002 and OD-004 |
| `EB-05` | Usage counters/limit consumption | `BLOCKED` | exact semantics and affected module contracts |
| `EB-06` | Beacon Management integration | `NOT_STARTED` | Run 15 contract acceptance |
| `EB-07` | Payment provider adapter | `BLOCKED` | OD-005 and current official provider evidence |
| `EB-08` | Payment reconciliation/refunds | `BLOCKED` | provider, refund and recurrence policy |
| `EB-09` | Persistence and migrations | `BLOCKED` | physical schema and migration gates |
| `EB-10` | Full evidence/handoff | `NOT_STARTED` | applicable subtasks complete |

## 24. Task packet requirements

A future task must include exact paths, stable ID, parent SHA, allowed/forbidden scope, approved tariff/capability inputs, authorization, idempotency, commit points, reconciliation, rollback/roll-forward, fixtures, matrix rows, static/runtime checks, evidence format and final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 25. Report and handoff

A future implementation report must include:

- task/iteration ID and exact commit SHA;
- changed paths;
- contract versions and owned state touched;
- decisions and references used;
- fixtures/matrix rows and exact results;
- idempotency/authorization/commit-point/reconciliation evidence;
- sensitive-data redaction confirmation;
- migration/runtime evidence only when explicitly in scope;
- prohibited-artifact check;
- known blockers and next safe task;
- exact final marker for independent review.

## 26. Acceptance criteria

The playbook is acceptable only when:

- owned and foreign state are explicit;
- entitlement, subscription and payment semantics remain distinct;
- payment response is not access authority;
- DRAFT tariff values are not promoted to implementation defaults;
- OD-001–OD-005 remain open;
- authorization, account scope, idempotency, commit point and reconciliation are explicit;
- dependencies/fakes, fixtures and matrix rows are named;
- roadmap does not authorize implementation;
- no code, dependency, lock, test, fixture file, migration, database, provider integration, Docker/CI/CD, deploy/runtime, service, port or sensitive access material is created;
- GitHub publication and exact server synchronization are independently verified.

## 27. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### EB-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 14 initial tariff, entitlement, subscription, manual-access, usage-limit and future payment boundaries defined.
- DRAFT tariff context remains non-authoritative for implementation.
- OD-001–OD-005 remain unresolved.
- No implementation or payment artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
