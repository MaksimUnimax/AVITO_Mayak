# Identity & Access

**Статус:** APPROVED documentation playbook v1.0; Run 13 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- internal account boundary;
- account identities for Telegram, MAX, email, phone and future local credentials;
- verified contact points;
- credential references without raw secret material;
- server-side role assignment;
- auth sessions;
- auth and identity-link challenges;
- account-link/merge safety gates.

The module does not own tariffs, Beacons, parser state, notification delivery, provider adapter payloads, admin work items or Web Cabinet presentation state.

This publication creates no code, dependency files, lock, tests, migrations, database, runtime or infrastructure.
