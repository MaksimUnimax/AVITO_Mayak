# Маяк Авито — Beacon Management Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 15 of 24
**Дата:** 2026-07-07
**Модуль:** `04-beacon-management`
**Основание:** Architecture Baseline v1.1, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Entitlements & Billing Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Technical Baseline v1.0, Acceptance Matrix v1.1, Avito Reference Foundation, Target Model v0.1 as DRAFT context and OPEN_DECISIONS.md.
**Не является:** product-code, parser implementation, supported-filter catalog, physical database schema, migration, executable test, external Avito call, scheduler, notification flow, runtime configuration or permission to implement.

---

## 1. Назначение

Beacon Management владеет account-owned Маяком как объектом настройки мониторинга: source URL, accepted extracted snapshot, explicit user overrides, deterministic effective configuration, immutable configuration revisions and lifecycle authority.

Модуль отвечает на вопрос «какая именно версия конфигурации какого Маяка принадлежит какому account и может быть использована downstream-модулями». Он не парсит Avito, не запускает scans, не хранит listing history и не вычисляет тарифные права самостоятельно.

## 2. Границы и non-ownership

Beacon Management owns:

- `Beacon`;
- `BeaconSourceUrl`;
- `ExtractedSearchConfigurationSnapshot` as accepted normalized evidence received from Parser Adapter;
- `BeaconFilterOverride`;
- `BeaconConfigurationRevision`;
- Beacon lifecycle/activation authority;
- safe Beacon read models and revision references;
- audit references for protected Beacon mutations.

It does not own:

- Account, identity, roles, sessions or credentials;
- TariffDefinition, Subscription, EntitlementGrant or payment state;
- parser transport, HTML, `searchCore`, `context`, provider payload or Avito request mechanics;
- ScanRun, listing observations, baseline/diff or listing history;
- egress routes, agents or leases;
- notification events, outbox or delivery attempts;
- provider adapter UI state;
- Filter Catalog definitions/options/evidence;
- exact retention/deletion policy while OD-013 is open.

Other modules use public Beacon contracts and never write Beacon-owned state directly.

## 3. Confirmed decisions

1. One Beacon belongs to exactly one immutable internal `account_id` ownership scope.
2. `beacon_id` is the isolation boundary for configuration references and downstream history.
3. Submitted source URL is preserved separately and is not rewritten by extraction result or user override.
4. Extracted snapshot and user override remain distinguishable by provenance.
5. Effective configuration is deterministic from accepted source reference, extracted snapshot, override set and revision metadata.
6. Every effective configuration change creates a new immutable `BeaconConfigurationRevision`; historical revisions are not edited.
7. Entitlements & Billing supplies effective decisions for active Beacon count, geography, interval and edit capability; Beacon Management does not duplicate tariff tables or infer rights from UI.
8. Avito Parser Adapter may return normalized extraction/validation outcomes but cannot create, activate or mutate Beacon state directly.
9. Scan Orchestration consumes an explicit immutable configuration revision reference; it does not infer “latest” silently for an already accepted run request.
10. Telegram, MAX, Web Cabinet and Admin invoke public commands and do not become Beacon data owners.
11. External URLs and parser outputs remain untrusted until validation/normalization; no external string may be interpolated into shell execution.
12. DRAFT target-model workflow and filter examples are not implementation defaults unless separately approved.

## 4. DRAFT product context — not automatic implementation rules

Target Model v0.1 describes a candidate user flow:

1. user submits a ready Avito search URL;
2. service performs safe test extraction;
3. recognized parameters are shown;
4. only supported parameters may be changed;
5. a test search validates the effective configuration;
6. explicit confirmation precedes activation.

It also describes three conceptual configuration levels:

- `source_url`;
- `extracted_snapshot`;
- `overrides`;

and deterministic effective configuration stored as a versioned revision.

Run 15 accepts the ownership/provenance/revision boundaries already present in approved Data Model and Contract documents. It does not approve exact UI flow, parser behavior, filter catalog, intervals, state enum, validation thresholds or activation workflow implementation.

## 5. Open decisions and blockers

Run 15 does not resolve:

