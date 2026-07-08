# Маяк Авито — Module 03 Entitlements & Billing Full Evidence Handoff v1.0

**Статус:** MODULE 03 SEMANTIC SCOPE COMPLETE / RUNTIME GATES BLOCKED  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Accepted module SHA:** `81b4754a2097503542d84fcb153d0f08817e30be`

## 1. Purpose

Summarize accepted module 03 state, completed semantic scope, accepted evidence, blocked runtime gates, open decisions and handoff guidance for later modules.

This document is evidence/handoff only. It does not implement product features and it does not authorize runtime/payment/persistence/Admin UI/Web Cabinet UI work.

## 2. Source-of-truth basis

- GitHub `main` is the source of truth.
- Module playbook: `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md`.
- Governance files used: `docs/00-governance/DECISION_LOG_APPEND_ONLY.md` and `docs/00-governance/OPEN_DECISIONS.md`.
- Module decision files used:
  - `docs/04-modules/03-entitlements-and-billing/OWNER_BILLING_DECISIONS_CAPTURE_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/ENTITLEMENT_PRECEDENCE_DECISION_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/MANUAL_ACCESS_AUTHORIZATION_DECISION_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/USAGE_COUNTERS_LIMIT_CONSUMPTION_DECISION_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/PAYMENT_PROVIDER_OFFICIAL_EVIDENCE_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/PAYMENT_RECONCILIATION_REFUNDS_DECISION_v1.0.md`
  - `docs/04-modules/03-entitlements-and-billing/ADMIN_TARIFF_MANAGEMENT_BOUNDARY_DECISION_v1.0.md`
- Accepted final semantic module SHA remains `81b4754a2097503542d84fcb153d0f08817e30be`.
- This handoff is subordinate to GitHub source-of-truth and does not supersede it.

## 3. Accepted roadmap state

| Roadmap step | Status | Accepted SHA / evidence | What was accepted | Still blocked |
|---|---|---|---|---|
| EB-00 current state / parallel-main verification | VERIFIED | `81b4754a2097503542d84fcb153d0f08817e30be` | Current main matched the accepted module state and the worktree was clean. | No module change; baseline only. |
| EB-01 owner billing decisions governance capture | ACCEPTED | `f37ca3c45869931edbf9ddfa11e7037228634d00` | Owner billing decisions for Free/Basic and first-stage billing policy. | Runtime/payment/persistence scope stays blocked. |
| EB-02 semantic contracts and synthetic fixtures | ACCEPTED | `4d31aaa209e50765475e574b619b2e5b423dfbed` | Semantic contract primitives and safe synthetic fixture basis. | Runtime/payment/persistence scope stays blocked. |
| EB-03 precedence governance and effective entitlement evaluation | ACCEPTED | `9c1ef8ed3b03f564919fd04e49a343a7bb4e9ba6` / `f61b0261a253773eb4aed8f8a6ae8f7c95eec1c1` | Precedence policy and deterministic effective entitlement evaluation. | Runtime evaluation, DB-backed evaluation and foreign-state mutation remain blocked. |
| EB-04 manual access authorization governance and semantic contracts | ACCEPTED | `bb0cb2fc22972550194bde3d58fdd659d93ba0bc` / `ac01d3aec45a2fea5ebd8a4ff44da7da1ec22574` | Manual access authorization policy and lifecycle semantics. | Admin UI, role runtime and persistence remain blocked. |
| EB-05 subscription lifecycle semantics | ACCEPTED | `b6e2d50202173288cca712bdea0ce198e308f55c` | Subscription lifecycle semantic contracts/tests. | Runtime billing and persistence remain blocked. |
| EB-06 usage counter decision and usage consumption semantics | ACCEPTED | `4b1ed544d3e1ff1134a73485553cb185ee78b5a8` / `ef6e4a1b7cc41d2dd6ccd506b7a16484f11a8342` | Approved counter families and deterministic usage-consumption semantics. | Runtime quota decrement, DB usage store and non-approved counter families remain blocked. |
| EB-07 Beacon Management integration gate and semantic integration | READ-ONLY VERIFIED | no commit; base remained `ef6e4a1b7cc41d2dd6ccd506b7a16484f11a8342`; semantic integration `92fc55dcc36624705ad2c9e8b2f5adb8885645d7` | Gate verification and Beacon integration semantics. | Beacon mutation and runtime integration remain blocked. |
| EB-08 provider evidence capture and provider boundary semantics | ACCEPTED | `3355994d5c2ab938fcc7123feac8833995e5e2af` / `7522faf51be63b0037205e5c2e59fd88324c83e2` | Official provider evidence and provider-boundary semantics. | Provider runtime integration, SDK/API calls and webhooks remain blocked. |
| EB-09 reconciliation/refunds governance and semantics | ACCEPTED | `e590fa974e4ce206653f8a091285fd7bb21f0ef8` / `f2ebc3082aaf1d982fc2dc081be91620ffc8b89a` | Reconciliation/refunds policy and deterministic semantic outcomes. | Runtime reconciliation/refunds, recurring billing and chargeback automation remain blocked. |
| EB-10 persistence/migrations gate | BLOCKED | `f2ebc3082aaf1d982fc2dc081be91620ffc8b89a`; `STOP_RETENTION_POLICY_REQUIRED` | Gate did not open. | Persistence, migrations and physical schema decisions remain blocked. |
| EB-11 Admin tariff-management boundary governance and semantics | ACCEPTED | `2cb4b8a912b9653285687505df2bcf441d8d2be9` / `81b4754a2097503542d84fcb153d0f08817e30be` | Admin tariff boundary policy and semantic contracts/tests. | Admin UI, Web Cabinet UI/runtime, role runtime, persistence and billing runtime remain blocked. |
| EB-12 this handoff | CREATED | evidence-only handoff on current main `81b4754a2097503542d84fcb153d0f08817e30be` | Final evidence/handoff summary for module 03. | Does not authorize runtime work. |

