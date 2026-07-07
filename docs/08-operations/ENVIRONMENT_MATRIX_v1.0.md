# Маяк Авито — Environment Matrix

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Environment Isolation Policy v1.0, Architecture Baseline v1.0, Security and Privacy Model v1.0, Test Strategy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, OPEN_DECISIONS.md.
**Не является:** перечнем provisioned environments, deployment topology, host inventory, port allocation, runtime configuration, cloud/provider choice или разрешением создавать infrastructure.

---

## 1. Назначение

Environment Matrix задаёт единый документный способ описывать будущие project environments, их ownership, разрешённое назначение, readiness gates и допустимое evidence.

Матрица не утверждает существование project runtime. Она предотвращает подмену: видимый host/resource не становится project-owned environment без отдельного доказанного approval.

## 2. Source-of-truth hierarchy

1. Public GitHub `main` и approved governance state.
2. Approved Environment Isolation Policy.
3. Approved architecture, security, data, quality and compatibility documents.
4. Этот Environment Matrix.
5. Future environment-specific approved record and exact task packet.
6. Read-only/runtime evidence конкретного environment после разрешённого действия.

Local server state, discovered process, listener, container, database, volume, reverse proxy or credential не переопределяют approved documentation.

## 3. Environment classes

Следующие классы являются документационными категориями, а не созданной инфраструктурой:

| Environment class | Назначение | Текущий статус | Runtime разрешён |
|---|---|---|---|
| Local development | Будущая изолированная разработка и локальные проверки | not designed / not provisioned | NO |
| Shared development host | Ограниченный read-only evidence/source host | observed evidence-only; foreign resources prohibited | NO |
| Isolated test environment | Будущие repeatable contract, integration, migration and recovery checks | not designed / not provisioned | NO |
| Production | Будущая эксплуатация пользовательского продукта | not designed / not provisioned | NO |

Введение нового environment class требует отдельного documentation change packet и не может происходить только через runtime action.

## 4. Mandatory environment record

До любого разрешённого использования environment его approved record обязан содержать:

| Поле | Требование |
|---|---|
| `environment_id` | Stable logical identifier, не IP/hostname как единственный identity |
| `environment_class` | Один approved class из матрицы или separately approved extension |
| `purpose` | Exact allowed use and prohibited use |
| `status` | Documentation readiness state |
| `owner` | Project/accountable owner, не inferred host user |
| `approval_reference` | Approved decision/task/document revision |
| `source_revision` | Exact Git SHA or release identity, если runtime разрешён |
| `filesystem_boundary` | Dedicated project-owned paths; foreign paths prohibited |
| `runtime_boundary` | Project-owned process/container/service boundary after approval |
| `data_boundary` | Project-owned storage only; foreign databases/queues prohibited |
| `network_boundary` | Explicit exposure decision; bind/port ownership separately approved |
| `secret_boundary` | Delivery, access, rotation and redaction boundary after approval |
| `identity_boundary` | Project service/operator identity and least privilege |
| `external_connectivity` | Allowed providers/endpoints based on current evidence |
| `observability_boundary` | Safe signals, health semantics and redaction |
| `backup_recovery_boundary` | Approved scope and proof, or explicit `NOT_APPROVED` |
| `release_rollback_boundary` | Approved procedure, or explicit `NOT_APPROVED` |
| `retention_boundary` | Approved policy, or explicit blocked/open state |
| `evidence_freshness` | Date/revision and conditions requiring refresh |

Missing mandatory field means the environment is not approved for runtime.

## 5. Documentation readiness states

| State | Meaning |
|---|---|
| `UNDEFINED` | Environment is only a concept; no approved record |
| `DOCUMENTED` | Purpose and boundaries described; runtime still forbidden |
| `EVIDENCE_ONLY` | Exact read-only evidence actions may be approved; no project runtime |
| `RUNTIME_BLOCKED` | Record exists but one or more mandatory gates are absent |
| `RUNTIME_ELIGIBLE` | Documentation gates are complete; a separate exact provisioning/use task is still required |
| `SUSPENDED` | Further use prohibited pending reconciliation or security/ownership review |
| `RETIRED` | No new use; retained evidence and disposal obligations remain |

`RUNTIME_ELIGIBLE` is not permission to provision or deploy. It only allows a separate owner decision and exact task to be prepared.

## 6. Current environment matrix

### 6.1. Local development

**State:** `UNDEFINED`.

Required before use:

- approved local filesystem and dependency isolation;
- synthetic/redacted test data only;
- no production credentials;
- approved fake dependencies;
- exact supported toolchain decision after separate approval;
- reproducible cleanup and evidence boundaries.

Not decided:

- operating system support matrix;
- language, framework, package manager or test runner;
- container versus non-container execution;
- local database/queue/storage technology;
- local port allocation.

### 6.2. Shared development host

**State:** `EVIDENCE_ONLY`.

Known approved interpretation:

- host contains foreign resources;
- visibility does not establish ownership;
- existing containers, databases, queues, Nginx, ports, networks, volumes, certificates, service accounts, credentials, logs and backups are prohibited project dependencies;
- only explicitly approved read-only evidence work is permitted;
- `/opt/avito-mayak` repository sync does not authorize runtime or reuse of other host resources.

