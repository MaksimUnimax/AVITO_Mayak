# Автономные module playbooks

**Статус:** ACTIVE documentation route — Runs 12–23 accepted; Run 24 published; final audit pending after exact Run 24 server synchronization.

Each module has one canonical `MODULE_PLAYBOOK.md`.

Published:

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
- `13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` — Run 24; exact server synchronization/acceptance pending.

All 13 module playbooks are published. Final documentation acceptance remains pending until Run 24 server synchronization and final independent audit are accepted.

Every playbook must include purpose/boundaries, data owner, confirmed and open decisions, public inputs/outputs, allowed/forbidden changes, immutable common contracts, dependencies/fakes, fixtures/test vectors, acceptance criteria, roadmap, report/handoff and append-only history.

A playbook is a prerequisite only. It does not authorize code, dependency installation, database, migrations, agents, routes, tunnels, ports, provider calls, notifications, services or deployment without a separate exact task and gates.
