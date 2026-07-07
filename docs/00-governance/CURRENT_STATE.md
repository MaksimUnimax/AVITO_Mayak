# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.10
**Статус:** APPROVED snapshot
**Дата:** 2026-07-07

## Фаза

`A0.12 — Operations and external-reference documentation active; Runs 6–9 accepted; Run 10 Telegram and MAX references pending`

Public repository: `MaksimUnimax/AVITO_Mayak`, branch `main`.

Run 9 Avito reference package is published as one predeclared documentation change set: Reference Registry, Avito Reference Policy, Avito Reference Evidence, governance-state updates and append-only acceptance.

Public `main` is the factual source of truth. Independent verification procedure: `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.

TASK-001 remains limited proof-only evidence. Shared-host facts do not authorize foreign containers, databases, Nginx, ports, networks, volumes, backups, credentials or secrets.

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

### Avito Reference Foundation

- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`.

The accepted documents define modular ownership, conceptual data and contract semantics, error/idempotency, compatibility, security/privacy, quality, environments, observability, recovery/release, Windows egress and external-evidence boundaries.

Run 9 establishes that accessible first-party evidence reviewed here concerns the separate Avito Ads product. It does not establish an official consumer-search contract, permission to scrape, stable internal endpoint/page structure, supported filter catalog, country-wide support or monitoring cadence. `Duff89/parser_avito` remains a primary implementation reference only at exact commit `48441c352e36919abef13c436f41a3a62636da17`.

No product code, executable tests, fixture data files, CI/CD, migrations, backups, monitoring configuration, Windows agent, route, tunnel, service, scheduled task, listener, port, credential, provider call, parser, deployment, runtime configuration or infrastructure is created. OD-001–OD-014 remain unresolved; specifically OD-009–OD-011 remain blocked by evidence and owner decisions.

## Next safe step

Run 10 of 23: Telegram and MAX reference documentation only:

- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

Run 10 must use current official/primary sources, record retrieval date, URL, scope, status and limitations, preserve unresolved decisions, and create no bots, provider calls, credentials, code, services or runtime artifacts.
