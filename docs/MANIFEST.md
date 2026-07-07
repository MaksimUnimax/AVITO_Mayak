# Маяк Авито — манифест документации

**Версия манифеста:** 2.0
**Статус:** APPROVED

## Порядок входа

1. `README.md`
2. `docs/00-governance/PROJECT_ENTRYPOINT.md`
3. `docs/00-governance/CURRENT_STATE.md`
4. `docs/00-governance/ROADMAP.md`
5. `docs/00-governance/DOCUMENTATION_BACKLOG.md`
6. `docs/00-governance/REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`
7. relevant append-only decision/worklog entries
8. `docs/00-governance/OPEN_DECISIONS.md`
9. current architecture/technical/contracts/data/quality/operations/reference/module documents

## Current approved foundation documents

### Architecture and Technical Foundation

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_ISOLATION_POLICY_v1.0.md`.

Historical revision retained:

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`.

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
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

Historical revision retained:

- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`.

### Operations Environment Foundation

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`.

Historical revision retained:

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`.

### Recovery and Release Boundaries

- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`.

### Windows Egress Agent Boundaries

- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### Avito Reference Foundation

- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`.

## Каталоги

| Каталог | Назначение | Current status |
|---|---|---|
| `00-governance` | rules, state, decisions, worklog | approved governance |
| `01-product` | product model | v0.1 DRAFT |
| `02-architecture` | architecture, technical, security, data and compatibility | current baselines approved |
| `03-contracts` | common contracts | APPROVED |
| `04-modules` | 13 playbooks | pending Runs 12–24 |
| `05-tasks` | literal CLI packets | TASK-001 completed |
| `06-reports` | evidence reports | REPORT-001 accepted |
| `07-quality` | strategy, fixtures, acceptance, reference regression | current matrix v1.1 APPROVED |
| `08-operations` | isolation, environments, observability, recovery, release, Windows egress | current environment matrix v1.1 APPROVED |
| `09-references` | external evidence | Avito APPROVED; Telegram/MAX Run 11 next |

Statuses: `DRAFT`, `CANDIDATE`, `APPROVED`, `SUPERSEDED`, `ARCHIVED`. Historical approved revisions remain evidence for documents that used them; current work uses the versions listed as current above.
