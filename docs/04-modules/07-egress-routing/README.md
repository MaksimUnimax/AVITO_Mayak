# Egress Routing

**Статус:** APPROVED documentation playbook v1.0; Run 18 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- logical Egress agent and route registration;
- capability, trust, readiness, health and quarantine state;
- bounded route leases and transport assignments;
- server-side route-selection decisions and safe evidence;
- explicit dispatch/send/transport outcome classes;
- idempotency, interruption and reconciliation;
- replaceable Windows Egress Agent execution boundary;
- no false-success conversion into Parser or Scan results.

The module does not own Account, Entitlements, Beacon configuration, Scan work/listing state, Parser extraction/normalization, Notification Delivery, provider UI, primary database, Windows/server/network configuration or secrets.

OD-009, OD-010, OD-011 and OD-013 remain unresolved. Exact route technology, connectivity topology, ports, tunnel/VPN/proxy, credentials, capability mappings, route priority/fallback, lease/heartbeat/readiness thresholds, retries/rate limits, cookies/sessions and retention remain blocked.

This publication creates no agent, route, lease, service, scheduled task, tunnel, proxy, VPN, port, listener, certificate, credential, product code, dependency file, lock, executable test, fixture data, database, migration, provider request, notification delivery, runtime or infrastructure.
