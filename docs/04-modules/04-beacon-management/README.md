# Beacon Management

**Статус:** APPROVED documentation playbook v1.0; Run 15 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- account-owned Beacon lifecycle;
- immutable submitted source URL and validation state;
- normalized extracted search snapshot received from Parser Adapter;
- explicit user overrides with provenance;
- deterministic effective configuration;
- immutable configuration revisions;
- entitlement-gated activation and configuration changes;
- public configuration/lifecycle outcomes for adapters, UI and Scan Orchestration.

The module does not own accounts, tariffs, parser implementation, scan/listing state, egress routes, notification delivery, filter catalog evidence or channel presentation state.

OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain unresolved. This publication creates no code, dependency files, lock, tests, fixture files, migrations, database, parser call, runtime or infrastructure.
