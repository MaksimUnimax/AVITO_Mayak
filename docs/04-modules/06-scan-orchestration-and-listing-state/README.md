# Scan Orchestration & Listing State

**Статус:** APPROVED documentation playbook v1.0; Run 17 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- durable scan intent, work claim and run lifecycle;
- one immutable Beacon configuration revision per run;
- explicit Parser outcome consumption and provenance;
- immutable per-run listing observations;
- authoritative listing state isolated by `beacon_id`;
- first complete baseline establishment;
- subsequent new-listing and new identity+price-pair difference decisions;
- reconciliation, concurrency control and post-commit scan-domain events.

The module does not own Beacon configuration/lifecycle, tariff/payment authority, Parser extraction mappings, Egress routes/agents/leases, notification outbox/delivery, Telegram/MAX provider behavior or raw provider retention policy.

OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain unresolved. Exact interval values, expiry handling, listing identity/price mapping, route policy, retry timings, retention and physical storage remain blocked.

This publication creates no scheduler/worker, queue, product code, dependency file, lock, executable test, fixture data, database, migration, parser/provider request, notification delivery, runtime or infrastructure.
