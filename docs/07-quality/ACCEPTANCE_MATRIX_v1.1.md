# Маяк Авито — Acceptance Matrix

**Версия:** 1.1
**Статус:** APPROVED documentation matrix
**Дата:** 2026-07-07
**Заменяет:** `ACCEPTANCE_MATRIX_v1.0.md` для future work; v1.0 сохраняется как historical accepted revision.
**Основание:** Test Strategy v1.0, Fixture Registry v1.0, Reference Regression Policy v1.0, Architecture Baseline v1.1, Technical Baseline v1.0, Technology Selection Method v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, OPEN_DECISIONS.md.
**Не является:** executed test report, CI matrix, product implementation checklist, production certification или разрешением создавать code/runtime.

---

## 1. Назначение

Matrix связывает approved requirements с fixtures, evidence и stop conditions. Строка определяет минимальный gate и не отменяет более строгий requirement затронутого документа.

## 2. Статусы и evidence

| Status | Meaning |
|---|---|
| `PASS` | requirement доказан exact evidence |
| `FAIL` | evidence противоречит requirement |
| `BLOCKED` | отсутствует required decision/reference/dependency |
| `NOT_RUN` | check не выполнялся |
| `NOT_APPLICABLE` | неприменимость доказана scope |
| `AMBIGUOUS` | evidence недостаточно; acceptance запрещена |

Только `PASS` и доказанный `NOT_APPLICABLE` допускают принятие строки.

| Code | Evidence |
|---|---|
| `DOC` | literal approved GitHub document |
| `DIFF` | exact changed paths/patch/compare |
| `FIXTURE` | named fixture ID/version |
| `RUN` | reproducible task/test report |
| `STATE` | authoritative read-only state |
| `AUDIT` | redacted protected audit evidence |
| `REFERENCE` | official/primary source record |
| `RECON` | reconciliation evidence |
| `ROLLBACK` | rollback/roll-forward evidence |
| `LOCK` | exact runtime/tool/dependency lock identity |

Sensitive values, raw access material, shell history, unredacted provider payload and foreign-host internals are invalid evidence.

## 3. Governance and architecture

| ID | Requirement | Minimum evidence | Stop condition |
|---|---|---|---|
| `AM-DOC-001` | Manifest/state/roadmap/backlog agree | `DOC`, `DIFF` | contradictory state/missing path |
| `AM-DOC-002` | Append-only prefix preserved | additions-only `DIFF` | historical deletion/modification |
| `AM-DOC-003` | No forbidden implementation artifacts in documentation run | `DIFF`, tree evidence | code, migrations, CI, DB, deploy or runtime artifact |
| `AM-ARCH-001` | Only owning module authorizes mutation | `DOC`, future `RUN` | foreign direct mutation |
| `AM-ARCH-002` | UI/adapters/admin do not become data owners | `DOC`, future `RUN` | module-boundary bypass |
| `AM-ARCH-003` | Framework/ORM/provider types do not become public contracts | `DOC`, future `RUN` | leaked implementation type |
| `AM-ARCH-004` | Shared-host availability is not project ownership or technology approval | `DOC`, `STATE` | foreign resource/tool treated as approved |

## 4. Technical Baseline

| ID | Requirement | Minimum evidence | Stop condition |
|---|---|---|---|
| `AM-TECH-001` | Core selection follows Technology Selection Method with official/primary evidence and alternatives | `DOC`, `REFERENCE` | memory/popularity/host-only choice |
| `AM-TECH-002` | Language/runtime/toolchain major lines are explicit | `DOC` | implicit or conflicting stack |
| `AM-TECH-003` | Dependency declaration and exact lock are repository-owned before product-code | future `LOCK`, `RUN` | unbounded/unidentified environment |
| `AM-TECH-004` | Core, dev/test and provider dependencies are isolated by owner/scope | `DOC`, future `LOCK`, `RUN` | adapter dependency leaks into all processes |
| `AM-TECH-005` | Reference behavior is reimplemented without unproven source reuse | `REFERENCE`, `DOC`, future `RUN` | copied source with unclear permission |
| `AM-TECH-006` | Selected stack passes isolated install/import/test/type/lint/architecture proof | future `RUN`, `LOCK` | proof missing/foreign resources used |
| `AM-TECH-007` | Deferred technology remains blocked until named playbook/evidence/ADR | `DOC` | agent chooses deferred component |
| `AM-TECH-008` | Durable work survives process restart through authoritative state | future `RUN`, `STATE` | in-memory state treated as durable |
| `AM-TECH-009` | External broker/cache is absent until separate measured decision | `DOC`, future `DIFF` | undeclared stateful service |
| `AM-TECH-010` | Technical documentation run creates no code, lockfile, packages, DB or runtime | `DIFF` | implementation artifact in Run 10 |

## 5. Contracts, errors and idempotency

