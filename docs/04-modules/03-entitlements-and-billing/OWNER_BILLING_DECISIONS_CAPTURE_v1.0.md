# Маяк Авито — Entitlements & Billing Owner Billing Decisions Capture v1.0

**Статус:** APPROVED decision capture for module planning  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0009`  
**Связанный open-decision register update:** `docs/00-governance/OPEN_DECISIONS.md`, section `Governance capture update — 2026-07-08 — OD-001–OD-005`

## 1. Purpose

This document captures owner-provided billing decisions for the Entitlements & Billing module after governance approval in `ADR-0009`.

It is a planning and semantic-contract source for later exact tasks. It is not product-code, runtime implementation, database schema, migration, payment integration, provider account setup, Admin UI, deployment configuration or permission to use secrets.

## 2. Closed owner decisions

### OD-001 — Basic price period

The Basic tariff price `990 ₽` is for one month.

### OD-002 — Current tariff set

At the current stage, the approved product tariff families are:

- `Free`;
- `Basic`.

There are no other paid tariffs at this stage.

Future tariffs must be possible through Admin capability, but future tariff names, prices, limits and defaults are not predeclared by this document.

### OD-003 — Interval and Free/Basic policy

`Basic` policy:

- monitoring intervals start from 5 minutes;
- interval step is 5 minutes;
- examples: 5, 10, 15, 20 minutes and further by the same step.

`Free` policy:

- one Beacon;
- reduced functionality;
- monitoring intervals start from 3 hours;
- interval step is 3 hours;
- examples: 3, 6, 9, 12 hours and further by the same step;
- Free uses the same entitlement mechanism as a paid tariff, but with stricter limits.

### OD-004 — Expired paid access behavior

After paid access expires:

1. only Free remains available;
2. all Beacons are frozen;
3. the user receives a message that the tariff has ended;
4. the user must choose one Beacon that will remain under Free;
5. the user must bring the chosen Beacon into Free requirements;
6. the user must manually start that Beacon.

The system must not automatically choose the remaining Free Beacon.

### OD-005 — First-stage payment policy

Provider candidates:

- YooKassa;
- Telegram Stars;
- Tinkoff.

First-stage payment mode:

- manual renewal only;
- no recurring payments now;
- manual refunds only;
- supported units: RUB and Telegram Stars.

Trial, grace and proration:

- no trial;
- no grace period;
- no proration;
- Free tariff acts as the alternative to trial/grace.

Manual access and Admin capability:

- manual access is required as an Admin capability;
- Admin capability must eventually allow changing roles;
- Admin capability must eventually allow adding new tariffs;
- Admin capability must eventually allow editing existing tariffs;
- Admin capability must eventually allow manually assigning tariffs/access to accounts.

## 3. Explicit non-authorization

This decision capture does not authorize:

- payment provider integration;
- payment account setup;
- real provider SDK calls;
- webhook endpoints;
- invoice, receipt or tax implementation;
- card data handling;
- Telegram Stars runtime integration;
- Tinkoff runtime integration;
- YooKassa runtime integration;
- Admin UI implementation;
- database schema;
- migrations;
- billing runtime service;
- Docker;
- CI/CD;
- deploy;
- runtime configuration;
- secrets;
- tokens;
- payment credentials.

## 4. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

- `OD-010` — country-wide availability by market;
- `OD-011` — minimum monitoring frequency safety;
- `OD-013` — retention of billing, audit and personal data.

The following areas remain gated:

- persistence and migrations;
- provider-specific payment runtime;
- Admin UI and Web Cabinet runtime;
- Beacon runtime mutation;
- scheduler integration;
- notification sending;
- usage counters and limit consumption.

## 5. Use in later roadmap steps

Later exact tasks may use this document and `ADR-0009` as approved input for semantic contracts and synthetic fixtures.

They still must preserve the module boundaries:

- payment provider response is external evidence and never grants access by itself;
- entitlement mutation requires verified actor context, authorization, ownership/scope validation, idempotency, explicit commit point and auditable outcome;
- manual access requires actor, reason, scope, effective interval and audit reference;
- Entitlements & Billing returns effective entitlement decisions but does not mutate Beacon, scheduler, notification, identity, provider or UI state directly.
