# Автономные module playbooks

**Статус:** `MODULE_14_RF02_ACTIVE` — modules 01–13 are accepted; RF-02 reconciliation is active; exact closure evidence remains pending; RF-03 is not started.

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

- `14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED; RF-00 and RF-01 accepted; RF-02 active.
- `14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED; owner decisions for RF-01–RF-30.
- `14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md` — accepted RF-02 audit input.

Accepted RF-02 prerequisite surfaces:

- reconciliation audit;
- primary governance;
- current decision register;
- documentation manifest;
- applicable documentation indexes.

RF-02 remains active until an exact closure-evidence and status-transition task is published and independently accepted.

RF-03 must not start before RF-02 is independently closed.

All 13 domain module playbooks remain published and accepted. Their final documentation acceptance remains historical evidence. Module 14 is the active cross-cutting implementation and integration module.

Module 14 work is authorized only through exact RF prerequisites and one exact atomic task. The playbook and owner decisions do not by themselves prove runtime implementation, database persistence, deployment or production readiness.

Every playbook preserves its purpose, ownership, public boundaries, accepted decisions, forbidden changes, dependencies, fixtures, acceptance criteria, roadmap and evidence history.

Modules 01–13 remain semantic and ownership prerequisites. Module 14 may authorize later code, dependency, database, migration, infrastructure and deployment work only when its approved owner decisions, current roadmap prerequisite and one exact gated task permit that mutation.

The current Module 14 target is `READY_FOR_OPERATOR_ACCEPTANCE`.

Module 14 must not claim `PRODUCTION_READY`.
