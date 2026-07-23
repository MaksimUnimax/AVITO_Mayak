# Module 14 Owner Decisions

**Version:** 1.0
**Status:** APPROVED
**Date:** 2026-07-23
**Module:** `14-runtime-foundation-and-autonomous-integration`
**Related playbook:** `MODULE_PLAYBOOK.md`

## 1. Authority

This document records owner decisions for RF-01–RF-30.

CLI may not reopen, alter or expand these decisions.

An undocumented technical fork is resolved by ChatGPT using the minimal, reversible, least-privilege, synthetic-first, provider-disabled-by-default, no-public-ingress, no-new-stateful-dependency, ownership-safe, testable and documented option.

## 2. Runtime phase

- phase: `AUTONOMOUS_RUNTIME_COMPLETION`;
- target: `SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`;
- completion boundary: `READY_FOR_OPERATOR_ACCEPTANCE`;
- public production launch is outside module 14;
- runtime mutations require exact accepted roadmap tasks.

## 3. Existing server

- use the existing project server;
- do not require a separate server;
- source path is `/opt/avito-mayak`;
- project-owned worktrees, runtime, configuration, secrets, data and backups are allowed by exact tasks;
- foreign resources must not be altered or reused;
- global Docker prune is forbidden.

## 4. Runtime stack

- Docker Engine and Docker Compose;
- Compose project `avito-mayak`;
- FastAPI and Uvicorn;
- separate API, worker and scheduler processes;
- PostgreSQL 18;
- SQLAlchemy 2;
- Psycopg 3;
- Alembic;
- PostgreSQL-backed durable work and outbox;
- no Redis, RabbitMQ, Celery, Kafka or external broker.

## 5. Network and secrets

- local-only acceptance runtime;
- API only on `127.0.0.1:18080–18099`;
- PostgreSQL is not host-published;
- no public ingress, DNS, TLS, firewall or Nginx changes;
- configuration uses Pydantic Settings;
- secrets remain outside Git as file-backed values with mode `0400` or `0600`;
- missing optional credentials disable only the affected provider;
- automatic core completion does not wait for provider credentials.

## 6. Toolchain, CI and Web

- CPython 3.14 standard GIL;
- exact pinned `uv`;
- committed `pyproject.toml` and `uv.lock`;
- GitHub Actions;
- required static, architecture, test, migration, security, dependency, Docker and Compose gates;
- Web uses FastAPI, Jinja2, local CSS and minimal vanilla JavaScript;
- no Node/npm build requirement;
- no SPA framework or third-party tracking.

## 7. Identity decisions

`OD-006`:
Standalone phone/password login is outside MVP.

`OD-007`:
Phone is not mandatory.

`OD-008`:
Automatic account merge is forbidden. Any future merge requires a separate audited Admin workflow and acceptance.

Additional identity rules:

- internal `account_id` is authoritative;
- Telegram is the primary practical identity/channel;
- synthetic identity is acceptance-only;
- MAX linking is secondary/future;
- recovery uses verified provider relinking or audited Admin procedure.

## 8. Billing decisions

- tariffs are Free and Basic;
- Basic costs 990 RUB/month;
- Basic interval minimum is 5 minutes with 5-minute step;
- Free permits one active Beacon;
- Free interval minimum is 3 hours with 3-hour step;
- paid expiry freezes Beacons;
- the system never automatically chooses a Free Beacon;
- manual grants, renewals, revocations and refund records are required;
- YooKassa is the first sandbox-ready payment adapter;
- Telegram Stars boundary is prepared;
- Tinkoff remains future;
- recurring billing, trial, grace and proration are disabled;
- payment evidence never grants entitlement directly.

Accepted entitlement ADRs, including ADR-0009, remain authoritative.

## 9. Avito and filter decisions

`OD-009`:
Do not invent a complete Avito filter catalog. Editable filters require evidence-backed catalog versions. Synthetic catalogs are allowed for automated tests.

