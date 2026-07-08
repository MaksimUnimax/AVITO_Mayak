# Маяк Авито — Entitlements & Billing Precedence Decision v1.0

**Статус:** APPROVED decision capture for EB-03 semantic planning  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0010`  
**Предыдущая policy capture:** `docs/04-modules/03-entitlements-and-billing/OWNER_BILLING_DECISIONS_CAPTURE_v1.0.md`

## 1. Purpose

This document captures the owner-approved precedence policy required before EB-03 `Effective entitlement evaluation semantics`.

It is a semantic planning source for later exact tasks. It is not a runtime implementation, database schema, migration, repository, provider adapter, payment integration, Admin UI, Beacon mutation, scheduler integration, notification integration, deployment configuration or permission to use secrets.

## 2. Approved precedence policy

### 2.1 TariffDefinition

`TariffDefinition` defines the baseline tariff policy:

- approved capability set;
- approved limits;
- approved scan interval rules;
- price and period semantics where applicable;
- explicit future gates.

`TariffDefinition` does not by itself prove that an account currently has access. It defines what a tariff can mean when selected by an authorized account-level state.

### 2.2 Subscription

An active `Subscription` selects the currently applicable tariff family for an account.

If paid access is active, the subscription selects the paid tariff policy.

If paid access is expired or unavailable, evaluation moves to the Free-only requirement state described in this document and in `ADR-0009`.

### 2.3 EntitlementGrant

`EntitlementGrant` may add, restrict or qualify individual capabilities only inside its explicit:

- account scope;
- capability scope;
- effective interval.

An entitlement grant must not silently mutate the selected tariff definition.

An entitlement grant must not create a new tariff family.

### 2.4 ManualAccessGrant

`ManualAccessGrant` has highest precedence only inside its explicit:

- target account;
- capability/scope;
- effective interval;
- reason;
- actor context;
- idempotency reference;
- audit reference.

A valid manual grant may override a tariff/subscription denial only for that exact explicit scope and interval.

Outside that scope or interval, normal tariff/subscription/grant evaluation applies.

### 2.5 PaymentRecord and PaymentEvent

`PaymentRecord` and `PaymentEvent` are non-authority evidence.

They never grant access directly.

They never produce an entitlement by themselves.

Any future payment-derived access requires a separate server-authorized transition and its own exact task.

### 2.6 Expired paid access

If paid access is expired, the effective result must represent a Free-only requirement state.

All paid Beacons are treated as requiring user action:

- user-choice-required;
- free-compliance-required.

The system must not automatically choose the remaining Free Beacon.

### 2.7 Conflict and ambiguity

If sources disagree or the evaluator cannot prove a safe deterministic result, the result must be:

- `AMBIGUOUS`; or
- `CONFLICT`.

The evaluator must not silently allow access in this case.

## 3. Approved EB-03 semantic result statuses

EB-03 semantic evaluator contracts/tests may use the following result statuses only as semantic outcomes:

- `ALLOWED`;
- `DENIED`;
- `BLOCKED`;
- `EXPIRED`;
- `AMBIGUOUS`;
- `UNSUPPORTED`;
- `USER_CHOICE_REQUIRED`;
- `FREE_COMPLIANCE_REQUIRED`;
- `CONFLICT`.

## 4. Evaluation precedence order for EB-03 semantic contracts/tests

EB-03 semantic contracts/tests must use this order:

1. Validate account ownership/scope first.
2. Treat payment records/events as evidence only and never as authority.
3. Determine the baseline tariff policy from active subscription state and approved tariff definitions.
4. If paid access is expired, return the Free-only requirement state instead of choosing a Beacon or mutating Beacon state.
5. Apply valid entitlement grants only within their explicit scope and effective interval.
6. Apply valid manual access grants only within their explicit scope and effective interval, with actor, reason, idempotency and audit reference.
7. If a deterministic safe decision remains impossible, return `AMBIGUOUS` or `CONFLICT`.

## 5. Explicit non-authorization

This decision does not authorize:

- runtime evaluator implementation;
- database-backed evaluation;
- repositories;
- persistence;
- migrations;
- provider adapters;
- provider SDK/API calls;
- webhooks;
- payment-derived access without server-authorized transition;
- invoice, receipt or tax implementation;
- card data handling;
- Admin UI;
- Web Cabinet;
- Beacon mutation;
- automatic Beacon choice;
- scheduler integration;
- notification sending;
- Docker;
- CI/CD;
- deploy;
- runtime configuration;
- secrets;
- tokens;
- payment credentials.

## 6. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

- `OD-010` — country-wide availability by market;
- `OD-011` — minimum monitoring frequency safety;
- `OD-013` — billing, audit and personal-data retention.

The following areas remain gated:

- usage counters and limit consumption;
- Beacon Management integration;
- provider-specific payment runtime;
- reconciliation and refunds;
- persistence and migrations;
- Admin UI and Web Cabinet runtime.

## 7. Use in later roadmap steps

Later exact EB-03 tasks may use this document and `ADR-0010` as approved input for deterministic semantic evaluator contracts/tests only.

Those tasks must remain:

- transport-neutral;
- provider-neutral;
- framework-neutral;
- ORM-neutral;
- runtime-neutral.

Entitlements & Billing may return effective entitlement decisions, but it must not mutate Beacon, scheduler, notification, identity, provider or UI state directly.
