# Маяк Авито — Environment Matrix

**Версия:** 1.1
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Заменяет:** `ENVIRONMENT_MATRIX_v1.0.md` как current environment matrix; v1.0 сохраняется как historical accepted revision.
**Основание:** Environment Isolation Policy v1.0, Architecture Baseline v1.1, Technical Baseline v1.0, Security and Privacy Model v1.0, Test Strategy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, OPEN_DECISIONS.md.
**Не является:** provisioned environments, deployment topology, host inventory, port allocation, runtime configuration, cloud/provider choice или разрешением создавать infrastructure.

---

## 1. Назначение

Матрица задаёт ownership, разрешённое назначение, readiness states и evidence для future environments.

Technical Baseline выбирает application toolchain, но не создаёт ни одного environment.

## 2. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance state.
2. Environment Isolation Policy.
3. Architecture Baseline v1.1 and Technical Baseline v1.0.
4. Security, data, quality, recovery and release documents.
5. Этот Environment Matrix.
6. Future environment-specific approved record and exact task.
7. Read-only/runtime evidence после разрешённого действия.

Discovered process, listener, container, database, volume, sensitive configuration or installed binary never overrides approved documentation.

## 3. Environment classes

| Environment class | Назначение | Current state | Runtime разрешён |
|---|---|---|---|
| Local development | isolated development and synthetic checks | `RUNTIME_BLOCKED` | NO |
| Shared development host | read-only evidence/source checkout | `EVIDENCE_ONLY` | NO |
| Isolated test environment | repeatable toolchain/contract/integration/migration/recovery proofs | `UNDEFINED` | NO |
| Production | user-facing operation | `UNDEFINED` | NO |

`RUNTIME_BLOCKED` for local development means the technical stack is selected, but filesystem, dependency installation, test services, configuration and cleanup boundaries are not yet approved/provisioned.

## 4. Mandatory environment record

Before runtime use, an approved record includes:

| Field | Requirement |
|---|---|
| `environment_id` | stable logical identifier |
| `environment_class` | approved class |
| `purpose` | exact allowed/prohibited use |
| `status` | readiness state |
| `owner` | accountable project owner |
| `approval_reference` | decision/task/document revision |
| `source_revision` | exact Git SHA/release |
| `toolchain_revision` | Python/uv/lock identity |
| `filesystem_boundary` | dedicated project paths |
| `runtime_boundary` | project-owned processes/services |
| `data_boundary` | project-owned storage only |
| `network_boundary` | explicit exposure and egress |
| `configuration_boundary` | delivery/access/rotation/redaction |
| `identity_boundary` | least-privilege service/operator identity |
| `external_connectivity` | approved providers/endpoints |
| `observability_boundary` | safe signals and health semantics |
| `backup_recovery_boundary` | approved scope or `NOT_APPROVED` |
| `release_rollback_boundary` | approved procedure or `NOT_APPROVED` |
| `retention_boundary` | approved policy or blocked state |
| `evidence_freshness` | date/revision and refresh triggers |

Missing field means environment is not runtime eligible.

## 5. Readiness states

| State | Meaning |
|---|---|
| `UNDEFINED` | concept only |
| `DOCUMENTED` | boundaries described; runtime forbidden |
| `EVIDENCE_ONLY` | exact read-only evidence actions only |
| `RUNTIME_BLOCKED` | selected design exists but mandatory environment gates are absent |
| `RUNTIME_ELIGIBLE` | documentation gates complete; separate exact task still required |
| `SUSPENDED` | use prohibited pending reconciliation/security review |
| `RETIRED` | no new use; evidence/disposal obligations remain |

`RUNTIME_ELIGIBLE` is not provisioning or deployment permission.

## 6. Local development

**State:** `RUNTIME_BLOCKED`.

Approved toolchain target:

- CPython 3.14 standard build;
- uv with exact bootstrap pin;
- repository `pyproject.toml` and committed `uv.lock` after implementation task;
- core libraries from Technical Baseline v1.0;
- synthetic/redacted data only.

Still required:

- approved local filesystem boundary;
- exact OS support record;
- deterministic Python/uv installation;
- dependency cache and cleanup boundary;
- approved fake dependencies;
- no production access material;
- isolated PostgreSQL strategy for integration tests;
- network deny-by-default;
- exact toolchain proof task;
- no Docker assumption until separate decision.

Not decided:

- supported developer operating systems;
- container versus non-container local services;
- local PostgreSQL provisioning method;
- local ports;
- configuration delivery;
- frontend/browser toolchain.

## 7. Shared development host

**State:** `EVIDENCE_ONLY`.

Known boundaries:

- host contains foreign resources;
- visible resources are not project-owned;
- `/opt/avito-mayak` checkout does not authorize runtime;
- installed Python, uv, Node/npm or other tools are observations only;
- existing containers, databases, queues, Nginx, ports, networks, volumes, certificates, service accounts, configuration, logs and backups are prohibited dependencies.

Prohibited:

- package installation;
- virtual environment creation for product runtime;
- services/containers/users/listeners;
- reading foreign configuration/data/process arguments;
- firewall/DNS/ingress/Nginx/TLS changes;
- reusing occupied resources;
- storing sensitive values in repo, shell history or reports.

An exact server-sync task may only fast-forward the clean checkout to an approved GitHub SHA.

## 8. Isolated test environment

**State:** `UNDEFINED`.

Before `RUNTIME_ELIGIBLE`:

- dedicated ownership/isolation proof;
- exact source and toolchain revision;
- deterministic `uv lock`/`uv sync` evidence;
- synthetic/redacted fixtures and fake dependencies;
- no production personal data or access material;
- isolated PostgreSQL 18 strategy;
- repeatable reset/rebuild;
- toolchain, contract and migration checks;
- observability and explicit failure/ambiguity evidence;
- backup/recovery dependency for destructive tests;
- provider access separately justified by current evidence.

No external provider traffic is required for the first Platform & Contracts toolchain proof.

## 9. Production

**State:** `UNDEFINED`.

Production remains blocked until:

- owner/provider/location approved;
- runtime/data/network/configuration identities explicit;
- exact supported Python/uv/lock artifact proven;
- ingress/reverse proxy/TLS/ports approved;
- database provisioning/backup/recovery approved;
- observability backend and alert delivery approved;
- retention/privacy decisions resolved where required;
- current provider evidence;
- module playbooks and implementation tasks accepted;
- exact provisioning/deployment task accepted.

No current document claims production readiness.

## 10. Cross-environment rules

1. Environment identity is explicit in every report.
2. A revision accepted in one environment is not accepted in another automatically.
3. Production data/access material is not copied to local/test by default.
4. Synthetic/redacted fixtures are preferred outside production.
5. Lock/source revision must match the exact task.
6. Configuration promotion cannot change ownership/security/contract semantics silently.
7. Sensitive values never travel through Git, ordinary prompts or reports.
8. External connectivity is deny-by-default.
9. Shared-host foreign resources remain foreign.
10. Environment mismatch causes stop/reconciliation.
11. Tool presence in PATH does not prove supported project toolchain.
12. Python/uv patch updates require lock and compatibility evidence.

## 11. Entry gates

Before mutation/runtime action, task proves:

1. environment identity/class;
2. current documentation state;
3. source revision;
4. toolchain/lock identity;
5. owner/authorization;
6. clean known initial state;
7. dedicated filesystem/runtime/data/network boundaries;
8. configuration delivery without disclosure;
9. applicable fixtures/Acceptance Matrix v1.1 rows;
10. observability and safe evidence;
11. backup/recovery/rollback dependency when required;
12. no unresolved decision is selected silently;
13. exact allowed/forbidden actions.

Missing gate returns blocked status before mutation.

## 12. Exit evidence

Accepted action reports:

- environment and revision identity;
- toolchain/lock identity;
- before/after state;
- action class;
- succeeded/failed/partial/ambiguous inventory;
- health/readiness evidence;
- isolation/ownership checks;
- no foreign resource use;
- no sensitive-value exposure;
- rollback/reconciliation state;
- independent acceptance where required.

Exit code, reachable port or running process alone is insufficient.

## 13. Remaining open technology/operations decisions

This matrix does not select:

- OS support matrix;
- containerization;
- database provisioning;
- cache/broker/object storage;
- ports/DNS/ingress/TLS;
- configuration delivery product;
- service identities;
- monitoring backend;
- retention;
- RPO/RTO;
- release/deployment mechanism;
- Windows packaging/service model;
- frontend toolchain.

## 14. Explicit prohibitions

Этот документ не разрешает:

- provisioning;
- package installation;
- virtual environment creation on shared host;
- users/services/containers/networks/volumes/ports;
- databases/queues/migrations/backups;
- Git/SSH/server config changes;
- foreign resource or sensitive-value access;
- product-code or deployment;
- provider calls.

## 15. Acceptance criteria

Matrix accepted when:

- Technical Baseline is reflected without claiming environment provisioning;
- all environment classes have explicit states;
- shared-host evidence-only restrictions preserved;
- toolchain revision is a mandatory identity;
- entry/exit gates explicit;
- operations decisions remain deferred;
- no runtime artifact is created.

## 16. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial environment ownership/readiness matrix without stack selection. |
| 1.1 | 2026-07-07 | Reflected approved Technical Baseline while keeping every environment unprovisioned and shared host evidence-only. |
