# Автономные module playbooks

**Статус:** ACTIVE documentation route — Runs 12–13 accepted; Run 14 published; Runs 15–24 remain RESERVED.

Each module has one canonical `MODULE_PLAYBOOK.md`.

Published:

- `01-platform-and-contracts/MODULE_PLAYBOOK.md` — Run 12; exact server synchronization accepted.
- `02-identity-and-access/MODULE_PLAYBOOK.md` — Run 13; exact server synchronization accepted.
- `03-entitlements-and-billing/MODULE_PLAYBOOK.md` — Run 14; exact server synchronization/acceptance pending.

Reserved route:

- Run 15 — Beacon Management;
- Run 16 — Avito Parser Adapter;
- Run 17 — Scan Orchestration & Listing State;
- Run 18 — Egress Routing;
- Run 19 — Notification Delivery;
- Run 20 — Telegram Adapter;
- Run 21 — MAX Adapter;
- Run 22 — Admin & Support;
- Run 23 — Web Cabinet;
- Run 24 — Filter Catalog & Builder.

Every playbook must include purpose/boundaries, data owner, confirmed and open decisions, public inputs/outputs, allowed/forbidden changes, immutable common contracts, dependencies/fakes, fixtures/test vectors, acceptance criteria, roadmap, report/handoff and append-only history.

A playbook is a prerequisite only. It does not authorize code, dependency installation, database, migrations, payment/provider integration, services or deployment without a separate exact task and gates.
