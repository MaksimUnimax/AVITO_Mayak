# Runtime Foundation & Autonomous Integration Module Playbook

**Version:** 1.0
**Status:** APPROVED
**Date:** 2026-07-23
**Module:** `14-runtime-foundation-and-autonomous-integration`
**Phase:** `AUTONOMOUS_RUNTIME_COMPLETION`
**Target:** `SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`
**Baseline:** `315d8c63bccc870a8c55bac0cd3896a687597177`
**Completion:** `READY_FOR_OPERATOR_ACCEPTANCE`

## 1. Purpose

Module 14 converts the accepted semantics, contracts, tests and evidence of modules 01–13 into an isolated, reproducible and deployed acceptance runtime on the existing project server.

It owns governance reconciliation, runtime assembly, deterministic toolchain, CI, Docker Compose, PostgreSQL, migrations, persistence adapters, API, worker, scheduler, cross-module wiring, Web Cabinet, Admin & Support, synthetic providers, sandbox-ready external adapters, E2E, security, observability, backup/recovery, deployment and operator handoff.

It does not own domain state of modules 01–13 and cannot claim `PRODUCTION_READY`.

## 2. Sources of truth

Precedence:

1. Current public GitHub `main`.
2. Accepted append-only decisions.
3. This playbook.
4. Accepted module 01–13 playbooks and handoffs.
5. Current architecture, contracts, data, quality, security and operations documents.
6. Current runtime evidence.
7. `OWNER_DECISIONS_v1.0.md`.

Earlier documentation-only runtime prohibitions are superseded only inside exact governed module 14 tasks. General governance reconciliation remains RF-02 scope.

## 3. Ownership boundary

Every table, command, mutation, event, work item, outbox record and projection has one owning module.

Forbidden:

- direct foreign-module table writes;
- private implementation imports replacing public contracts;
- UI state becoming domain authority;
- provider payload becoming an internal contract;
- provider acceptance becoming proof of human reading;
- blind retry after ambiguous external effect;
- silent account merge;
- invented provider capabilities or filters.

## 4. Existing server boundary

Use the existing server. A separate server is neither required nor authorized.

Project-owned boundaries:

- source: `/opt/avito-mayak`;
- task worktrees: `/opt/avito-mayak-worktrees/`;
- runtime: `/opt/avito-mayak-runtime/`;
- configuration: `/etc/avito-mayak/`;
- secrets: `/etc/avito-mayak/secrets/`;
- persistent data: project-owned Docker volumes or `/var/lib/avito-mayak/`;
- backups: `/var/backups/avito-mayak/`.

Foreign containers, networks, volumes, databases, Nginx, listeners and services must not be altered or reused.

Global Docker prune, firewall changes, DNS changes, certificate changes and public ingress are forbidden.

## 5. Runtime topology

Runtime mechanism:

- Docker Engine;
- Docker Compose;
- Compose project `avito-mayak`;
- optional acceptance project `avito-mayak-acceptance`;
- services `mayak-api`, `mayak-worker`, `mayak-scheduler`, `mayak-postgres`;
- one application image may use separate commands.

Kubernetes, Swarm, Redis, RabbitMQ, Celery, Kafka and external brokers are outside the accepted architecture.

## 6. Database and durable work

Authoritative persistence:

- PostgreSQL 18.x;
- SQLAlchemy 2.x;
- Psycopg 3.x;
- Alembic.

Requirements:

- one project-owned database;
- separate application and migration roles;
- PostgreSQL only on the internal project network;
- no host-published PostgreSQL port;
- no SQLite authoritative store;
- deterministic migration from zero;
- current-head verification;
- downgrade only where proven safe;
- otherwise roll-forward recovery;
- PostgreSQL-backed idempotency, leases, durable work and transactional outbox;
- no in-memory authoritative work queue;
- no framework background tasks for durable work.

## 7. Processes

API:

- FastAPI;
- Uvicorn;
- Pydantic v2;
- typed settings;
- authorization before mutation;
- transport DTOs are not domain authority.

Worker:

- claims PostgreSQL-backed work;
- bounded leases;
- explicit retry and reconciliation;
- graceful shutdown;
- restart-safe behavior.

Scheduler:

- durable due-work records;
- duplicate-safe;
- restart-safe;
- accepted tariff cadence enforcement.

## 8. Network and secrets

Acceptance runtime is local-only.

