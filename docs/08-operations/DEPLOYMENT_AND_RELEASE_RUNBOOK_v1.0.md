# Маяк Авито — Deployment and Release Runbook

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Environment Isolation Policy v1.0, Environment Matrix v1.0, Observability and Alerting v1.0, Backup and Recovery v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.0, OPEN_DECISIONS.md.
**Не является:** deployment pipeline, CI/CD configuration, infrastructure design, command list, service definition, port allocation, ingress/reverse-proxy/TLS decision, runtime selection, production readiness certificate или разрешением выполнять deploy.

---

## 1. Назначение

Runbook задаёт framework-neutral release and deployment gates для будущего продукта.

Он определяет, какие доказательства обязательны до, во время и после controlled release, как различаются release publication, deployment mutation, activation, validation, rollback and recovery, и когда операция обязана остановиться.

Документ не выбирает технологию и не создаёт deployment capability.

## 2. Главный принцип

Release/deployment допустимы только после отдельного явного решения владельца и exact task packet.

Наличие Git commit, package artifact, host access, running process, free port, container runtime, reverse proxy или TLS certificate не является разрешением использовать их для проекта.

Public GitHub `main` остаётся документационным source of truth. Runtime environment требует отдельного approved environment record and release identity.

## 3. Термины

| Термин | Значение |
|---|---|
| Release candidate | Exact immutable source/artifact set proposed for acceptance |
| Release | Accepted version identity and evidence package; не обязательно deployed |
| Deployment | Controlled mutation approved target environment |
| Activation | Moment when approved workload/configuration begins serving its intended scope |
| Validation | Semantic and operational checks after mutation/activation |
| Rollback | Controlled return to proven compatible previous release/state |
| Roll-forward | Approved corrective forward release when rollback unsafe/impossible |
| Promotion | Approval of exact accepted release identity for another environment |
| Configuration set | Versioned non-secret configuration identity; secrets excluded |
| Deployment unit | Future approved runtime unit; not selected here |
| Maintenance boundary | Approved user/system impact window, if required |
| Reconciliation | Determination of actual state after interruption/ambiguous mutation |

## 4. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance state.
2. Approved architecture, contracts, data, quality, environment, backup/recovery and reference documents.
3. Approved module playbooks and exact implementation/release package.
4. Immutable release candidate identity and evidence.
5. Approved environment-specific deployment plan.
6. Runtime evidence from the exact deployment task.

Local branch, unreviewed artifact, package tag, container image label, host filesystem or CLI output cannot silently redefine the accepted release.

## 5. Release and deployment are distinct

A release may be accepted as an immutable candidate without being deployed.

Deployment acceptance requires additional evidence:

- exact target environment;
- approved deployment mechanism;
- environment ownership/isolation;
- configuration/secret readiness;
- network/ingress decisions where applicable;
- backup/recovery gate;
- compatibility/migration gate;
- observability and alerting gate;
- rollback/roll-forward plan;
- post-deployment semantic validation.

A successful build or source publication is not deployment success.

## 6. Mandatory release record

Before deployment planning, the release package must include:

| Field | Requirement |
|---|---|
| `release_id` | Stable immutable release identity |
| `source_sha` | Exact accepted Git SHA |
| `release_version` | Explicit version under approved policy |
| `artifact_identity` | Exact immutable artifact set if artifacts exist |
| `artifact_provenance` | How artifacts map to source and approved build process |
| `contract_versions` | Produced/consumed contract versions |
| `data_compatibility` | Required data/schema/migration state |
| `module_scope` | Included modules and excluded scope |
| `security_privacy_review` | Applicable acceptance evidence |
| `quality_evidence` | Fixtures, matrix rows and test/run evidence |
| `reference_evidence` | Current provider evidence where behavior depends on it |
| `configuration_identity` | Versioned non-secret configuration set |
| `secret_requirements` | Names/classes only, no values |
| `environment_eligibility` | Approved target environment state |
| `backup_recovery_gate` | Exact approved plan/evidence or `BLOCKED` |
| `rollback_rollforward` | Exact semantic boundary |
| `observability_gate` | Health/readiness/business validation semantics |
| `known_risks` | Explicit limitations and blocked decisions |
| `approval_reference` | Owner/ChatGPT acceptance reference |

