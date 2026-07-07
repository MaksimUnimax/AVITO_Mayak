# Маяк Авито — манифест документации

**Версия манифеста:** 2.8
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

Historical revision retained: `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`.

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

Historical revision retained: `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`.

### Operations Foundation

- current documents under `docs/08-operations/` listed by its README and backlog;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### External Reference Foundation

- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

### Module Playbooks

- `docs/04-modules/01-platform-and-contracts/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/02-identity-and-access/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/06-scan-orchestration-and-listing-state/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md` — v1.0 APPROVED document; Run 18 server acceptance pending.
- Modules 08–13 — RESERVED; Runs 19–24.

## Каталоги

| Каталог | Назначение | Current status |
|---|---|---|
| `00-governance` | rules, state, decisions, worklog | approved governance |
| `01-product` | product model | v0.1 DRAFT |
| `02-architecture` | architecture, technical, security, data and compatibility | current baselines approved |
| `03-contracts` | common contracts | APPROVED documentation baseline |
| `04-modules` | 13 playbooks | 7 published; 6 reserved |
| `05-tasks` | literal execution packets | TASK-001 historical/completed; no active implementation task |
| `06-reports` | evidence reports and handoffs | REPORT-001 accepted historically; no product-code report |
| `07-quality` | strategy, fixtures, acceptance, reference regression | APPROVED documentation baseline |
| `08-operations` | isolation, environments, observability, recovery, release, Windows egress | APPROVED documentation baseline; no runtime/deploy |
| `09-references` | external evidence | Avito, Telegram and MAX documentation approved; provider implementation absent |

Statuses: `DRAFT`, `CANDIDATE`, `RESERVED`, `APPROVED`, `SUPERSEDED`, `ARCHIVED`. A document may be APPROVED on GitHub while its run remains pending exact server synchronization; `CURRENT_STATE.md` is authoritative for run acceptance.
