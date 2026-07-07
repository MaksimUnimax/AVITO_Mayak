# Маяк Авито — Backup and Recovery

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Environment Isolation Policy v1.0, Environment Matrix v1.0, Observability and Alerting v1.0, Architecture Baseline v1.0, Security and Privacy Model v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.0, OPEN_DECISIONS.md.
**Не является:** созданным backup, snapshot, dump, restore script, storage selection, disaster-recovery implementation, retention schedule, production certification или разрешением подключаться к database/runtime.

---

## 1. Назначение

Документ определяет обязательные semantic gates для будущего backup, restore and recovery проекта Маяк Авито.

Он нужен, чтобы:

- foreign host resources не считались project recovery assets;
- backup existence не путалась с recoverability;
- restore не перезаписывал более новое authoritative state без доказанного решения;
- secrets и personal data не попадали в ordinary reports;
- migration/release не объявлялись безопасными без конкретного recovery evidence;
- ambiguous or partial recovery не объявлялся success.

## 2. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance documents.
2. Approved data ownership, contracts, security/privacy and environment records.
3. Этот Backup and Recovery baseline.
4. Future approved environment-specific backup plan.
5. Exact execution task and authorized operator context.
6. Runtime backup/restore evidence конкретной операции.

Backup tool metadata, filesystem visibility, database snapshot label, provider console or CLI report не переопределяют approved ownership and recovery semantics.

## 3. Термины

| Термин | Значение |
|---|---|
| Backup asset | Project-owned recovery artifact с identity, scope, provenance and protection metadata |
| Backup set | Согласованный набор assets, необходимый для определённой recovery scope |
| Restore | Controlled materialization backup data в approved isolated target |
| Recovery | Доказанное возвращение system/data capability к accepted semantic state |
| Recovery point | Exact source state/revision/time boundary represented by backup evidence |
| Recovery target | Approved environment and scope, куда выполняется восстановление |
| Verification | Non-destructive checks backup identity, completeness and readability |
| Restore rehearsal | Controlled recovery test в approved isolated environment |
| Rollback | Возврат к доказанно совместимому previous state |
| Roll-forward | Controlled repair/migration вперёд, если safe rollback невозможен |
| Reconciliation | Проверка фактического authoritative state после ambiguous interruption |
| Foreign recovery asset | Snapshot/dump/volume/service, ownership которого проектом не доказан |

## 4. Core recovery invariants

1. Backup covers only explicitly project-owned data and configuration scope.
2. A visible snapshot, dump, volume or provider feature is not a project backup without approved ownership evidence.
3. Backup success is not recovery success.
4. Recovery success requires semantic validation against approved contracts/data invariants.
5. Restore target is isolated and identified before mutation.
6. Restore never authorizes cross-account or cross-Beacon mixing.
7. Source URL provenance, immutable history and append-only records remain protected.
8. Secrets are restored only through approved secret-management boundaries and never printed in reports.
9. Unknown restore effect becomes `RECONCILIATION_REQUIRED`.
10. Newer accepted authoritative state is not overwritten by an older backup without explicit decision and impact evidence.
11. Derived read models may be rebuilt only from known authoritative sources and do not define the recovery point.
12. Recovery operation cannot close OD-013 or invent retention/RPO/RTO values.

## 5. Backup scope classes

Future environment-specific plans classify each asset:

| Scope class | Examples of semantic content | Required owner |
|---|---|---|
| Authoritative business state | Accounts, Beacons, entitlements, listing/notification state after implementation approval | Owning module(s) |
| Contract/idempotency evidence | Request fingerprints, terminal outcomes, deduplication and reconciliation state | Contract/state owner |
| Audit and protected history | Approved audit records and append-only operational history | Security/governance owner |
| Derived state | Read models, indexes, caches, generated projections | Source owner; rebuild preferred when safe |
| Configuration references | Non-secret project configuration identity/version | Environment/release owner |
| Secret references | References/identifiers required to reconnect approved secrets | Security owner; raw values excluded from ordinary evidence |
| External-reference evidence | Approved provider evidence and provenance | Reference policy owner |
| Documentation/source | Public Git repository revision and accepted documents | GitHub `main` remains source of truth |

Physical storage objects are not selected by this document.

## 6. Mandatory backup plan record

Before any backup creation, an approved plan must include:

| Field | Requirement |
|---|---|
| `backup_plan_id` | Stable identifier |
| `plan_version` | Explicit semantic version |
| `environment_id` | Approved source environment |
| `asset_owner` | Accountable owner per asset class |
| `source_revision` | Exact release/schema/contract identity where applicable |
| `scope_inventory` | Included and explicitly excluded assets |
| `authoritative_sources` | Source-of-truth mapping per asset |
| `consistency_boundary` | What must represent one coherent recovery point |
| `backup_method_class` | Logical method without secret-bearing command text |
| `destination_owner` | Project-owned destination boundary |
| `encryption_boundary` | Protection requirements without key disclosure |
| `access_boundary` | Authorized roles/service identity |
| `retention_status` | Approved value or `BLOCKED_BY_OD_013` |
| `recovery_objectives_status` | Approved values or `NOT_DECIDED` |
| `verification_method` | Integrity/completeness/readability checks |
| `restore_target_class` | Approved isolated target class |
| `rehearsal_frequency_status` | Approved value or `NOT_DECIDED` |
| `dependency_order` | Required restore sequence |
| `rollback_rollforward` | Decision boundary after failed recovery |
| `observability` | Safe progress/outcome signals |
| `privacy_constraints` | Personal/secret data handling |
| `approval_reference` | Decision/task/document revision |

Missing mandatory field blocks backup execution.

## 7. Backup identity and provenance

Every future backup asset must have or inherit:

- backup plan ID and version;
- unique asset/set identity;
- source environment ID;
- source revision and semantic data/contract version;
- creation start/end or equivalent boundary under approved time policy;
- consistency state;
- scope inventory and counts where safe;
- content/integrity fingerprint or provider-equivalent evidence;
- destination ownership class;
- encryption/protection status without key material;
- verification status;
- expiration/retention status, including blocked/unknown;
- supersession relation;
- safe reason/outcome codes.

Filename, directory date or provider snapshot label alone is insufficient identity.

## 8. Backup lifecycle states

| State | Meaning |
|---|---|
| `PROPOSED` | Plan drafted; execution forbidden |
| `APPROVED` | Plan accepted; exact execution task still required |
| `CREATING` | Authorized backup operation in progress |
| `CREATED_UNVERIFIED` | Artifact exists, but recovery use prohibited |
| `VERIFYING` | Integrity/completeness/readability checks running |
| `VERIFIED` | Checks passed for declared scope; recoverability still requires rehearsal/evidence |
| `REHEARSAL_VALIDATED` | Approved isolated restore/recovery rehearsal passed |
| `DEGRADED` | Scope/readability/freshness limitation known |
| `AMBIGUOUS` | Effect or identity cannot be proven; reconciliation required |
| `SUPERSEDED` | New accepted backup replaces ordinary recovery preference |
| `EXPIRED` | Outside approved retention/use boundary |
| `QUARANTINED` | Security/integrity/ownership concern blocks use |
| `DELETED` | Deletion accepted with evidence when policy permits |

`VERIFIED` does not mean production recovery readiness unless required restore rehearsal and dependencies are accepted.

## 9. Consistency and dependency boundaries

A future plan must state:

- which authoritative states must share one recovery point;
- which assets can be restored independently;
- ordering between identity, entitlements, Beacons, scan/listing state, notification state and adapters;
- relationship between business state and idempotency/audit evidence;
- treatment of in-flight, pending and ambiguous operations;
- whether external effects require reconciliation rather than local restoration;
- which derived states are rebuilt instead of restored;
- what exact source revision/contracts can read the restored representation.

A backup that loses idempotency or delivery evidence may create duplicate external effects and therefore cannot be accepted silently.

## 10. Verification requirements

Backup verification includes, as applicable:

1. Exact plan/asset/source identity.
2. Declared scope present and exclusions confirmed.
3. Integrity/fingerprint check.
4. Readability through approved non-destructive mechanism.
5. Consistency boundary evidence.
6. Version/compatibility metadata.
7. Encryption/protection and access-boundary status.
8. No raw secret exposure.
9. Account/Beacon isolation sample or invariant checks.
10. Immutable/append-only history protection.
11. Explicit missing, failed or ambiguous inventory.
12. Destination ownership and isolation proof.
13. Evidence freshness.

Verification by file existence, size greater than zero or provider status `completed` alone is insufficient.