Missing mandatory field keeps release `BLOCKED`.

## 7. Release lifecycle

| State | Meaning |
|---|---|
| `PROPOSED` | Candidate scope drafted; release/deploy forbidden |
| `BUILD_ELIGIBLE` | Documentation gates complete; build task still separately required |
| `CANDIDATE` | Immutable candidate identity exists; acceptance pending |
| `VALIDATING` | Quality/security/compatibility evidence under review |
| `ACCEPTED` | Release candidate accepted; deployment still separately gated |
| `PROMOTION_BLOCKED` | Target environment or dependency gate incomplete |
| `DEPLOYMENT_ELIGIBLE` | Exact target plan complete; deployment task still required |
| `SUPERSEDED` | Replaced by newer accepted release |
| `WITHDRAWN` | Candidate/release removed from promotion due to proven defect/risk |
| `RETIRED` | No new deployment; compatibility/recovery obligations remain |

`DEPLOYMENT_ELIGIBLE` is not authorization to deploy.

## 8. Deployment lifecycle

| State | Meaning |
|---|---|
| `REQUESTED` | Deployment desired; no mutation authorized |
| `APPROVED` | Exact plan accepted; executor task still required |
| `PREPARING` | Target and gates checked read-only |
| `MUTATING` | Controlled allowed environment changes in progress |
| `PAUSED` | Safe checkpoint; completion not assumed |
| `RECONCILIATION_REQUIRED` | Actual target state unknown or partially changed |
| `ACTIVATING` | Approved release being made active for defined scope |
| `VALIDATING` | No further rollout; health and semantic checks running |
| `DEPLOYED_CANDIDATE` | Mutation completed; final acceptance pending |
| `ACCEPTED` | Exact target release and criteria proven |
| `ROLLBACK_REQUIRED` | Approved rollback must be executed |
| `ROLL_FORWARD_REQUIRED` | Rollback unsafe/unavailable; approved correction required |
| `FAILED` | Defined failure with preserved evidence |

Only `ACCEPTED` is deployment success.

## 9. Environment gate

Deployment target must have an approved Environment Matrix record at least `RUNTIME_ELIGIBLE`, plus a separately approved exact use/provisioning decision.

The target plan must identify:

- environment ID and class;
- accountable owner;
- filesystem/runtime/data/network/secret boundaries;
- target source/release identity;
- project-owned dependencies;
- observability boundary;
- backup/recovery boundary;
- release/rollback boundary;
- evidence freshness.

Shared development host remains `EVIDENCE_ONLY`; repository sync on `/opt/avito-mayak` does not make it a runtime/deployment target.

## 10. Blocking infrastructure gates

The following remain undefined and must not be invented:

- runtime/process/container model;
- deployment units;
- target host/provider/region;
- DNS names;
- bind addresses;
- port allocation;
- ingress ownership;
- reverse proxy ownership/configuration;
- TLS/certificate ownership and rotation;
- firewall/network policy;
- database/queue/cache/storage provisioning;
- secret delivery/rotation mechanism;
- service identities and permissions;
- monitoring implementation;
- CI/CD/build/release tooling.

If a deployment requires any item above and no approved decision exists, status is `PROMOTION_BLOCKED` or `STOP_MISSING_DEPLOYMENT_GATE` before mutation.

No default port, localhost binding, existing Nginx site, shared certificate, visible database or available container runtime may be assumed.

## 11. Pre-release gates

Before a release candidate can become `ACCEPTED`:

