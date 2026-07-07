# Маяк Авито — backlog документации

**Версия:** 1.4
**Статус:** APPROVED planning register

## DB-00 — accepted evidence and supervision

`TASK-001`, `REPORT-001`, TASK-001 errata, remote-supervision protocol, ADR-0006 and relevant append-only worklog entries. This does not permit code or deploy.

## DB-01 — Architecture Foundation — ACCEPTED

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

Этот package фиксирует boundaries and gates only. It does not select stack, runtime, ingress, storage, secrets product, ports, deployment method or physical data model.

## DB-02 — Common Contract Foundation — ACCEPTED

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

Этот package фиксирует semantic contract boundaries, ownership, error handling, idempotency rules and change control. It does not create API schemas, transport, runtime, queue, database objects or deployment configuration.

## DB-03 — data and compatibility — NEXT

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

## DB-04 — quality

Test Strategy, Fixture Registry, Acceptance Matrix, Reference Regression Policy.

## DB-05 — operations and references

Environment Matrix, Observability/Alerting, Backup/Recovery, Deployment/Release, Windows Egress; Reference Registry and Avito/Telegram/MAX policies/evidence.

## DB-06 — playbooks

One autonomous playbook for each of 13 modules after DB-01–DB-05.

## DB-07 — final audit

Reconcile main/manifest/roadmap/backlog; links; append-only integrity; no duplicate layouts; unresolved decisions stay open; no forbidden artifacts; reference evidence; all 13 compatible playbooks. Then stop documentation work.
