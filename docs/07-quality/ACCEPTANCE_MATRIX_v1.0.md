# Маяк Авито — Acceptance Matrix

**Версия:** 1.0
**Статус:** APPROVED documentation matrix
**Дата:** 2026-07-07
**Основание:** Test Strategy v1.0, Fixture Registry v1.0, Architecture Baseline v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, OPEN_DECISIONS.md.
**Не является:** executed test report, CI matrix, implementation checklist, production certification или разрешением создавать code/tests/runtime.

---

## 1. Назначение

Matrix связывает approved requirements с canonical fixtures, обязательным evidence и stop conditions.

Она используется будущими module playbooks, exact implementation tasks, migration packages, reference updates and final acceptance. Строка matrix определяет минимальный gate, но не заменяет более строгий requirement затронутого документа.

## 2. Статусы проверки

| Статус | Значение |
|---|---|
| `PASS` | Requirement доказан exact evidence на named revision |
| `FAIL` | Получен результат, противоречащий requirement |
| `BLOCKED` | Нужное approved decision/reference/dependency отсутствует |
| `NOT_RUN` | Проверка не выполнялась |
| `NOT_APPLICABLE` | Неприменимость обоснована scope, а не удобством |
| `AMBIGUOUS` | Effect/evidence недостаточны; acceptance запрещена до reconciliation |

Только `PASS` и доказанный `NOT_APPLICABLE` допускают принятие конкретной строки.

## 3. Evidence classes

| Код | Evidence |
|---|---|
| `DOC` | Literal content approved GitHub document |
| `DIFF` | Exact changed paths and patch/compare evidence |
| `FIXTURE` | Named fixture ID/version and expected outcome |
| `RUN` | Reproducible test/task report with exact revision |
| `STATE` | Authoritative state/read-only query evidence |
| `AUDIT` | Redacted protected audit evidence |
| `REFERENCE` | Official/primary source record with date, URL, scope, status, limitations |
| `RECON` | Reconciliation evidence after ambiguous interruption |
| `ROLLBACK` | Proven rollback/roll-forward readiness evidence |

Secret values, raw credentials, shell history, unredacted provider payload or foreign-host internals are never valid evidence.

## 4. Foundation acceptance matrix

| ID | Requirement | Source | Required fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|---|
| `AM-DOC-001` | Canonical paths/statuses agree across manifest/state/roadmap/backlog | Governance | none | `DOC`, `DIFF` | Contradictory state or missing path |
| `AM-DOC-002` | Append-only historical prefix preserved | Governance | none | `DIFF` additions-only proof | Historical deletion/modification |
| `AM-DOC-003` | No forbidden implementation artifacts in documentation run | Architecture/Governance | none | `DIFF`, repository tree evidence | Code, migrations, CI, DB, deploy or runtime artifact |
| `AM-ARCH-001` | Only owning module authorizes mutation | Architecture/Data | `FX-CONTRACT-VALID-001`, `FX-OWNER-FOREIGN-ACCOUNT-001` | `DOC`, future `RUN` | Foreign direct mutation |
| `AM-ARCH-002` | UI/adapters/admin do not become data owners | Architecture/Module Registry | `FX-AUTH-FORBIDDEN-001`, `FX-DATA-READMODEL-STALE-001` | `DOC`, future `RUN` | Bypass of module boundary |
| `AM-CONTRACT-001` | Contract type/version/metadata are explicit | Contract Package | `FX-CONTRACT-VALID-001`, `FX-CONTRACT-MISSING-META-001` | `FIXTURE`, future `RUN` | Implicit version/default |
| `AM-CONTRACT-002` | Authorization precedes ownership check and mutation | Contract/Security | `FX-AUTH-UNAUTHENTICATED-001`, `FX-AUTH-FORBIDDEN-001` | `FIXTURE`, future `RUN`, `AUDIT` | Effect before authorization |
| `AM-CONTRACT-003` | Explicit result class; failure not converted to success | Contract/Error Policy | `FX-EXT-REJECTED-001`, `FX-EXT-UNAVAILABLE-001`, `FX-EXT-AMBIGUOUS-001` | `FIXTURE`, future `RUN` | Fabricated success/empty result |
| `AM-IDEMP-001` | Same key/same request does not duplicate effect | Error Policy | `FX-IDEMP-FIRST-001`, `FX-IDEMP-REPLAY-SAME-001` | `FIXTURE`, future `RUN`, `STATE` | Second effect |
| `AM-IDEMP-002` | Same key/different fingerprint is rejected | Error Policy | `FX-IDEMP-REPLAY-MISMATCH-001` | `FIXTURE`, future `RUN` | Different mutation executed |
| `AM-INTERRUPT-001` | Pre-commit interruption emits no success/event | Error/Data | `FX-INTERRUPT-PRECOMMIT-001` | `FIXTURE`, future `RUN`, `STATE` | Success before commit |
| `AM-INTERRUPT-002` | Unknown commit state reconciles before retry | Error/Migration | `FX-INTERRUPT-UNKNOWN-001` | `FIXTURE`, future `RUN`, `RECON` | Blind retry or success |
| `AM-BATCH-001` | Partial batch reports per-unit outcomes | Error/Migration | `FX-BATCH-PARTIAL-001`, `FX-MIG-PARTIAL-001` | `FIXTURE`, future `RUN` | Generic whole-batch success |