1. Exact source SHA and full changed scope identified.
2. Module playbooks for affected code approved.
3. Contracts and data ownership identified.
4. Open decisions do not require guessed behavior.
5. Applicable fixtures and Acceptance Matrix rows selected.
6. Security/privacy review completed.
7. External/provider behavior has current official/primary evidence where applicable.
8. Compatibility classification and consumer matrix completed.
9. Migration/backfill/repair requirements explicit; none executed by release documentation.
10. Configuration identity known without secrets.
11. Artifact provenance and integrity evidence available when artifacts exist.
12. Known failures, ambiguity and unsupported states documented.
13. Rollback/roll-forward and recovery dependencies defined.
14. Independent GitHub/content acceptance completed.

## 12. Pre-deployment gates

Before any target mutation:

1. Release state is `ACCEPTED`.
2. Deployment target and environment record are exact.
3. Target initial state is clean/known and compatible.
4. Workload ownership and authorization are proven.
5. Source/artifact/release fingerprints match.
6. Configuration set matches the release and target.
7. Required secrets are available through approved boundary without disclosure.
8. Project-owned dependency readiness is proven.
9. Backup/recovery plan and required evidence pass.
10. Migration state/plan passes required gates.
11. Ingress/port/TLS/network decisions are approved if required.
12. Observability and validation checks are executable and safe.
13. Maintenance/user-impact decision is approved if required.
14. Rollback or roll-forward trigger and authority are explicit.
15. Exact allowed/forbidden commands, files and resources are listed in the execution task.
16. No foreign resources are included.

Any failed, blocked or ambiguous gate stops before mutation.

## 13. Deployment strategy boundary

This runbook does not select rolling, blue/green, canary, recreate, in-place, immutable image, package copy or any other strategy.

A future strategy proposal must prove:

- compatibility with selected runtime/environment;
- ownership and isolation;
- how mixed versions behave;
- data/contract compatibility;
- activation and commit point;
- traffic/user scope;
- observability and stop conditions;
- rollback/roll-forward feasibility;
- secret/configuration handling;
- capacity and failure behavior;
- no duplicate external effects.

Strategy name alone is not sufficient evidence.

## 14. Controlled deployment sequence

Future exact deployment plan follows this semantic order unless a separately approved plan proves another safe sequence:

```text
identify exact release and target
→ verify all gates read-only
→ establish protected pre-change evidence/recovery boundary
→ perform only approved bounded mutation
→ determine actual mutation state
→ activate only after prerequisites pass
→ stop further rollout
→ validate liveness/readiness/dependencies/business invariants separately
→ reconcile ambiguous/partial outcomes
→ accept, rollback or roll-forward
→ preserve evidence and update release state
```

This sequence is semantic, not a command list.

## 15. Activation and commit point

Every future deployment plan must define:

- what constitutes environment mutation;
- what constitutes release activation;
- what event/state proves activation;
- whether traffic/work may reach mixed versions;
- when old release remains usable;
- when rollback becomes unsafe;
- how configuration/secret changes align with code/data versions;
- how duplicate scheduler/worker/external effects are prevented;
- how interruption after possible activation is reconciled.

A process start, open port, healthy container or successful command does not by itself prove accepted activation.

## 16. Health and validation

Post-deployment validation distinguishes:

- process liveness;
- application readiness;
- project-owned dependency health;
- contract compatibility;
- data compatibility/invariants;
- authorization/ownership behavior;
- idempotency/replay behavior;
- external dependency state;
- business outcome;
- observability/evidence completeness.

Required checks depend on release scope but must include:

- exact environment/release identity;
- no unexpected foreign resource use;
- correct source/configuration identity;
- safe readiness behavior when dependency/reference/config is missing;
- account and Beacon isolation;
- no false-success conversion;
- no secret/personal-data exposure;
- explicit failed/partial/ambiguous inventory;
- rollback/roll-forward readiness;
- backup/recovery consistency after mutation.