## 11. Restore and recovery lifecycle

| State | Meaning |
|---|---|
| `REQUESTED` | Recovery need recorded; mutation not authorized |
| `APPROVED` | Scope/target/evidence accepted; exact task required |
| `PREPARING` | Target isolation, backup identity and dependencies verified |
| `RESTORING` | Controlled materialization in progress |
| `RESTORE_PAUSED` | Safe checkpoint; completion not assumed |
| `RECONCILIATION_REQUIRED` | Restore effect or external/business state ambiguous |
| `VALIDATING` | Mutation stopped; semantic checks running |
| `RECOVERED_CANDIDATE` | Restore completed but final acceptance pending |
| `ACCEPTED` | Semantic and operational recovery criteria proven |
| `ROLLBACK_REQUIRED` | Approved reversal to pre-restore target state required |
| `ROLL_FORWARD_REQUIRED` | Safe reversal unavailable; approved repair path required |
| `FAILED` | Defined failure with preserved evidence |

Only `ACCEPTED` is recovery success.

## 12. Restore entry gates

Before restore mutation, exact task must prove:

- approved recovery reason and owner;
- exact backup set identity and state;
- source and target environment identities;
- target isolation and clean/known initial state;
- target revision/contracts/schema compatibility;
- whether target contains newer accepted state;
- preserved pre-restore evidence or rollback boundary;
- authorization and protected operator identity;
- scope and exclusions;
- dependency order;
- external-effect reconciliation plan;
- secret delivery without disclosure;
- fixtures and Acceptance Matrix rows;
- observability and safe reason codes;
- allowed/forbidden commands and paths;
- stop conditions;
- independent acceptance authority.

Missing ingress/port/TLS details are irrelevant to an isolated rehearsal unless the approved task explicitly requires them. They cannot be guessed for production recovery.

## 13. Recovery validation

Recovery validation checks semantic outcomes, not only technical restore completion:

- exact target revision and environment;
- authoritative owners and readable contract versions;
- account ownership and Beacon isolation;
- source URL provenance and configuration revision history;
- immutable listing/notification/audit history where applicable;
- no fabricated defaults for open decisions;
- idempotency/replay state and pending/ambiguous inventory;
- external effects reconciled separately;
- derived read-model provenance and freshness;
- privacy/redaction/access boundaries;
- no foreign-resource dependency;
- readiness state according to approved observability semantics;
- rollback/roll-forward decision;
- evidence package completeness.

Production traffic or provider calls are not required or authorized by this documentation baseline.

## 14. Restore rehearsal

A future restore rehearsal must run only in an approved isolated target and use permitted synthetic/redacted or specifically approved data.

Required scenarios include:

- minimum valid backup set;
- empty declared scope;
- missing asset;
- corrupt/unreadable asset;
- wrong environment or source revision;
- incompatible version;
- partial backup set;
- interrupted restore before commit;
- interruption after possible commit;
- duplicate/replayed restore task;
- newer target state conflict;
- cross-account/Beacon isolation checks;
- lost/mismatched idempotency evidence;
- secret/redaction checks;
- derived read-model rebuild;
- rollback and roll-forward branches;
- ambiguous external-effect reconciliation.

A rehearsal does not authorize production restore.

## 15. Recovery point and recovery time objectives

Concrete RPO, RTO, maximum data loss, maximum downtime and rehearsal frequency are not selected here.

Until separately approved:

- reports use `NOT_DECIDED`, not guessed numeric targets;
- no environment is declared production-ready based on undefined objectives;
- provider defaults do not become project commitments;
- an implementation proposal must show cost, privacy, consistency, ownership and operational implications;
- OD-013 remains open for retention-related decisions.

## 16. Security and privacy

Backup/recovery must:

- use project-owned access boundaries;
- apply least privilege;
- protect backup data at rest/in transit after technology selection;
- keep raw keys/tokens/passwords/cookies/one-time codes out of prompts, Git and ordinary reports;
- avoid unnecessary personal data copies;
- preserve auditability of access and recovery actions;
- quarantine suspected tampered/foreign assets;
- avoid shell interpolation of external values;
- define safe deletion/disposal after retention approval;
- prevent backup artifacts from becoming an uncontrolled export channel.

This document does not select encryption algorithms, KMS, secrets manager or storage provider.

## 17. Foreign and shared-host resources