- API binds only to `127.0.0.1`;
- host port is selected from `18080–18099`;
- exact allocation is recorded;
- PostgreSQL is not host-published;
- operator access is local or through an SSH tunnel;
- live providers are disabled by default;
- no public DNS, TLS or ingress.

Configuration uses Pydantic Settings.

Secrets remain outside Git as least-privilege file-backed values with mode `0400` or `0600`, read-only mounts and redacted diagnostics.

Missing optional provider credentials disable only that provider. They do not block core runtime work.

## 9. Toolchain and CI

Toolchain:

- CPython 3.14.x standard GIL;
- exact pinned `uv`;
- committed `pyproject.toml`;
- committed `uv.lock`;
- FastAPI, Uvicorn, Pydantic v2, pydantic-settings and HTTPX;
- SQLAlchemy 2, Psycopg 3 and Alembic;
- pytest, pytest-asyncio, RESpx, Ruff, mypy, import-linter and coverage.py;
- OpenTelemetry API/SDK boundary.

CI provider is GitHub Actions.

Required future gates include lock verification, isolated dependency sync, static and architecture checks, unit/contract/integration/E2E tests, PostgreSQL integration, migration from zero, migration current-head proof, secret scan, vulnerability and license evidence, Docker build and Compose validation.

## 10. Identity

- internal `account_id` is authoritative;
- phone is not mandatory;
- standalone phone/password login is outside MVP;
- automatic account merge is forbidden;
- Telegram is the primary practical identity/channel;
- synthetic identity is acceptance-only;
- MAX linking is secondary/future;
- recovery uses verified provider relinking or audited Admin procedure.

## 11. Entitlements and billing

Tariffs:

- Free;
- Basic.

Basic:

- 990 RUB/month;
- minimum interval 5 minutes;
- interval step 5 minutes.

Free:

- one active Beacon;
- minimum interval 3 hours;
- interval step 3 hours.

Paid expiry freezes Beacons. The system does not automatically select a Free-compliant Beacon.

Payment evidence does not grant entitlement directly.

Runtime scope includes manual grants, renewals, revocations, refund records, YooKassa sandbox-ready adapter, Telegram Stars boundary and future Tinkoff boundary.

Recurring billing, trial, grace and proration are disabled.

## 12. Avito, filters and scan semantics

- source URL is initial authority;
- editable filters require evidence-backed catalog versions;
- synthetic catalogs are allowed for tests;
- unsupported, stale or ambiguous fields remain blocked;
- Filter Catalog produces a candidate only;
- Beacon Management accepts or rejects actual change;
- country-wide search is unsupported by default;
- live Avito traffic remains disabled until operator proof;
- CAPTCHA/restriction is not an empty result;
- malformed or partial response is not success;
- route failure is not parser success;
- first baseline emits no notification;
- only newly observed listings notify;
- price-change notifications are outside current scope.

## 13. Egress and channels

Server-side Egress Routing runtime is required.

Windows Egress Agent scope includes protocol boundaries, simulator, packaging/build instructions, contract tests and redacted diagnostics.

Missing Windows host is not a blocker.

Foreign proxy reuse and silent fallback are forbidden.

Current channels:

1. Telegram.
2. Web Cabinet.
3. MAX as secondary/future.
4. Other channels deferred.

Notification Delivery owns generic outbox and delivery lifecycle.

Telegram and MAX use fake providers, sandbox-ready adapters and disabled readiness without credentials.

Unknown external effect is reconcile-first.

## 14. Web Cabinet and Admin

Web Cabinet uses FastAPI server-rendered HTML, Jinja2, local CSS, minimal vanilla JavaScript and progressive enhancement.

No Node/npm build, SPA framework, external tracking or advertising pixels.

Web and Admin call owning module services and never mutate foreign-module state directly.

Every Admin mutation requires actor, authorization, reason, target, idempotency and audit.

## 15. Retention, observability and recovery

Acceptance retention:

- production personal data prohibited;
- synthetic DB records maximum 14 days;
- logs 7 days;
- test artifacts 30 days;
- backup artifacts 7 days;
- sessions maximum 24 hours;
- raw provider payloads not persisted by default;
- safe provider evidence metadata 30 days.

Required observability:

- structured JSON logs;
- environment and source SHA;
- module and operation;
- request/correlation/run/work/attempt identifiers;
- result class, latency, readiness and migration revision;
- mandatory redaction;
- liveness, readiness, version/build and safe diagnostics.

