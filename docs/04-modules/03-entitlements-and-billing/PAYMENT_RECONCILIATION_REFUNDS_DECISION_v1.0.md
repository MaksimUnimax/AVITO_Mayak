# Маяк Авито — Payment Reconciliation & Manual Refund Semantics Decision v1.0

**Статус:** APPROVED semantic decision for EB-09 contracts/tests only  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0014`

## 1. Purpose

This document captures deterministic semantic policy for EB-09 `Payment reconciliation / refunds`.

It is not a runtime reconciliation engine, provider API implementation, webhook implementation, refund executor, recurring billing implementation, invoice/receipt/tax implementation, database schema, migration, repository, Admin UI, Web Cabinet UI, provider token/secret handling or entitlement-grant authority.

## 2. Current payment policy

Current payment policy remains:

- provider candidates: YooKassa, Telegram Stars, Tinkoff/T-Bank;
- first stage: manual renewal only;
- recurring payments are not implemented now;
- refunds are manual only;
- currencies: RUB and Telegram Stars;
- no trial/grace/proration;
- Free tariff is the alternative to trial/grace.

## 3. Global boundary

A payment provider response is external evidence only.

Raw provider payload is not entitlement authority.

Payment evidence must not create, change or extend access by itself.

A future entitlement/subscription transition requires a separate server-authorized business transition, idempotency, actor/service context where applicable, audit reference and an approved commit point.

## 4. Approved reconciliation outcomes

The approved semantic reconciliation outcomes are:

- `RECORDED`;
- `DUPLICATE`;
- `REJECTED`;
- `AMBIGUOUS`;
- `RECONCILE_REQUIRED`;
- `CONFIRMED`;
- `UNRESOLVED`;
- `MANUAL_REVIEW_REQUIRED`;
- `REPLAYED`;
- `IDEMPOTENCY_MISMATCH`;
- `BLOCKED`.

Outcome meanings:

- `RECORDED`: normalized semantic payment evidence was accepted as evidence only, without granting access.
- `DUPLICATE`: same provider event identity or same idempotency/fingerprint was already processed semantically.
- `REJECTED`: malformed, unsupported, non-redacted or contradictory evidence was rejected.
- `AMBIGUOUS`: external/provider effect cannot be safely classified.
- `RECONCILE_REQUIRED`: ambiguous/unknown external effect must be reconciled before retry or business transition.
- `CONFIRMED`: reconciliation evidence confirms the semantic external effect state, still without direct entitlement grant.
- `UNRESOLVED`: reconciliation cannot determine final effect.
- `MANUAL_REVIEW_REQUIRED`: manual operator/business review is required.
- `REPLAYED`: same idempotency key + same fingerprint + prior terminal semantic outcome.
- `IDEMPOTENCY_MISMATCH`: same idempotency key + different request fingerprint.
- `BLOCKED`: runtime/provider/refund/recurring/unsupported action remains blocked.

## 5. Approved manual refund outcomes

The approved manual refund semantic outcomes are:

- `MANUAL_REFUND_REVIEW_REQUIRED`;
- `MANUAL_REFUND_REFERENCED`;
- `AUTOMATIC_REFUND_BLOCKED`;
- `PROVIDER_REFUND_API_BLOCKED`;
- `REFUND_REJECTED`;
- `REFUND_REPLAYED`;
- `REFUND_IDEMPOTENCY_MISMATCH`.

Outcome meanings:

- `MANUAL_REFUND_REVIEW_REQUIRED`: a manual refund case needs human/business review.
- `MANUAL_REFUND_REFERENCED`: semantic reference to an already manual/business-handled refund may be recorded as evidence only.
- `AUTOMATIC_REFUND_BLOCKED`: automatic refund remains forbidden.
- `PROVIDER_REFUND_API_BLOCKED`: direct provider refund API call remains forbidden.
- `REFUND_REJECTED`: invalid or unsupported refund semantic evidence.
- `REFUND_REPLAYED`: same idempotency key + same fingerprint + prior terminal refund semantic outcome.
- `REFUND_IDEMPOTENCY_MISMATCH`: same idempotency key + different refund request fingerprint.

## 6. Duplicate provider event semantics

A stable provider event identity must be used where officially available.

The same provider event identity must not create a second semantic effect.

A duplicate provider event returns `DUPLICATE`, `REPLAYED` or the original terminal semantic outcome.

Duplicate payment evidence must not extend access, grant entitlement, renew subscription or create another refund effect by itself.

## 7. Ambiguous provider effect and reconcile-first behavior

Unknown external provider effect must not be treated as “no effect”.

Unknown or ambiguous external effect must return one of:

- `AMBIGUOUS`;
- `RECONCILE_REQUIRED`;
- `UNRESOLVED`;
- `MANUAL_REVIEW_REQUIRED`.

Blind retry after unknown provider effect is forbidden.

Retry is allowed only after a semantic reconciliation decision makes the next action explicit.

A future server-authorized business transition remains separate from payment evidence.

## 8. Idempotency

For reconciliation/refund semantic mutations:

- idempotency key is required;
- missing key returns `REJECTED` before any semantic effect;
- same key + same request fingerprint + prior terminal outcome returns `REPLAYED` or the original terminal outcome deterministically;
- same key + different request fingerprint returns `IDEMPOTENCY_MISMATCH`;
- provider event identity must be stable where officially available;
- duplicate provider event identity must not create a second semantic effect.

## 9. Commit point semantics

Commit-point terminology in EB-09 is semantic-only.

This decision does not implement a database commit, event store, repository or persistence layer.

A successful semantic reconciliation/refund decision may become event-candidate evidence only after a future owning runtime/persistence task reaches its separately approved commit point.

Unknown commit state returns `UNRESOLVED`, `RECONCILE_REQUIRED`, `MANUAL_REVIEW_REQUIRED` or `BLOCKED`, never silent success.

## 10. Refund policy

Refunds are manual only.

Manual refund evidence may be represented semantically as:

- `MANUAL_REFUND_REVIEW_REQUIRED`;
- `MANUAL_REFUND_REFERENCED`.

Automatic refund remains blocked.

Provider refund API calls remain blocked.

Chargeback automation remains blocked.

## 11. Recurrence policy

Manual renewal only remains the current policy.

Recurring billing is not implemented now.

Recurring billing attempts remain `BLOCKED`.

Trial/grace/proration remain absent and are not introduced here.

## 12. Redaction and payload handling

Raw provider payload is not entitlement authority.

Raw provider payload must not be stored as entitlement state.

Future semantic contracts may represent only:

- provider candidate;
- synthetic or redacted provider event reference;
- stable provider event identity where officially available;
- redaction status;
- normalized amount/currency evidence if needed;
- semantic outcome;
- audit/reference id.

Fixtures/tests must not contain provider tokens, secrets, credentials, card data, PAN, CVV or raw provider payload bodies.

## 13. Explicit non-authorization

This decision does not authorize:

- runtime reconciliation engine;
- provider SDK/API calls;
- provider refund API calls;
- YooKassa runtime integration;
- Telegram Stars runtime integration;
- Tinkoff/T-Bank runtime integration;
- webhooks;
- payment account setup;
- invoice, receipt or tax implementation;
- automatic refunds;
- recurring billing;
- chargeback automation;
- blind retry after unknown provider effect;
- payment-derived entitlement grant;
- raw provider payload storage as entitlement state;
- card data handling;
- provider credentials, tokens or secrets;
- database schema;
- repositories;
- persistence;
- migrations;
- Admin UI;
- Web Cabinet UI;
- Telegram/MAX payment screens;
- Beacon mutation;
- scheduler integration;
- notification sending;
- Docker, CI/CD, deploy or runtime configuration.

## 14. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

- `OD-010` — country-wide availability by market;
- `OD-011` — minimum monitoring frequency safety;
- `OD-013` — billing, audit and personal-data retention.

The following remain gated:

- provider-specific runtime adapter implementation;
- webhook processing;
- payment account setup;
- invoice/receipt/tax behavior;
- physical persistence and migrations;
- Admin UI/Web Cabinet runtime;
- secrets/tokens/credentials handling.

## 15. Use in later roadmap steps

Later exact EB-09 tasks may use this document and `ADR-0014` as approved input for deterministic semantic reconciliation/refund contracts/tests only.

Any runtime reconciliation, provider refund API, recurring billing, persistence or provider-specific adapter still requires a separate exact task and must preserve the rule that provider response is evidence only, not entitlement authority.
