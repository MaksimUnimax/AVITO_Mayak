# Маяк Авито — манифест документации

**Версия манифеста:** 4.0
**Статус:** `MODULE_14_RF02_ACTIVE`
**Дата актуализации:** 2026-07-23

## Порядок входа

Перед любой новой задачей читать в следующем порядке:

1. `README.md`
2. `docs/00-governance/PROJECT_ENTRYPOINT.md`
3. `docs/00-governance/CURRENT_STATE.md`
4. `docs/00-governance/ROADMAP.md`
5. `docs/MANIFEST.md`
6. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`
7. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md`
8. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md`
9. `docs/00-governance/OPEN_DECISIONS.md`
10. relevant append-only decision and worklog entries
11. affected architecture, contract, module, quality, operations and reference documents
12. affected module evidence handoffs

`docs/06-reports/accepted/FINAL_DOCUMENTATION_ACCEPTANCE_v1.0.md` remains historical evidence for the earlier documentation cycle. It is not the current roadmap endpoint and must not precede the active Module 14 governance when determining current work.

Exact current GitHub `main` must be fetched before every task. SHA values written in documents are evidence baselines and never replace a fresh parallel-main check.

## Current repository contour

The repository currently contains:

- Python source under `src/mayak`;
- executable unit, contract and architecture tests;
- synthetic fixture files;
- committed `pyproject.toml`;
- committed `uv.lock`;
- accepted semantic implementations and evidence handoffs for modules 01–13;
- approved Module 14 governance;
- an accepted RF-02 audit baseline recording 4511 passing tests on Python 3.14.

The semantic implementation contour exists and must not be described as absent.

The following acceptance-runtime capabilities are not yet accepted merely because source and semantic tests exist:

- GitHub Actions quality gates;
- Docker and Docker Compose foundation;
- PostgreSQL 18 authoritative persistence;
- SQLAlchemy, Psycopg and Alembic runtime integration;
- migrations from zero;
- separate API, worker and scheduler runtime entry points;
- DB-backed module persistence;
- cross-module HTTP and command wiring;
- deployed Web Cabinet and Admin runtime;
- synthetic end-to-end deployment proof;
- backup, restore and recovery proof;
- deployment on the existing project server;
- operator acceptance pack;
- final Module 14 handoff.

## Current roadmap state

- RF-00 — accepted.
- RF-01 — accepted.
- RF-02 — active current-main governance reconciliation.
- RF-02 reconciliation audit — accepted.
- RF-02 primary governance reconciliation — accepted.
- RF-02 current decision register reconciliation — accepted.
- RF-03–RF-30 — not accepted.

RF-02 remains active until the manifest and applicable documentation indexes no longer contradict the repository tree, current governance and Module 14 playbook.

RF-03 must not start before RF-02 is independently closed.

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

These documents remain accepted semantic and design foundations. Exact Module 14 physical runtime architecture and data model remain RF-04 scope.

### Common Contract Foundation

- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

Modules 01–13 retain ownership of their domain state. Module 14 may assemble runtime only through public contracts and must not introduce direct foreign-module writes.

### Data and Compatibility Foundation

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

These are accepted logical and compatibility foundations. PostgreSQL physical schema, Alembic migration chain and persistence adapters remain later exact Module 14 tasks.

### Quality Foundation

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

Historical revision retained:

- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`.

Executable tests and synthetic fixtures exist. The accepted RF-02 audit baseline records 4511 passing tests. This does not prove future CI, PostgreSQL integration, migration, Docker, deployed E2E or recovery gates.

### Operations Foundation

Current documents under `docs/08-operations/` define:

- environment isolation;
- environment matrix;
- observability boundaries;
- backup and recovery expectations;
- deployment and release boundaries;
- Windows Egress Agent boundaries.

`docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md` remains an accepted operations foundation.

The existing project server is authorized for Module 14 through exact gated tasks. Foreign resources remain protected. A complete project-owned runtime deployment is not yet accepted.

### External Reference Foundation

- `docs/09-references/REFERENCE_REGISTRY_v1.1.md`;
- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

Provider evidence does not authorize live traffic by itself.

Module 14 requires synthetic providers and sandbox-ready adapters while live provider profiles remain disabled until credentials, exact evidence and operator acceptance are available.

Missing optional provider credentials are not a core Module 14 blocker.

## Module playbooks

### Accepted domain modules

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

Modules 01–13 are accepted semantic, contract, ownership, test and evidence prerequisites. Their acceptance does not by itself prove DB-backed runtime deployment.

### Active cross-cutting module

- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md` — v1.0 APPROVED.
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md` — v1.0 APPROVED.
- `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md` — RF-02 accepted audit input.

Module 14 is active.

Its target is:

`SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`

Its completion boundary is:

`READY_FOR_OPERATOR_ACCEPTANCE`

Module 14 must not claim:

`PRODUCTION_READY`

before separate operator acceptance and a future production launch gate.

## Historical final documentation evidence

- `docs/06-reports/accepted/FINAL_DOCUMENTATION_ACCEPTANCE_v1.0.md` — historical `FINAL_GOVERNANCE_ACCEPTANCE_PUBLISHED` evidence for the earlier documentation-only cycle.

It remains valid historical evidence but is not the current project endpoint.

The historical no-runtime conclusion is superseded only inside exact governed Module 14 tasks. Public production launch remains blocked.

## Каталоги

| Каталог | Назначение | Current status |
|---|---|---|
| `00-governance` | rules, current state, roadmap, decisions and worklog | RF-02 current-main reconciliation active |
| `01-product` | historical product target and product context | v0.1 draft retained; current Module 14 decisions governed separately |
| `02-architecture` | architecture, technical, security, data and compatibility | semantic foundations accepted; RF-04 physical runtime design pending |
| `03-contracts` | common and public module contracts | accepted semantic foundation |
| `04-modules` | modules 01–13 plus cross-cutting Module 14 | modules 01–13 accepted; Module 14 active; RF-02 in progress |
| `05-tasks` | historical literal execution packets | historical task evidence; current roadmap authority remains governance and GitHub main |
| `06-reports` | accepted reports and module handoffs | modules 01–13 evidence accepted; Module 14 final handoff pending |
| `07-quality` | strategy, fixtures, acceptance and regression | executable tests and synthetic fixtures exist; CI/deployed runtime gates pending |
| `08-operations` | isolation, environments, observability, recovery, release and Windows egress | design boundaries accepted; project runtime deployment pending |
| `09-references` | external evidence and provider policies | evidence accepted within scope; live providers disabled by default |

## Non-negotiable current boundaries

- GitHub `main` is the only repository source of truth.
- Exact current `main` is fetched before every task.
- CLI performs one literal atomic task and does not choose the next roadmap step.
- Modules 01–13 retain domain-state ownership.
- Direct foreign-module table writes are forbidden.
- Provider payloads are not internal contracts or business authority.
- Provider acceptance is not proof of human reading.
- Ambiguous external effects are reconcile-first.
- Secrets, private keys, populated `.env` files and production personal data must not enter Git or reports.
- Foreign server resources must not be altered or reused.
- Runtime is local-only until a separate future production gate.
- PostgreSQL must not be host-published.
- Public ingress, DNS, TLS, firewall and production-provider activation remain unauthorized.