## 4. Semantic contracts accepted

- `contracts.py`: frozen semantic primitives for tariffs, subscriptions, grants, payment evidence, actor context and effective intervals. It is non-runtime and does not couple to transport, DB, provider SDKs or foreign module state.
- `policies.py`: approved Free/Basic policy constants and future decision gates. It is non-runtime policy evidence, not a feature implementation.
- `evaluation.py`: pure deterministic effective entitlement evaluator. It makes account/scope/interval decisions without side effects and does not mutate Beacon, scheduler, notification, provider or UI state.
- `manual_access.py`: manual grant create/revoke lifecycle semantics with actor, reason, scope, interval, idempotency and audit references. It is semantic-only and does not implement Admin UI or role runtime.
- `subscription_lifecycle.py`: subscription lifecycle semantics for manual renewal, expired access handling and Free-compliance behavior. It is semantic-only and does not implement billing runtime.
- `usage_consumption.py`: approved usage counter families and deterministic usage-consumption semantics. It is semantic-only and does not implement a DB usage store or quota decrement.
- `beacon_integration.py`: Beacon Management request/decision boundary that consumes entitlement, usage and subscription decisions. Entitlements returns decisions only and does not mutate Beacon state.
- `payment_provider_boundary.py`: provider evidence boundary for YooKassa, Telegram Stars and Tinkoff/T-Bank references. It is evidence-only and does not authorize provider runtime, SDK/API calls or raw payload authority.
- `payment_reconciliation.py`: reconciliation and manual refund semantic contracts. It is semantic-only and does not implement runtime reconciliation, refunds or recurring billing.
- `admin_tariff_management.py`: tariff-draft, publish and assignment boundary semantics with approved capability references. It is semantic-only and does not implement Admin/Web/Identity runtime or direct writes.
- `fixtures.py`: safe synthetic fixture registry for deterministic tests. It is fixture-only and does not represent runtime state or production evidence.

## 5. Product policy captured

