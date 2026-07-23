# Автономные module playbooks

**Статус:** `MODULE_14_RF03_ACTIVE` — modules 01–13 are accepted; RF-02 is independently accepted; RF-03 integration inventory is active.

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

- `14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED; RF-00–RF-02 accepted; RF-03 active.
- `14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED; owner decisions for RF-01–RF-30.
- `14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md` — accepted RF-02 audit input.
- `14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md` — RF-02 closure evidence published for independent acceptance.

RF-02 evidence chain:

- reconciliation audit at `59f86084bbc17386070dde34485aba6c1706712c`;
- primary governance at `63de1f4c62e1b72626f20278dbba9eef190b6a99`;
- current decision register at `f7733447f5f10cc3f3702c8f863accb4d9403c05`;
- documentation manifest at `8d3ff83198d90f062906925d6f4becf66c81ed9a`;
- applicable documentation indexes at `34db47cbbffd7f31a918963b181e3048229307be`;
- module registry and playbook gate at `ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`;
- closure evidence accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- `14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_COMPLETION_MATRIX_v1.0.md` — RF-03-01 first artifact published for independent acceptance.
- `14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_RUNTIME_GAP_MATRIX_v1.0.md` — RF-03-02 independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`.
- `14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_CONSISTENCY_AUDIT_v1.0.md` — RF-03-03 third artifact published for independent acceptance.

RF-02 is independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`. RF-03 is active; RF-03-01 is independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 is independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`; RF-03-03 is published for independent acceptance; RF-03 closure remains pending; RF-04 is not started. Runtime mutation remains none and production remains blocked.

All 13 domain module playbooks remain published and accepted. Their final documentation acceptance remains historical evidence. Module 14 remains the active cross-cutting implementation and integration module.

Module 14 work is authorized only through exact RF prerequisites and one exact atomic task. The playbook, owner decisions and RF-02 closure do not by themselves prove runtime implementation, database persistence, deployment or production readiness.

Every playbook preserves its purpose, ownership, public boundaries, accepted decisions, forbidden changes, dependencies, fixtures, acceptance criteria, roadmap and evidence history.

Modules 01–13 remain semantic and ownership prerequisites. Module 14 may authorize later code, dependency, database, migration, infrastructure and deployment work only when its approved owner decisions, current roadmap prerequisite and one exact gated task permit that mutation.

The current Module 14 target is `READY_FOR_OPERATOR_ACCEPTANCE`.

Module 14 must not claim `PRODUCTION_READY`.
