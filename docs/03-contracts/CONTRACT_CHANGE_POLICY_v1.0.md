# Маяк Авито — Contract Change Policy

**Версия:** 1.0
**Статус:** APPROVED documentation policy
**Дата:** 2026-07-07
**Основание:** Common Contract Package v1.0, Error and Idempotency Policy v1.0, Documentation Governance, Architecture Baseline v1.0.
**Не является:** schema-registry implementation, release process, CI rule, migration execution plan or permission to change code.

---

## 1. Назначение

Политика задаёт обязательный путь изменения contract semantics.

Её цель — не допустить silent breakage между модулями, adapters, clients, workers, future external providers and operations boundaries.

## 2. Contract lifecycle

| Status | Meaning |
|---|---|
| `DRAFT` | Contract text exists for design review; implementation is not authorized |
| `CANDIDATE` | Text has passed scoped review but remains unaccepted |
| `APPROVED` | Contract semantics may be used as an implementation prerequisite |
| `SUPERSEDED` | New approved contract replaces this one for future use |
| `ARCHIVED` | Historical reference only; no new producer use |

A status change must be explicit in documentation. A code change cannot silently upgrade contract status.

## 3. Change classes

### 3.1. Clarification

A clarification is allowed only when it changes no observable meaning, ownership, authorization, idempotency, error semantics or compatibility obligation.

Clarification must preserve all existing consumer interpretations.

### 3.2. Compatible extension

A compatible extension may add an optional semantic capability only when:

- existing producer behavior remains valid;
- existing consumer behavior remains valid;
- missing new data has documented safe meaning;
- authorization and ownership do not broaden silently;
- error and idempotency behavior remain compatible;
- fixtures and acceptance evidence are planned before implementation.

### 3.3. Breaking change

The following are breaking:

- removing or renaming an existing required semantic element;
- changing the meaning of a stable field or code;
- changing owner of mutable state;
- expanding access without explicit security decision;
- weakening account or Beacon isolation;
- changing idempotency scope or duplicate behavior;
- reclassifying a previously ambiguous result as success;
- changing retry semantics;
- changing error category meaning;
- changing external verification obligation;
- making previously optional data required;
- changing client-visible privacy boundary;
- changing payload interpretation without a version boundary.

Breaking changes require a new explicit version boundary and consumer migration plan before implementation.

## 4. Mandatory change packet

Every proposed contract change must contain:

1. contract name and current status;
2. proposed change class;
3. source and target version;
4. reason and evidence;
5. affected modules and adapters;
6. data owner and authorization impact;
7. idempotency impact;
8. error and retry impact;
9. privacy and logging impact;
10. compatibility analysis;
11. fake dependency and test-vector plan;
12. rollback or supersession behavior;
13. open decisions touched or intentionally not touched;
14. required documentation updates;
15. explicit approval authority.

A task packet lacking any required item is invalid. ChatGPT must not issue it to CLI until the packet is completed and independently approved.

CLI receives only a final literal task and must not decide whether a proposed change is sufficient, compatible, breaking, secure or complete.

## 5. Version boundary rules

- A stable contract must declare its version explicitly.
- A producer must not silently reinterpret an approved contract version.
- A consumer must not assume unknown fields, unknown error codes or new provider fields are harmless.
- A breaking change requires a new supported version or a separately approved replacement contract.
- Compatibility duration, dual-write, dual-read and deprecation timing are open decisions until a future approved release/operations policy defines them.
- Documentation version of this file is not a wire-contract version.

## 6. External provider changes

For Avito, Telegram, MAX or another external provider:

- current official or fixed reference evidence is required before changing contract semantics;
- provider documentation change does not automatically authorize product behavior;
- the adapter boundary must identify unsupported, ambiguous and deprecated provider behavior;
- external payload changes must preserve verification, privacy and idempotency requirements;
- no provider-specific code or configuration is created by this policy.

## 7. Approval path

A contract change may proceed only after:

1. ChatGPT independently reads current public `main`;
2. affected approved documents are identified;
3. required evidence is checked;
4. full literal document text is prepared;
5. CLI receives only allowed paths and exact text;
6. GitHub public result is independently verified after the report;
7. append-only records are used when required by governance.

CLI never decides whether a contract change is compatible, breaking, secure or complete.

## 8. Required downstream updates

When applicable, a contract change must update or explicitly assess:

- architecture baseline;
- security and privacy model;
- module playbook;
- data and compatibility policy;
- test strategy and fixtures;
- reference evidence;
- operations and observability documents;
- acceptance matrix;
- future implementation task packet.

No dependent document may be silently left contradictory.

## 9. Prohibited shortcuts

- editing an approved contract without change classification;
- changing a field meaning while keeping the same version;
- deleting a required semantic requirement to make implementation easier;
- widening authorization by client-only behavior;
- treating provider ambiguity as compatibility;
- using a code change as the first record of a contract change;
- selecting transport, serialization, queue or database technology through a contract edit;
- closing OPEN_DECISIONS by implication.

## 10. Explicit non-decisions

This policy does not choose:

- release cadence;
- deprecation window;
- schema-registry tool;
- API gateway;
- code generation tool;
- CI compatibility checker;
- migration mechanism;
- runtime deployment process;
- provider implementation library;
- production rollback procedure.

## 11. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый policy baseline for contract lifecycle, compatibility and change control without implementation tooling. |