- Current approved tariff families are `Free` and `Basic`.
- `Basic` is `990 RUB / 1 month`.
- `Free` allows one Beacon and stricter limits.
- `Basic` scan interval policy starts at 5 minutes with a 5-minute step.
- `Free` scan interval policy starts at 3 hours with a 3-hour step.
- Expired paid access becomes Free-only and requires user choice plus Free-compliance handling.
- The user must manually start the Free-compliant Beacon; the system must not auto-select it.
- Manual renewal only is the current payment policy.
- Manual refunds only are the current refund policy.
- No recurring payments are approved now.
- No trial, grace period or proration is approved now.
- Provider candidates are evidence only: YooKassa, Telegram Stars and Tinkoff/T-Bank.
- Admin capability must eventually support adding tariffs, editing tariffs, assigning tariffs/access and changing roles.
- Future tariffs, names, prices, limits and defaults are not predeclared here.

## 6. Effective entitlement and lifecycle semantics

- EB-03 precedence is explicit: ownership/scope first, payment evidence only as evidence, then active tariff/subscription, then entitlement grants, then manual access grants.
- Effective entitlement outcomes include `ALLOWED`, `DENIED`, `BLOCKED`, `EXPIRED`, `AMBIGUOUS`, `UNSUPPORTED`, `USER_CHOICE_REQUIRED`, `FREE_COMPLIANCE_REQUIRED` and `CONFLICT`.
- Free and Basic are evaluated through approved tariff definitions only.
- Expired paid access returns a Free-only requirement state and does not automatically choose a Beacon.
- Free-compliance and user-choice requirements are explicit outcomes, not hidden implementation behavior.
- No foreign module state is mutated by entitlement evaluation.

## 7. Manual access semantics

- Actor context is required.
- Target account is required.
- Reason, scope, interval, idempotency key and audit reference are required.
- `ENTITLEMENTS_MANUAL_ACCESS_ADMIN` is the approved capability reference.
- Semantic lifecycle outcomes include `CREATED`, `REPLAYED`, `REVOKED`, `EXPIRED`, `REJECTED`, `CONFLICT`, `IDEMPOTENCY_MISMATCH`, `UNAUTHORIZED` and `OUT_OF_SCOPE`.
- Open-ended grants are forbidden in current scope.
- Manual access semantics do not authorize Admin UI, role runtime or direct database edits.

## 8. Usage consumption semantics

- Approved counter families are `ACTIVE_BEACON_SLOT` and `SCAN_INTERVAL_WINDOW`.
- Payment-related consumption is blocked.
- Scan-count quotas are blocked.
- Notification-count quotas are blocked.
- No DB usage counter store is approved here.
- No runtime quota decrement is approved here.
- `ACTIVE_BEACON_SLOT` is owned by Beacon Management source facts and `SCAN_INTERVAL_WINDOW` is owned by Scan Orchestration source facts.
- `OD-011` remains open and must not be closed by EB-06 semantics.

## 9. Beacon integration semantics

- Beacon Management asks Entitlements for a decision.
- Entitlements does not mutate Beacon state.
- Expired paid access returns user-choice-required or Free-compliance-required decisions.
- Active Beacon and scan interval semantics are evaluated through approved semantic contracts only.
- Geography expansion assumptions are blocked by `OD-010`.

## 10. Payment provider boundary

- Official provider evidence was captured for YooKassa, Telegram Stars and Tinkoff/T-Bank.
- Provider response is external evidence only.
- Raw payload is not entitlement authority.
- No direct entitlement grant may come from provider evidence.
- No provider SDK/API calls, webhooks or payment account setup are authorized.
- Redaction and idempotency semantics are explicit and required.

## 11. Reconciliation/refunds semantics

- Reconciliation outcomes include `RECORDED`, `DUPLICATE`, `REJECTED`, `AMBIGUOUS`, `RECONCILE_REQUIRED`, `CONFIRMED`, `UNRESOLVED`, `MANUAL_REVIEW_REQUIRED`, `REPLAYED`, `IDEMPOTENCY_MISMATCH` and `BLOCKED`.
- Manual refund outcomes include `MANUAL_REFUND_REVIEW_REQUIRED`, `MANUAL_REFUND_REFERENCED`, `AUTOMATIC_REFUND_BLOCKED`, `PROVIDER_REFUND_API_BLOCKED`, `REFUND_REJECTED`, `REFUND_REPLAYED` and `REFUND_IDEMPOTENCY_MISMATCH`.
- Duplicate provider event identity must not create a second effect.
- Ambiguous provider effect must trigger reconcile-first behavior.
- Blind retry after unknown provider effect is forbidden.
- Manual refunds only remain the approved policy.
- Automatic/provider refund API calls remain blocked.
- Recurring billing remains blocked.
- Chargeback automation remains blocked.

