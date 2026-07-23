# Physical Data Model

Version: `1.0`  
Status: `RF-04_ACTIVE_FIRST_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`  
Date: `2026-07-23`  
Module: `14-runtime-foundation-and-autonomous-integration`  
Roadmap step: `RF-04`  
Technical-ID: `RF-04-01-PHYSICAL-DATA-MODEL-20260723`  
Source branch: `main`  
Source base SHA: `32712e1fbf56272e17cf0b5687f1a9a3b6a94c0a`  
RF-03 accepted chain head: `32712e1fbf56272e17cf0b5687f1a9a3b6a94c0a`  
Runtime mutation: `none`  
Production verdict: `NOT_CLAIMED`  
Final target: `READY_FOR_OPERATOR_ACCEPTANCE`

## Authority and scope

GitHub `main` is the authority. This is a design artifact and is not permission to create DDL, ORM mappings, migrations, a database, or a deployment. Modules 01–13 retain authoritative domain-state ownership. Module 14 owns runtime-assembly design, not domain state. An FK supplies reference integrity only and never foreign write authority. Cross-module mutation is performed only through the public contract/service of the owning module. Physical implementation is permitted no earlier than RF-09 and only after its prerequisites. Live providers are disabled by default; a missing optional credential means `PROVIDER_DISABLED_CONTINUE`. Production/public launch is not permitted.

The model is acceptance-runtime design before DDL, ORM, Alembic, Docker, dependency, server, provider, or runtime mutation. No semantic not proven by the current canonical playbooks, handoffs, contracts, architecture, governance, and RF-03 artifacts is inferred.

## Global physical decisions

- PostgreSQL 18.x; one project-owned instance/container and one application database.
- application schema is `mayak`; application tables are never in `public`. The future Alembic version table is in `mayak`.
- Separate migration and application roles. The application role is a non-superuser and has no DDL ownership.
- Lowercase snake_case and owning-module table prefixes are mandatory.
- Internal identifiers are PostgreSQL `uuid`, application-generated UUIDv7, with no extension. External identifiers are bounded `text` and never replace internal IDs.
- Timestamps are `timestamptz` with UTC semantics. Mutable current rows have `row_version bigint NOT NULL CHECK (row_version > 0)`, initially `1`.
- States use bounded `text` plus `CHECK`; PostgreSQL enums are not used. Money is `bigint` minor units plus `char(3)` currency; floats are forbidden.
- JSONB is only bounded, normalized, versioned internal data: internal event/config 64 KiB, listing snapshot 32 KiB, safe provider metadata 8 KiB.
- Fingerprints are lowercase SHA-256 `char(64)`. Raw provider payload, HTML, token, cookie, and secret are forbidden.
- Cross-module FKs use `ON DELETE RESTRICT`; there is no cross-module cascade. No extensions, triggers, stored business procedures, partitioning, or materialized views are in baseline.
- No SQLite authoritative store; no Redis, Celery, RabbitMQ, Kafka, or broker.
- Application authorization precedes mutation. There is no initial RLS; future RLS requires a separately accepted design.
- Baseline indexes are B-tree. Partial indexes are used for due/claimable work. No speculative GIN, BRIN, or full-text indexes.
- Acceptance retention: synthetic records max 14 days; sessions max 24 hours; safe provider evidence max 30 days; raw provider payload retention zero. Cleanup is later, explicit, and project-owned.

## Conventions for the catalogue

Every entry below is one authoritative application table. `common` means `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL` for mutable rows, and `row_version bigint NOT NULL DEFAULT 1 CHECK (row_version > 0)` where the mutability is current/work-state. `uuid` means application-generated UUIDv7. `id` is the primary key unless stated otherwise. Each entry gives owner, purpose, mutability, PK, required columns/types/nullability, FKs/actions, exact uniques, exact indexes/predicate intent, checks, retention, privacy, forbidden contents, and writer boundary.

## Numbered canonical table catalogue (51 tables)

### 1. `platform_idempotency_records`
Owner: module 01. Purpose: closed idempotency results. Mutability: `current-state`. PK: `id uuid`. Required: `scope text NOT NULL`, `idempotency_key varchar(200) NOT NULL`, `request_fingerprint char(64) NOT NULL`, `result jsonb NOT NULL`, `expires_at timestamptz NOT NULL`, `created_at timestamptz NOT NULL`. FKs: none. Unique: `(scope,idempotency_key)`. Indexes: `(expires_at)` for expiry lookup; `(scope,idempotency_key)`. Checks: key/scope nonempty, JSON <=64 KiB, fingerprint lowercase SHA-256. Retention/delete: delete after expiry, max 14 days synthetic. Privacy: operational-sensitive. Forbidden: secrets/raw provider data. Writer: module 01 idempotency boundary only; same key/different fingerprint fails closed.

### 2. `platform_audit_entries`
Owner: module 01. Purpose: immutable security/business audit. Mutability: `append-only`. PK: `id uuid`. Required: `actor_account_id uuid NULL`, `action_code varchar(64) NOT NULL`, `target_type varchar(128) NOT NULL`, `target_id text NULL`, `reason text NOT NULL`, `correlation_id text NOT NULL`, `details jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: actor -> `identity_accounts.id` `RESTRICT` (optional). Unique: none. Indexes: `(created_at)`, `(correlation_id)`, `(actor_account_id,created_at)` audit lookup. Checks: codes <=64, details <=64 KiB, reason nonempty. Retention/delete: project-owned explicit retention; no update. Privacy: operational-sensitive/personal actor. Forbidden: credentials, tokens, raw payload. Writer: authorized audit boundary only.

### 3. `platform_event_outbox`
Owner: module 01. Purpose: transactional domain-event publication. Mutability: `work-state`. PK: `id uuid`. Required: `event_fingerprint char(64) NOT NULL`, `contract_name varchar(128) NOT NULL`, `contract_version varchar(32) NOT NULL`, `payload jsonb NOT NULL`, `state varchar(64) NOT NULL`, `available_at timestamptz NOT NULL`, `lease_started_at timestamptz NULL`, `lease_expires_at timestamptz NULL`, `lease_token uuid NULL`, `attempt_count bigint NOT NULL DEFAULT 0`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: none. Unique: `event_fingerprint`. Indexes: partial `(available_at,id)` WHERE `state IN ('PENDING','RETRY')`; partial `(lease_expires_at)` WHERE `state='CLAIMED'`. Checks: payload <=64 KiB, attempts >=0, bounded state, lease expiry after start. Retention/delete: delete after terminal delivery/reconciliation, synthetic max 14 days. Privacy: operational-sensitive. Forbidden: raw provider data/secrets. Writer: owning transactional publisher; bounded lease only; distinct from notification outbox.

### 4. `identity_accounts`
Owner: module 02. Purpose: authoritative account identity. Mutability: `current-state`. PK: `id uuid`. Required: `phone text NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: none. Unique: no phone uniqueness unless explicit normalized partial design. Indexes: partial `(phone)` WHERE `phone IS NOT NULL`; `(state,created_at)`. Checks: state <=64; phone bounded and normalized when present. Retention/delete: project-owned account policy; no automatic merge. Privacy: personal. Forbidden: password, secret, token, raw provider payload. Writer: Identity service only; account_id is authoritative.