## 5. Data and privacy acceptance matrix

| ID | Requirement | Source | Required fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|---|
| `AM-DATA-001` | `account_id` is internal ownership boundary | Data/Security | `FX-DATA-ACCOUNT-BOUNDARY-001`, `FX-OWNER-FOREIGN-ACCOUNT-001` | `FIXTURE`, future `RUN`, `STATE` | Weak-signal account merge |
| `AM-DATA-002` | Beacon belongs to one account | Data | `FX-OWNER-FOREIGN-BEACON-001` | `FIXTURE`, future `RUN`, `STATE` | Multiple/foreign owner mutation |
| `AM-DATA-003` | Listing/notification history isolated by `beacon_id` | Architecture/Data | `FX-DATA-BEACON-ISOLATION-001` | `FIXTURE`, future `RUN`, `STATE` | Cross-Beacon contamination |
| `AM-DATA-004` | Source URL preserved; overrides create distinct revision semantics | Data | `FX-DATA-SOURCE-URL-IMMUTABLE-001` | `FIXTURE`, future `RUN`, `STATE` | Source URL overwritten |
| `AM-DATA-005` | Historical observation/revision not rewritten | Data | `FX-DATA-HISTORY-IMMUTABLE-001` | `FIXTURE`, future `RUN`, `DIFF`/`STATE` | Historical mutation |
| `AM-DATA-006` | Read model has provenance/freshness and is not source of truth | Data | `FX-DATA-READMODEL-STALE-001` | `FIXTURE`, future `RUN`, `STATE` | Projection used as authority |
| `AM-DATA-007` | Open decisions do not receive fabricated defaults | Data/Open Decisions | `FX-DATA-UNKNOWN-NO-DEFAULT-001` | `DOC`, `FIXTURE`, future `RUN` | Guessed tariff/filter/retention/lifecycle |
| `AM-SEC-001` | Secrets absent from logs/reports/fixtures | Security | `FX-SEC-SECRET-REDACTION-001` | `FIXTURE`, future `RUN`, redacted output inspection | Raw secret exposure |
| `AM-SEC-002` | Personal data minimized | Security/Data | `FX-SEC-PERSONAL-MINIMIZATION-001` | `FIXTURE`, future `RUN` | Unnecessary collection/display |
| `AM-SEC-003` | External strings never become shell commands | Security | `FX-SEC-SHELL-INTERPOLATION-001` | `FIXTURE`, future `RUN` | Shell interpolation/execution |
| `AM-SEC-004` | Provider ingress verified before trust | Security | `FX-SEC-PROVIDER-VERIFY-001` | `FIXTURE`, future `RUN`, `REFERENCE` | Unverified identity/action accepted |

## 6. External adapter and reference acceptance matrix

| ID | Requirement | Source | Required fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|---|
| `AM-EXT-001` | Explicit provider success requires verified usable response | Contract/Security | `FX-EXT-SUCCESS-001` | `REFERENCE`, `FIXTURE`, future `RUN` | Raw/unverified response trusted |
| `AM-EXT-002` | Provider rejection remains rejection | Error Policy | `FX-EXT-REJECTED-001` | `FIXTURE`, future `RUN` | Rejection converted to empty/success |
| `AM-EXT-003` | Unavailable/malformed result remains explicit | Error/Data | `FX-EXT-UNAVAILABLE-001`, `FX-EXT-MALFORMED-001` | `FIXTURE`, future `RUN` | Clean empty result |
| `AM-EXT-004` | Ambiguous external effect reconciles | Error Policy | `FX-EXT-AMBIGUOUS-001` | `FIXTURE`, future `RUN`, `RECON` | Blind retry |
| `AM-AVITO-001` | CAPTCHA/blocked access not interpreted as no listings | Data/Security | `FX-AVITO-CAPTCHA-001` | `REFERENCE`, `FIXTURE`, future `RUN` | Empty listing set |
| `AM-EGRESS-001` | Route failure not interpreted as parser success | Architecture/Data | `FX-ROUTE-FAILURE-001` | `FIXTURE`, future `RUN` | False parser success |
| `AM-REF-001` | Reference-dependent assertion has current official/primary evidence | Contract/Migration | `FX-REF-CURRENT-001` | `REFERENCE` | Memory-only assertion |
| `AM-REF-002` | Stale/missing evidence blocks acceptance | Reference Policy | `FX-REF-STALE-001`, `FX-REF-MISSING-001` | `REFERENCE`, `DOC` | Silent use of stale/absent source |
| `AM-REF-003` | Provider change classified for compatibility | Contract Change Policy | `FX-REF-CHANGED-COMPATIBLE-001`, `FX-REF-CHANGED-BREAKING-001` | `REFERENCE`, `DIFF`, affected fixture review | Silent same-version break |
| `AM-REF-004` | Unsupported/uncertain behavior remains explicit | Data/Reference Policy | `FX-REF-UNSUPPORTED-001` | `REFERENCE`, `FIXTURE` | Unsupported marked supported |