Required recovery:

- daily project-owned PostgreSQL dump;
- 7-day retention;
- restore test;
- rebuild from zero;
- migration from zero;
- API/worker/scheduler restart proof;
- interrupted work and migration handling;
- outbox and unknown-effect reconciliation;
- acceptance RPO 24 hours;
- acceptance RTO 2 hours.

## 16. Autonomous execution

After owner activation, work continues one atomic task at a time.

After every CLI report, ChatGPT independently verifies GitHub and applicable server evidence, accepts or rejects the result, issues a minimal corrective task when required and automatically continues.

Missing Telegram token, MAX token or eligibility, Avito live access, payment credentials, Windows host, public DNS, TLS, public ingress or external telemetry backend are not module blockers.

No new owner question is allowed for decisions recorded in this playbook or `OWNER_DECISIONS_v1.0.md`.

## 17. Parallel main policy

Every changing task requires:

- clean dedicated worktree;
- exact expected base;
- fetch and verify before changes;
- fetch and verify before commit and push;
- stop if GitHub main changes;
- no merge, rebase, cherry-pick, reset, amend, squash or force-push.

CLI does not choose the next roadmap step.

## 18. Roadmap

- RF-00 current state, GitHub and server verification.
- RF-01 governance capture and module 14 playbook.
- RF-02 current-main governance reconciliation.
- RF-03 thirteen-module integration inventory.
- RF-04 runtime architecture and physical data model.
- RF-05 existing-server environment record.
- RF-06 toolchain and dependency proof.
- RF-07 CI quality gates.
- RF-08 container and Compose foundation.
- RF-09 PostgreSQL and Alembic foundation.
- RF-10 Platform & Contracts runtime.
- RF-11 Identity & Access runtime.
- RF-12 Entitlements & Billing runtime.
- RF-13 Beacon Management runtime.
- RF-14 Avito Parser Adapter runtime.
- RF-15 Scan Orchestration & Listing State runtime.
- RF-16 Egress Routing runtime.
- RF-17 Notification Delivery runtime.
- RF-18 Telegram Adapter runtime.
- RF-19 MAX Adapter runtime.
- RF-20 Admin & Support runtime.
- RF-21 Web Cabinet runtime.
- RF-22 Filter Catalog & Builder runtime.
- RF-23 cross-module API and command wiring.
- RF-24 synthetic end-to-end vertical slices.
- RF-25 security, privacy and supply-chain verification.
- RF-26 observability, backup and recovery.
- RF-27 deployment on the existing server.
- RF-28 automated final regression and failure drills.
- RF-29 operator acceptance pack.
- RF-30 final evidence handoff.

## 19. Current gate

RF-00 current-state, GitHub and server verification is accepted at baseline `315d8c63bccc870a8c55bac0cd3896a687597177` with 4511 passing tests.

RF-01 governance capture and Module 14 registration are accepted.

RF-02 current-main governance reconciliation is complete at repository-content level.

The accepted RF-02 prerequisite evidence chain is:

- reconciliation audit at `59f86084bbc17386070dde34485aba6c1706712c`;
- primary governance reconciliation at `63de1f4c62e1b72626f20278dbba9eef190b6a99`;
- current decision register reconciliation at `f7733447f5f10cc3f3702c8f863accb4d9403c05`;
- documentation manifest reconciliation at `8d3ff83198d90f062906925d6f4becf66c81ed9a`;
- applicable documentation indexes reconciliation at `34db47cbbffd7f31a918963b181e3048229307be`;
- module registry and playbook gate reconciliation at `ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`.

RF-02 closure evidence is:

`CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md`

The closure document and status transition are published by task:

`RF-02-07-CURRENT-MAIN-RECONCILIATION-CLOSURE-20260723`

from expected base:

`ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`

RF-03 is the next permitted roadmap step after independent ChatGPT acceptance of the closure commit.

RF-03 remains not started until that acceptance.

Runtime, dependency, CI, Docker, database, migration, API, worker, scheduler, Web, Admin, provider, service, port and secret mutations require the applicable later RF prerequisite and one exact gated task.

Module 14 completes only after all applicable RF-00–RF-30 and corrective steps are independently accepted, deployed acceptance evidence passes, the operator pack exists and the final verdict is `READY_FOR_OPERATOR_ACCEPTANCE`.

The module must not claim `PRODUCTION_READY`.