### 5. `identity_provider_links`
Owner: module 02. Purpose: external identity subject link. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `provider_code varchar(64) NOT NULL`, `provider_subject text NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `(provider_code,provider_subject)`. Indexes: `(account_id)`. Checks: identifiers nonempty, <=255; state <=64. Retention/delete: explicit unlink policy. Privacy: personal. Forbidden: token/cookie/credential. Writer: Identity service; adapters cannot create/merge accounts.

### 6. `identity_role_assignments`
Owner: module 02. Purpose: account roles and actor trace. Mutability: `append-only`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `role_code varchar(64) NOT NULL`, `assigned_by_account_id uuid NOT NULL`, `reason text NOT NULL`, `created_at timestamptz NOT NULL`, `revoked_at timestamptz NULL`. FKs: account and actor -> `identity_accounts.id` `RESTRICT`. Unique: `(account_id,role_code,created_at)`. Indexes: partial `(account_id,role_code)` WHERE `revoked_at IS NULL`; `(assigned_by_account_id,created_at)`. Checks: role <=64, reason nonempty, revoke >= creation. Retention/delete: audit retention; append-only. Privacy: personal/operational-sensitive. Forbidden: credentials. Writer: Identity authorization command plus audit.

### 7. `identity_sessions`
Owner: module 02. Purpose: bounded session state. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `token_hash char(64) NOT NULL`, `issued_at timestamptz NOT NULL`, `expires_at timestamptz NOT NULL`, `revoked_at timestamptz NULL`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `token_hash`. Indexes: `(account_id,expires_at)`, partial `(expires_at)` WHERE `revoked_at IS NULL`. Checks: expiry after issue, max 24 hours. Retention/delete: delete at expiry/revocation, max 24 hours. Privacy: personal. Forbidden: raw token/password/secret. Writer: Identity session service; token hash only.

### 8. `identity_link_challenges`
Owner: module 02. Purpose: one-time account-link challenge. Mutability: `work-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `challenge_hash char(64) NOT NULL`, `provider_code varchar(64) NOT NULL`, `expires_at timestamptz NOT NULL`, `consumed_at timestamptz NULL`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `challenge_hash`. Indexes: partial `(expires_at)` WHERE `consumed_at IS NULL`. Checks: expiry after creation, hash lowercase 64. Retention/delete: delete consumed/expired, synthetic max 14 days. Privacy: personal. Forbidden: challenge raw value, token, secret. Writer: Identity linking service.

### 9. `entitlement_tariff_definitions`
Owner: module 03. Purpose: versioned Free/Basic tariff terms. Mutability: `immutable`. PK: `id uuid`. Required: `code varchar(64) NOT NULL`, `version bigint NOT NULL`, `price_minor bigint NOT NULL`, `currency char(3) NOT NULL`, `min_interval_seconds bigint NOT NULL`, `step_seconds bigint NOT NULL`, `active_from timestamptz NOT NULL`, `active_until timestamptz NULL`, `created_at timestamptz NOT NULL`. FKs: none. Unique: `(code,version)`. Indexes: `(code,active_from)`. Checks: price/interval/step nonnegative/positive as policy; currency length 3; active_until > active_from. Retention/delete: immutable, retain synthetic max 14 days only where applicable. Privacy: internal. Forbidden: provider payload. Writer: Entitlement owner only.

### 10. `entitlement_access_grants`
Owner: module 03. Purpose: time-bounded authorization grants. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `tariff_id uuid NOT NULL`, `source_code varchar(64) NOT NULL`, `valid_from timestamptz NOT NULL`, `valid_until timestamptz NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`; tariff -> `entitlement_tariff_definitions.id` `RESTRICT`. Unique: none. Indexes: `(account_id,valid_until)`; partial `(account_id,valid_from,valid_until)` WHERE `state='ACTIVE'`. Checks: valid_until > valid_from; state/source <=64. Retention/delete: explicit entitlement retention. Privacy: personal/operational-sensitive. Forbidden: raw payment payload. Writer: Entitlement service; payment evidence cannot grant automatically.

### 11. `entitlement_usage_counters`
Owner: module 03. Purpose: nonnegative consumption windows. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `counter_code varchar(64) NOT NULL`, `window_start timestamptz NOT NULL`, `window_end timestamptz NOT NULL`, `consumed bigint NOT NULL DEFAULT 0`, `limit_value bigint NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `(account_id,counter_code,window_start)`. Indexes: `(account_id,counter_code,window_end)`. Checks: consumed/limit >=0; window_end > window_start; code <=64. Retention/delete: after window, explicit cleanup. Privacy: personal/operational-sensitive. Forbidden: raw payment data. Writer: Entitlement service only; never Beacon/Scan writes.

### 12. `billing_payment_records`
Owner: module 03. Purpose: normalized payment evidence. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `provider_code varchar(64) NOT NULL`, `external_payment_id varchar(255) NOT NULL`, `amount_minor bigint NOT NULL`, `currency char(3) NOT NULL`, `state varchar(64) NOT NULL`, `observed_at timestamptz NOT NULL`, `safe_metadata jsonb NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `(provider_code,external_payment_id)`. Indexes: `(account_id,observed_at)`, partial `(state,observed_at)` WHERE `state IN ('PENDING','UNKNOWN')`. Checks: amount >=0, currency 3, metadata <=8 KiB, external ID <=255. Retention/delete: safe evidence max 30 days. Privacy: operational-sensitive/personal. Forbidden: raw payment payload/token/secret. Writer: Billing evidence service; no automatic grant.

