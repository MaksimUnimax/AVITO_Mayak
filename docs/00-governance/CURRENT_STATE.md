# Маяк Авито — текущее состояние проекта

**Версия снимка:** 3.0
**Статус:** `MODULE_14_RF05_CLOSURE_PUBLISHED_RF06_BLOCKED_PENDING_ACCEPTANCE`
**Дата:** 2026-07-23
**RF-02 audit baseline:** `59f86084bbc17386070dde34485aba6c1706712c`

## Фаза

`AUTONOMOUS_RUNTIME_COMPLETION`

Target:

`SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`

Completion boundary:

`READY_FOR_OPERATOR_ACCEPTANCE`

Public repository:

- repository: `MaksimUnimax/AVITO_Mayak`;
- branch: `main`;
- exact current SHA must be fetched before every task.

The recorded RF-02 audit baseline is evidence only and does not replace a fresh GitHub check.

## Accepted roadmap state

- RF-00 — current state, GitHub and server verification: accepted.
- RF-01 — governance capture and Module 14 playbook: accepted.
- RF-02 — current-main governance reconciliation: independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-02 reconciliation audit: accepted at `59f86084bbc17386070dde34485aba6c1706712c`.
- RF-02 primary governance reconciliation: accepted at `63de1f4c62e1b72626f20278dbba9eef190b6a99`.
- RF-02 current decision register reconciliation: accepted at `f7733447f5f10cc3f3702c8f863accb4d9403c05`.
- RF-02 documentation manifest reconciliation: accepted at `8d3ff83198d90f062906925d6f4becf66c81ed9a`.
- RF-02 documentation indexes reconciliation: accepted at `34db47cbbffd7f31a918963b181e3048229307be`.
- RF-02 module registry and playbook gate reconciliation: accepted at `ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`.
- RF-02 closure evidence: `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md`; accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- RF-03 — complete at repository-content level; RF-03-01 is independently accepted through `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 is independently accepted through corrective chain head `061757c4cfd9c5c4ea466539c4a92499e5b269d5`; RF-03-03 is independently accepted at `e8a38a1ce3e506f5d880129bb9781802cd69f48b`; RF-03 closure is published for independent acceptance.
- RF-04 — independently accepted through current base `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
- RF-05 — server allocations verified; repository content complete; closure published for independent acceptance. Environment is `RUNTIME_ELIGIBLE`; runtime mutation beyond RF-05 allocations is absent; verdict is `NOT_PRODUCTION_READY`.
- RF-06 — not started and blocked pending independent acceptance of the RF-05 closure. RF-07–RF-30 remain not started/not accepted.

RF-02 closure commit `c92e9299e5c0bd11ea18362673a8ac342b835483` is independently accepted.

RF-04 is accepted through the current base. RF-05 repository content and closure are published for independent acceptance. The environment is `RUNTIME_ELIGIBLE`, but runtime implementation/startup is absent and runtime mutation beyond RF-05 allocations is none. `NOT_PRODUCTION_READY` remains the production verdict; `PRODUCTION_READY` is not claimed. RF-06 is not started and remains blocked pending independent RF-05 closure acceptance.

## Current repository contour

The current repository contains:

- `src/mayak`;
- executable unit, contract and architecture tests;
- synthetic fixtures;
- `pyproject.toml`;
- `uv.lock`;
- accepted semantic implementation and handoff evidence for modules 01–13;
- approved Module 14 playbook and owner decisions;
- a lock-compatible Python 3.14 suite with 4511 passing tests at the accepted RF-02 audit baseline.

Claims that source, tests, fixtures, `pyproject.toml` or `uv.lock` do not exist are stale.

The repository is not an empty documentation-only tree.

## Module state

Modules 01–13 remain accepted semantic, contract, ownership, fixture, test and handoff prerequisites:

1. Platform & Contracts;
2. Identity & Access;
3. Entitlements & Billing;
4. Beacon Management;
5. Avito Parser Adapter;
6. Scan Orchestration & Listing State;
7. Egress Routing;
8. Notification Delivery;
9. Telegram Adapter;
10. MAX Adapter;
11. Admin & Support;
12. Web Cabinet;
13. Filter Catalog & Builder.

Module 14 Runtime Foundation & Autonomous Integration is active.

Module 14 assembles runtime across public boundaries and does not take ownership of domain state from modules 01–13.

## Current decision state

For the current Module 14 and MVP scope:

- OD-001–OD-004 are closed by ADR-0009.
- OD-005 is governed by ADR-0009 and accepted Module 14 billing scope.
- OD-006 is closed for MVP: no standalone phone/password flow.
- OD-007 is closed for MVP: phone is not mandatory.
- OD-008 is closed for MVP: automatic account merge is disabled.
- OD-009 is governed for current scope by evidence-backed editable filters; no invented complete catalog.
- OD-010 is governed for current scope: country-wide search is unsupported by default.
- OD-011 is governed for current scope by accepted tariff intervals; live Avito safety proof remains a future operator/evidence gate.
- OD-012 is governed for current scope: Telegram primary, Web Cabinet first-party, MAX secondary/future, other channels deferred.
- OD-013 is governed for the acceptance environment; future production legal/privacy retention remains separately gated.
- OD-014 is closed for MVP by the accepted Web Cabinet, Admin & Support and Admin analytics v1 scope.

Historical decision rows remain traceability evidence and must not be deleted.

## Runtime status

The complete Module 14 acceptance runtime is not yet implemented or deployed.

Current future gaps include:

- deterministic toolchain proof for the expanded runtime dependency set;
- GitHub Actions CI;
- Docker and Compose foundation;
- PostgreSQL 18 provisioning;
- SQLAlchemy/Psycopg/Alembic physical persistence;
- migration from zero;
- API, worker and scheduler assembly;
- DB-backed runtime for modules 01–13;
- Web Cabinet and Admin runtime;
- provider-disabled-by-default external adapters;
- cross-module API and command wiring;
- synthetic E2E;
- security and supply-chain evidence;
- observability, backup and recovery;
- deployment on the existing server;
- final regression;
- operator acceptance pack;
- final evidence handoff.

Absence of optional provider credentials is not a blocker for this roadmap.

## Existing-server boundary

The existing project server is the authorized runtime host.

Accepted project boundaries:

- source: `/opt/avito-mayak`;
- worktrees: `/opt/avito-mayak-worktrees`;
- future runtime: `/opt/avito-mayak-runtime`;
- future configuration: `/etc/avito-mayak`;
- future data: project-owned Docker volumes or `/var/lib/avito-mayak`;
- future backups: `/var/backups/avito-mayak`.

Project-owned runtime resources may be created only by exact later RF tasks.

Foreign resources must not be altered or reused.

## Current prohibitions

Until an exact applicable later RF task authorizes them, the following remain prohibited:

- runtime service mutation;
- Docker or Compose resource creation;
- PostgreSQL provisioning;
- physical schema and migrations;
- API, worker or scheduler start;
- public ingress;
- host-published PostgreSQL;
- Nginx, firewall, DNS or certificate mutation;
- live Avito, Telegram, MAX or payment calls;
- production personal data;
- secrets in Git or reports;
- foreign-resource mutation;
- direct foreign-module state writes;
- blind retry of ambiguous external effects;
- claims of deployed runtime;
- claims of `PRODUCTION_READY`.

## Next safe work

RF-05 closure evidence is published for independent acceptance. RF-06 is the next gated step only after independent acceptance of the RF-05 closure; it is not started and remains blocked.

RF-04 and every runtime, dependency, CI, Docker, database, migration, API, worker, scheduler, Web, Admin, provider, service, port or secret mutation remain forbidden until their applicable prerequisites and exact tasks.
