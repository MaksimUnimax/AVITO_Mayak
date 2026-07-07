# Маяк Авито — backlog документации

**Версия:** 1.7
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

## DB-04 — quality — ACCEPTED

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

This package fixes framework-neutral quality gates, canonical semantic fixtures, acceptance traceability and external-reference regression control. It does not create executable tests, fixture data files or CI/CD.

## DB-05 — operations and references — ACTIVE

### Run 6 — environment and observability — ACCEPTED

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`.

This package fixes environment ownership/readiness, shared-host restrictions, health semantics, signal classes, redaction and alert lifecycle without provisioning or monitoring configuration.

### Run 7 — backup and release boundaries — NEXT

- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`.

### Remaining DB-05 route

- Run 8: `WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`;
- Run 9: Avito reference registry, policy and evidence;
- Run 10: Telegram and MAX reference policies.

These runs define documentation boundaries and evidence only. They do not create runtime, deploy, monitoring stack, credentials or provider implementations.

## DB-06 — playbooks

One autonomous playbook for each of 13 modules after DB-01–DB-05.

## DB-07 — final audit

Reconcile main/manifest/roadmap/backlog; links; append-only integrity; no duplicate layouts; unresolved decisions stay open; no forbidden artifacts; reference evidence; all 13 compatible playbooks. Then stop documentation work.