### 13. `billing_payment_operations`
Owner: module 03. Purpose: idempotent payment effects. Mutability: `work-state`. PK: `id uuid`. Required: `payment_record_id uuid NOT NULL`, `operation_code varchar(64) NOT NULL`, `idempotency_key varchar(200) NOT NULL`, `request_fingerprint char(64) NOT NULL`, `state varchar(64) NOT NULL`, `attempt_count bigint NOT NULL DEFAULT 0`, `next_due_at timestamptz NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: payment -> `billing_payment_records.id` `RESTRICT`. Unique: `(payment_record_id,operation_code,idempotency_key)`. Indexes: partial `(next_due_at)` WHERE `state IN ('PENDING','RETRY')`. Checks: attempts >=0; key <=200; fingerprint 64; unknown effect is not retryable before reconciliation. Retention/delete: explicit synthetic max 14 days. Privacy: operational-sensitive. Forbidden: raw provider response. Writer: Billing service only.

### 14. `billing_reconciliations`
Owner: module 03. Purpose: unresolved payment-effect reconciliation. Mutability: `work-state`. PK: `id uuid`. Required: `payment_record_id uuid NOT NULL`, `operation_id uuid NULL`, `state varchar(64) NOT NULL`, `due_at timestamptz NOT NULL`, `resolved_at timestamptz NULL`, `safe_metadata jsonb NOT NULL`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: payment -> `billing_payment_records.id` `RESTRICT`; operation -> `billing_payment_operations.id` `RESTRICT`. Unique: `(payment_record_id,operation_id)` null-safe explicit design. Indexes: partial `(due_at)` WHERE `resolved_at IS NULL`. Checks: metadata <=8 KiB; resolved_at >= created_at. Retention/delete: safe evidence max 30 days. Privacy: operational-sensitive. Forbidden: raw provider payload. Writer: Billing reconciliation boundary.

### 15. `beacon_beacons`
Owner: module 04. Purpose: account-owned Beacon current state. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `name text NOT NULL`, `current_revision_no bigint NOT NULL`, `current_revision_id uuid NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`; same-Beacon `(id,current_revision_no)` -> `beacon_configuration_revisions(beacon_id,revision_no)` `RESTRICT`. Unique: `(id,current_revision_no)`. Indexes: `(account_id,state)`. Checks: name nonempty; revision positive; state <=64. Retention/delete: explicit account-owned policy. Privacy: personal. Forbidden: secrets/raw provider data. Writer: Beacon service alone accepts/rejects candidates.

### 16. `beacon_configuration_revisions`
Owner: module 04. Purpose: immutable positive configuration revisions. Mutability: `immutable`. PK: `(beacon_id,revision_no)`. Required: `beacon_id uuid NOT NULL`, `revision_no bigint NOT NULL`, `source_url varchar(4096) NOT NULL`, `filter_candidate jsonb NULL`, `accepted_filter jsonb NOT NULL`, `created_by_account_id uuid NOT NULL`, `created_at timestamptz NOT NULL`, `catalog_version_id uuid NULL`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`; creator -> `identity_accounts.id` `RESTRICT`; catalog -> `filter_catalog_versions.id` `RESTRICT`. Unique: `(beacon_id,revision_no)`. Indexes: `(beacon_id,created_at)`. Checks: revision >0, URL <=4096, JSON each <=64 KiB. Retention/delete: immutable; explicit Beacon retention. Privacy: personal/external-untrusted-normalized. Forbidden: HTML/raw payload/token. Writer: Beacon owner service only; catalog only produces candidate.

### 17. `beacon_filter_overrides`
Owner: module 04. Purpose: explicit owner filter decisions. Mutability: `current-state`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `revision_no bigint NOT NULL`, `field_code varchar(128) NOT NULL`, `value jsonb NOT NULL`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: composite revision -> `beacon_configuration_revisions(beacon_id,revision_no)` `RESTRICT`. Unique: `(beacon_id,revision_no,field_code)`. Indexes: `(beacon_id,field_code)`. Checks: field nonempty; value <=64 KiB. Retention/delete: revision-scoped explicit policy. Privacy: personal/external-untrusted-normalized. Forbidden: invented unsupported field/raw provider data. Writer: Beacon service only.

### 18. `beacon_lifecycle_events`
Owner: module 04. Purpose: immutable Beacon lifecycle history. Mutability: `append-only`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `from_state varchar(64) NULL`, `to_state varchar(64) NOT NULL`, `actor_account_id uuid NULL`, `reason text NOT NULL`, `created_at timestamptz NOT NULL`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`; actor -> `identity_accounts.id` `RESTRICT`. Unique: none. Indexes: `(beacon_id,created_at)`. Checks: states <=64, reason nonempty. Retention/delete: explicit audit retention. Privacy: personal/operational-sensitive. Forbidden: secrets/raw payload. Writer: Beacon service plus authorized actor boundary.

### 19. `parser_outcomes`
Owner: module 05. Purpose: bounded normalized parser outcome. Mutability: `immutable`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `run_id uuid NULL`, `route_id uuid NULL`, `outcome_code varchar(64) NOT NULL`, `listing_snapshot jsonb NULL`, `observed_at timestamptz NOT NULL`, `fingerprint char(64) NOT NULL`, `created_at timestamptz NOT NULL`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`; run -> `scan_runs.id` `RESTRICT`; route -> `egress_routes.id` `RESTRICT`. Unique: `(run_id,fingerprint)` null-safe explicit design. Indexes: `(beacon_id,observed_at)`, `(outcome_code,observed_at)`. Checks: outcome distinguishes success/restriction/CAPTCHA/malformed/partial/route failure; snapshot <=32 KiB. Retention/delete: synthetic max 14 days. Privacy: external-untrusted-normalized. Forbidden: body/HTML/raw provider payload. Writer: Parser only; cannot mutate Beacon/Scan/Notification state.

### 20. `scan_schedules`
Owner: module 06. Purpose: one durable schedule per Beacon. Mutability: `current-state`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `interval_seconds bigint NOT NULL`, `next_due_at timestamptz NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`. Unique: `beacon_id`. Indexes: partial `(next_due_at,id)` WHERE `state='ACTIVE'`. Checks: interval >0; state <=64. Retention/delete: explicit Beacon lifecycle. Privacy: operational-sensitive/personal. Forbidden: provider payload. Writer: Scan service only.

### 21. `scan_work_items`
Owner: module 06. Purpose: durable due work with bounded lease. Mutability: `work-state`. PK: `id uuid`. Required: `schedule_id uuid NOT NULL`, `beacon_id uuid NOT NULL`, `due_at timestamptz NOT NULL`, `state varchar(64) NOT NULL`, `lease_started_at timestamptz NULL`, `lease_expires_at timestamptz NULL`, `lease_token uuid NULL`, `attempt_count bigint NOT NULL DEFAULT 0`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: schedule -> `scan_schedules.id` `RESTRICT`; beacon -> `beacon_beacons.id` `RESTRICT`. Unique: `(schedule_id,due_at)`. Indexes: partial `(due_at,id)` WHERE `state IN ('DUE','RETRY')`; partial `(lease_expires_at)` WHERE `state='CLAIMED'`. Checks: attempts >=0; lease expiry after start. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: raw provider data. Writer: Scan scheduler/worker only.