- `OD-003` — exact allowed intervals and change rules;
- `OD-004` — behavior after entitlement/access expiry;
- `OD-009` — exact first-stage supported editable Avito filters;
- `OD-010` — country-wide availability by market;
- `OD-011` — safe minimum monitoring frequency;
- `OD-013` — retention, archive, deletion and personal-data lifetime;
- exact lifecycle state enum and transition table;
- exact delete/archive/restore semantics;
- whether identical source URLs may coexist in multiple Beacons of one account;
- source URL canonicalization policy and equivalence rules;
- exact Beacon naming constraints;
- exact acceptance criteria for an extracted snapshot;
- exact precedence/merge algorithm for multivalue overrides;
- exact rule for switching active configuration revision;
- exact response when entitlement changes while a mutation is in progress;
- exact optimistic concurrency/version-conflict mechanism;
- exact revision retention and compaction policy.

Open means blocked. No code, test, CLI or UI may fabricate a value or enum.

## 6. Authoritative state

| Record | Purpose | Required boundary |
|---|---|---|
| `Beacon` | Account-owned monitoring configuration/lifecycle root | exactly one owner account |
| `BeaconSourceUrl` | Submitted URL and validation provenance | preserved; not overwritten by override/extraction |
| `ExtractedSearchConfigurationSnapshot` | Accepted normalized extraction outcome | parser evidence, not provider/raw payload authority |
| `BeaconFilterOverride` | Explicit user-authorized structured change | separate from snapshot/source URL |
| `BeaconConfigurationRevision` | Immutable effective configuration revision | historical revision never rewritten |
| `BeaconActivationState` | Conceptual lifecycle authority | exact enum/transitions deferred |
| `BeaconReadModel` | Rebuildable view with provenance/freshness | not authoritative mutation source |

## 7. Configuration provenance model

Required provenance chain:

```text
BeaconSourceUrl
  -> ParserAdapter normalized extraction outcome
  -> accepted ExtractedSearchConfigurationSnapshot
  -> explicit BeaconFilterOverride set
  -> deterministic effective configuration
  -> immutable BeaconConfigurationRevision
```

Rules:

- source URL remains available as submitted evidence;
- parser outcome is not accepted as a clean snapshot when malformed, incomplete, blocked, CAPTCHA-affected, route-failed or ambiguous;
- overrides operate on structured supported parameters, not blind string substitution;
- multivalue parameter semantics must preserve all approved values and must not collapse them silently;
- effective revision records source/snapshot/override references and safe provenance;
- unsupported or uncertain parameter remains explicit and blocks silent activation where it affects correctness.

## 8. Ownership and authorization

- Client mutation requires verified actor context linked to the owning `account_id`.
- A foreign account receives no existence-sensitive detail beyond approved error semantics.
- Admin & Support may request protected action only through public commands with server-side role/scope and audit.
- UI visibility, Telegram/MAX username, chat role or client-supplied account value is not authorization.
- System-initiated lifecycle action identifies service actor class, causation and policy source.
- Entitlement evaluation occurs before an action whose effect depends on active count, geography, interval or edit capability.

## 9. Public input families

Exact Python and wire schemas remain future task scope.

| Input family | Purpose |
|---|---|
| `CreateBeaconPreparationCommand` | Create an account-scoped preparation boundary from a submitted source URL without implicit activation |
| `RecordSourceValidationOutcomeCommand` | Attach a normalized Parser Adapter validation/extraction outcome |
| `AcceptExtractedSnapshotCommand` | Accept a usable normalized snapshot under actor/account scope |
| `SetBeaconOverridesCommand` | Create a structured override set without rewriting source URL/snapshot |
| `CreateBeaconConfigurationRevisionCommand` | Materialize a deterministic immutable effective revision |
| `ConfirmBeaconConfigurationCommand` | Record explicit confirmation when required by future workflow policy |
| `ActivateBeaconCommand` | Request activation after ownership, entitlement, revision and precondition checks |
| `PauseBeaconCommand` | Request non-destructive pause under approved lifecycle policy |
| `ResumeBeaconCommand` | Request resume after current entitlement/precondition evaluation |
| `RenameBeaconCommand` | Change presentation name without changing effective search configuration |
| `ArchiveBeaconCommand` | Future protected archive/delete boundary after retention policy approval |
| `GetBeaconQuery` | Read one authorized Beacon view with current revision provenance |
| `ListAccountBeaconsQuery` | Read authorized account-scoped Beacon summaries |
| `GetBeaconRevisionQuery` | Read one immutable revision and safe provenance |