`OD-010`:
Country-wide search is unsupported by default and may be enabled only by accepted capability evidence.

`OD-011`:
Scheduler enforces accepted tariff intervals. Live Avito traffic remains disabled until operator live-proof.

Additional parser and scan rules:

- source URL is initial authority;
- unsupported, stale or ambiguous fields remain blocked;
- Filter Catalog creates a candidate only;
- Beacon Management owns accepted configuration changes;
- CAPTCHA/restriction is not an empty result;
- malformed or partial response is not success;
- route failure is not parser success;
- first baseline emits no notification;
- only newly observed listings notify;
- price-change notifications are outside current scope.

## 10. Egress and channel decisions

- server-side Egress Routing runtime is required;
- Windows Agent protocol, simulator, packaging/build path and tests are required;
- missing Windows host is not a blocker;
- foreign proxy reuse and silent fallback are forbidden.

`OD-012`:
Current channels are Telegram as primary practical channel, Web Cabinet as first-party channel and MAX as secondary/future. Other channels are deferred.

Notification Delivery owns generic outbox and delivery lifecycle.

Telegram and MAX require fake providers, sandbox-ready adapters and disabled readiness without credentials.

Unknown external effect is reconcile-first.

## 11. Web, Admin and analytics decisions

`OD-014`:
Web Cabinet MVP includes account summary, active Beacons, Beacon history/archive, lifecycle commands, tariff/access/limits, scan status, notification history, channel status and support status/public answer.

`OD-014` also fixes Admin & Support MVP scope:

- account lookup and safe summary;
- Beacon, tariff, access, limit, scan, anchor and notification summaries;
- role commands through Identity;
- tariff/access commands through Entitlements;
- Beacon commands through Beacon Management;
- anchor correction through Scan;
- support cases, notes and audit history;
- first-party aggregated analytics for visitors, registered users, active users, Free users and paid users grouped by tariff;
- period, tariff and account/use-status filters;
- sortable aggregated table;
- no third-party analytics or marketing pixels.

Web and Admin never directly mutate foreign-module tables.

Every Admin mutation requires actor, authorization, reason, target, idempotency and audit.

## 12. Retention, observability and recovery

Acceptance retention:

- production personal data is prohibited;
- synthetic records maximum 14 days;
- logs 7 days;
- test artifacts 30 days;
- backups 7 days;
- sessions maximum 24 hours;
- raw provider payload persistence disabled by default;
- safe provider evidence metadata 30 days.

Required observability:

- structured JSON logs;
- source SHA and environment ID;
- module and operation;
- correlation and work identifiers;
- result, latency, readiness and migration revision;
- mandatory redaction;
- liveness, readiness, version/build and safe diagnostics.

Required recovery:

- daily PostgreSQL dump;
- restore and rebuild-from-zero tests;
- migration from zero;
- API/worker/scheduler restart;
- interrupted work and migration handling;
- outbox and unknown-effect reconciliation;
- acceptance RPO 24 hours;
- acceptance RTO 2 hours.

## 13. No-new-owner-question policy

Do not ask the owner new questions about server, container runtime, database, process topology, CI, frontend, phone/password/merge, tariffs, filter fallback, country-wide support, cadence, channels, retention, local port, secrets, observability, backup, payment adapter or synthetic scope.

## 14. External non-blockers

Module 14 does not stop for missing Telegram token, MAX token or eligibility, Avito live access, payment credentials, Windows host, public DNS, TLS, public ingress or external telemetry backend.

Code, fake/sandbox tests, disabled readiness and exact operator instructions must be completed, then the roadmap continues.

## 15. Final boundary

Automatic work ends only after all applicable RF-00–RF-30 and corrective steps are accepted, deployed acceptance runtime passes, operator pack exists and final handoff states `READY_FOR_OPERATOR_ACCEPTANCE`.

The project must not claim `PRODUCTION_READY` before separate operator and production-launch acceptance.