### 22. `scan_runs`
Owner: module 06. Purpose: one run per work item and exact revision execution. Mutability: `work-state`. PK: `id uuid`. Required: `work_item_id uuid NOT NULL`, `beacon_id uuid NOT NULL`, `revision_no bigint NOT NULL`, `parser_outcome_id uuid NULL`, `route_id uuid NULL`, `state varchar(64) NOT NULL`, `started_at timestamptz NOT NULL`, `completed_at timestamptz NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: work/beacon -> respective Scan/Beacon tables `RESTRICT`; revision -> `beacon_configuration_revisions(beacon_id,revision_no)` `RESTRICT`; parser -> `parser_outcomes.id` `RESTRICT`; route -> `egress_routes.id` `RESTRICT`. Unique: `work_item_id`. Indexes: `(beacon_id,started_at)`, partial `(state,started_at)` WHERE `state IN ('RUNNING','PENDING_RECONCILIATION')`. Checks: revision >0; completion >= start. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive/personal. Forbidden: raw response. Writer: Scan service; lost lease/stale version fails closed.

### 23. `scan_listing_observations`
Owner: module 06. Purpose: immutable per-run normalized listing observations. Mutability: `immutable`. PK: `id uuid`. Required: `run_id uuid NOT NULL`, `beacon_id uuid NOT NULL`, `external_listing_key varchar(255) NOT NULL`, `snapshot jsonb NOT NULL`, `observed_at timestamptz NOT NULL`, `fingerprint char(64) NOT NULL`. FKs: run -> `scan_runs.id` `RESTRICT`; beacon -> `beacon_beacons.id` `RESTRICT`. Unique: `(run_id,external_listing_key)`. Indexes: `(beacon_id,observed_at)`. Checks: key <=255, snapshot <=32 KiB. Retention/delete: synthetic max 14 days. Privacy: external-untrusted-normalized. Forbidden: raw HTML/provider payload. Writer: Scan commit boundary only.

### 24. `scan_beacon_listing_state`
Owner: module 06. Purpose: current listing state isolated per Beacon. Mutability: `current-state`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `external_listing_key varchar(255) NOT NULL`, `last_seen_at timestamptz NOT NULL`, `last_snapshot jsonb NOT NULL`, `first_seen_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`, `updated_at timestamptz NOT NULL`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`. Unique: `(beacon_id,external_listing_key)`. Indexes: `(beacon_id,last_seen_at)`. Checks: key <=255, snapshot <=32 KiB. Retention/delete: explicit synthetic cleanup. Privacy: external-untrusted-normalized. Forbidden: raw provider payload/HTML. Writer: Scan service only; no price-change notification.

### 25. `scan_anchors`
Owner: module 06. Purpose: one current rolling anchor per Beacon. Mutability: `current-state`. PK: `id uuid`. Required: `beacon_id uuid NOT NULL`, `anchor_key varchar(255) NOT NULL`, `corrected_by_account_id uuid NULL`, `correction_reason text NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: beacon -> `beacon_beacons.id` `RESTRICT`; actor -> `identity_accounts.id` `RESTRICT`. Unique: `beacon_id`. Indexes: `(beacon_id,updated_at)`. Checks: key <=255; correction actor/reason paired. Retention/delete: current row; correction history is audit elsewhere. Privacy: operational-sensitive/personal. Forbidden: raw payload. Writer: Scan owner with actor/reason for correction.

### 26. `egress_agents`
Owner: module 07. Purpose: project-owned agent registry. Mutability: `current-state`. PK: `id uuid`. Required: `agent_code varchar(128) NOT NULL`, `credential_fingerprint char(64) NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: none. Unique: `agent_code`. Indexes: `(state,agent_code)`. Checks: code nonempty <=128; fingerprint 64 if present. Retention/delete: explicit project-owned cleanup. Privacy: operational-sensitive. Forbidden: secret value, token, cookie. Writer: Egress service/operator boundary only.

### 27. `egress_routes`
Owner: module 07. Purpose: project-owned route metadata. Mutability: `current-state`. PK: `id uuid`. Required: `agent_id uuid NOT NULL`, `route_code varchar(128) NOT NULL`, `endpoint_ref varchar(255) NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: agent -> `egress_agents.id` `RESTRICT`. Unique: `(agent_id,route_code)`. Indexes: `(state,agent_id)`. Checks: refs <=255; no foreign proxy fallback. Retention/delete: explicit project-owned cleanup. Privacy: operational-sensitive. Forbidden: credential/secret/cookie. Writer: Egress service only.

### 28. `egress_agent_heartbeats`
Owner: module 07. Purpose: normalized agent liveness. Mutability: `append-only`. PK: `id uuid`. Required: `agent_id uuid NOT NULL`, `observed_at timestamptz NOT NULL`, `state varchar(64) NOT NULL`, `safe_metadata jsonb NOT NULL`. FKs: agent -> `egress_agents.id` `RESTRICT`. Unique: none. Indexes: `(agent_id,observed_at)`. Checks: metadata <=8 KiB; state <=64. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: secret/credential/network payload. Writer: Agent protocol through Egress service.

### 29. `egress_route_leases`
Owner: module 07. Purpose: bounded route lease for work. Mutability: `work-state`. PK: `id uuid`. Required: `route_id uuid NOT NULL`, `work_item_id uuid NOT NULL`, `lease_token uuid NOT NULL`, `lease_started_at timestamptz NOT NULL`, `lease_expires_at timestamptz NOT NULL`, `state varchar(64) NOT NULL`. FKs: route -> `egress_routes.id` `RESTRICT`; work -> `scan_work_items.id` `RESTRICT`. Unique: `lease_token`; `(route_id,work_item_id)` for active lease design. Indexes: partial `(lease_expires_at)` WHERE `state='ACTIVE'`. Checks: expiry after start; state <=64. Retention/delete: delete after expiry, synthetic max 14 days. Privacy: operational-sensitive. Forbidden: secret value. Writer: Egress lease boundary; failure cannot become parser success.

### 30. `notification_endpoints`
Owner: module 08. Purpose: account-owned delivery endpoint metadata. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `provider_code varchar(64) NOT NULL`, `endpoint_ref varchar(255) NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `(provider_code,endpoint_ref)`. Indexes: `(account_id,state)`. Checks: endpoint <=255; state <=64. Retention/delete: explicit account policy. Privacy: personal/operational-sensitive. Forbidden: token/cookie/secret. Writer: Notification service.

