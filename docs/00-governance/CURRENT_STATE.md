# Маяк Авито — текущее состояние проекта

**Версия снимка:** 3.0
**Статус:** `MODULE_14_RF10_PLATFORM_CONTRACTS_RUNTIME_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
**Дата:** 2026-07-29

## RF-06-04 closure current gate

- RF-06-03-C06 is accepted at `372ecc630106e9b813bddf1edd384ce36f48db6d`; authoritative artifact count is 48/246/294.
- Authoritative current mypy count is 249; historical 248 cause is not proven and its closure expectation is superseded.
- RF-06 is accepted; RF-07 remains active only for genuinely deferred runtime-dependent gates; RF-08 is independently accepted through `104e9777f298c47428fa8bdb07af109c234c4630`; RF-09 is independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; RF-10 implementation and closure are published for independent acceptance; RF-11 is not started; complete runtime/deployment is not reached; environment is `RUNTIME_ELIGIBLE`; production is `NOT_PRODUCTION_READY`.
- Runtime is stopped; eligibility is `RUNTIME_ELIGIBLE`; production verdict is `NOT_PRODUCTION_READY`.
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
- RF-05 — independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`; server allocations verified; repository content and closure complete. Environment is `RUNTIME_ELIGIBLE`; runtime mutation beyond RF-05 allocations is absent; verdict is `NOT_PRODUCTION_READY`.
- RF-06 is accepted; RF-07 remains active only for genuinely deferred runtime-dependent gates; RF-08 is independently accepted through `104e9777f298c47428fa8bdb07af109c234c4630`; RF-09 is independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; RF-10 corrective is published for independent review and remains pending independent acceptance; RF-11 is not started; runtime/deployment is incomplete; environment is `RUNTIME_ELIGIBLE`; production is `NOT_PRODUCTION_READY`.

RF-02 closure commit `c92e9299e5c0bd11ea18362673a8ac342b835483` is independently accepted.

RF-04 is accepted through the current base. RF-05 is independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`. RF-06 is independently accepted; RF-07-01 and RF-07-02-C01 are independently accepted; RF-07-02 implementation chain and closure are independently accepted through `ace1218dd6e1ab7cf889fac3e53051cb3c5b5782`; RF-07 remains active because runtime-dependent gates remain open. The dependency graph is synchronized and runtime remains stopped. `RUNTIME_ELIGIBLE` applies to the environment allocation; `NOT_PRODUCTION_READY` remains the production verdict; `PRODUCTION_READY` is not claimed.

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

## RF-09 closure current gate

- RF-09 independent acceptance is recorded in the closure artifact through `54300eb672a883cc052c131bf788501ed4b4a918`; verdict `INDEPENDENTLY_ACCEPTED`; no `PRODUCTION_READY` claim.

- RF-09 implementation/corrective chain is present through the independently accepted head `54300eb672a883cc052c131bf788501ed4b4a918`; the closure artifact is `docs/04-modules/14-runtime-foundation-and-autonomous-integration/POSTGRESQL_AND_ALEMBIC_FOUNDATION_CLOSURE_v1.0.md`.
- PostgreSQL 18/Alembic zero-to-head, idempotent replay, current-head, drift, role, lock contention/release and second clean rebuild evidence is recorded; RF-09 is independently accepted and no production-ready claim is made.
- RF-30 remains the only route to `READY_FOR_OPERATOR_ACCEPTANCE`.

## RF-10 closure current gate

- RF-10 implementation chain is preserved through the expected base `c6401f02443d6db958719694039fdbb1c249e286`; corrective closure is `docs/04-modules/14-runtime-foundation-and-autonomous-integration/PLATFORM_AND_CONTRACTS_RUNTIME_CLOSURE_v1.0.md`.
- The RF-10 corrective is published for independent acceptance; acceptance remains pending and `CHATGPT_REVIEW_REQUIRED: YES`.
- Runtime/deployment is incomplete; runtime is stopped; environment is `RUNTIME_ELIGIBLE`; production is `NOT_PRODUCTION_READY`.

## Runtime status

The complete Module 14 acceptance runtime is not yet implemented or deployed.

Current remaining gaps include:

  - remaining RF-07 runtime-dependent gates are genuinely deferred; synthetic E2E remains owned by RF-24; Docker build and Compose configuration validation foundation are satisfied by RF-08/RF-09 evidence;
  - RF-10 independent review/corrective acceptance;
- RF-11–RF-22 runtime for modules 01–13, including API, worker, scheduler, Web Cabinet, Admin and provider-disabled-by-default adapters;
- RF-23 cross-module API and command wiring;
- RF-24 deterministic synthetic end-to-end vertical slices;
- RF-25 remaining runtime security and privacy verification beyond the independently accepted RF-07-02 CI security and supply-chain foundation;
- RF-26 observability, backup, restore and recovery proof;
- RF-27 deployment on the existing project server;
- RF-28 deployed regression and failure drills;
- RF-29 operator acceptance pack;
- RF-30 final evidence handoff.

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

RF-05 is independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`. RF-06 is accepted through `f03e97ec433e9278247a15dafcb1d96387132eba`; RF-07-01 and RF-07-02 closure are independently accepted through the current corrective-chain head `ace1218dd6e1ab7cf889fac3e53051cb3c5b5782`, while RF-07 remains active only for deferred runtime-dependent gates. RF-08 is independently accepted through `104e9777f298c47428fa8bdb07af109c234c4630`; RF-09 is independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; RF-10 corrective is published for independent review and acceptance remains pending. Exact CPython/uv and dependencies are project-owned, and runtime is stopped.

RF-04 and every runtime, dependency, CI, Docker, database, migration, API, worker, scheduler, Web, Admin, provider, service, port or secret mutation remain forbidden outside the exact authorized task scope. RF-09 is independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; RF-10 corrective acceptance and later runtime work remain separately gated.