| ID | Requirement | Fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|
| `AM-CONTRACT-001` | Contract type/version/metadata explicit | `FX-CONTRACT-VALID-001`, `FX-CONTRACT-MISSING-META-001` | `FIXTURE`, future `RUN` | implicit version/default |
| `AM-CONTRACT-002` | Authorization precedes ownership/mutation | `FX-AUTH-UNAUTHENTICATED-001`, `FX-AUTH-FORBIDDEN-001` | `FIXTURE`, future `RUN`, `AUDIT` | effect before authorization |
| `AM-CONTRACT-003` | Explicit result class; failure is not success | `FX-EXT-REJECTED-001`, `FX-EXT-UNAVAILABLE-001`, `FX-EXT-AMBIGUOUS-001` | `FIXTURE`, future `RUN` | fabricated success/empty |
| `AM-IDEMP-001` | Same key/same request has no duplicate effect | `FX-IDEMP-FIRST-001`, `FX-IDEMP-REPLAY-SAME-001` | `FIXTURE`, future `RUN`, `STATE` | second effect |
| `AM-IDEMP-002` | Same key/different fingerprint rejected | `FX-IDEMP-REPLAY-MISMATCH-001` | `FIXTURE`, future `RUN` | different mutation executed |
| `AM-INTERRUPT-001` | Pre-commit interruption emits no success/event | `FX-INTERRUPT-PRECOMMIT-001` | `FIXTURE`, future `RUN`, `STATE` | success before commit |
| `AM-INTERRUPT-002` | Unknown commit state reconciles first | `FX-INTERRUPT-UNKNOWN-001` | `FIXTURE`, future `RUN`, `RECON` | blind retry/success |
| `AM-BATCH-001` | Partial batch reports per-unit outcomes | `FX-BATCH-PARTIAL-001`, `FX-MIG-PARTIAL-001` | `FIXTURE`, future `RUN` | generic whole-batch success |

## 6. Data, privacy and security

| ID | Requirement | Fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|
| `AM-DATA-001` | `account_id` is internal ownership boundary | `FX-DATA-ACCOUNT-BOUNDARY-001`, `FX-OWNER-FOREIGN-ACCOUNT-001` | `FIXTURE`, future `RUN`, `STATE` | weak-signal merge |
| `AM-DATA-002` | Beacon belongs to one account | `FX-OWNER-FOREIGN-BEACON-001` | `FIXTURE`, future `RUN`, `STATE` | foreign/multiple owner mutation |
| `AM-DATA-003` | History isolated by `beacon_id` | `FX-DATA-BEACON-ISOLATION-001` | `FIXTURE`, future `RUN`, `STATE` | cross-Beacon contamination |
| `AM-DATA-004` | Source URL preserved; overrides are separate revisions | `FX-DATA-SOURCE-URL-IMMUTABLE-001` | `FIXTURE`, future `RUN`, `STATE` | source overwritten |
| `AM-DATA-005` | Historical observation/revision immutable | `FX-DATA-HISTORY-IMMUTABLE-001` | `FIXTURE`, future `RUN`, `STATE` | historical mutation |
| `AM-DATA-006` | Read model has provenance/freshness and is not authority | `FX-DATA-READMODEL-STALE-001` | `FIXTURE`, future `RUN`, `STATE` | projection used as truth |
| `AM-DATA-007` | Open decisions receive no fabricated defaults | `FX-DATA-UNKNOWN-NO-DEFAULT-001` | `DOC`, `FIXTURE`, future `RUN` | guessed value |
| `AM-SEC-001` | Sensitive values absent from logs/reports/fixtures | `FX-SEC-SECRET-REDACTION-001` | `FIXTURE`, future `RUN` | raw sensitive value exposure |
| `AM-SEC-002` | Personal data minimized | `FX-SEC-PERSONAL-MINIMIZATION-001` | `FIXTURE`, future `RUN` | unnecessary collection |
| `AM-SEC-003` | External strings never become shell commands | `FX-SEC-SHELL-INTERPOLATION-001` | `FIXTURE`, future `RUN` | shell interpolation |
| `AM-SEC-004` | Provider ingress verified before trust | `FX-SEC-PROVIDER-VERIFY-001` | `FIXTURE`, future `RUN`, `REFERENCE` | unverified action accepted |

## 7. External adapters and references

