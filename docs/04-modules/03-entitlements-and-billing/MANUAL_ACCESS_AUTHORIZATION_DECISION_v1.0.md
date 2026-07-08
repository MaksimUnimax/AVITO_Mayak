# Маяк Авито — Manual Access Authorization Decision v1.0

**Статус:** APPROVED decision capture for EB-04 semantic planning  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0011`  
**Предыдущие policy captures:**
- `docs/04-modules/03-entitlements-and-billing/OWNER_BILLING_DECISIONS_CAPTURE_v1.0.md`
- `docs/04-modules/03-entitlements-and-billing/ENTITLEMENT_PRECEDENCE_DECISION_v1.0.md`

## 1. Purpose

This document captures the owner-approved manual access grant authorization and lifecycle policy required before EB-04 `Manual access grants`.

It is a semantic planning source for later exact tasks. It is not a runtime implementation, database schema, migration, repository, provider adapter, payment integration, Admin UI, Web Cabinet runtime, Beacon mutation, scheduler integration, notification integration, deployment configuration or permission to use secrets.

## 2. Approved authorization policy

### 2.1 Required capability

Manual access grant creation and revocation may be performed only by a server-side actor with capability:

```text
ENTITLEMENTS_MANUAL_ACCESS_ADMIN

This capability is approved only as semantic authorization input for EB-04 contracts/tests.

It does not implement a runtime role service, Admin UI, Web Cabinet UI or client-side admin flag.

2.2 Required actor context

The actor context must include:

actor_id;

actor_category;

authorization_scope;

authorization_reference;

audit_reference.

A missing actor context or missing authorization reference must not create or revoke a manual access grant.

2.3 Target and grant scope

A manual access grant is valid only for:

one explicit target_account_id;

one explicit capability/scope;

one explicit effective interval;

one required reason;

one required idempotency key;

one required audit reference.

Unscoped grants are forbidden.

A manual access grant must not silently apply to another account, another capability, another scope or another interval.

2.4 Effective interval

Open-ended manual grants are forbidden for current scope.

Every manual access grant must define both:

starts_at;

ends_at.

A grant outside its effective interval is not active.

3. Approved lifecycle outcomes

EB-04 semantic contracts/tests may use only these manual grant lifecycle outcomes:

CREATED;

REPLAYED;

REVOKED;

EXPIRED;

REJECTED;

CONFLICT;

IDEMPOTENCY_MISMATCH;

UNAUTHORIZED;

OUT_OF_SCOPE.

4. Idempotency policy

Manual access grant creation and revocation require an idempotency key.

The approved idempotency behavior is:

Same key plus same request fingerprint plus terminal outcome returns the original outcome.

Same key plus different request fingerprint returns IDEMPOTENCY_MISMATCH.

Missing idempotency key returns REJECTED before any effect.

5. Revocation policy

Revocation may be performed only by an actor with capability:

ENTITLEMENTS_MANUAL_ACCESS_ADMIN

Revocation requires:

target grant_id;

target account_id;

reason;

idempotency key;

audit reference.

Revocation must not delete history.

For EB-04 semantic contracts/tests, revocation may only produce a semantic revoked outcome.

6. Commit and audit boundary

A successful manual grant or revocation event may exist only after an authoritative semantic commit point.

The following are not valid manual access grants:

UI toggle;

chat message;

direct database edit;

provider/payment event;

client-side admin flag.

7. Explicit non-authorization

This decision does not authorize:

runtime Admin UI;

Web Cabinet runtime;

runtime role service;

database-backed manual grant state;

repositories;

persistence;

migrations;

direct database edits;

provider/payment integration;

provider SDK/API calls;

webhooks;

Beacon mutation;

automatic Beacon choice;

scheduler integration;

notification sending;

Docker;

CI/CD;

deploy;

runtime configuration;

secrets;

tokens;

payment credentials.

8. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

OD-010 — country-wide availability by market;

OD-011 — minimum monitoring frequency safety;

OD-013 — billing, audit and personal-data retention.

The following areas remain gated:

Admin UI and Web Cabinet runtime;

runtime role service;

usage counters and limit consumption;

Beacon Management integration;

provider-specific payment runtime;

reconciliation and refunds;

persistence and migrations.

9. Use in later roadmap steps

Later exact EB-04 tasks may use this document and ADR-0011 as approved input for deterministic semantic manual access grant contracts/tests only.

Those tasks must remain:

transport-neutral;

provider-neutral;

framework-neutral;

ORM-neutral;

runtime-neutral.

Entitlements & Billing may define semantic manual access grant contracts and outcomes, but it must not mutate Beacon, scheduler, notification, identity, provider or UI state directly.