“All green”, reachable HTTP, running process or absent alerts is insufficient acceptance evidence.

## 17. Data and migration coordination

Release does not authorize migration automatically.

When data change exists:

- approved Migration and Compatibility package identifies expand/migrate/contract sequence;
- exact migration task is separate and may precede/follow deployment only as approved;
- old/new reader/writer compatibility is explicit;
- backup/recovery evidence is concrete;
- plan fingerprint, idempotency and reconciliation are defined;
- mixed-version window is bounded;
- rollback cannot destroy newer accepted data;
- contract legacy removal waits for evidence, not script completion.

If safe rollback is impossible, release is irreversible and requires approved roll-forward plan and stricter gates.

## 18. Configuration and secrets

Release configuration must have versioned non-secret identity and target scope.

Rules:

- secret values never enter Git, ordinary prompts, reports or artifacts;
- secret names/classes may be listed when necessary;
- configuration absence/mismatch fails readiness;
- environment-specific values do not become hidden release semantics;
- changing authorization, provider behavior, retention or business rule through unreviewed configuration is prohibited;
- secret rotation and rollback interactions must be explicit after mechanism selection;
- old release compatibility with new secret/configuration state must be assessed.

No configuration format or secrets product is selected here.

## 19. External providers and egress

Deployment involving Avito, Telegram, MAX or egress requires:

- current official/primary reference evidence;
- approved adapter/egress playbooks;
- provider verification/authentication boundary;
- safe test/fake dependency evidence;
- explicit unsupported/rejected/unavailable/ambiguous states;
- no production/provider call as an implicit deployment test;
- delivery/idempotency/reconciliation behavior;
- no foreign route, agent or credential reuse.

Run 8–10 remain prerequisites for affected deployment planning.

## 20. Rollback requirements

Rollback is permitted only when:

- exact previous release/configuration identity is known;
- previous representation remains compatible and valid;
- authoritative state will not lose newer accepted effects;
- external effects will not be duplicated or contradicted;
- reverse configuration/data mapping is deterministic;
- secret/authorization state remains valid;
- backup/recovery or pre-change evidence supports the operation;
- rollback task has explicit scope and validation;
- append-only/audit history is preserved.

Rollback is a controlled deployment, not a destructive reset.

## 21. Roll-forward requirements

Roll-forward is required when:

- data/configuration change is irreversible;
- previous release cannot safely read current state;
- rollback would lose accepted effects;
- provider compatibility prevents return;
- secret rotation cannot be safely reversed;
- rollback path is unverified or ambiguous.

Roll-forward needs a separately approved corrective release with first proven wrong object/value/action, bounded impact, fixtures, recovery boundary and independent acceptance.

## 22. Failure and interruption handling

- Wrong target/release/configuration stops before mutation.
- Dirty or unidentified target state blocks deployment.
- Missing ingress/port/TLS/network approval blocks any plan that requires it.
- Failed backup/recovery or migration gate blocks deployment.
- Interruption before mutation produces no success.
- Interruption after possible mutation/activation becomes `RECONCILIATION_REQUIRED`.
- Partial deployment is reported per unit/scope.
- Validation failure stops rollout and requires explicit rollback/roll-forward decision.
- External/provider failure is not clean success.
- Secret exposure triggers protected stop/review.
- Corrective action targets the first proven wrong object/value/action.
- Failure does not authorize force operations, destructive reset or use of foreign resources.

## 23. Release promotion

Promotion to another environment is a new controlled decision.

It requires:

- same immutable release identity;
- environment-specific gates and configuration identity;
- fresh evidence where time/provider/environment-sensitive;
- target-specific backup/recovery and rollback boundary;
- compatibility with target dependencies;
- separate approval and report.

A release accepted in test is not automatically accepted for production.

## 24. Evidence package

A future release/deployment report must include:

