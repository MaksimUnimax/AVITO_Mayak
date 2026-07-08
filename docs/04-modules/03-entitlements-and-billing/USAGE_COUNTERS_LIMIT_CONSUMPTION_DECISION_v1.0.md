# Маяк Авито — Usage Counters / Limit Consumption Decision v1.0

**Статус:** APPROVED decision capture for EB-06 semantic planning  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0012`  
**Предыдущие policy captures:**
- `docs/04-modules/03-entitlements-and-billing/OWNER_BILLING_DECISIONS_CAPTURE_v1.0.md`
- `docs/04-modules/03-entitlements-and-billing/ENTITLEMENT_PRECEDENCE_DECISION_v1.0.md`
- `docs/04-modules/03-entitlements-and-billing/MANUAL_ACCESS_AUTHORIZATION_DECISION_v1.0.md`

## 1. Purpose

This document captures the owner-approved usage counters and limit consumption semantic policy required before EB-06 `Usage counters / limit consumption`.

It is a semantic planning source for later exact tasks. It is not a runtime implementation, database schema, migration, repository, provider adapter, payment integration, Admin UI, Web Cabinet runtime, Beacon mutation, Scan Orchestration mutation, scheduler integration, notification integration, deployment configuration or permission to use secrets.

## 2. Scope opened by this decision

EB-06 is opened only for deterministic semantic contracts/tests.

Entitlements & Billing owns only semantic usage-consumption policy and decisions.

Entitlements & Billing does not own:

- Beacon state;
- scan execution state;
- notification delivery state;
- payment provider state.

## 3. Approved EB-06 semantic counter families

Current approved EB-06 semantic counter families are:

- `ACTIVE_BEACON_SLOT`;
- `SCAN_INTERVAL_WINDOW`.

## 4. Explicitly not approved in current EB-06 scope

The following are not approved in current EB-06 scope:

- scan-count quotas;
- notification-count quotas;
- payment-related consumption;
- storage quotas;
- provider-specific quotas;
- monetary/payment consumption.

## 5. ACTIVE_BEACON_SLOT semantics

Requester module:

```text
Beacon Management

Source facts owner:

Beacon Management

Entitlements receives only synthetic snapshot/evidence for semantic evaluation.

Entitlements must not:

create Beacons;

freeze Beacons;

start Beacons;

stop Beacons;

delete Beacons;

choose Beacons;

mutate Beacon state.

Free may use the accepted current limit of one active Beacon.

Basic active Beacon numeric limit remains gated unless already accepted elsewhere in current source-of-truth.

Unsupported or missing limit returns UNAVAILABLE or BLOCKED, not ACCEPTED.

6. SCAN_INTERVAL_WINDOW semantics

Requester module:

Scan Orchestration

Source facts owner:

Scan Orchestration

Entitlements receives only synthetic last/next scan timing evidence for semantic evaluation.

Entitlements must not:

schedule scans;

run scans;

cancel scans;

mutate scheduler state;

mutate Scan Orchestration state.

Free uses accepted interval policy:

starting at 3 hours, step 3 hours

Basic uses accepted interval policy:

starting at 5 minutes, step 5 minutes

OD-011 minimum monitoring frequency safety remains open and must not be closed by EB-06.

If OD-011 safety is required to decide a case, EB-06 semantics must return BLOCKED or UNAVAILABLE.

7. Approved semantic outcomes

EB-06 semantic contracts/tests may use these outcomes:

ACCEPTED;

DENIED;

REPLAYED;

CONFLICT;

UNAVAILABLE;

IDEMPOTENCY_MISMATCH;

REJECTED;

BLOCKED.

8. Idempotency policy

Usage-consumption semantic requests require an idempotency key.

The approved idempotency behavior is:

Same key plus same request fingerprint plus terminal outcome returns REPLAYED or the original terminal outcome.

Same key plus different request fingerprint returns IDEMPOTENCY_MISMATCH.

Missing idempotency key returns REJECTED before any effect.

9. Commit-point policy

EB-06 may define semantic commit-point terminology only.

No actual persistent commit is implemented in EB-06.

A successful semantic usage decision may become an event candidate only after the owning requester module reaches its own future approved commit point.

Unknown commit state returns UNAVAILABLE or BLOCKED, never silent ACCEPTED.

10. Reset/window policy

ACTIVE_BEACON_SLOT has no reset window in EB-06. It is evaluated from current source facts snapshot.

SCAN_INTERVAL_WINDOW is evaluated from current time plus supplied last/next scan evidence.

The following are not approved in EB-06:

daily quota reset;

monthly quota reset;

rolling counters;

notification counters;

payment counters.

11. Conflict and missing-evidence handling

Conflicting source facts return CONFLICT.

Missing required source facts return UNAVAILABLE or REJECTED.

Unsupported counter family returns BLOCKED.

Ambiguous evidence must not return ACCEPTED.

12. Explicit non-authorization

This decision does not authorize:

runtime counter store;

database-backed usage counters;

database schema;

repositories;

persistence;

migrations;

runtime quota decrement;

scan-count consumption implementation;

notification-count consumption implementation;

payment-related consumption implementation;

provider/payment integration;

provider SDK/API calls;

webhooks;

Beacon mutation;

Scan Orchestration mutation;

Notification Delivery mutation;

automatic Beacon choice;

scheduler integration;

notification sending;

Admin UI;

Web Cabinet UI;

Docker;

CI/CD;

deploy;

runtime configuration;

secrets;

tokens;

credentials.

13. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

OD-010 — country-wide availability by market;

OD-011 — minimum monitoring frequency safety;

OD-013 — billing, audit and personal-data retention.

The following areas remain gated:

Beacon Management integration;

Scan Orchestration integration;

Notification Delivery integration;

provider-specific payment runtime;

reconciliation and refunds;

persistence and migrations;

Admin UI and Web Cabinet runtime.

14. Use in later roadmap steps

Later exact EB-06 tasks may use this document and ADR-0012 as approved input for deterministic semantic usage-consumption contracts/tests only.

Those tasks must remain:

transport-neutral;

provider-neutral;

framework-neutral;

ORM-neutral;

runtime-neutral.

Entitlements & Billing may define semantic usage-consumption contracts and outcomes, but it must not mutate Beacon, Scan Orchestration, Notification Delivery, provider, payment, identity, Admin UI or Web Cabinet state directly.