## 7. Migration and compatibility acceptance matrix

| ID | Requirement | Source | Required fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|---|
| `AM-MIG-001` | Exact migration ID, plan fingerprint and target revision | Migration Policy | `FX-MIG-MINIMAL-001`, `FX-MIG-PLAN-MISMATCH-001` | future `RUN`, `STATE` | Unidentified plan/target |
| `AM-MIG-002` | Empty/minimal scope handled explicitly | Migration Policy | `FX-MIG-EMPTY-001`, `FX-MIG-MINIMAL-001` | `FIXTURE`, future `RUN` | Fabricated processing/broader scope |
| `AM-MIG-003` | Mixed versions follow declared compatibility behavior | Migration/Contract Change | `FX-MIG-MIXED-VERSIONS-001` | `FIXTURE`, future `RUN`, `STATE` | Silent reinterpretation |
| `AM-MIG-004` | Replayed unit produces no duplicate | Migration/Error | `FX-MIG-DUPLICATE-REPLAY-001` | `FIXTURE`, future `RUN`, `STATE` | Duplicate backfill/repair |
| `AM-MIG-005` | Interrupted/partial migration reconciles per unit | Migration | `FX-MIG-PARTIAL-001` | `FIXTURE`, future `RUN`, `RECON` | Whole-run success |
| `AM-MIG-006` | Rollback requires reversible valid previous state | Migration | `FX-MIG-ROLLBACK-001` | `ROLLBACK`, future `RUN` | Destructive/unproven rollback |
| `AM-MIG-007` | Irreversible change has roll-forward gate | Migration | `FX-MIG-ROLLFORWARD-001` | `ROLLBACK`, future `RUN`, approval evidence | Pretend reversible |
| `AM-MIG-008` | Read-model rebuild preserves authoritative source/provenance | Migration/Data | `FX-MIG-READMODEL-REBUILD-001` | `FIXTURE`, future `RUN`, `STATE` | Projection becomes truth |
| `AM-MIG-009` | Physical migration blocked until quality/operations/recovery gates approved | Architecture/Migration | applicable rows above | `DOC` | Migration/code/database created early |

## 8. Module playbook adoption matrix

Каждый Run 11–23 playbook обязан создать module-specific section со следующими строками:

| Gate | Required content |
|---|---|
| Ownership | Owned authoritative state and forbidden foreign mutations |
| Inputs/outputs | Public commands, queries, events, adapter outcomes |
| Authorization | Actor, role, account/Beacon scope |
| Idempotency | Required keys, replay and commit point |
| Errors | Explicit categories, retry/reconciliation behavior |
| Dependencies | Real boundary and approved fake dependency |
| Fixtures | Selected registry IDs plus approved module extensions |
| Privacy | Data classes, minimization and redaction |
| References | Current evidence requirements for external behavior |
| Acceptance | Exact matrix row IDs and evidence package |
| Open decisions | OD dependencies left unresolved |
| Handoff | Report format, final marker and independent review |

Playbook нельзя принять, если required matrix row не покрыта или необоснованно отмечена `NOT_APPLICABLE`.

## 9. Run-level acceptance rules

Для каждого future implementation/documentation run:

1. Current public GitHub SHA назван до изменения.
2. Full scope and modes declared before write.
3. Required matrix rows selected.
4. Expected fixtures and evidence named.
5. Forbidden paths/actions explicit.
6. Published result independently verified.
7. Server sync относится к exact published SHA.
8. Any `FAIL`, `BLOCKED` or `AMBIGUOUS` prevents acceptance.
9. Corrective action addresses first proven wrong object/value/action.
10. Next run begins only after current acceptance.

## 10. Open decisions and non-decisions

Matrix не определяет:

- concrete test tooling or CI;
- performance/SLA thresholds;
- provider field mappings;
- retention duration;
- exact business values blocked by OD-001–OD-014;
- production readiness certification;
- deployment/release approval.

Rows affected by unresolved decisions remain `BLOCKED`, not guessed.

## 11. Acceptance criteria for this matrix

Matrix принята, когда:

- each approved foundation area has traceable rows;
- fixture IDs exist in Fixture Registry;
- evidence and stop conditions are explicit;
- provider/reference gates distinguish current, stale, missing and changed evidence;
- migration gates do not authorize migrations;
- module playbook adoption requirements are present;
- no executable test, CI or runtime artifact created.

## 12. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первая traceability matrix для governance, contracts, data, privacy, adapters, references, migrations and future module playbooks. |
