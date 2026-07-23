# Автономные module playbooks

**Статус:** `MODULE_14_RF06_DEPENDENCY_SYNC_PUBLISHED_PENDING_ACCEPTANCE` — RF-05, RF-06-01 and RF-06-02 are accepted; RF-06-03 corrective dependency proof is published pending independent acceptance; project-owned environment is synchronized; runtime is stopped; `RUNTIME_ELIGIBLE`; `NOT_PRODUCTION_READY`.

Each module has one canonical `MODULE_PLAYBOOK.md`.

## Accepted domain modules

- `01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12; exact server synchronization accepted.
- `02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13; exact server synchronization accepted.
- `03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14; exact server synchronization accepted.
- `04-beacon-management/MODULE_PLAYBOOK.md` — Run 15; exact server synchronization accepted.
- `05-avito-parser-adapter/MODULE_PLAYBOOK.md` — Run 16; exact server synchronization accepted.
- `06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md` — Run 17; exact server synchronization accepted.
- `07-egress-routing/MODULE_PLAYBOOK.md` — Run 18; exact server synchronization accepted.
- `08-notification-delivery/MODULE_PLAYBOOK.md` — Run 19; exact server synchronization accepted.
- `09-telegram-adapter/MODULE_PLAYBOOK.md` — Run 20; exact server synchronization accepted.
- `10-max-adapter/MODULE_PLAYBOOK.md` — Run 21; exact server synchronization accepted.
- `11-admin-and-support/MODULE_PLAYBOOK.md` — Run 22; exact server synchronization accepted.
- `12-web-cabinet/MODULE_PLAYBOOK.md` — Run 23; exact server synchronization accepted.
- `13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` — Run 24; exact server synchronization accepted.

## Active cross-cutting integration module

- `14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED; RF-06-02 accepted; RF-06-03 corrective publication pending acceptance with synchronized dependency environment, differential no-regression proof and full tests; runtime stopped; RF-06-04/RF-07 blocked.
- `14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED; owner decisions for RF-01–RF-30.
- `14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md` — accepted RF-02 audit input.
- `14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md` — RF-02 closure evidence published for independent acceptance.

RF-06-01 corrective chain is accepted through `f77a1d85d7c8b8fd1f2e60694729d1b7c3a1598c`; RF-06-02 is independently accepted at `4c28354bceaf8325084d8ffd99a31e662c518a71`; RF-06-03 corrective publication is pending independent acceptance; RF-06-04 and RF-07 remain blocked.

RF-02 evidence chain:

- reconciliation audit at `59f86084bbc17386070dde34485aba6c1706712c`;
- primary governance at `63de1f4c62e1b72626f20278dbba9eef190b6a99`;
- current decision register at `f7733447f5f10cc3f3702c8f863accb4d9403c05`;
- documentation manifest at `8d3ff83198d90f062906925d6f4becf66c81ed9a`;
- applicable documentation indexes at `34db47cbbffd7f31a918963b181e3048229307be`;
- module registry and playbook gate at `ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`;
- closure evidence accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- `14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_COMPLETION_MATRIX_v1.0.md` — RF-03-01 independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`.
- `14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_RUNTIME_GAP_MATRIX_v1.0.md` — RF-03-02 independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`.
- `14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_CONSISTENCY_AUDIT_v1.0.md` — RF-03-03 independently accepted at `e8a38a1ce3e506f5d880129bb9781802cd69f48b`.
- `14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_INTEGRATION_INVENTORY_CLOSURE_v1.0.md` — RF-03-04 original closure evidence was published at `a6c5277fcb5596d3c53a59fbcdaec5c06e3456ff`; its corrective index-state chain is published for independent acceptance.

RF-02 is independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`. RF-03 is repository-content complete. RF-04 is accepted through current base. RF-05 is independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`. RF-06 is active; RF-06-01 and RF-06-02 are accepted, and RF-06-03 corrective dependency publication is pending independent acceptance. CPython/uv and dependencies are project-owned, runtime is stopped, RF-06-04/RF-07 are blocked, and `NOT_PRODUCTION_READY` remains current.

Current RF-04 artifacts: `PHYSICAL_DATA_MODEL_v1.0.md`, `TRANSACTION_AND_OUTBOX_BOUNDARIES_v1.0.md`, `RUNTIME_PROCESS_AND_PACKAGE_MODEL_v1.0.md`, `MIGRATION_AND_SCHEMA_EVOLUTION_PLAN_v1.0.md`, `RUNTIME_TOPOLOGY_AND_ENVIRONMENT_RECORD_CANDIDATE_v1.0.md`, `CONFIGURATION_AND_SECRETS_BOUNDARY_v1.0.md`, and `RUNTIME_ARCHITECTURE_AND_PHYSICAL_DATA_MODEL_CLOSURE_v1.0.md`. Current RF-05 artifacts: `EXISTING_SERVER_ENVIRONMENT_RECORD_v1.0.md` and `EXISTING_SERVER_ENVIRONMENT_RECORD_CLOSURE_v1.0.md`. Current RF-06 artifacts: `TOOLCHAIN_AND_DEPENDENCY_BASELINE_v1.0.md`, `TOOLCHAIN_AND_DEPENDENCY_BASELINE_CORRECTION_v1.0.md` (RF-06-01 corrective chain accepted), `TOOLCHAIN_BOOTSTRAP_AND_EXECUTABLE_VERIFICATION_v1.0.md` (RF-06-02 independently accepted), and `DEPENDENCY_EXPANSION_LOCK_AND_CLEAN_SYNC_v1.0.md` (RF-06-03 corrective publication pending independent acceptance).

All 13 domain module playbooks remain published and accepted. Their final documentation acceptance remains historical evidence. Module 14 remains the active cross-cutting implementation and integration module.

Module 14 work is authorized only through exact RF prerequisites and one exact atomic task. The playbook, owner decisions and RF-02 closure do not by themselves prove runtime implementation, database persistence, deployment or production readiness.

Every playbook preserves its purpose, ownership, public boundaries, accepted decisions, forbidden changes, dependencies, fixtures, acceptance criteria, roadmap and evidence history.

Modules 01–13 remain semantic and ownership prerequisites. Module 14 may authorize later code, dependency, database, migration, infrastructure and deployment work only when its approved owner decisions, current roadmap prerequisite and one exact gated task permit that mutation.

The current Module 14 target is `READY_FOR_OPERATOR_ACCEPTANCE`.

Module 14 must not claim `PRODUCTION_READY`.