1. task/iteration ID;
2. release ID/version/source SHA/artifact identity;
3. environment ID/class;
4. before/after target state;
5. configuration identity without secrets;
6. gate results;
7. action classes actually performed;
8. mutation/activation state;
9. validation results by liveness/readiness/dependency/business semantics;
10. succeeded/failed/pending/ambiguous inventory;
11. backup/recovery and migration state;
12. rollback/roll-forward/reconciliation decision;
13. ownership/isolation/privacy checks;
14. foreign-resource and secret exposure statements;
15. GitHub/repository/Git/SSH/server configuration change statements;
16. exact final marker;
17. independent acceptance result when required.

Raw secrets, unredacted provider payloads and foreign-host internals are excluded.

## 25. Required future fixtures and scenarios

Before implementation of release/deployment automation or tasks, cover at least:

- correct release/target;
- wrong source SHA or artifact fingerprint;
- wrong environment;
- dirty/unknown target;
- missing configuration;
- missing secret reference without disclosure;
- unavailable/rejecting dependency;
- missing ingress/port/TLS gate;
- current/stale/missing provider evidence;
- compatible and incompatible data versions;
- interruption before mutation;
- interruption after possible mutation;
- interruption after activation;
- partial multi-unit deployment;
- exact replay;
- plan/release fingerprint mismatch;
- readiness failure after liveness success;
- false-success prevention;
- rollback valid/invalid branches;
- roll-forward-required branch;
- secret/redaction and foreign-resource checks.

No executable fixtures/tests are created by this document.

## 26. Change control

Changing release identity semantics, promotion rules, activation point, deployment strategy, health criteria, rollback triggers, configuration boundary or evidence format requires:

- reason and authoritative evidence;
- old/new semantics;
- affected environments/modules/contracts/data;
- security/privacy analysis;
- migration/compatibility impact;
- backup/recovery impact;
- fixtures and Acceptance Matrix updates;
- operational rollout/rollback decision;
- open decisions touched but not closed;
- approved publication and independent review.

Silent change under the same release/plan version is prohibited.

## 27. Open decisions

This runbook does not choose:

- build/package/artifact technology;
- CI/CD or deployment tooling;
- runtime/process/container model;
- deployment strategy;
- hosts/providers/regions;
- ports, DNS, ingress, reverse proxy or TLS;
- database/queue/cache/storage;
- secret manager and service identities;
- maintenance windows;
- release cadence/versioning scheme;
- SLI/SLO/SLA or alert thresholds;
- production approval authority/on-call process;
- capacity/scaling policy;
- RPO/RTO and retention;
- provider-specific rollout behavior.

## 28. Explicit prohibitions

This document does not authorize:

- building or publishing artifacts;
- creating CI/CD or deployment scripts;
- deploying or activating product-code;
- changing server/runtime/Git/SSH configuration;
- creating users, services, containers, networks, volumes or ports;
- modifying DNS, firewall, ingress, Nginx, reverse proxy or TLS;
- creating database, queue, cache, schema or migration;
- creating backup/snapshot/restore;
- installing packages;
- reading credentials, `.env`, private keys, shell history or process arguments;
- accessing foreign resources;
- sending provider/production traffic;
- declaring production readiness.

## 29. Acceptance criteria

Deployment and Release Runbook is accepted when:

- release and deployment identities/lifecycles are distinct and explicit;
- pre-release and pre-deployment gates cover environment, quality, security, data, recovery and observability;
- undefined ingress, reverse proxy, ports, TLS, runtime and tooling remain blocking gates;
- activation, validation, interruption, rollback and roll-forward semantics are defined;
- shared-host evidence-only restriction is preserved;
- no deployment pipeline, command, service, port, credential, runtime or infrastructure is created;
- open decisions remain open.

## 30. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First technology-neutral release/deployment gate runbook without infrastructure, commands, ingress/port/TLS assumptions or deploy execution. |
