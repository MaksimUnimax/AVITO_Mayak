# Entitlements & Billing

**Статус:** APPROVED documentation playbook v1.0; Run 14 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- tariff definitions as versioned server policy records;
- subscriptions as lifecycle records distinct from entitlements;
- entitlement grants and effective entitlement decisions;
- manual access grants with actor/reason/scope/time/audit;
- future payment records/events after provider and policy decisions;
- usage counters only after separate approval.

The module does not own accounts, identities, Beacons, parser state, scan history, notification delivery, provider adapters, Admin UI or Web Cabinet presentation state.

Target-model tariff values remain DRAFT context and are not implementation defaults. OD-001–OD-005 remain unresolved.

This publication creates no code, dependency files, lock, tests, migrations, database, payment integration, runtime or infrastructure.