Prohibited:

- creating services, users, containers, networks, volumes, databases or listeners;
- reading foreign configuration, application data, credentials or process arguments;
- modifying firewall, DNS, ingress, Nginx, TLS, system services or package state;
- treating an occupied or visible resource as available capacity;
- storing project secrets in repository, shell history or ordinary reports.

### 6.3. Isolated test environment

**State:** `UNDEFINED`.

Before `RUNTIME_ELIGIBLE`, required:

- dedicated ownership and isolation proof;
- exact source revision identity;
- synthetic/redacted fixtures and fake dependencies;
- no production personal data or credentials;
- repeatable reset/rebuild boundary without destructive use of foreign state;
- observability and explicit failure/ambiguity evidence;
- migration/reconciliation gates when applicable;
- backup/recovery dependency for destructive or irreversible tests;
- network/provider access separately justified by current reference evidence.

### 6.4. Production

**State:** `UNDEFINED`.

Production remains blocked until at least:

- environment owner and provider/location are approved;
- filesystem/runtime/data/network/secret identities are explicit;
- ingress, reverse proxy, TLS and port ownership are approved;
- observability and alerting semantics are approved and implementable;
- backup/recovery and release/rollback documents are accepted;
- retention/privacy decisions required by the scope are accepted;
- provider reference evidence is current;
- module playbooks and implementation tasks are accepted;
- exact provisioning and deployment tasks receive separate approval.

No current document claims production readiness.

## 7. Cross-environment rules

1. Environment identity must be explicit in every operational report.
2. A revision accepted in one environment is not automatically accepted in another.
3. Production data, credentials and provider sessions must not be copied to local/test by default.
4. Synthetic/redacted fixtures are preferred outside production.
5. Configuration promotion cannot silently change ownership, authorization, privacy or contract semantics.
6. Secret values are never transferred through Git, ordinary task prompts or reports.
7. External connectivity is deny-by-default until provider, scope and evidence are approved.
8. A read model, cache, snapshot or backup does not become authoritative source by relocation.
9. Shared-host foreign resources remain foreign across all environment classes.
10. Environment mismatch produces stop/reconciliation, not best-effort continuation.

## 8. Environment entry gates

Before any future mutation or runtime action, the exact task must prove:

1. expected `environment_id` and class;
2. current documentation state;
3. exact Git/release revision;
4. owner and authorization;
5. clean/known initial state;
6. dedicated filesystem/runtime/data/network boundaries;
7. secret delivery without disclosure;
8. applicable fixtures and Acceptance Matrix rows;
9. observability and safe evidence;
10. backup/recovery and rollback/roll-forward dependency when required;
11. no unresolved decision is being silently selected;
12. exact allowed and forbidden actions.

A missing gate returns a blocked status before mutation.

## 9. Environment exit and acceptance evidence

A future environment action is accepted only with:

- exact environment and revision identity;
- before/after state;
- performed action class;
- explicit succeeded, failed, partial and ambiguous inventory;
- health/readiness evidence according to approved semantics;
- clean ownership and isolation checks;
- no foreign resource use;
- no secret exposure;
- rollback/reconciliation state;
- independent acceptance where governance requires it.

Exit code, reachable port, running process or container status alone does not prove readiness or correctness.

## 10. Change control

Environment boundary change requires:

- reason and authoritative evidence;
- old/new environment record;
- ownership and security impact;
- network/data/secret impact;
- affected operations, contracts and module playbooks;
- migration/compatibility analysis if persisted state is affected;
- observability and acceptance updates;
- rollback/retirement plan;
- approved publication and independent review.

Moving workload between hosts/providers is not a mere address change when ownership, trust or recovery boundaries differ.

## 11. Open decisions

This matrix intentionally does not decide:

- environment providers, regions or hosts;
- operating systems;
- containerization/runtime model;
- language/framework/toolchain;
- database, queue, cache or object storage;
- ports, DNS, ingress, reverse proxy or TLS;
- secrets manager and rotation mechanism;
- service identities and permission implementation;
- monitoring stack and alert channels;
- retention periods;
- production recovery objectives;
- release/deployment mechanism.

## 12. Explicit prohibitions

This document does not authorize:

- provisioning any environment;
- creating users, services, containers, networks, volumes or ports;
- installing packages;
- creating databases, queues, migrations or backups;
- changing Git/SSH/server configuration;
- accessing foreign resources or secrets;
- deploying product-code;
- performing provider calls;
- marking production ready.

## 13. Acceptance criteria

Environment Matrix is accepted when:

- all approved environment classes have explicit current states;
- shared-host evidence-only restrictions are preserved;
- mandatory environment record and readiness states are defined;
- entry/exit evidence and stop gates are explicit;
- no concrete infrastructure, port, provider, credential or runtime is invented;
- Environment Isolation, Security, Quality and Compatibility requirements remain consistent;
- open decisions remain open.

## 14. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First environment ownership/readiness matrix without provisioning, topology or runtime selection. |
