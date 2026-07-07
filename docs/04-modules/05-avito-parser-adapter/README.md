# Avito Parser Adapter

**Статус:** APPROVED documentation playbook v1.0; Run 16 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- evidence-bound Avito source and response analysis;
- explicit transport-versus-parser outcome classification;
- normalized search-configuration extraction;
- normalized listing candidates with safe provenance;
- multivalue parameter preservation;
- compatibility/reference profile identity and warnings;
- explicit malformed, incomplete, restricted, unavailable, stale, unsupported and ambiguous outcomes.

The module does not own Beacon configuration/lifecycle, account or tariff state, Egress routes/leases, scheduling, scan/listing history, baseline/diff, notifications, provider adapters, filter-catalog authority or retention policy.

`AVITO-PRIMARY-PARSER-001` at commit `48441c352e36919abef13c436f41a3a62636da17` is implementation evidence only, not an official provider contract or permission. OD-009, OD-010, OD-011 and OD-013 remain unresolved.

This publication creates no parser code, live Avito request, endpoint probe, dependency file, lock, executable test, fixture data, database, migration, cookie/session/proxy configuration, runtime or infrastructure.
