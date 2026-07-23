# Migration and Schema Evolution Plan

Version: 1.0
Status: RF-04_ACTIVE_FOURTH_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE
Date: 2026-07-23
Module: 14-runtime-foundation-and-autonomous-integration
Roadmap step: RF-04
Technical-ID: RF-04-04-MIGRATION-AND-SCHEMA-EVOLUTION-PLAN-20260723
Source branch: main
Source base SHA: 37785e2cde19b80ba69edd23d07d6b38949dc0cb
RF-04-01 accepted chain head: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
RF-04-02 accepted chain head: 710f965a66488f99b4c3cc9cf9f44bef54c7434a
RF-04-03 accepted SHA: 37785e2cde19b80ba69edd23d07d6b38949dc0cb
Canonical domain table count: 51
Runtime mutation: none
Production verdict: NOT_CLAIMED
Final target: READY_FOR_OPERATOR_ACCEPTANCE

## 1. Authority and scope

GitHub `main` is the sole source of truth. RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`, RF-04-02 through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`, and RF-04-03 at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`. This artifact is documentation/design only: no migration implementation exists or is created by this task.

The authoritative database is PostgreSQL 18.x. The persistence stack is SQLAlchemy 2.x + Psycopg 3.x + Alembic. The physical model remains authoritative for exactly 51 domain tables. `alembic_version` is Alembic infrastructure state and is not an additional domain table. No table name, ownership, FK, constraint or index from the physical model may be silently changed. Modules 01–13 retain domain ownership; RF-09 owns physical implementation. RF-04 remains active and RF-05 remains not started.

This plan covers deterministic zero-to-head migration, schema verification, recovery, privileges and future evolution. It creates no Alembic files, migrations, SQL, ORM, database, roles, containers, runtime code, dependencies, CI or server resources.

## 2. Accepted schema invariants

- Exactly 51 canonical domain tables, owned in order by modules 01–13 as `3/5/6/4/1/6/4/5/3/4/3/0/7`; module 12 owns zero authoritative tables.
- One authoritative PostgreSQL database and one schema unless the accepted physical model explicitly says otherwise; the accepted model uses project-owned schema `mayak`.
- Separate migration and application roles; the application role has no DDL authority.
- No SQLite authoritative path, foreign database, or PostgreSQL extension without a future separately proven need.
- One Alembic head; deterministic from-zero upgrade; no API/worker/scheduler automatic migration.
- No direct foreign-module state mutation and no raw provider payload persistence.
- No production personal data in automated migration tests; synthetic fixtures only.
- No destructive operation without a backup/recovery gate; migration success does not imply production readiness.
- All physical-model `ON DELETE RESTRICT` semantics, composite identity, bounded JSONB, UUIDv7 application identifiers, timestamp and check semantics remain unchanged.
- Platform event outbox and notification outbox remain distinct, with the accepted transaction and outbox boundaries preserved.

## 3. Current repository migration state

The following are evidence-backed observations from the expected-base tree:

| Inspected path | State | Evidence basis | Future RF owner |
|---|---|---|---|
| `alembic.ini` | ABSENT | exact filesystem and tracked-tree lookup at source base | RF-09 |
| `alembic/` | ABSENT | exact filesystem and tracked-tree lookup at source base | RF-09 |
| `migrations/` | ABSENT | exact filesystem and tracked-tree lookup at source base | RF-09 |
| revision files | ABSENT | no `alembic/` or `migrations/` path; no revision files in tracked tree | RF-09 |
| SQLAlchemy/Alembic runtime dependencies | PRESENT | `pyproject.toml` declares `sqlalchemy`, `alembic`, `psycopg`, and `psycopg2`; this task does not alter them | RF-06/RF-09 |
| executable migration tests | ABSENT | repository-wide search found no migration implementation or DB-backed migration test; contract references are deferred gates only | RF-07/RF-09 |

The current dependency declarations do not prove a usable persistence runtime. No current source path is treated as an Alembic implementation.

## 4. Migration ownership model

Module 14/RF-09 owns the migration mechanism and orchestration. Each table retains exactly one domain owner from the physical model. A migration file may create or alter several tables only when its revision batch explicitly maps every affected table and preserves each table owner. The migration role executes DDL; the application role never executes DDL. Runtime code does not call Alembic. API, worker and scheduler start only after schema compatibility proof.

Migration implementation cannot redefine domain semantics. Cross-module FK changes require both owning contracts to remain accepted. Migration evidence is operational evidence, not domain ownership transfer. No FK grants foreign write authority, and no migration may authorize direct foreign-module mutation.

## 5. Canonical revision graph

The initial implementation is one deterministic, linear, single-head graph:

`RF09_BOOTSTRAP -> RF09_M01 -> RF09_M02 -> RF09_M03 -> RF09_M13 -> RF09_M04 -> RF09_M07 -> RF09_M06 -> RF09_M05 -> RF09_M08 -> RF09_M09 -> RF09_M10 -> RF09_M11 -> RF09_FINALIZE`

`RF09_BOOTSTRAP` establishes the `mayak` schema, role/grant bootstrap boundary and Alembic metadata. Every module with accepted tables has one non-empty batch: `RF09_M01`, `RF09_M02`, `RF09_M03`, `RF09_M04`, `RF09_M05`, `RF09_M06`, `RF09_M07`, `RF09_M08`, `RF09_M09`, `RF09_M10`, `RF09_M11`, and `RF09_M13`. Module 12 is explicitly represented as `NO_TABLE_BATCH` and is not an Alembic revision. `RF09_FINALIZE` is the single final constraints/index/current-head verification revision for accepted deferred dependencies.

The labels are symbolic planned labels, not fabricated Alembic hashes. Every planned revision is mapped to RF-09. There are no merge revisions, branch heads, or no-op revisions. The deterministic topological rule is: FK prerequisites first; lower module number when batches are otherwise eligible; physical-model table order within a batch; defer a cross-module constraint only when creation cannot otherwise be safe; cycles are forbidden after deferred constraints are accounted for. The accepted physical cycles are explicit deferred-constraint cases, not unresolved graph cycles. If a future accepted FK cycle cannot be implemented with deferred constraints, the correct result is `STOP_SCOPE_REQUIRED`.

## 6. Module migration batch matrix

| Module/name | Count | Accepted tables | Batch | Predecessor prerequisites | Tables created here | Deferred FKs/indexes | Table owner | Implementation owner | Proof owner |
|---|---:|---|---|---|---|---|---|---|---|
| 01 Platform & Contracts | 3 | `platform_idempotency_records`; `platform_audit_entries`; `platform_event_outbox` | `RF09_M01` | `RF09_BOOTSTRAP` | yes | audit actor FK may be deferred; baseline indexes | M01 | RF-09 | RF-09 with M01 contract proof |
| 02 Identity & Access | 5 | `identity_accounts`; `identity_provider_links`; `identity_role_assignments`; `identity_sessions`; `identity_link_challenges` | `RF09_M02` | `RF09_M01` | yes | none beyond normal FK/index creation | M02 | RF-09 | RF-09 with M02 proof |
| 03 Entitlements & Billing | 6 | `entitlement_tariff_definitions`; `entitlement_access_grants`; `entitlement_usage_counters`; `billing_payment_records`; `billing_payment_operations`; `billing_reconciliations` | `RF09_M03` | `RF09_M02` | yes | none | M03 | RF-09 | RF-09 with M03 proof |
| 04 Beacon Management | 4 | `beacon_beacons`; `beacon_configuration_revisions`; `beacon_filter_overrides`; `beacon_lifecycle_events` | `RF09_M04` | `RF09_M13`, `RF09_M03` | yes | Beacon/current-revision cycle deferred | M04 | RF-09 | RF-09 with M04 proof |
| 05 Avito Parser Adapter | 1 | `parser_outcomes` | `RF09_M05` | `RF09_M04`, `RF09_M07`, `RF09_M06` | yes | run/route FKs deferred; outcome indexes | M05 | RF-09 | RF-09 with M05 proof |
| 06 Scan Orchestration & Listing State | 6 | `scan_schedules`; `scan_work_items`; `scan_runs`; `scan_listing_observations`; `scan_beacon_listing_state`; `scan_anchors` | `RF09_M06` | `RF09_M04`, `RF09_M02` | yes | parser/route/run cycle FKs deferred | M06 | RF-09 | RF-09 with M06 proof |
| 07 Egress Routing | 4 | `egress_agents`; `egress_routes`; `egress_agent_heartbeats`; `egress_route_leases` | `RF09_M07` | `RF09_M01` | yes | work-item lease FK may be deferred | M07 | RF-09 | RF-09 with M07 proof |
| 08 Notification Delivery | 5 | `notification_endpoints`; `notification_events`; `notification_outbox`; `notification_delivery_attempts`; `notification_delivery_reconciliations` | `RF09_M08` | `RF09_M02`, `RF09_M04`, `RF09_M05`, `RF09_M06` | yes | event/run FKs are immediate after prerequisites | M08 | RF-09 | RF-09 with M08 proof |
| 09 Telegram Adapter | 3 | `telegram_inbound_updates`; `telegram_identity_mappings`; `telegram_delivery_mappings` | `RF09_M09` | `RF09_M02`, `RF09_M08` | yes | none | M09 | RF-09 | RF-09 with M09 proof |
| 10 MAX Adapter | 4 | `max_inbound_events`; `max_identity_mappings`; `max_delivery_mappings`; `max_miniapp_nonces` | `RF09_M10` | `RF09_M02`, `RF09_M08` | yes | none | M10 | RF-09 | RF-09 with M10 proof |
| 11 Admin & Support | 3 | `support_cases`; `support_case_notes`; `support_case_events` | `RF09_M11` | `RF09_M02` | yes | none | M11 | RF-09 | RF-09 with M11 proof |
| 12 Web Cabinet | 0 | none | `NO_TABLE_BATCH` | `RF09_M02` read boundary only | no | no Alembic revision; no indexes | none | RF-09 mechanism only | RF-09 with M12 boundary proof |
| 13 Filter Catalog & Builder | 7 | `filter_catalog_versions`; `filter_definitions`; `filter_options`; `filter_dependencies`; `filter_category_applicability`; `filter_evidence_references`; `filter_capability_profiles` | `RF09_M13` | `RF09_BOOTSTRAP` | yes | evidence/definition child ordering is immediate | M13 | RF-09 | RF-09 with M13 proof |

M12 remains a presentation/application boundary. It owns no authoritative table and no invented Web-owned table is permitted.

## 7. Table-to-revision mapping

The following are exactly the 51 accepted domain-table rows. Identity and index summaries are copied at semantic level from the physical model; RF-09 must prove exact names, columns, predicates, checks and actions against that model.

| # | Exact table | Owner | Batch | Prerequisite tables | PK form | FK count | Unique/constraint identity | Index identity summary | Implementation RF | Verification RF |
|---:|---|---|---|---|---|---:|---|---|---|---|
| 1 | `platform_idempotency_records` | M01 | `RF09_M01` | none | `id uuid` | 0 | `(scope,idempotency_key)`; key/fingerprint checks | expiry; scope/key | RF-09 | RF-09 |
| 2 | `platform_audit_entries` | M01 | `RF09_M01` | `identity_accounts` | `id uuid` | 1 | none; actor/reason checks | created; correlation; actor/time | RF-09 | RF-09 |
| 3 | `platform_event_outbox` | M01 | `RF09_M01` | none | `id uuid` | 0 | event fingerprint; lease/check invariants | partial available; partial lease expiry | RF-09 | RF-09 |
| 4 | `identity_accounts` | M02 | `RF09_M02` | none | `id uuid` | 0 | no phone uniqueness in baseline | partial phone; state/time | RF-09 | RF-09 |
| 5 | `identity_provider_links` | M02 | `RF09_M02` | `identity_accounts` | `id uuid` | 1 | provider/subject | account | RF-09 | RF-09 |
| 6 | `identity_role_assignments` | M02 | `RF09_M02` | `identity_accounts` | `id uuid` | 2 | account/role/time | active account/role; actor/time | RF-09 | RF-09 |
| 7 | `identity_sessions` | M02 | `RF09_M02` | `identity_accounts` | `id uuid` | 1 | token hash; expiry checks | account/expiry; active expiry | RF-09 | RF-09 |
| 8 | `identity_link_challenges` | M02 | `RF09_M02` | `identity_accounts` | `id uuid` | 1 | challenge hash; expiry checks | unconsumed expiry | RF-09 | RF-09 |
| 9 | `entitlement_tariff_definitions` | M03 | `RF09_M03` | none | `id uuid` | 0 | code/version; active interval checks | code/active time | RF-09 | RF-09 |
| 10 | `entitlement_access_grants` | M03 | `RF09_M03` | `identity_accounts`; `entitlement_tariff_definitions` | `id uuid` | 2 | validity/state checks | account/expiry; active interval | RF-09 | RF-09 |
| 11 | `entitlement_usage_counters` | M03 | `RF09_M03` | `identity_accounts` | `id uuid` | 1 | account/code/window | account/code/end | RF-09 | RF-09 |
| 12 | `billing_payment_records` | M03 | `RF09_M03` | `identity_accounts` | `id uuid` | 1 | provider/external payment | account/time; pending/unknown | RF-09 | RF-09 |
| 13 | `billing_payment_operations` | M03 | `RF09_M03` | `billing_payment_records` | `id uuid` | 1 | payment/operation/idempotency | pending/retry due | RF-09 | RF-09 |
| 14 | `billing_reconciliations` | M03 | `RF09_M03` | `billing_payment_records`; `billing_payment_operations` | `id uuid` | 2 | payment/operation null-safe | unresolved due | RF-09 | RF-09 |
| 15 | `beacon_beacons` | M04 | `RF09_M04` | `identity_accounts`; `beacon_configuration_revisions` | `id uuid` | 2 | id/current revision; revision checks | account/state | RF-09 | RF-09 |
| 16 | `beacon_configuration_revisions` | M04 | `RF09_M04` | `beacon_beacons`; `identity_accounts`; `filter_catalog_versions` | `(beacon_id,revision_no)` | 3 | composite identity; positive revision | beacon/time | RF-09 | RF-09 |
| 17 | `beacon_filter_overrides` | M04 | `RF09_M04` | `beacon_configuration_revisions` | `id uuid` | 1 | beacon/revision/field | beacon/field | RF-09 | RF-09 |
| 18 | `beacon_lifecycle_events` | M04 | `RF09_M04` | `beacon_beacons`; `identity_accounts` | `id uuid` | 2 | state/reason checks | beacon/time | RF-09 | RF-09 |
| 19 | `parser_outcomes` | M05 | `RF09_M05` | `beacon_beacons`; `scan_runs`; `egress_routes` | `id uuid` | 3 | run/fingerprint null-safe; outcome checks | beacon/time; outcome/time | RF-09 | RF-09 |
| 20 | `scan_schedules` | M06 | `RF09_M06` | `beacon_beacons` | `id uuid` | 1 | one schedule/beacon | active due/id | RF-09 | RF-09 |
| 21 | `scan_work_items` | M06 | `RF09_M06` | `scan_schedules`; `beacon_beacons` | `id uuid` | 2 | schedule/due; lease checks | due; claimed expiry | RF-09 | RF-09 |
| 22 | `scan_runs` | M06 | `RF09_M06` | `scan_work_items`; `beacon_beacons`; `beacon_configuration_revisions`; `parser_outcomes`; `egress_routes` | `id uuid` | 5 | one run/work; completion checks | beacon/time; active states | RF-09 | RF-09 |
| 23 | `scan_listing_observations` | M06 | `RF09_M06` | `scan_runs`; `beacon_beacons` | `id uuid` | 2 | run/external key | beacon/time | RF-09 | RF-09 |
| 24 | `scan_beacon_listing_state` | M06 | `RF09_M06` | `beacon_beacons` | `id uuid` | 1 | beacon/external key | beacon/last seen | RF-09 | RF-09 |
| 25 | `scan_anchors` | M06 | `RF09_M06` | `beacon_beacons`; `identity_accounts` | `id uuid` | 2 | one anchor/beacon | beacon/time | RF-09 | RF-09 |
| 26 | `egress_agents` | M07 | `RF09_M07` | none | `id uuid` | 0 | agent code; fingerprint checks | state/code | RF-09 | RF-09 |
| 27 | `egress_routes` | M07 | `RF09_M07` | `egress_agents` | `id uuid` | 1 | agent/route code | state/agent | RF-09 | RF-09 |
| 28 | `egress_agent_heartbeats` | M07 | `RF09_M07` | `egress_agents` | `id uuid` | 1 | state/metadata checks | agent/time | RF-09 | RF-09 |
| 29 | `egress_route_leases` | M07 | `RF09_M07` | `egress_routes`; `scan_work_items` | `id uuid` | 2 | lease token; active route/work | active lease expiry | RF-09 | RF-09 |
| 30 | `notification_endpoints` | M08 | `RF09_M08` | `identity_accounts` | `id uuid` | 1 | provider/endpoint | account/state | RF-09 | RF-09 |
| 31 | `notification_events` | M08 | `RF09_M08` | `identity_accounts`; `beacon_beacons`; `scan_runs` | `id uuid` | 3 | source effect fingerprint | account/time; beacon/time | RF-09 | RF-09 |
| 32 | `notification_outbox` | M08 | `RF09_M08` | `notification_events`; `notification_endpoints` | `id uuid` | 2 | event/endpoint; lease checks | pending/retry; claimed expiry | RF-09 | RF-09 |
| 33 | `notification_delivery_attempts` | M08 | `RF09_M08` | `notification_outbox` | `id uuid` | 1 | outbox/attempt | outbox/time | RF-09 | RF-09 |
| 34 | `notification_delivery_reconciliations` | M08 | `RF09_M08` | `notification_delivery_attempts` | `id uuid` | 1 | one reconciliation/attempt | unresolved due | RF-09 | RF-09 |
| 35 | `telegram_inbound_updates` | M09 | `RF09_M09` | none | `id uuid` | 0 | provider update/fingerprint | provider update; received | RF-09 | RF-09 |
| 36 | `telegram_identity_mappings` | M09 | `RF09_M09` | `identity_provider_links` | `id uuid` | 1 | Telegram ref; provider link | provider link | RF-09 | RF-09 |
| 37 | `telegram_delivery_mappings` | M09 | `RF09_M09` | `notification_delivery_attempts` | `id uuid` | 1 | one mapping/attempt; optional message ref | message ref partial | RF-09 | RF-09 |
| 38 | `max_inbound_events` | M10 | `RF09_M10` | none | `id uuid` | 0 | provider event/fingerprint | provider event; received | RF-09 | RF-09 |
| 39 | `max_identity_mappings` | M10 | `RF09_M10` | `identity_provider_links` | `id uuid` | 1 | MAX ref; provider link | provider link | RF-09 | RF-09 |
| 40 | `max_delivery_mappings` | M10 | `RF09_M10` | `notification_delivery_attempts` | `id uuid` | 1 | one mapping/attempt; optional message ref | message ref partial | RF-09 | RF-09 |
| 41 | `max_miniapp_nonces` | M10 | `RF09_M10` | `identity_accounts` | `id uuid` | 1 | nonce hash; expiry checks | unconsumed expiry | RF-09 | RF-09 |
| 42 | `support_cases` | M11 | `RF09_M11` | `identity_accounts` | `id uuid` | 3 | state/subject checks | open/pending; account/time | RF-09 | RF-09 |
| 43 | `support_case_notes` | M11 | `RF09_M11` | `support_cases`; `identity_accounts` | `id uuid` | 2 | visibility/body checks | case/time | RF-09 | RF-09 |
| 44 | `support_case_events` | M11 | `RF09_M11` | `support_cases`; `identity_accounts` | `id uuid` | 2 | event/reason checks | case/time; actor/time | RF-09 | RF-09 |
| 45 | `filter_catalog_versions` | M13 | `RF09_M13` | none | `id uuid` | 0 | version; evidence fingerprint | state/time | RF-09 | RF-09 |
| 46 | `filter_definitions` | M13 | `RF09_M13` | `filter_catalog_versions`; `filter_evidence_references` | `id uuid` | 2 | catalog/field; support checks | catalog/state; field | RF-09 | RF-09 |
| 47 | `filter_options` | M13 | `RF09_M13` | `filter_definitions` | `id uuid` | 1 | definition/option | definition/order | RF-09 | RF-09 |
| 48 | `filter_dependencies` | M13 | `RF09_M13` | `filter_catalog_versions`; `filter_definitions` | `id uuid` | 3 | catalog/source/dependency; source != dependency | catalog/source | RF-09 | RF-09 |
| 49 | `filter_category_applicability` | M13 | `RF09_M13` | `filter_catalog_versions`; `filter_definitions`; `filter_evidence_references` | `id uuid` | 3 | catalog/category/definition; state checks | catalog/category; definition | RF-09 | RF-09 |
| 50 | `filter_evidence_references` | M13 | `RF09_M13` | `filter_catalog_versions` | `id uuid` | 1 | catalog/reference; evidence fingerprint | catalog/time | RF-09 | RF-09 |
| 51 | `filter_capability_profiles` | M13 | `RF09_M13` | `filter_catalog_versions` | `id uuid` | 1 | catalog/profile | catalog/profile | RF-09 | RF-09 |

No row grants direct foreign-module mutation authorization. No table is added for `alembic_version`.

## 8. Foreign-key dependency ordering

All 35 inter-module FK edge-columns in the accepted model are accounted for below. All use `ON DELETE RESTRICT`; nullable and mandatory semantics remain those of the physical model. `D` means immediate after the predecessor exists; `F` means explicitly deferred and finalized by `RF09_FINALIZE`.

| # | Child table/module | Parent table/module | Effect | Decision | Reason | Verification owner |
|---:|---|---|---|---|---|---|
| 1 | `platform_audit_entries`/M01 | `identity_accounts`/M02 | M02 precedes actor FK | D | nullable actor, parent available | RF-09 |
| 2 | `entitlement_access_grants`/M03 | `identity_accounts`/M02 | M02 precedes account FK | D | mandatory parent | RF-09 |
| 3 | `entitlement_usage_counters`/M03 | `identity_accounts`/M02 | M02 precedes account FK | D | mandatory parent | RF-09 |
| 4 | `billing_payment_records`/M03 | `identity_accounts`/M02 | M02 precedes account FK | D | mandatory parent | RF-09 |
| 5 | `beacon_beacons`/M04 | `identity_accounts`/M02 | M02 precedes owner FK | D | mandatory parent | RF-09 |
| 6 | `beacon_configuration_revisions`/M04 | `identity_accounts`/M02 | M02 precedes creator FK | D | mandatory parent | RF-09 |
| 7 | `beacon_configuration_revisions`/M04 | `filter_catalog_versions`/M13 | M13 precedes optional catalog FK | D | optional accepted candidate provenance | RF-09 |
| 8 | `beacon_lifecycle_events`/M04 | `identity_accounts`/M02 | M02 precedes actor FK | D | nullable actor, restricted reference | RF-09 |
| 9 | `parser_outcomes`/M05 | `beacon_beacons`/M04 | M04 precedes beacon FK | D | mandatory parent | RF-09 |
| 10 | `parser_outcomes`/M05 | `scan_runs`/M06 | M06 creates run target | F | accepted parser/run cycle | RF-09 |
| 11 | `parser_outcomes`/M05 | `egress_routes`/M07 | M07 precedes route FK | D | optional route reference | RF-09 |
| 12 | `scan_schedules`/M06 | `beacon_beacons`/M04 | M04 precedes schedule FK | D | mandatory parent | RF-09 |
| 13 | `scan_work_items`/M06 | `beacon_beacons`/M04 | M04 precedes work FK | D | mandatory parent | RF-09 |
| 14 | `scan_runs`/M06 | `beacon_configuration_revisions`/M04 | M04 precedes pinned revision FK | D | exact revision pinning | RF-09 |
| 15 | `scan_runs`/M06 | `egress_routes`/M07 | M07 precedes route FK | D | optional route reference | RF-09 |
| 16 | `scan_runs`/M06 | `parser_outcomes`/M05 | M05 creates outcome target | F | accepted run/outcome cycle | RF-09 |
| 17 | `scan_listing_observations`/M06 | `beacon_beacons`/M04 | M04 precedes observation FK | D | mandatory parent | RF-09 |
| 18 | `scan_beacon_listing_state`/M06 | `beacon_beacons`/M04 | M04 precedes state FK | D | mandatory parent | RF-09 |
| 19 | `scan_anchors`/M06 | `beacon_beacons`/M04 | M04 precedes anchor FK | D | mandatory parent | RF-09 |
| 20 | `scan_anchors`/M06 | `identity_accounts`/M02 | M02 precedes correction actor FK | D | nullable actor | RF-09 |
| 21 | `egress_route_leases`/M07 | `scan_work_items`/M06 | M06 creates lease target | F | route/work lifecycle cycle | RF-09 |
| 22 | `notification_endpoints`/M08 | `identity_accounts`/M02 | M02 precedes endpoint FK | D | mandatory owner | RF-09 |
| 23 | `notification_events`/M08 | `identity_accounts`/M02 | M02 precedes account FK | D | mandatory owner | RF-09 |
| 24 | `notification_events`/M08 | `beacon_beacons`/M04 | M04 precedes optional Beacon FK | D | event provenance | RF-09 |
| 25 | `notification_events`/M08 | `scan_runs`/M06 | M06 precedes optional run FK | D | event provenance | RF-09 |
| 26 | `telegram_identity_mappings`/M09 | `identity_provider_links`/M02 | M02 precedes mapping FK | D | adapter cannot create identity | RF-09 |
| 27 | `telegram_delivery_mappings`/M09 | `notification_delivery_attempts`/M08 | M08 precedes delivery FK | D | adapter maps generic attempt | RF-09 |
| 28 | `max_identity_mappings`/M10 | `identity_provider_links`/M02 | M02 precedes mapping FK | D | adapter cannot create identity | RF-09 |
| 29 | `max_delivery_mappings`/M10 | `notification_delivery_attempts`/M08 | M08 precedes delivery FK | D | adapter maps generic attempt | RF-09 |
| 30 | `max_miniapp_nonces`/M10 | `identity_accounts`/M02 | M02 precedes optional account FK | D | Identity boundary owns account | RF-09 |
| 31 | `support_cases.account_id`/M11 | `identity_accounts`/M02 | M02 precedes account FK | D | mandatory account reference | RF-09 |
| 32 | `support_cases.opened_by_account_id`/M11 | `identity_accounts`/M02 | M02 precedes opener FK | D | mandatory actor reference | RF-09 |
| 33 | `support_cases.assigned_to_account_id`/M11 | `identity_accounts`/M02 | M02 precedes assignee FK | D | nullable actor reference | RF-09 |
| 34 | `support_case_notes.author_account_id`/M11 | `identity_accounts`/M02 | M02 precedes author FK | D | mandatory actor reference | RF-09 |
| 35 | `support_case_events.actor_account_id`/M11 | `identity_accounts`/M02 | M02 precedes actor FK | D | mandatory actor reference | RF-09 |

The intra-module and composite edges are also present in section 7. The Beacon/current-revision, parser/run, and route/work cycles are never hidden: their constraints are explicitly deferred, validated with `RF09_FINALIZE`, and must be `NOT VALID` only temporarily during controlled creation, then proven valid before the head is accepted. A future graph with an unresolved cycle is `STOP_SCOPE_REQUIRED`. Referential integrity never authorizes a foreign-module command.

## 9. Roles, privileges and connection boundaries

- The migration role has DDL and migration-metadata authority only for the project-owned `mayak` schema and executes the Alembic connection using a migration secret reference.
- The application role has DML only on project-owned schema objects required by runtime repositories and uses an application secret reference; it never owns or creates schema objects and has no DDL privilege.
- PostgreSQL superuser is not used by application runtime. Ownership/grants are applied through the explicit RF-09 bootstrap/migration mechanism and least privilege is proven there.
- Provider adapters have no direct database credentials. There is no host-published database port and no foreign database access.
- Credential values remain outside Git and are never printed in diagnostics. No final usernames or secret values are invented by this design artifact.

## 10. Upgrade from zero procedure

The future RF-09 procedure is exact and repeatable:

1. Create an isolated project-owned empty PostgreSQL 18 database.
2. Create and verify separate migration and application roles through the approved boundary.
3. Verify the database is empty except approved PostgreSQL system objects.
4. Run an explicit Alembic upgrade to one accepted head.
5. Verify all 51 domain tables.
6. Verify `alembic_version` and exactly one current head.
7. Verify PK, FK, unique, check and index inventory against the physical model.
8. Verify ownership and grants, including no application-role DDL.
9. Run the current-head check.
10. Run DB-backed smoke/integration tests with synthetic data.
11. Record source SHA, lock identity, migration revision and environment ID.

No SQLite substitution, API-start migration, live provider call, production PII or foreign resource is allowed. The procedure must be repeatable from a newly empty database; a second `upgrade head` is no-op success.

## 11. Current-head and drift verification

Future gates require exactly one Alembic head and current revision equal to the expected accepted head. There must be no untracked revision file and no model/schema drift. The metadata table set must equal the 51 accepted domain tables plus Alembic infrastructure. Every expected constraint and index must be present; every unexpected table, column, constraint or index fails the gate.

If revision is behind, ahead or unknown, application readiness is `NOT_READY`. API, worker and scheduler perform no silent auto-upgrade or auto-downgrade. CI and deployment both execute the same current-head, object-inventory and privilege verification.

## 12. Transactional DDL and interruption handling

The default is one PostgreSQL transaction per Alembic revision. Migrations contain no external/provider call. No long-running application process remains active while an incompatible migration is applied. Lock and timeout behavior must be bounded and documented at RF-09.

Interruption before transaction commit leaves the revision unapplied. Interruption after DDL commit is reconciled through `alembic_version` and schema inspection. Any ambiguous state is `NOT_READY`; no blind rerun occurs before current revision and schema are inspected. A nontransactional operation requires exact future evidence and a separate roll-forward plan. Concurrent migration writers are forbidden. An advisory lock or equivalent project-owned serialization is implemented and proven at RF-09.

## 13. Downgrade and roll-forward policy

Downgrade is allowed only where verified safe and data-preserving. Destructive or data-transforming revisions default to roll-forward recovery. API, worker, scheduler and deploy startup never perform automatic downgrade. An accepted environment backup is required before destructive change.

Downgrade cannot cross an irreversible boundary. An irreversible revision declares its reason, precondition, backup requirement, roll-forward repair, verification and operator evidence. The initial from-zero chain must remain rebuildable even where downgrade is unsupported. Production rollback policy remains outside the current acceptance launch gate.

## 14. Future schema evolution rules

- One atomic purpose per future revision, with exact domain owner and Technical ID in revision naming/metadata.
- Every change is classified for backward/forward compatibility and uses expand/migrate/contract where necessary.
- Add nullable/additive shape before required enforcement; no rename/drop without an accepted compatibility plan.
- Table ownership never transfers silently. Outbox or idempotency semantics cannot change without RF-04 boundary reconciliation.
- Enum-like state and check changes are explicit; index creation/removal has a measured reason and proof.
- A new extension requires a future ADR and evidence. The chain remains one head.
- A merge revision requires an independently accepted exceptional task; routine parallel heads are forbidden.
- Schema drift is a failure, not an automatically repairable condition.

## 15. Data migration and backfill policy

RF-09 tests use synthetic fixtures only; no production data is used in automated migration tests. Future large backfills use bounded batches, are resumable and idempotent, and persist a checkpoint in project-owned state where required. They make no provider call and do not transform raw payloads outside the accepted retention/security policy.

Large backfills do not use one long transaction. Correctness is verified before tightening a constraint. An interrupted or ambiguous backfill is reconciled before retry. Destructive cleanup requires proof and backup. Data is never fabricated to satisfy a constraint.

## 16. Migration failure and recovery matrix

| # | Scenario | Detection | Persisted/schema state | Readiness/deploy effect | Retry/reconcile action | Rollback or roll-forward | Safe evidence | Forbidden response | Future RF proof owner |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | migration configuration invalid | parse/validation failure | no revision start | `NOT_READY`; deploy stops | correct config, revalidate | none; roll-forward after proof | redacted error and SHA | guessing defaults | RF-09 |
| 2 | migration credential missing | secret reference unavailable | no DB mutation | `NOT_READY` | restore reference outside Git | no downgrade | secret-presence boolean only | print credential | RF-09 |
| 3 | PostgreSQL unavailable before migration | bounded connection timeout | unchanged | `NOT_READY`; deploy stops | restore isolated DB/connectivity | retry same head after check | redacted connectivity status | provider/live fallback | RF-08/RF-09 |
| 4 | database not empty at from-zero start | object inventory mismatch | pre-existing objects retained | from-zero gate fails | isolate new empty DB or reconcile owner | no destructive cleanup | object names/types only | drop unknown objects | RF-09 |
| 5 | multiple Alembic heads detected | heads count > 1 | graph ambiguous | `NOT_READY` | accepted merge task or remove unaccepted branch | no blind merge | revision IDs, no secrets | select arbitrary head | RF-07/RF-09 |
| 6 | current revision behind expected | current-head check | valid older revision | `NOT_READY` | explicit upgrade after compatibility gate | roll-forward | current/expected labels | auto-upgrade on start | RF-09/RF-23 |
| 7 | current revision ahead or unknown | revision lookup | unknown/incompatible state | `NOT_READY` | inspect source/schema and stop | operator-approved recovery | current label and inventory | downgrade blindly | RF-09 |
| 8 | revision transaction fails before commit | transaction error | revision unapplied | deploy fails | inspect `alembic_version`, retry if clean | roll-forward same revision | redacted error and revision | assume partial success | RF-09 |
| 9 | connection lost during revision | connection/lock timeout | ambiguous until inspected | `NOT_READY` | inspect revision and schema before rerun | roll-forward only after proof | DB state inventory | blind rerun | RF-09/RF-26 |
| 10 | process interrupted after DDL commit | process exit plus head check | commit may be durable | `NOT_READY` until verified | inspect head/object inventory | roll-forward if committed | revision and catalog proof | repeat blindly | RF-09/RF-26 |
| 11 | advisory lock already held | bounded lock timeout | no writer mutation | migration blocked | identify project-owned holder and wait/reconcile | retry after serialization | lock timeout metadata | concurrent migration | RF-09 |
| 12 | unexpected schema object detected | inventory diff | drift/extraneous object | `NOT_READY` | stop and obtain owner evidence | accepted repair only | object identity, no data | drop object automatically | RF-07/RF-09 |
| 13 | table/constraint/index drift detected | exact catalog comparison | schema differs from model | deploy blocked | reconcile against accepted model | explicit roll-forward revision | redacted inventory diff | silent repair | RF-07/RF-09 |
| 14 | application role has DDL privilege | privilege audit | security invariant violated | `NOT_READY`; revoke before use | correct grants and reverify | no application rollback | grant names only | run with excess privilege | RF-25 |
| 15 | downgrade across irreversible boundary | policy precondition | data-preservation not proven | request rejected | use declared repair plan | roll-forward only | operator decision and backup proof | force downgrade | RF-09/RF-26 |
| 16 | backfill interrupted | checkpoint/row invariant | partial bounded progress | `NOT_READY` if compatibility incomplete | reconcile checkpoint and idempotently resume | roll-forward | synthetic counts/checkpoint | duplicate or fabricate data | RF-09/RF-26 |
| 17 | destructive change lacks valid backup | backup gate failure | change not started | deploy blocked | produce accepted backup evidence | no change; no downgrade | backup identity, no contents | proceed anyway | RF-26 |
| 18 | foreign database/resource collision | boundary/resource inventory | target ownership ambiguous | hard stop | isolate project resource and reverify | no foreign mutation | redacted ownership metadata | connect or alter foreign resource | RF-05/RF-08/RF-09 |

## 17. Roadmap implementation and proof ownership

| RF | Exact ownership |
|---|---|
| RF-05 | environment/database boundary evidence only |
| RF-06 | dependency/import/toolchain proof |
| RF-07 | CI migration jobs and drift gates |
| RF-08 | PostgreSQL container/Compose and explicit migration command shell |
| RF-09 | Alembic implementation, roles, 51-table schema, upgrade from zero, current-head proof |
| RF-10–RF-22 | DB-backed module repository/runtime verification |
| RF-23 | process readiness integration |
| RF-24 | synthetic E2E on migrated DB |
| RF-25 | privilege/secret/schema security verification |
| RF-26 | backup/restore/interruption recovery |
| RF-27 | deployed migration execution |
| RF-28 | final migration/regression drills |

No implementation gap is unassigned. RF-04 defines the design and preserves accepted boundaries; RF-09 is the implementation owner.

## 18. Acceptance checklist and final state

- RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`.
- RF-04-02 is accepted through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`.
- RF-04-03 is accepted at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`.
- This is the RF-04 fourth artifact; exactly 51 accepted domain tables are mapped in exactly 51 rows.
- There are exactly 13 module rows; ownership counts are exactly `3/5/6/4/1/6/4/5/3/4/3/0/7`; module 12 has no table revision.
- The plan has one single-head chain, with all deferred cycles explicit and no unresolved graph cycle.
- No migration implementation was created; no runtime, dependency, CI, Docker, DB, server or provider mutation occurred; no provider call or secret value is present.
- RF-04 remains active and is not closed. RF-05 remains not started. `PRODUCTION_READY` is not claimed.

Acceptance marker: RF04_MIGRATION_AND_SCHEMA_EVOLUTION_PLAN_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE

RF04_MIGRATION_AND_SCHEMA_EVOLUTION_PLAN_PUBLISHED
