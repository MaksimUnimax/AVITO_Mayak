# Маяк Авито — backlog документации

**Версия:** 1.5
**Статус:** APPROVED planning register

## DB-00 — accepted evidence and supervision

`TASK-001`, `REPORT-001`, TASK-001 errata, remote-supervision protocol, ADR-0006 and relevant append-only worklog entries. This does not permit code or deploy.

## DB-01 — Architecture Foundation — ACCEPTED

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

This package fixes architecture, isolation and security boundaries without selecting implementation technology.

## DB-02 — Common Contract Foundation — ACCEPTED

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

This package fixes contract semantics, ownership, errors, idempotency and change control without implementation schemas.

## DB-03 — data and compatibility — ACCEPTED

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

This package fixes conceptual data ownership, isolation, privacy and future compatibility gates. It does not create physical storage or executable migrations.

## DB-04 — quality — NEXT

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

## DB-05 — operations and references

Environment Matrix, Observability/Alerting, Backup/Recovery, Deployment/Release, Windows Egress; Reference Registry and Avito/Telegram/MAX policies/evidence.

## DB-06 — playbooks

One autonomous playbook for each of 13 modules after DB-01–DB-05.

## DB-07 — final audit

Reconcile main/manifest/roadmap/backlog; links; append-only integrity; no duplicate layouts; unresolved decisions stay open; no forbidden artifacts; reference evidence; all 13 compatible playbooks. Then stop documentation work.
