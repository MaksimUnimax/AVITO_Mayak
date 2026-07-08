# Маяк Авито — Admin Tariff Management Boundary Decision v1.0

**Статус:** APPROVED semantic decision for EB-11 contracts/tests only  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0015`

## 1. Purpose

This document captures deterministic semantic policy for EB-11 `Admin tariff management boundary`.

It is not Admin UI, Web Cabinet UI, Identity role runtime, tariff management runtime, billing runtime, database schema, migration, repository, persistence, payment provider integration, provider account setup, deploy/runtime configuration, credential handling or product-code.

## 2. Current owner policy

Current owner policy remains:

- current stage tariffs are `Free` and `Basic`;
- future tariffs must be possible through Admin capability;
- future tariff names, prices, limits and defaults are not predeclared here;
- Admin capability must eventually allow adding tariffs;
- Admin capability must eventually allow editing tariffs;
- Admin capability must eventually allow manually assigning tariffs/access to accounts;
- Admin capability must eventually allow changing roles, but role changing belongs to Identity/Admin boundaries and is not implemented by Entitlements.

## 3. Global boundary

Entitlements & Billing owns tariff, subscription, entitlement grant, manual access grant and effective entitlement semantics.

Admin & Support and Web Cabinet do not own tariff, subscription, entitlement or payment state.

Admin & Support and Web Cabinet must not write Entitlements state directly.

Admin & Support and Web Cabinet must not write billing tables directly.

All protected tariff/admin mutations must go through Entitlements-owned semantic commands after verified actor context, server-side capability/scope authorization, idempotency, reason and audit reference.

## 4. Approved semantic capability references

The approved EB-11 semantic capability references are:

- `ENTITLEMENTS_TARIFF_ADMIN`;
- `ENTITLEMENTS_TARIFF_ASSIGN_ADMIN`;
- `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.

Meanings:

- `ENTITLEMENTS_TARIFF_ADMIN` is required for protected tariff draft/edit/publish semantics inside Entitlements.
- `ENTITLEMENTS_TARIFF_ASSIGN_ADMIN` is required for protected account tariff assignment semantics inside Entitlements.
- `ENTITLEMENTS_MANUAL_ACCESS_ADMIN` remains the existing approved manual access capability from `ADR-0011`.

These are module-level semantic capability references only.

They do not implement Identity roles.

They do not close exact admin role taxonomy.

They do not authorize UI flags, provider usernames, chat titles, local config or client-supplied admin flags.

They must be supplied only through verified server-side actor context.

## 5. Approved semantic command families

The approved EB-11 semantic command families are:

- `CreateTariffDraftCommand`;
- `EditTariffDraftCommand`;
- `PublishTariffDefinitionCommand`;
- `AssignAccountTariffCommand`;
- `AssignManualAccessCommand`;
- `RejectAdminTariffCommand`.

Meanings:

- `CreateTariffDraftCommand`: creates semantic tariff draft candidate only.
- `EditTariffDraftCommand`: updates semantic tariff draft candidate only.
- `PublishTariffDefinitionCommand`: publishes a tariff definition only if all required product fields are approved and no open-decision blocker applies.
- `AssignAccountTariffCommand`: protected assignment of an account to an already approved tariff definition, semantic-only.
- `AssignManualAccessCommand`: protected manual access assignment using existing manual-access semantics and `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.
- `RejectAdminTariffCommand`: returns deterministic rejection/blocking outcome when required policy/gate is absent.

## 6. Approved semantic outcomes

The approved EB-11 semantic outcomes are:

- `DRAFT_CREATED`;
- `DRAFT_UPDATED`;
- `PUBLISH_READY`;
- `PUBLISHED`;
- `ASSIGNED`;
- `MANUAL_ACCESS_ASSIGNED`;
- `REJECTED`;
- `FORBIDDEN`;
- `CONFLICT`;
- `REPLAYED`;
- `IDEMPOTENCY_MISMATCH`;
- `BLOCKED`;
- `UNAVAILABLE`.

Outcome meanings:

- `DRAFT_CREATED`: protected semantic tariff draft candidate accepted as non-authoritative draft.
- `DRAFT_UPDATED`: protected semantic tariff draft candidate update accepted as non-authoritative draft.
- `PUBLISH_READY`: draft has all approved product fields and can be published by a future exact semantic publish operation.
- `PUBLISHED`: tariff definition is semantically published by Entitlements, not Admin/Web, with approved fields only.
- `ASSIGNED`: protected account tariff assignment semantic decision accepted.
- `MANUAL_ACCESS_ASSIGNED`: protected manual access semantic decision accepted under existing manual-access rules.
- `REJECTED`: invalid, unsupported, unscoped or malformed request.
- `FORBIDDEN`: actor/capability/scope check failed.
- `CONFLICT`: conflicting draft/publish/assignment facts or version conflict.
- `REPLAYED`: same idempotency key + same fingerprint + prior terminal outcome.
- `IDEMPOTENCY_MISMATCH`: same idempotency key + different request fingerprint.
- `BLOCKED`: policy gate/open decision/runtime scope blocks the request.
- `UNAVAILABLE`: required authoritative source fact is missing or not available.

## 7. Tariff draft/edit/publish semantics

A tariff draft is not an active tariff.

A tariff draft does not change user access.

A tariff draft does not change subscription state.

A tariff draft does not create payment/provider behavior.

A tariff draft must include:

- semantic draft id;
- actor context;
- requested fields;
- reason;
- idempotency key;
- audit reference.

Future tariff names, prices, limits and defaults may not be invented by code/tests.

Only current approved `Free` and `Basic` product values may be used as current published policy where already accepted by prior ADRs.

Future tariffs must remain draft-only or blocked unless exact owner-approved values are captured.

Publishing requires all product fields to be approved and no open-decision blocker relevant to the field.

Publishing must be performed by Entitlements semantic command, not by Admin/Web direct write.

Editing an already published tariff must create a new semantic version or be blocked until versioning rules are approved.

Direct mutation of historical tariff definitions is blocked.

Deleting tariff history is blocked.

Retiring/disabling tariffs remains blocked unless separately approved.

## 8. Account tariff and manual assignment semantics

Protected assignment requires:

- verified actor context;
- server-side capability reference;
- target `account_id`;
- target approved tariff or manual-access scope;
- reason;
- idempotency key;
- audit reference.

Assignment to non-approved or draft-only tariff returns `BLOCKED` or `REJECTED`.

Assignment cannot be derived from payment provider evidence.

Assignment cannot be derived from UI/client flag.

Assignment cannot bypass subscription/manual-access semantics already accepted.

Assignment does not mutate Beacon, scheduler, notification, provider or UI state.

Assignment is semantic-only until persistence/runtime gates open.

## 9. Authorization and actor boundary

Admin/Web must supply verified server-side actor context.

UI flags, provider usernames, chat titles, local config and client-supplied admin flags are not authorization.

Identity owns role assignment and actor verification.

Entitlements may only consume actor/capability/scope facts as synthetic semantic input.

EB-11 does not implement role assignment, role revocation or role-changing.

EB-11 does not close exact admin role taxonomy.

Role-changing remains outside Entitlements and requires a future Identity/Admin exact task.

## 10. Admin & Support / Web Cabinet boundary

Admin & Support may request protected tariff/manual assignment actions only through public command envelopes.

Web Cabinet may display effective entitlements and submit approved command envelopes only where future UI/runtime tasks allow.

Admin & Support and Web Cabinet do not own tariff/subscription/entitlement/payment state.

Admin & Support and Web Cabinet must not write Entitlements state directly.

Admin & Support and Web Cabinet must not write billing tables directly.

Admin & Support and Web Cabinet must not invent tariffs, prices, limits, retention policy, provider behavior or runtime access.

Admin/Web UI runtime remains blocked.

## 11. Idempotency and audit reference

Every tariff draft/edit/publish/assignment semantic mutation requires an idempotency key.

Missing idempotency key returns `REJECTED`.

Same key + same request fingerprint + prior terminal outcome returns `REPLAYED` or original terminal outcome.

Same key + different request fingerprint returns `IDEMPOTENCY_MISMATCH`.

Audit reference is required as semantic reference only.

Audit retention/storage remains blocked by `OD-013`.

Historical semantic records are append-style and must not be silently rewritten.

## 12. Explicit non-authorization

This decision does not authorize:

- Admin UI;
- Web Cabinet UI;
- Identity role runtime;
- role assignment/change implementation;
- runtime tariff management service;
- billing runtime service;
- database schema;
- repositories;
- persistence;
- migrations;
- physical audit store;
- provider/payment runtime;
- direct table writes;
- direct domain writes from Admin/Web;
- future tariff product values not explicitly approved by owner;
- price/limits/defaults for future tariffs;
- retention/deletion/archive policy;
- secrets/tokens/credentials;
- Docker, CI/CD, deploy or runtime configuration.

## 13. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

- `OD-010` — country-wide availability by market;
- `OD-011` — minimum monitoring frequency safety;
- `OD-013` — billing, audit and personal-data retention.

The following also remain blocked:

- exact global admin role taxonomy beyond module-level semantic capability references;
- role-changing runtime implementation;
- Admin UI;
- Web Cabinet UI;
- persistence and migrations;
- billing runtime;
- provider/payment runtime;
- tariff retirement/deletion;
- future tariff product values not explicitly approved by owner;
- audit retention/storage.

## 14. Use in later roadmap steps

Later exact EB-11 tasks may use this document and `ADR-0015` as approved input for deterministic semantic Admin tariff-management boundary contracts/tests only.

Any runtime Admin UI, Web Cabinet UI, Identity role runtime, billing runtime, persistence, migration, database, provider/payment runtime or actual tariff management service still requires a separate exact task.