### 31. `notification_events`
Owner: module 08. Purpose: immutable generic notification event. Mutability: `immutable`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `beacon_id uuid NULL`, `run_id uuid NULL`, `source_effect_fingerprint char(64) NOT NULL`, `event_code varchar(64) NOT NULL`, `payload jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: account -> `identity_accounts.id` `RESTRICT`; beacon -> `beacon_beacons.id` `RESTRICT`; run -> `scan_runs.id` `RESTRICT`. Unique: `source_effect_fingerprint`. Indexes: `(account_id,created_at)`, `(beacon_id,created_at)`. Checks: payload <=64 KiB; fingerprint 64. Retention/delete: synthetic max 14 days. Privacy: personal/operational-sensitive. Forbidden: raw provider payload. Writer: Notification service; provider accepted is not human read.

### 32. `notification_outbox`
Owner: module 08. Purpose: one endpoint delivery row per event. Mutability: `work-state`. PK: `id uuid`. Required: `event_id uuid NOT NULL`, `endpoint_id uuid NOT NULL`, `state varchar(64) NOT NULL`, `available_at timestamptz NOT NULL`, `lease_started_at timestamptz NULL`, `lease_expires_at timestamptz NULL`, `lease_token uuid NULL`, `attempt_count bigint NOT NULL DEFAULT 0`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: event -> `notification_events.id` `RESTRICT`; endpoint -> `notification_endpoints.id` `RESTRICT`. Unique: `(event_id,endpoint_id)`. Indexes: partial `(available_at,id)` WHERE `state IN ('PENDING','RETRY')`; partial `(lease_expires_at)` WHERE `state='CLAIMED'`. Checks: attempts >=0; lease expiry after start. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive/personal. Forbidden: token/secret/raw payload. Writer: Notification service; distinct from platform event outbox.

### 33. `notification_delivery_attempts`
Owner: module 08. Purpose: immutable attempt history. Mutability: `append-only`. PK: `id uuid`. Required: `outbox_id uuid NOT NULL`, `attempt_number bigint NOT NULL`, `state varchar(64) NOT NULL`, `provider_reference varchar(255) NULL`, `effect_fingerprint char(64) NOT NULL`, `started_at timestamptz NOT NULL`, `completed_at timestamptz NULL`, `safe_metadata jsonb NOT NULL`. FKs: outbox -> `notification_outbox.id` `RESTRICT`. Unique: `(outbox_id,attempt_number)`. Indexes: `(outbox_id,started_at)`. Checks: attempt >=1; metadata <=8 KiB; completion >= start. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: token/raw response. Writer: Notification delivery boundary.

### 34. `notification_delivery_reconciliations`
Owner: module 08. Purpose: ambiguous delivery effect reconciliation. Mutability: `work-state`. PK: `id uuid`. Required: `attempt_id uuid NOT NULL`, `state varchar(64) NOT NULL`, `due_at timestamptz NOT NULL`, `resolved_at timestamptz NULL`, `safe_metadata jsonb NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: attempt -> `notification_delivery_attempts.id` `RESTRICT`. Unique: `attempt_id`. Indexes: partial `(due_at)` WHERE `resolved_at IS NULL`. Checks: metadata <=8 KiB; state <=64. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: raw provider payload. Writer: Notification reconciliation service; reconcile before retry.

### 35. `telegram_inbound_updates`
Owner: module 09. Purpose: deduplicated normalized Telegram inbound event. Mutability: `append-only`. PK: `id uuid`. Required: `provider_update_id varchar(255) NOT NULL`, `event_fingerprint char(64) NOT NULL`, `schema_version varchar(32) NOT NULL`, `normalized_data jsonb NOT NULL`, `received_at timestamptz NOT NULL`. FKs: none. Unique: `(provider_update_id,event_fingerprint)`. Indexes: `(provider_update_id)`, `(received_at)`. Checks: ID <=255; data <=64 KiB; fingerprint 64. Retention/delete: synthetic max 14 days. Privacy: external-untrusted-normalized. Forbidden: raw payload/token/cookie. Writer: Telegram adapter only.

### 36. `telegram_identity_mappings`
Owner: module 09. Purpose: Telegram identity to Identity provider link. Mutability: `current-state`. PK: `id uuid`. Required: `provider_link_id uuid NOT NULL`, `telegram_user_ref varchar(255) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: provider link -> `identity_provider_links.id` `RESTRICT`. Unique: `telegram_user_ref`; `provider_link_id`. Indexes: `(provider_link_id)`. Checks: ref <=255 and nonempty. Retention/delete: explicit unlink policy. Privacy: personal. Forbidden: token/raw payload. Writer: adapter mapping command; cannot create/merge account.

### 37. `telegram_delivery_mappings`
Owner: module 09. Purpose: Telegram delivery to generic notification attempt. Mutability: `append-only`. PK: `id uuid`. Required: `attempt_id uuid NOT NULL`, `telegram_message_ref varchar(255) NULL`, `created_at timestamptz NOT NULL`. FKs: attempt -> `notification_delivery_attempts.id` `RESTRICT`. Unique: `(attempt_id)`; partial `(telegram_message_ref)` where non-null. Indexes: `(telegram_message_ref)` where non-null. Checks: ref <=255. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: token/raw provider response. Writer: adapter; cannot mark generic business success directly.

### 38. `max_inbound_events`
Owner: module 10. Purpose: deduplicated normalized MAX inbound event. Mutability: `append-only`. PK: `id uuid`. Required: `provider_event_id varchar(255) NOT NULL`, `event_fingerprint char(64) NOT NULL`, `schema_version varchar(32) NOT NULL`, `normalized_data jsonb NOT NULL`, `received_at timestamptz NOT NULL`. FKs: none. Unique: `(provider_event_id,event_fingerprint)`. Indexes: `(provider_event_id)`, `(received_at)`. Checks: data <=64 KiB; ID <=255; fingerprint 64. Retention/delete: synthetic max 14 days. Privacy: external-untrusted-normalized. Forbidden: raw payload/token. Writer: MAX adapter only.

### 39. `max_identity_mappings`
Owner: module 10. Purpose: MAX identity to Identity provider link. Mutability: `current-state`. PK: `id uuid`. Required: `provider_link_id uuid NOT NULL`, `max_user_ref varchar(255) NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: provider link -> `identity_provider_links.id` `RESTRICT`. Unique: `max_user_ref`; `provider_link_id`. Indexes: `(provider_link_id)`. Checks: ref nonempty <=255. Retention/delete: explicit unlink policy. Privacy: personal. Forbidden: token/raw payload. Writer: MAX adapter mapping command; no account create/merge.

