# Автономные module playbooks

**Статус:** MODULE_14_AUTONOMOUS_RUNTIME_COMPLETION_ACTIVE — modules 01–13 are accepted; module 14 RF-01 governance is complete and RF-02 is next.

Each module has one canonical `MODULE_PLAYBOOK.md`.

Accepted domain modules:

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

Active cross-cutting integration module:

- `14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED; RF-01 governance complete; RF-02 next.
- `14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED; owner decisions for RF-01–RF-30.

All 13 domain module playbooks remain published and accepted. Their final documentation acceptance remains historical evidence. Module 14 is the active cross-cutting implementation and integration module. Its approved playbook and owner decisions authorize work only through exact RF tasks and do not by themselves prove runtime implementation, deployment or production readiness.

Every playbook includes purpose/boundaries, data owner, confirmed and open decisions, public inputs/outputs, allowed/forbidden changes, immutable common contracts, dependencies/fakes, fixtures/test vectors, acceptance criteria, roadmap, report/handoff and append-only history.

Playbooks for modules 01–13 remain semantic and ownership prerequisites. Module 14 may authorize later code, dependency, database, migration, infrastructure and deployment work only when its approved owner decisions, current roadmap prerequisite and one exact gated task all permit that mutation. RF-01 is documentation-only and does not authorize runtime mutation.