| ID | Requirement | Fixtures | Minimum evidence | Stop condition |
|---|---|---|---|---|
| `AM-EXT-001` | Explicit provider success requires verified usable response | `FX-EXT-SUCCESS-001` | `REFERENCE`, `FIXTURE`, future `RUN` | raw response trusted |
| `AM-EXT-002` | Provider rejection remains rejection | `FX-EXT-REJECTED-001` | `FIXTURE`, future `RUN` | rejection converted to empty/success |
| `AM-EXT-003` | Unavailable/malformed remains explicit | `FX-EXT-UNAVAILABLE-001`, `FX-EXT-MALFORMED-001` | `FIXTURE`, future `RUN` | clean empty result |
| `AM-EXT-004` | Ambiguous external effect reconciles | `FX-EXT-AMBIGUOUS-001` | `FIXTURE`, future `RUN`, `RECON` | blind retry |
| `AM-AVITO-001` | Restricted access is not no listings | `FX-AVITO-CAPTCHA-001` | `REFERENCE`, `FIXTURE`, future `RUN` | empty listing set |
| `AM-EGRESS-001` | Route failure is not parser success | `FX-ROUTE-FAILURE-001` | `FIXTURE`, future `RUN` | false parser success |
| `AM-REF-001` | Reference assertion has current evidence | `FX-REF-CURRENT-001` | `REFERENCE` | memory-only assertion |
| `AM-REF-002` | Stale/missing evidence blocks acceptance | `FX-REF-STALE-001`, `FX-REF-MISSING-001` | `REFERENCE`, `DOC` | silent stale use |
| `AM-REF-003` | Provider change classified for compatibility | `FX-REF-CHANGED-COMPATIBLE-001`, `FX-REF-CHANGED-BREAKING-001` | `REFERENCE`, `DIFF` | silent break |
| `AM-REF-004` | Unsupported behavior remains explicit | `FX-REF-UNSUPPORTED-001` | `REFERENCE`, `FIXTURE` | unsupported marked supported |

## 8. Migration and compatibility

| ID | Requirement | Minimum evidence | Stop condition |
|---|---|---|---|
| `AM-MIG-001` | Exact migration ID/plan fingerprint/target | future `RUN`, `STATE` | unidentified plan |
| `AM-MIG-002` | Empty/minimal scope explicit | `FIXTURE`, future `RUN` | fabricated broader processing |
| `AM-MIG-003` | Mixed versions follow declared compatibility | `FIXTURE`, future `RUN`, `STATE` | silent reinterpretation |
| `AM-MIG-004` | Replay has no duplicate | `FIXTURE`, future `RUN`, `STATE` | duplicate backfill |
| `AM-MIG-005` | Interrupted/partial migration reconciles per unit | `FIXTURE`, future `RUN`, `RECON` | whole-run success |
| `AM-MIG-006` | Rollback requires proven previous state | `ROLLBACK`, future `RUN` | destructive/unproven rollback |
| `AM-MIG-007` | Irreversible change has roll-forward gate | `ROLLBACK`, future `RUN` | pretend reversible |
| `AM-MIG-008` | Read-model rebuild preserves authority/provenance | `FIXTURE`, future `RUN`, `STATE` | projection becomes truth |
| `AM-MIG-009` | Physical migration blocked until all gates | `DOC` | early migration/code/database |

## 9. Module playbook adoption

Каждый Run 12–24 module playbook включает:

| Gate | Required content |
|---|---|
| Ownership | authoritative state and forbidden foreign mutation |
| Inputs/outputs | commands, queries, events, adapter outcomes |
| Authorization | actor/role/account/Beacon scope |
| Idempotency | keys, replay and commit point |
| Errors | categories, retry/reconciliation |
| Dependencies | real boundary and approved fake |
| Technology | core baseline use, module-specific selected/deferred dependencies |
| Fixtures | registry IDs and approved extensions |
| Privacy | classes, minimization, redaction |
| References | current evidence requirements |
| Acceptance | exact matrix row IDs/evidence |
| Open decisions | unresolved OD dependencies |
| Handoff | report marker and independent review |

Playbook cannot be accepted if a required row is uncovered or unjustifiably `NOT_APPLICABLE`.

## 10. Run-level rules

For every future run:

1. current public SHA named;
2. full scope and modes declared;
3. matrix rows selected;
4. fixtures/evidence named;
5. forbidden paths/actions explicit;
6. result independently verified;
7. server sync references exact published SHA;
8. `FAIL`, `BLOCKED` or `AMBIGUOUS` prevents acceptance;
9. correction targets first proven wrong object/value/action;
10. next run begins only after acceptance.

## 11. Open decisions

Matrix does not determine CI provider, coverage percentage, performance thresholds, provider field mappings, retention, product values blocked by OD-001–OD-014, production certification or deployment approval.

Technical tools selected in Technical Baseline do not create executable tests or runtime.

## 12. Acceptance criteria

Matrix is accepted when:

- foundation and Technical Baseline have traceable rows;
- evidence and stop conditions are explicit;
- append-only and forbidden-artifact gates preserved;
- module runs correctly numbered 12–24;
- no executable test, CI or runtime artifact created.

## 13. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial foundation/module traceability matrix. |
| 1.1 | 2026-07-07 | Added AM-TECH gates, LOCK evidence, current baseline references and module run renumbering to 12–24. |