Mutation-capable inputs require contract metadata, actor/account scope, idempotency key and normalized request fingerprint.

## 10. Public output families

| Output family | Meaning |
|---|---|
| `BeaconPreparationOutcome` | created, replayed, rejected, conflict or blocked |
| `SourceValidationOutcome` | usable, rejected, incomplete, ambiguous, blocked or unsupported |
| `ExtractedSnapshotAcceptanceOutcome` | accepted, replayed, rejected or conflict |
| `BeaconOverrideOutcome` | created, replayed, rejected, unsupported or conflict |
| `BeaconConfigurationRevisionOutcome` | created, replayed, rejected, blocked or conflict |
| `BeaconLifecycleOutcome` | activated, paused, resumed, archived, unchanged replay, blocked or conflict |
| `BeaconReadResult` | authorized current view with provenance/freshness |
| `BeaconRevisionReadResult` | immutable revision view or explicit error |

Outputs remain transport, framework, ORM and provider neutral.

## 11. Public event families

Events may be emitted only after the owning mutation reaches its defined commit point:

- `BeaconPreparationCreated`;
- `BeaconSourceValidationRecorded`;
- `BeaconExtractedSnapshotAccepted`;
- `BeaconOverridesChanged`;
- `BeaconConfigurationRevisionCreated`;
- `BeaconActivated`;
- `BeaconPaused`;
- `BeaconResumed`;
- future `BeaconArchived` after deletion/retention policy approval.

Events are immutable facts, not commands and not raw parser/provider payloads.

## 12. Entitlement dependency

For operations governed by product access, Beacon Management requests `EffectiveEntitlementsResult` or `EntitlementDecisionOutcome` from Entitlements & Billing.

At minimum the future decision may cover:

- active Beacon count capability;
- geography capability;
- scan interval class;
- supported filter/edit capability.

Rules:

- no numeric/default tariff values are introduced by Beacon Management;
- an entitlement denial returns explicit blocked/denied outcome and does not mutate billing state;
- Beacon Management does not cache a client-visible/UI flag as authority;
- behavior after entitlement expiry remains OD-004;
- ambiguous entitlement result blocks effect rather than guessing.

## 13. Parser Adapter dependency

Parser Adapter is an external-boundary adapter and future Run 16 owner of extraction semantics.

Beacon Management may request or receive a normalized outcome containing safe references to:

- validated source URL context;
- extracted geography/category/filter parameters;
- normalization warnings;
- unsupported/uncertain parameter evidence;
- provider/reference version evidence;
- explicit failure/ambiguity classification.

Parser Adapter must not:

- write Beacon rows;
- choose user overrides;
- activate a Beacon;
- convert blocked/CAPTCHA/malformed/incomplete outcome into a clean snapshot;
- return raw framework/HTTP/ORM objects as public contracts.

Run 15 performs no parser or external call.

## 14. Scan Orchestration dependency

Scan Orchestration receives an explicit immutable `beacon_id` + `configuration_revision_id` reference and approved lifecycle/entitlement context.

Rules:

- a scan request does not rewrite Beacon configuration;
- a historical run retains the revision reference used for that run;
- creation of a newer revision does not silently reinterpret an already recorded historical run;
- exact scheduling and baseline/diff semantics belong to Run 17;
- paused/expired/blocked lifecycle handling remains explicit and policy-gated.

## 15. Filter Catalog dependency

Future Filter Catalog & Builder may provide verified definitions/options and validation rules.

It must not:

- become a second Beacon store;
- rewrite source URL;
- silently mark uncertain filters supported;
- create a separate incompatible configuration path.

The builder edits the same structured override/effective-revision model. Initial supported editable filter set remains OD-009.

## 16. Lifecycle semantics

Run 15 defines lifecycle authority, not an exact persisted enum.

Required semantic properties:

- preparation/configuration is distinct from active monitoring;
- activation requires an accepted immutable revision and applicable entitlement decision;
- pause does not rewrite source/snapshot/revision history;
- resume re-evaluates current preconditions rather than assuming old entitlement;
- archived/deleted behavior is blocked until OD-013 and exact policy;
- no success is emitted before lifecycle mutation commit point;
- repeated same command is idempotent;
- conflicting concurrent revision/lifecycle request returns explicit conflict.

