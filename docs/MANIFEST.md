# Маяк Авито — манифест документации

**Версия манифеста:** 1.9
**Статус:** APPROVED

## Порядок входа

1. `README.md`
2. `docs/00-governance/PROJECT_ENTRYPOINT.md`
3. `CURRENT_STATE.md`
4. `ROADMAP.md`
5. `DOCUMENTATION_BACKLOG.md`
6. `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`
7. relevant append-only decision/worklog entries
8. `OPEN_DECISIONS.md`
9. relevant architecture, data, contract, quality, operations, task, report, module playbook and reference evidence.

## Approved foundation documents

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

## Каталоги

| Каталог | Назначение | Статус |
|---|---|---|
| `00-governance` | rules, state, decisions, worklog | approved governance |
| `01-product` | product model | v0.1 DRAFT |
| `02-architecture` | architecture, security, data and compatibility documents | map DRAFT; approved baselines present |
| `03-contracts` | common contracts | Common Contract Foundation APPROVED |
| `04-modules` | 13 playbooks | pending |
| `05-tasks` | literal CLI packets | TASK-001 completed |
| `06-reports` | accepted/rejected evidence | REPORT-001 accepted |
| `07-quality` | quality gates, fixtures, acceptance and reference regression | Quality Foundation APPROVED |
| `08-operations` | isolation, environment, observability, recovery, release and Windows egress boundaries | Runs 6–8 APPROVED |
| `09-references` | external reference evidence | Run 9 APPROVED; Run 10 next |

Statuses: `DRAFT`, `CANDIDATE`, `APPROVED`, `SUPERSEDED`, `ARCHIVED`. Change rules: `DOCUMENTATION_GOVERNANCE.md`.
