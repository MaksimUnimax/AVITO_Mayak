# Маяк Авито — манифест документации

**Версия манифеста:** 3.1
**Статус:** MODULE_14_AUTONOMOUS_RUNTIME_COMPLETION_ACTIVE

## Порядок входа

1. `README.md`
2. `docs/00-governance/PROJECT_ENTRYPOINT.md`
3. `docs/00-governance/CURRENT_STATE.md`
4. `docs/00-governance/ROADMAP.md`
5. `docs/00-governance/DOCUMENTATION_BACKLOG.md`
6. `docs/06-reports/accepted/FINAL_DOCUMENTATION_ACCEPTANCE_v1.0.md`
7. `docs/00-governance/REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`
8. relevant append-only decision/worklog entries
9. `docs/00-governance/OPEN_DECISIONS.md`
10. current architecture/technical/contracts/data/quality/operations/reference/module documents
11. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`
12. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md`

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
- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/08-notification-delivery/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/11-admin-and-support/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/12-web-cabinet/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` — v1.0 APPROVED and accepted.
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED; cross-cutting integration module; RF-01 active.
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED; owner decisions for RF-01–RF-30.

### Final governance

- `docs/06-reports/accepted/FINAL_DOCUMENTATION_ACCEPTANCE_v1.0.md` — FINAL_GOVERNANCE_ACCEPTANCE_PUBLISHED; exact final server synchronization pending.

The final documentation acceptance remains the historical baseline for modules 01–13. Module 14 is now active under its approved playbook and owner decisions. This activation supersedes the historical no-runtime conclusion only inside exact governed module 14 tasks. Broader current-main governance reconciliation remains RF-02 scope.

## Каталоги

| Каталог | Назначение | Current status |
|---|---|---|
| `00-governance` | rules, state, decisions, worklog | final governance state published |
| `01-product` | product model | v0.1 DRAFT |
| `02-architecture` | architecture, technical, security, data and compatibility | current baselines approved |
| `03-contracts` | common contracts | APPROVED documentation baseline |
| `04-modules` | 13 accepted domain playbooks plus module 14 cross-cutting integration governance | modules 01–13 accepted; module 14 RF-01 active |
| `05-tasks` | literal execution packets | TASK-001 historical/completed; no active implementation task |
| `06-reports` | evidence reports and handoffs | final documentation acceptance published; no product-code report |
| `07-quality` | strategy, fixtures, acceptance, reference regression | APPROVED documentation baseline |
| `08-operations` | isolation, environments, observability, recovery, release, Windows egress | APPROVED documentation baseline; no runtime/deploy |
| `09-references` | external evidence | Avito, Telegram and MAX documentation approved; provider implementation absent |

Statuses: `DRAFT`, `CANDIDATE`, `RESERVED`, `APPROVED`, `SUPERSEDED`, `ARCHIVED`, `FINAL_GOVERNANCE_ACCEPTANCE_PUBLISHED`, `MODULE_14_AUTONOMOUS_RUNTIME_COMPLETION_ACTIVE`. Modules 01–13 retain their accepted evidence. Module 14 is active and completes only with `READY_FOR_OPERATOR_ACCEPTANCE`; it must not claim `PRODUCTION_READY`.