## 12. Admin tariff-management semantic boundary

- Approved capability references are `ENTITLEMENTS_TARIFF_ADMIN`, `ENTITLEMENTS_TARIFF_ASSIGN_ADMIN` and `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.
- Approved command families are create draft, edit draft, publish definition, assign account tariff, assign manual access and reject admin tariff.
- Approved outcomes include draft, publish, assign, forbidden, conflict, replayed, idempotency mismatch, blocked and unavailable states.
- Tariff draft/edit/publish semantics are semantic-only and do not create runtime access.
- Assignment semantics are semantic-only and do not directly write billing tables.
- Admin/Web do not own Entitlements state.
- UI flags, provider usernames, client flags and local config are not authorization.
- Role taxonomy is not closed here.
- Audit retention/storage is blocked by `OD-013`.

## 13. Tests and checks evidence

- EB-11 post-timeout verification confirmed current main `81b4754a2097503542d84fcb153d0f08817e30be`.
- Verified evidence included parent `2cb4b8a912b9653285687505df2bcf441d8d2be9` and subject `eb-11: add admin tariff boundary semantics`.
- `pytest 269 passed`.
- `compileall passed`.
- `git diff --check passed`.
- Final worktree was clean.
- Architecture and import-boundary checks cover module 03 semantic files.
- No forbidden runtime/UI/DB/provider/secrets artifacts were present.
- Reported prior semantic subtask evidence:
  - EB-06 semantic usage consumption: `163 passed`, `1 warning`.
  - EB-07 semantic Beacon integration: `184 passed`.
  - EB-08 semantic provider boundary: `208 passed`, `1 warning`.
  - EB-09 semantic reconciliation/refunds: `236 passed`.

## 14. Remaining blocked gates

- payment provider runtime integration
- payment account setup
- SDK/API calls/webhooks
- invoice/receipt/tax runtime
- card data handling
- recurring billing
- automatic refunds
- chargeback automation
- billing runtime service
- database schema
- repositories
- persistence
- migrations
- SQLAlchemy/Psycopg/Alembic
- Admin UI
- Web Cabinet UI/runtime
- Identity role runtime
- exact global admin role taxonomy
- role-changing implementation
- Beacon mutation
- scheduler integration
- notification sending
- Docker/CI/CD/deploy/runtime config
- credentials/tokens/secrets
- raw provider payload storage

## 15. Open decisions

- `OD-010` remains OPEN.
- `OD-011` remains OPEN.
- `OD-013` remains OPEN.

These decisions block geography/country-wide availability assumptions, minimum monitoring frequency safety assumptions and billing/audit/personal-data retention and storage assumptions.

## 16. Cross-module dependency notes

- Beacon Management consumes entitlement and usage decisions but owns Beacon state.
- Scan Orchestration and Notification Delivery still gate future usage counters beyond the two approved families.
- Identity owns actor/role verification and role assignment.
- Admin & Support and Web Cabinet may request command envelopes but do not own Entitlements state.
- Platform/Contracts and future persistence gates own physical DB and migration decisions.

## 17. Handoff for future work

- Next work after this module must not assume runtime billing implementation exists.
- To open persistence/migrations, `OD-013` and physical schema/migration gates must be resolved.
- To open provider runtime, a provider-specific exact task and official integration design are required.
- To open Admin/Web runtime, Admin/Web/Identity runtime gates are required.
- Future tariff values must be owner-approved separately.
- GitHub `main` remains the source of truth.

## 18. Non-authorization reminder

This handoff does not authorize runtime, DB, migrations, payment provider integration, Admin/Web UI, role service, deploy or secrets work.
