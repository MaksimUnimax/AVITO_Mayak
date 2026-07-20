# Маяк Авито — Admin & Support Owner Decisions Capture v1.0

**Status:** OWNER-APPROVED decisions; repository capture pending independent acceptance
**Date:** 2026-07-20
**Module:** `11-admin-and-support`
**Roadmap step:** `AS-01`
**Technical ID:** `AS-01-PRECOMMIT-GATE-CORRECTION-REFRESH-TO-4622B2-20260720-006`
**Source tasks:** `AS-01-ADMIN-SUPPORT-OWNER-DECISIONS-CAPTURE-20260720-001`; `AS-01-ADMIN-SUPPORT-OWNER-DECISIONS-CAPTURE-REFRESH-TO-8D0682-20260720-002`; `AS-01-CLEAN-CHECKOUT-AND-GOVERNANCE-CAPTURE-20260720-003`; `AS-01-SSH-TRANSPORT-DIAGNOSIS-AND-CAPTURE-20260720-004`; `AS-01-HASH-EVIDENCE-CORRECTION-REFRESH-TO-8C9C28-20260720-005`
**Governance reference:** `ADR-0027`

## Purpose and boundary

This is an owner-decision capture for future exact semantic tasks. It is not product code, an executable contract or a wire schema. It does not authorize UI, runtime, database, migrations, providers, infrastructure or deploy. Ownership of related modules does not change. Numbered open decisions are not closed by assumption.

## Twelve owner decisions

### 1. First scope

The first scope includes safe read/explain; account summary; Beacon summary; tariff/access/limit summary; scan/anchor summary; limited manual actions; support cases/work items; internal support notes; and append-style audit. The authoritative effect is performed by the owning module, not Admin & Support.

### 2. Roles

Role change is initiated only through Identity & Access. It requires a verified actor, server-side capability/scope, target `account_id`, old/new role references, reason, idempotency, correlation/causation, Identity outcome and audit reference. Provider username, display name, chat title, Telegram/MAX ID, UI flag and client state are not authorization. Exact role taxonomy remains with Identity & Access.

### 3. Tariff catalog

Tariff create/edit/publish/deactivate is initiated only through Entitlements & Billing and requires actor, reason, version/effective interval, explicit intended effect, Entitlements outcome and audit. Prices, periods, currencies, limits and retroactive-effect policy are not invented here. Published tariff history cannot be silently rewritten. Changing active tariff conditions requires a future approved version/effect policy.

### 4. User access

Assign/change/extend/cancel subscription and create/revoke manual access grants are initiated only through Entitlements & Billing. They require a verified actor, target `account_id`, exact scope, explicit effective interval, reason, idempotency, owning-module outcome and audit. Current manual access grants require both `starts_at` and `ends_at`; open-ended grants remain blocked unless separately approved later. Payment screenshots, chat messages, UI toggles and provider flags are not authority.

### 5. Anchors

Anchor read/reset/rebase/recovery requests go only through Scan Orchestration and require `beacon_id`, current safe anchor summary, freshness/stale/ambiguous indicator, reason, intended action, Scan outcome and audit. Direct Scan writes, false confirmed-new claims, unsafe baseline deletion, clearing anchors on external/ambiguous failure, hard-coded anchor-window size, full listing archive and raw Avito payload are prohibited.

### 6. Beacon support

Future Beacon support action goes only through Beacon Management and preserves current working configuration, patch-based save, only supplied fields, no stale full-form overwrite, no unsupported/ambiguous field mutation, reload of authoritative current state after successful save, audit reason and no rewriting of committed scan/audit facts. This task does not authorize Beacon mutation contracts or runtime.

### 7. Manual-action minimum

Every manual action requires `support_action_id`; `support_case_id` when applicable; verified actor account/role/scope; target; action family; reason; idempotency key; semantic fingerprint; owning module; requested-command reference; explicit outcome; `correlation_id`; `causation_id`; timestamp-policy reference; safe evidence reference; and append-style audit.

### 8. No direct writes

Admin & Support does not write foreign authoritative state, call provider APIs, change routes/services/credentials, bypass authorization, hide outcomes or calculate entitlements independently.

### 9. Safe read/explain

Support reads are server-authorized, scoped, provenance-aware, freshness-aware, redacted and minimal-PII. `fresh`, `stale`, `unknown`, `ambiguous` and `forbidden` remain distinguishable. Ordinary support records contain no secrets, passwords, one-time codes, `.env`, private keys, shell history, process arguments, raw provider payloads, full private-message archives or excess PII.

### 10. Support notes

Support notes are internal by default, case-bound, written by a verified actor, redacted, append-style, not authoritative business state and not mutation authority. Customer-visible explanation remains a separate future safe form.

### 11. Notifications

Direct/blind resend is prohibited. Admin & Support may only prepare an authorized request to Notification Delivery. Notification Delivery retains ownership of outbox, attempts, lifecycle, idempotency, duplicate protection, replay/reconciliation and ambiguous provider effect. Direct Telegram/MAX send and direct outbox mutation are prohibited.

### 12. Blocked capabilities

Until separate explicit policies, break-glass, impersonation, login as user, session takeover, silent privileged override, full data export, full account deletion and retention/deletion implementation remain blocked.

## Ownership consequences

- Identity & Access owns account identity, roles and authorization.
- Entitlements & Billing owns tariff, subscription, grant and effective-access state.
- Beacon Management owns Beacon lifecycle and current configuration.
- Scan Orchestration owns scans, baseline, anchors/listing state and recovery facts.
- Notification Delivery owns generic outbox/delivery lifecycle.
- Egress Routing owns routes, agents and transport state.
- Telegram/MAX adapters own provider-specific mapping.
- Admin & Support owns only support cases/work items, safe notes, explanations/read models, command envelopes and support audit references.

## Open decisions preserved

This capture does not choose exact role taxonomy; tariff prices, periods, currencies or limits; tariff retroactive/version migration policy; exact command/wire names or schemas; exact anchor reset/rebase policy; anchor-window size; notification resend/suppression policy; staffing/approvals; Admin UI; search/filter capabilities; rate limits; evidence attachments; or audit retention.

`OD-006`, `OD-007`, `OD-008`, `OD-013` and `OD-014` remain open, as do other numbered open decisions unless governed by a separate accepted ADR. `OPEN_DECISIONS.md` is unchanged.

## Blocked implementation gates

No code, semantic contracts, tests, runtime, persistence, UI, provider calls, secrets or infrastructure are authorized by this document.
