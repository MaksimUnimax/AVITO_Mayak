# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.9
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.12 — Operations and external-reference documentation active; Runs 6–8 accepted; Run 9 Avito references pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 8 Windows Egress Agent package опубликован commit `8cd1082caa82c6eb61615f71b27f0bda10756c41` как основной deliverable одного заранее определённого documentation change set; governance-state updates и append-only acceptance входят в тот же Run 8 package.

Public `main` — фактический источник истины. Процедура независимой проверки: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 принят только как ограниченное proof-only evidence. Shared-host facts не разрешают использовать foreign containers, databases, Nginx, ports, networks, volumes, backups, credentials или secrets.

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

### Windows Egress Agent Boundaries

- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

Принятые documents фиксируют modular boundaries, ownership, conceptual data domains, contract semantics, error/idempotency rules, migration/compatibility gates, security/privacy limits, quality gates, canonical semantic fixtures, acceptance traceability, environment readiness/ownership, observability/alerting semantics, backup/recovery lifecycle, release/deployment gates and Windows egress agent/route/lease safety boundaries.

Они не выбирают implementation language, framework, package manager, test framework, CI provider, queue, transport, serialization, monitoring stack, alert thresholds/channels, backup/storage technology, retention, RPO/RTO, deployment tooling/strategy, ingress, reverse proxy, TLS, ports, tunnel/VPN/proxy protocol, Windows service/task model, agent credentials, route thresholds/switching policy, storage implementation, secrets product, physical database schema, migration tool или runtime topology.

No product code, executable tests, fixture data files, CI/CD, migrations, backup/snapshot, restore, monitoring configuration, live alerts, Windows agent, route, tunnel, service, scheduled task, inbound listener, port, credential, project service, deployment pipeline, deploy configuration, provider call, external key or new infrastructure exists. Existing approved ADRs remain authoritative only within their recorded scope; unresolved items remain in `OPEN_DECISIONS.md`.

## Next safe step

Run 9 of 23: Avito reference documentation only:

- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`.

Run 9 must use verified official or primary sources, record retrieval date, URL, scope, status and limitations, and must not send Avito requests, implement parser/route behavior, create credentials, close product decisions by assumption or create runtime artifacts.