### 40. `max_delivery_mappings`
Owner: module 10. Purpose: MAX delivery to generic notification attempt. Mutability: `append-only`. PK: `id uuid`. Required: `attempt_id uuid NOT NULL`, `max_message_ref varchar(255) NULL`, `created_at timestamptz NOT NULL`. FKs: attempt -> `notification_delivery_attempts.id` `RESTRICT`. Unique: `attempt_id`; partial `(max_message_ref)` where non-null. Indexes: `(max_message_ref)` where non-null. Checks: ref <=255. Retention/delete: synthetic max 14 days. Privacy: operational-sensitive. Forbidden: token/raw response. Writer: MAX adapter only; cannot directly mark generic success.

### 41. `max_miniapp_nonces`
Owner: module 10. Purpose: one-time MAX Mini App nonce. Mutability: `work-state`. PK: `id uuid`. Required: `nonce_hash char(64) NOT NULL`, `account_id uuid NULL`, `expires_at timestamptz NOT NULL`, `consumed_at timestamptz NULL`, `created_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: account -> `identity_accounts.id` `RESTRICT`. Unique: `nonce_hash`. Indexes: partial `(expires_at)` WHERE `consumed_at IS NULL`. Checks: hash 64; expiry after creation. Retention/delete: delete consumed/expired, synthetic max 14 days. Privacy: personal. Forbidden: raw nonce/token/secret. Writer: MAX adapter through Identity boundary.

### 42. `support_cases`
Owner: module 11. Purpose: account/operator support case. Mutability: `current-state`. PK: `id uuid`. Required: `account_id uuid NOT NULL`, `opened_by_account_id uuid NOT NULL`, `assigned_to_account_id uuid NULL`, `state varchar(64) NOT NULL`, `subject text NOT NULL`, `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `row_version bigint NOT NULL DEFAULT 1`. FKs: all actors/account -> `identity_accounts.id` `RESTRICT`. Unique: none. Indexes: partial `(state,updated_at)` WHERE `state IN ('OPEN','PENDING')`; `(account_id,updated_at)`. Checks: subject nonempty; state <=64. Retention/delete: explicit support retention. Privacy: personal. Forbidden: secrets/raw provider payload. Writer: Support service; foreign changes via owning commands.

### 43. `support_case_notes`
Owner: module 11. Purpose: append-only public/internal notes. Mutability: `append-only`. PK: `id uuid`. Required: `case_id uuid NOT NULL`, `author_account_id uuid NOT NULL`, `visibility varchar(64) NOT NULL`, `body text NOT NULL`, `created_at timestamptz NOT NULL`. FKs: case -> `support_cases.id` `RESTRICT`; author -> `identity_accounts.id` `RESTRICT`. Unique: none. Indexes: `(case_id,created_at)`. Checks: visibility exactly bounded public/internal policy; body nonempty. Retention/delete: explicit support retention; internal never customer-visible. Privacy: personal. Forbidden: credentials/secrets. Writer: authorized Support command only.

### 44. `support_case_events`
Owner: module 11. Purpose: append-only case audit with actor/reason. Mutability: `append-only`. PK: `id uuid`. Required: `case_id uuid NOT NULL`, `actor_account_id uuid NOT NULL`, `event_code varchar(64) NOT NULL`, `reason text NOT NULL`, `details jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: case -> `support_cases.id` `RESTRICT`; actor -> `identity_accounts.id` `RESTRICT`. Unique: none. Indexes: `(case_id,created_at)`, `(actor_account_id,created_at)`. Checks: details <=64 KiB; reason nonempty; code <=64. Retention/delete: explicit audit retention. Privacy: personal/operational-sensitive. Forbidden: secrets/raw payload. Writer: Support service/audit boundary.

### 45. `filter_catalog_versions`
Owner: module 13. Purpose: immutable catalog version/provenance. Mutability: `immutable`. PK: `id uuid`. Required: `version_code varchar(32) NOT NULL`, `provenance_ref varchar(255) NOT NULL`, `evidence_fingerprint char(64) NOT NULL`, `state varchar(64) NOT NULL`, `created_at timestamptz NOT NULL`. FKs: none. Unique: `version_code`; `evidence_fingerprint`. Indexes: `(state,created_at)`. Checks: code <=32; provenance <=255; fingerprint 64. Retention/delete: immutable synthetic max 14 days unless accepted catalog policy. Privacy: internal/operational-sensitive. Forbidden: invented complete catalog/raw payload. Writer: Filter Catalog publisher only.

### 46. `filter_definitions`
Owner: module 13. Purpose: version-scoped evidence-backed filter definitions. Mutability: `immutable`. PK: `id uuid`. Required: `catalog_version_id uuid NOT NULL`, `field_code varchar(128) NOT NULL`, `label text NOT NULL`, `support_state varchar(64) NOT NULL`, `evidence_id uuid NULL`, `created_at timestamptz NOT NULL`. FKs: catalog -> `filter_catalog_versions.id` `RESTRICT`; evidence -> `filter_evidence_references.id` `RESTRICT`. Unique: `(catalog_version_id,field_code)`. Indexes: `(catalog_version_id,support_state)`, `(field_code)`. Checks: code nonempty <=128; support state blocks unsupported/stale/ambiguous. Retention/delete: parent-scoped immutable retention. Privacy: internal/external-untrusted-normalized. Forbidden: invented support. Writer: Filter Catalog only.

### 47. `filter_options`
Owner: module 13. Purpose: version-scoped options. Mutability: `immutable`. PK: `id uuid`. Required: `definition_id uuid NOT NULL`, `option_code varchar(128) NOT NULL`, `label text NOT NULL`, `sort_order bigint NOT NULL`, `created_at timestamptz NOT NULL`. FKs: definition -> `filter_definitions.id` `RESTRICT`. Unique: `(definition_id,option_code)`. Indexes: `(definition_id,sort_order)`. Checks: sort_order >=0; code nonempty <=128. Retention/delete: parent-scoped immutable retention. Privacy: internal/external-untrusted-normalized. Forbidden: raw provider content. Writer: Filter Catalog only.

### 48. `filter_dependencies`
Owner: module 13. Purpose: version-scoped dependency rules. Mutability: `immutable`. PK: `id uuid`. Required: `catalog_version_id uuid NOT NULL`, `source_definition_id uuid NOT NULL`, `depends_on_definition_id uuid NOT NULL`, `rule jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: catalog and both definitions -> their exact parents, all `RESTRICT`. Unique: `(catalog_version_id,source_definition_id,depends_on_definition_id)`. Indexes: `(catalog_version_id,source_definition_id)`. Checks: rule <=64 KiB; source != dependency. Retention/delete: parent-scoped immutable retention. Privacy: internal. Forbidden: unsupported/invented rule. Writer: Filter Catalog only.

