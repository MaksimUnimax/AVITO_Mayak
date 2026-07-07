# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.8
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.12 — Operations and external-reference documentation active; Runs 6–7 accepted; Run 8 Windows egress pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 7 Recovery and Release package опубликован commits `d5234d2ad884e07caec12adbe8906b7470cf2950` и `5c3020490d15ad3b432209ebee0562e7291c5288` как один заранее определённый documentation change set.

Public `main` — фактический источник истины. Процедура независимой проверки: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 принят только как ограниченное proof-only evidence. Shared-host facts не разрешают использовать foreign containers, databases, Nginx, ports, networks, volumes, backups или secrets.

## Принятые foundation documents

### Architecture Foundation

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

### Common Contract Foundation

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

### Data and Compatibility Foundation

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

### Quality Foundation

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

### Operations Environment Foundation

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`.

### Recovery and Release Boundaries

- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`.

Принятые documents фиксируют modular boundaries, ownership, conceptual data domains, contract semantics, error/idempotency rules, migration/compatibility gates, security/privacy limits, quality gates, canonical semantic fixtures, acceptance traceability, environment readiness/ownership, observability/alerting semantics, backup/recovery lifecycle and release/deployment gates.

Они не выбирают implementation language, framework, package manager, test framework, CI provider, queue, transport, serialization, monitoring stack, alert thresholds/channels, backup/storage technology, retention, RPO/RTO, deployment tooling/strategy, ingress, reverse proxy, TLS, ports, storage implementation, secrets product, physical database schema, migration tool или runtime topology.

No product code, executable tests, fixture data files, CI/CD, migrations, backup/snapshot, restore, monitoring configuration, live alerts, project service, deployment pipeline, deploy configuration, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 8 of 23: Windows Egress Agent documentation only:

- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

Run 8 must not create or configure a Windows agent, host, route, tunnel, service, scheduler, credential, port, firewall rule, runtime or provider access. It documents ownership, registration, health, lease, quarantine, failure and evidence boundaries only.
