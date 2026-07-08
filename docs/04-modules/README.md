# Автономные module playbooks

**Статус:** ACTIVE documentation route — Runs 12–20 accepted; Run 21 published; Runs 22–24 remain RESERVED.

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
- `10-max-adapter/MODULE_PLAYBOOK.md` — Run 21; exact server synchronization/acceptance pending.

Reserved route:

- Run 22 — Admin & Support;
- Run 23 — Web Cabinet;
- Run 24 — Filter Catalog & Builder.

Every playbook must include purpose/boundaries, data owner, confirmed and open decisions, public inputs/outputs, allowed/forbidden changes, immutable common contracts, dependencies/fakes, fixtures/test vectors, acceptance criteria, roadmap, report/handoff and append-only history.

A playbook is a prerequisite only. It does not authorize code, dependency installation, database, migrations, agents, routes, tunnels, ports, provider calls, notifications, services or deployment without a separate exact task and gates.