Prohibited as project backup/recovery assets without separately proven ownership and approval:

- foreign database dumps or snapshots;
- foreign volumes, buckets or filesystems;
- foreign containers/services;
- existing Nginx/TLS configuration;
- visible credentials or environment files;
- host-level backup services;
- another project's logs/audit/history;
- provider account features not assigned to the project.

Read access or visibility does not establish permission.

## 18. Failure and ambiguity handling

- Wrong target, owner, revision or backup identity stops before mutation.
- Missing/failed verification blocks restore.
- Partial backup or restore is reported per asset/unit.
- Unknown effect becomes `RECONCILIATION_REQUIRED`.
- Newer target state conflict blocks overwrite.
- Secret exposure stops the operation and triggers protected review.
- Cross-account/Beacon contamination blocks acceptance.
- Validation failure does not authorize destructive reset.
- Corrective action targets the first proven wrong object/value/action.
- Failed recovery preserves safe evidence and explicit rollback/roll-forward state.

## 19. Evidence package

Future backup/recovery report must contain:

1. task/iteration ID;
2. plan/asset/set versions;
3. source and target environment IDs;
4. source and target revisions;
5. allowed scope and exclusions;
6. before/after state;
7. action class;
8. succeeded/failed/pending/ambiguous inventory;
9. verification and validation results;
10. ownership/isolation/privacy checks;
11. secret exposure statement;
12. rollback/roll-forward/reconciliation state;
13. no foreign-resource use statement;
14. repository/GitHub/Git/SSH/server mutation statement;
15. exact final marker;
16. independent acceptance result when required.

Raw backup content, credentials and personal data are excluded.

## 20. Relationship to migration and release

- Physical migration cannot claim production-ready recovery without a concrete approved backup plan and evidence.
- Release cannot proceed when required backup/recovery gate is `BLOCKED`, `AMBIGUOUS`, `DEGRADED` beyond approved risk or unverified.
- Backup creation immediately before release is insufficient unless verification and declared consistency requirements pass.
- Rollback to application revision is not data recovery automatically.
- Data rollback is prohibited when it would lose newer accepted effects or break contract compatibility.
- Irreversible change requires verified recovery boundary and roll-forward repair plan.

## 21. Change control

Changing backup scope, consistency boundary, retention, destination owner, protection, recovery objective, restore order or validation meaning requires:

- reason and authoritative evidence;
- old/new plan semantics;
- affected environments/modules/data classes;
- security/privacy analysis;
- compatibility/migration impact;
- fixture and Acceptance Matrix updates;
- rehearsal impact;
- rollback/roll-forward decision;
- open decisions touched but not closed;
- approved GitHub publication and independent review.

Silent weakening of backup/recovery guarantees is prohibited.

## 22. Open decisions

This baseline does not choose:

- backup/storage/provider technology;
- database or filesystem mechanism;
- full/incremental/logical/physical method;
- schedule/frequency;
- RPO/RTO values;
- retention duration or legal hold;
- encryption/KMS/secrets implementation;
- cross-region/offsite topology;
- immutable/WORM technology;
- compression/deduplication;
- operator/on-call ownership;
- automated restore tooling;
- production data volume/capacity;
- disaster classification and communication process.

## 23. Explicit prohibitions

This document does not authorize:

- creating backups, snapshots, dumps or exports;
- reading or copying database/application data;
- executing restore or recovery;
- accessing foreign resources;
- provisioning storage;
- creating database, migration or schema;
- changing runtime, server, Git or SSH configuration;
- creating services, containers, users, ports or credentials;
- installing packages;
- deploying product-code;
- selecting retention, RPO or RTO by assumption;
- declaring production recovery readiness.

## 24. Acceptance criteria

Backup and Recovery baseline is accepted when:

- backup scope, identity, provenance and lifecycle are explicit;
- verification is distinct from recoverability;
- restore/recovery states, entry gates and semantic validation are defined;
- account/Beacon isolation, idempotency, append-only history and external-effect reconciliation are protected;
- foreign/shared-host assets are prohibited;
- RPO/RTO/retention and technologies remain open;
- no backup, snapshot, restore, database, runtime or infrastructure artifact is created;
- open decisions remain open.

## 25. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First technology-neutral backup/recovery semantic baseline without backup creation, retention values or infrastructure selection. |
