# Маяк Авито — текущее состояние проекта

**Версия снимка:** 3.0
**Статус:** `MODULE_14_RF02_ACTIVE`
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
- RF-02 — current-main governance reconciliation: active.
- RF-02 reconciliation audit: accepted at `59f86084bbc17386070dde34485aba6c1706712c`.
- RF-03–RF-30: not accepted.

RF-02 is not complete until primary governance, current decision status, manifest and applicable indexes no longer contradict the repository tree and Module 14 governance.

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

Continue RF-02 through one exact documentation task at a time.

After all RF-02 reconciliation surfaces agree with current `main`, accepted decisions and the Module 14 playbook, ChatGPT independently closes RF-02 and automatically begins the first atomic RF-03 task.