### 49. `filter_category_applicability`
Owner: module 13. Purpose: evidence-bound category applicability. Mutability: `immutable`. PK: `id uuid`. Required: `catalog_version_id uuid NOT NULL`, `category_code varchar(128) NOT NULL`, `definition_id uuid NOT NULL`, `applicability_state varchar(64) NOT NULL`, `evidence_id uuid NULL`, `created_at timestamptz NOT NULL`. FKs: catalog/definition/evidence -> respective Filter Catalog tables `RESTRICT`. Unique: `(catalog_version_id,category_code,definition_id)`. Indexes: `(catalog_version_id,category_code)`, `(definition_id)`. Checks: code <=128; state blocks unsupported/stale/ambiguous. Retention/delete: parent-scoped immutable retention. Privacy: internal/external-untrusted-normalized. Forbidden: country-wide unsupported claim without accepted evidence. Writer: Filter Catalog only.

### 50. `filter_evidence_references`
Owner: module 13. Purpose: safe provenance reference. Mutability: `immutable`. PK: `id uuid`. Required: `catalog_version_id uuid NOT NULL`, `reference_code varchar(255) NOT NULL`, `evidence_fingerprint char(64) NOT NULL`, `safe_metadata jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: catalog -> `filter_catalog_versions.id` `RESTRICT`. Unique: `(catalog_version_id,reference_code)`; `evidence_fingerprint`. Indexes: `(catalog_version_id,created_at)`. Checks: reference <=255; fingerprint 64; metadata <=8 KiB. Retention/delete: safe provider evidence max 30 days. Privacy: external-untrusted-normalized/operational-sensitive. Forbidden: raw payload/HTML/token. Writer: Filter Catalog evidence boundary.

### 51. `filter_capability_profiles`
Owner: module 13. Purpose: version-scoped capability profile. Mutability: `immutable`. PK: `id uuid`. Required: `catalog_version_id uuid NOT NULL`, `profile_code varchar(128) NOT NULL`, `capabilities jsonb NOT NULL`, `created_at timestamptz NOT NULL`. FKs: catalog -> `filter_catalog_versions.id` `RESTRICT`. Unique: `(catalog_version_id,profile_code)`. Indexes: `(catalog_version_id,profile_code)`. Checks: code <=128; capabilities <=64 KiB. Retention/delete: parent-scoped immutable retention. Privacy: internal/external-untrusted-normalized. Forbidden: invented complete catalog. Writer: Filter Catalog only; builder creates candidates, never mutates Beacon.

## Exact ownership counts and domain invariants

| Module | Tables | Count |
|---|---|---:|
| 01 Platform & Contracts | 1–3 | 3 |
| 02 Identity & Access | 4–8 | 5 |
| 03 Entitlements & Billing | 9–14 | 6 |
| 04 Beacon Management | 15–18 | 4 |
| 05 Avito Parser Adapter | 19 | 1 |
| 06 Scan Orchestration & Listing State | 20–25 | 6 |
| 07 Egress Routing | 26–29 | 4 |
| 08 Notification Delivery | 30–34 | 5 |
| 09 Telegram Adapter | 35–37 | 3 |
| 10 MAX Adapter | 38–41 | 4 |
| 11 Admin & Support | 42–44 | 3 |
| 12 Web Cabinet | none | 0 |
| 13 Filter Catalog & Builder | 45–51 | 7 |
| 14 Runtime Foundation | none | 0 |

Platform invariants: `(scope,idempotency_key)` is unique; request fingerprints are required; same key/different fingerprint fails closed; expiry lookup is indexed; audit is append-only; event fingerprint is unique; outbox leases are bounded; platform and notification outboxes are distinct.

Identity invariants: `account_id` is authoritative; phone is optional; there is no password column; automatic account merge is disabled; provider subject is unique per provider; role changes carry actor, reason, and audit; sessions store only token hashes; link challenges store only challenge hashes.

Entitlement/Billing invariants: Free/Basic tariffs are versioned; Basic is `99000` RUB minor units with minimum/step `300` seconds; Free permits one active Beacon with minimum/step `10800` seconds; grants are time-bounded; payment evidence never automatically grants entitlement; paid expiry never automatically selects a Free Beacon; counters are nonnegative; external payment IDs are unique in provider scope; raw payment payload is forbidden; operations have idempotency/fingerprint; unknown effect requires reconciliation before retry.

Beacon invariants: one account owns each Beacon; revisions are immutable and positive; the current revision is same-Beacon composite-integrity constrained; source URL is preserved; Filter Catalog produces candidates only; Beacon service alone accepts/rejects; lifecycle history is append-only; stale revision/row_version fails closed.

Parser invariants: outcomes are bounded and normalized; success, restriction/CAPTCHA, malformed, partial, and route failure are distinct; raw body/HTML/provider payload is forbidden; parser cannot mutate Beacon, Scan, or Notification state.

Scan invariants: one durable schedule per Beacon; due work is durable and leased; schedule/due identity is unique; one run per work item; run references exact revision; observations are immutable and unique per run/external key; listing state is unique per Beacon/external key and isolated across Beacons; one current anchor per Beacon; corrections require actor/reason; baseline emits no notification; no price-change notification; lost lease/stale version cannot commit.

Egress invariants: only project-owned agents/routes/heartbeats/leases; credential reference/fingerprint only; no secret value; lease token unique; no foreign proxy fallback; route failure cannot become parser success.

Notification invariants: endpoints are account-owned; generic events are immutable and unique by source effect; one outbox row per event/endpoint; leases are bounded; attempt number is unique per outbox; provider acceptance is not human read; ambiguous attempts require reconciliation; platform and notification outboxes are explicitly different.

Telegram/MAX invariants: inbound deduplication uses provider ID and fingerprint; only normalized/versioned data is stored; no raw payload/token; identity mappings reference Identity provider links; adapters cannot create/merge accounts; delivery mappings reference generic Notification attempts; adapters cannot directly mark generic business success; MAX nonce stores a hash only; missing credentials do not block core readiness.

Support invariants: cases reference account and operator actors; notes are append-only with explicit public/internal visibility; internal notes are never customer-visible; events are append-only with actor/reason; foreign mutation uses owning-module commands.

Filter Catalog invariants: versions and provenance are immutable; children are version-scoped; unsupported/stale/ambiguous fields remain blocked; no invented complete Avito catalog; country-wide unsupported remains absent without accepted evidence profile; builder/candidate never mutates Beacon directly.

## Web Cabinet boundary

Module 12 owns zero authoritative tables. It consumes Identity sessions and owning-module services/read models. Browser/client state is not authority. It has no duplicate Account, Beacon, Tariff, Scan, Notification, or Support store and no persistent builder-draft table. Any future projection requires provenance, freshness, and rebuild rules.

## Required FK matrix and ownership notes

All FKs are `ON DELETE RESTRICT`; every cross-module FK is reference integrity only and never foreign write authority. The complete relationship set is:

- `platform_audit_entries.actor_account_id` -> `identity_accounts`; platform idempotency/outbox have no domain FK.
- Identity children (`identity_provider_links`, `identity_role_assignments`, `identity_sessions`, `identity_link_challenges`) -> `identity_accounts`; role actor also -> account.
- Entitlement/Billing -> account; grants -> tariff; payment operations/reconciliations -> payment and applicable operation.
- `beacon_beacons` -> account and same-Beacon current revision; revisions -> Beacon, optional Filter Catalog version, and creator account; overrides -> exact revision.
- Scan schedule/work/run/state/anchor -> Beacon; run -> exact Beacon revision, parser outcome, and optional route; parser outcome -> Beacon and optional route.
- Egress lease -> route and work; route -> agent; heartbeat -> agent.
- Notification endpoint/event -> account; event -> optional Beacon/run; outbox -> event/endpoint; attempt -> outbox; reconciliation -> attempt.
- Telegram/MAX identity mappings -> `identity_provider_links`; delivery mappings -> `notification_delivery_attempts`; MAX nonce -> optional account.
- Support case/note/event actor references -> accounts; notes/events -> case.
- Filter children -> exact catalog/definition/evidence parent. All children are blocked from cross-version references.

The composite Beacon current-revision FK and all cyclic/composite relationships are implementation-order concerns for the later migration plan; no DDL is included here.

## Constraint policy

Nonnegative money, usage, and attempt values are mandatory. `valid_until > valid_from`, `window_end > window_start`, expiry after creation, lease expiry after lease start, completion not before start, positive revision/row-version/interval, currency length 3, fingerprint length 64, state/code max 64, external/reference ID max 255, URL max 4096, idempotency key max 200, contract name max 128, contract version max 32, and nonempty required identifiers are mandatory. Nullable uniqueness is represented only by a partial index or explicit null-safe design. Every bounded JSON value uses its declared limit. Business states remain bounded text plus checks.

## Index intent

The baseline has B-tree indexes for due schedules, claimable scan work, expired leases, claimable platform outbox, claimable notification outbox, due billing and notification reconciliation, account Beacon lookup, Beacon run/listing history, account entitlement evaluation, provider inbound deduplication, support queue, expiry/retention cleanup, correlation/audit lookup, and catalog version/category/filter lookup. Work indexes are partial on the relevant pending/due/claimable state; cleanup indexes target expiry timestamps; dedup indexes target provider ID plus fingerprint. No GIN, BRIN, full-text, partition, trigger, or speculative index is part of baseline.

## Transaction implications

- Idempotency and the owning mutation later share a defined commit boundary.
- A domain event outbox row is inserted transactionally with the owning commit.
- Notification event/outbox creation is duplicate-safe.
- Claims use PostgreSQL bounded leases.
- An ambiguous external effect requires reconciliation before retry.
- Cross-module atomicity is not assumed.
- UI/provider adapters never write a foreign table directly.
- Lost lease, stale version, and same-key/different-fingerprint cases fail closed.
- Exact transaction/isolation/claim algorithm belongs to a separate next RF-04 artifact.

## Migration and security model

This is target design only; it contains no DDL or migration. RF-09 later creates the Alembic zero-to-head chain. The migration role owns DDL; the application role has no DDL. Cyclic/composite FKs are installed in deterministic order. Downgrade is allowed only if separately proven safe; otherwise roll-forward is required. No foreign or production backfill is allowed.

| Table class | Tables/fields | Handling |
|---|---|---|
| internal | tariff definitions, platform contracts, catalog structure | project-owned normalized records |
| personal | account phone, sessions, provider mappings, Beacon ownership, entitlements, notification endpoints, support actors/content | access-controlled, synthetic acceptance only |
| operational-sensitive | audit, outboxes, leases, routes, payment evidence, attempts, reconciliations | bounded metadata and retention |
| external-untrusted-normalized | parser outcomes, listing snapshots, Telegram/MAX normalized data, Filter provenance | evidence-bound, size-limited, never raw |

Personal fields are account phone, account ownership/actor identifiers, provider subjects, token/challenge hashes, Beacon source URL/configuration, entitlement/payment association, endpoint references, adapter mappings, nonce/account association, and support content. Credentials remain external file-backed secrets; only safe reference/fingerprint may be persisted. Forbidden contents throughout are raw provider payloads, HTML, tokens, cookies, secret values, passwords, populated environment values, and production personal data. Synthetic tests only. No initial RLS; future RLS requires accepted design.

## Explicit non-goals

No source code; SQLAlchemy; Alembic implementation; SQL/DDL; database/container; dependency change; Docker/Compose; server directory/user/role mutation; API/worker/scheduler; provider call; credential; ingress; health claim; production claim.

## Remaining RF-04 work

- transaction/outbox boundaries;
- runtime process/package layout;
- migration plan;
- runtime topology;
- configuration schema;
- secrets boundary;
- environment-record candidate;
- consistency audit;
- RF-04 closure/status transition.

## Acceptance checklist

This artifact contains exactly 51 numbered canonical catalogue entries, exact ownership counts `3/5/6/4/1/6/4/5/3/4/3/0/7/0`, all per-table specification fields, the complete FK matrix, constraint/index/transaction/migration/security/privacy sections, Web Cabinet boundary, non-goals, and remaining RF-04 work. It introduces no DDL, ORM, migration, runtime, provider, dependency, Docker, database, server, or production claim.

RF-04 is active and not closed. RF-05 is not started. Runtime mutation is none. Production is blocked. `PRODUCTION_READY` is not claimed.

RF-04_PHYSICAL_DATA_MODEL_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE

## Final state

RF04_PHYSICAL_DATA_MODEL_PUBLISHED