## 17. Idempotency and commit points

Idempotency is mandatory for every Beacon mutation.

Required behavior:

- same key + same semantic request + terminal outcome → return original outcome, no second Beacon/revision/transition;
- same key + different fingerprint → `IDEMPOTENCY_MISMATCH`;
- missing key → reject before effect;
- unknown commit state → reconcile before retry;
- success event only after authoritative state commit.

Future commands must define exact intended effect, owner, commit point, visible pre-commit state, interruption state, reconciliation and rollback/roll-forward boundary.

## 18. Errors and reconciliation

Applicable categories:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`;
- `FORBIDDEN`;
- `NOT_FOUND`;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `RATE_LIMITED`;
- `EXTERNAL_UNAVAILABLE`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

Parser failure, blocked access, CAPTCHA, malformed or incomplete outcome never becomes “valid empty configuration”. Unknown mutation commit state requires reconciliation before replay.

## 19. Dependencies

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity & Access verified actor/account context;
- Entitlements & Billing effective decision contract;
- Avito Parser Adapter normalized extraction outcome after Run 16 acceptance;
- Scan Orchestration immutable revision-reference contract after Run 17 acceptance;
- Filter Catalog definitions only after Run 24 acceptance;
- Pydantic v2 at validation/serialization boundaries;
- FastAPI only at entrypoint transport boundary;
- SQLAlchemy/Psycopg/Alembic only after physical database gates;
- PostgreSQL authoritative records after schema approval;
- pytest/pytest-asyncio for future deterministic tests.

Forbidden leakage:

- raw HTTP/provider/Avito payload in public Beacon contracts;
- ORM/session objects in public interfaces;
- parser SDK/framework types as domain state;
- UI-specific models as authoritative configuration;
- billing records copied into Beacon-owned tables;
- credentials/secrets in fixtures, reports or revisions.

## 20. Fake dependencies and test doubles

Future fakes may model:

- `ActorContextProvider`;
- `EntitlementDecisionProvider`;
- `SearchSourceAnalyzer` as a contract-level fake only;
- `FilterSupportValidator`;
- `BeaconRepository`;
- `BeaconRevisionRepository`;
- `ConfigurationAssembler`;
- `AuditSink`;
- `Clock`;
- `IdGenerator`.

Fakes use synthetic URLs/parameters/accounts only and never prove live Avito behavior.

## 21. Required fixtures and test vectors

Minimum fixture IDs:

- `FX-BM-OWNER-CREATE-001`;
- `FX-BM-FOREIGN-ACCOUNT-FORBIDDEN-001`;
- `FX-BM-SOURCE-URL-PRESERVED-001`;
- `FX-BM-SNAPSHOT-SEPARATE-001`;
- `FX-BM-OVERRIDE-SEPARATE-001`;
- `FX-BM-MULTIVALUE-PRESERVED-001`;
- `FX-BM-REVISION-IMMUTABLE-001`;
- `FX-BM-REVISION-REPLAY-001`;
- `FX-BM-REVISION-MISMATCH-001`;
- `FX-BM-ENTITLEMENT-DENIED-001`;
- `FX-BM-ENTITLEMENT-AMBIGUOUS-001`;
- `FX-BM-PARSER-INCOMPLETE-BLOCKS-001`;
- `FX-BM-PARSER-CAPTCHA-BLOCKS-001`;
- `FX-BM-UNSUPPORTED-FILTER-BLOCKED-001`;
- `FX-BM-COUNTRYWIDE-OD010-BLOCKED-001`;
- `FX-BM-INTERVAL-OD003-OD011-BLOCKED-001`;
- `FX-BM-EXPIRED-OD004-BLOCKED-001`;
- `FX-BM-SOURCE-NO-SHELL-001`;
- `FX-BM-READMODEL-STALE-NOT-AUTHORITY-001`;
- `FX-BM-PAUSE-HISTORY-PRESERVED-001`.

Run 15 creates no fixture files.

## 22. Acceptance Matrix coverage

Run 15 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-DATA-001`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004` where applicable;
- `AM-EXT-002`–`AM-EXT-004` for future parser outcome handling;
- `AM-REF-001`–`AM-REF-004` for Avito/filter assertions;
- `AM-MIG-008`–`AM-MIG-009`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Rows requiring runtime, parser, provider, state, migration or reconciliation execution remain future gates.

## 23. Allowed future changes

A later exact task may:

- create Beacon Management package skeleton inside approved layout;
- define transport-neutral Beacon commands/queries/events;
- add synthetic source/snapshot/override/revision fixtures;
- implement ownership, authorization, idempotency and revision immutability tests;
- integrate with accepted Entitlements and Parser contracts;
- add persistence only after physical schema/migration gates;
- expose adapters/UI through public Beacon services only.

## 24. Forbidden changes

Without new accepted decisions/tasks, this module must not:

- invent exact lifecycle enum or transition defaults;
- overwrite source URL with normalized/extracted/override values;
- mutate historical revisions;
- hard-code supported filters, country-wide support or interval values;
- decide expiry/delete/retention behavior;
- parse Avito or make external calls;
- create scan/listing/notification state;
- duplicate tariff or account authority;
- interpolate source URL or external parameter into shell commands;
- create product-code, dependency file, lockfile, executable tests, fixture files, migrations, database, Docker/CI/CD, service, port, deploy or runtime configuration.

## 25. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `BM-01` | Semantic contracts and synthetic fixtures | `NOT_STARTED` | Platform/Identity primitives and exact task |
| `BM-02` | Account ownership and authorization | `NOT_STARTED` | Identity actor-context contract |
| `BM-03` | Source URL preservation and preparation boundary | `NOT_STARTED` | exact URL validation/equivalence policy |
| `BM-04` | Extracted snapshot acceptance | `BLOCKED` | Run 16 Parser Adapter contract/evidence |
| `BM-05` | Structured overrides and effective assembler | `BLOCKED` | OD-009 and precedence rules |
| `BM-06` | Immutable configuration revisions | `NOT_STARTED` | concurrency/version policy and exact task |
| `BM-07` | Entitlement-gated lifecycle | `BLOCKED` | OD-003, OD-004, OD-010, OD-011 and effective-decision contract |
| `BM-08` | Scan revision-reference handoff | `BLOCKED` | Run 17 contract acceptance |
| `BM-09` | Persistence and migrations | `BLOCKED` | physical schema and migration gates |
| `BM-10` | Full evidence/handoff | `NOT_STARTED` | applicable subtasks complete |

## 26. Task packet requirements

A future task must include exact paths, stable ID, parent SHA, allowed/forbidden scope, actor/account rules, applicable entitlement inputs, source/snapshot/override/revision semantics, idempotency, commit points, reconciliation, concurrency, rollback/roll-forward, fixtures, matrix rows, references, static/runtime checks, evidence format and final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 27. Report and handoff

A future implementation report must include:

- task/iteration ID and exact commit SHA;
- changed paths;
- contract versions and owned state touched;
- source/snapshot/override/revision provenance evidence;
- entitlement/authorization/idempotency/commit-point evidence;
- fixtures/matrix rows and exact results;
- parser/reference evidence only when explicitly in scope;
- sensitive-data and external-string safety confirmation;
- migration/runtime evidence only when explicitly in scope;
- prohibited-artifact check;
- known blockers and next safe task;
- exact final marker for independent review.

## 28. Acceptance criteria

The playbook is acceptable only when:

- Beacon ownership and foreign non-ownership are explicit;
- source URL, extracted snapshot, overrides and effective revision remain distinct;
- historical revisions are immutable;
- Entitlements, Parser, Scan and Filter Catalog boundaries are explicit;
- open decisions remain open without fabricated defaults;
- authorization, account/Beacon scope, idempotency, commit point and reconciliation are explicit;
- dependencies/fakes, fixtures and matrix rows are named;
- roadmap does not authorize implementation;
- no code, dependency, lock, test, fixture file, migration, database, parser/external call, Docker/CI/CD, deploy/runtime, service, port or sensitive access material is created;
- GitHub publication and exact server synchronization are independently verified.

## 29. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### BM-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 15 initial Beacon ownership, source URL, extracted snapshot, overrides, effective configuration, immutable revision and lifecycle boundaries defined.
- Entitlements, Parser, Scan and Filter Catalog ownership boundaries preserved.
- OD-003, OD-004, OD-009, OD-010, OD-011 and OD-013 remain unresolved.
- No implementation, parser, database, runtime or infrastructure artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
