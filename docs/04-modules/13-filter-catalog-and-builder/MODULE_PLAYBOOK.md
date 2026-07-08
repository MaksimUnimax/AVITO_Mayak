# Маяк Авито — Filter Catalog & Builder Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 24 of 24
**Дата:** 2026-07-08
**Модуль:** `13-filter-catalog-and-builder`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Beacon Management Module Playbook v1.0, Avito Parser Adapter Module Playbook v1.0, Scan Orchestration & Listing State Module Playbook v1.0, Web Cabinet Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, Avito Reference Policy v1.0, Avito Reference Evidence v1.0, Target Model v0.1 and OPEN_DECISIONS.md.
**Не является:** supported-filter list approval, Avito official filter catalog, parser implementation, visual builder implementation, frontend implementation, UI design, database schema, migration, API route, live Avito probe, runtime configuration, service, port, credential, secret or permission to implement.

---

## 1. Назначение

Filter Catalog & Builder владеет verified filter definition boundary and visual-builder semantics over the existing Beacon configuration model.

Модуль отвечает на вопросы:

- как future supported filter definitions become evidence-bound and versioned;
- как category/geography/provider-surface compatibility is represented without pretending Avito provides a stable public filter API;
- как filter options, multivalue behavior, ranges, units and dependencies are classified before customer editing;
- как builder UI/schema can be derived from approved catalog definitions without owning Beacon state;
- как user edits become structured Beacon overrides rather than blind URL string edits;
- как Parser extraction evidence, Beacon accepted snapshots and Web Cabinet forms remain separated;
- как unsupported, stale, lossy or ambiguous filters block silent activation and false success;
- как OD-009 stays open until exact first-stage editable filters are approved separately.

Run 24 completes the module-playbook route. It does not approve a concrete list of Avito filters, categories, URLs, parser mappings, UI screens, database schema, frontend code or live provider behavior.

## 2. Boundaries and ownership

Filter Catalog & Builder owns semantic mutation authority for:

- filter catalog evidence references;
- filter definition records;
- filter option definition records;
- filter capability profiles by category/geography/provider surface;
- filter dependency and compatibility rules;
- builder field semantics and validation rules;
- filter value normalization semantics;
- filter deprecation/supersession references;
- catalog versioning and compatibility classification;
- safe builder read models.

It does not own:

- Beacon source URL, extracted snapshot, override set, effective configuration, revision or lifecycle;
- Parser extraction, provider request/response classification, Avito payloads or listing candidates;
- Scan runs, observations, baseline/difference or listing state;
- Entitlements, tariffs, intervals or payment state;
- Identity accounts, roles, sessions or credentials;
- Web Cabinet frontend, routes, forms or sessions;
- Telegram/MAX provider behavior;
- Admin & Support cases/audits;
- raw Avito provider payload retention while OD-013 remains open;
- exact supported first-stage filter list while OD-009 remains unresolved.

Only Filter Catalog & Builder may define catalog semantics. Beacon Management remains the owner of actual customer Beacon configuration and override acceptance.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted Beacon Management, Avito Parser Adapter and Web Cabinet playbooks.
4. Avito Reference Policy/Evidence and separately accepted official/primary evidence.
5. This playbook.
6. Future exact implementation task and accepted evidence.
7. Runtime evidence for one exact release/environment/provider surface.

A visual form, current parser observation, customer URL, provider payload, category name or external UI label is never catalog authority by itself.

## 4. Confirmed decisions

1. Filter Catalog & Builder is a filter-definition and builder-semantics boundary, not Beacon configuration ownership.
2. Beacon Management owns accepted extracted snapshots, user overrides, effective configuration and immutable revisions.
3. Avito Parser Adapter owns extraction/normalization evidence and parser warnings only; it does not decide supported editability.
4. Web Cabinet may render builder forms only from approved catalog definitions and cannot invent filter definitions.
5. Supported editability requires evidence-bound catalog approval, not just visible Avito UI, parser observation or user request.
6. OD-009 remains open; Run 24 does not select the exact first-stage editable filter list by category.
7. Internal Avito endpoints and embedded state are not stable provider contracts.
8. Multivalue filters must preserve all approved values and never silently collapse repeated provider parameters.
9. Range filters require explicit unit, boundary, inclusivity and normalization semantics before use.
10. Dependent filters require explicit dependency graph and compatibility classification before builder exposure.
11. Unsupported, uncertain, stale, lossy, provider-changed or category-incompatible filters must remain explicit.
12. Filter catalog versions are immutable after publication; changes create new catalog versions or supersession records.
13. Builder draft state is not authoritative Beacon state until Beacon accepts a public override/configuration command.
14. Client-side validation is usability only; server-side catalog and Beacon validation remain authoritative.
15. Filter Catalog cannot create parser calls, web screens, migrations, tables, services, jobs or runtime.
16. Run 24 creates no product-code, database, migration, fixture file, executable test, API route, frontend, provider call, port, credential, secret or deployment.

## 5. Open decisions and blockers

Run 24 does not resolve:

- `OD-003` — exact allowed intervals and change rules;
- `OD-009` — exact supported editable Avito filters by category for first stage;
- `OD-010` — country-wide availability by market;
- `OD-011` — safe minimum monitoring frequency;
- `OD-013` — retention/deletion of history, logs and personal data;
- `OD-014` — public website screens and analytics depth;
- exact Avito category taxonomy accepted for first stage;
- exact filter definition list and option sets;
- exact filter dependency graph;
- exact range units and boundary rules for each editable range;
- exact URL parameter mapping/canonicalization;
- exact parser compatibility-profile lifecycle for catalog evidence;
- exact supported builder screen composition;
- exact validation error wording and UX;
- exact catalog persistence schema, indexes and migrations;
- exact catalog release and rollback policy;
- exact evidence refresh cadence;
- exact acceptance thresholds for stale or changed Avito surfaces.

Open means blocked. No implementation, UI, parser task, fixture, migration, test or documentation update may fabricate exact filter lists/options/units/dependencies.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, frontend schemas, API routes or provider payloads.

| Record | Purpose | Required boundary |
|---|---|---|
| `FilterCatalogVersion` | Immutable catalog release with evidence and compatibility references | no silent mutation |
| `FilterDefinition` | One approved editable/searchable filter concept | evidence-bound and category-scoped |
| `FilterOptionDefinition` | Allowed option/value within a filter | explicit provenance and status |
| `FilterRangeDefinition` | Numeric/date/price/range semantics | units/bounds/inclusivity required |
| `FilterDependencyRule` | Dependency or incompatibility between filters/options | explicit condition and outcome |
| `FilterCapabilityProfile` | Category/geography/provider-surface capability state | not global by assumption |
| `FilterEvidenceReference` | Safe evidence pointer/fingerprint/date/scope | no raw provider payload by default |
| `BuilderFieldDefinition` | UI-neutral field semantics derived from catalog | not frontend component |
| `BuilderDraftValidationResult` | Result of draft validation against catalog | not Beacon acceptance |
| `CatalogCompatibilityWarning` | Stale/changed/unsupported/lossy/ambiguous warning | blocks silent success where relevant |
| `CatalogReadModel` | Safe catalog projection for Web/Beacon/Admin | rebuildable/provenance-aware |

## 7. Semantic identifiers and scope

- `filter_catalog_version_id` identifies one immutable catalog version.
- `filter_definition_id` identifies one normalized project filter concept.
- `filter_option_id` identifies one approved option within a filter definition.
- `filter_capability_profile_id` identifies category/geography/provider-surface capability evidence.
- `filter_evidence_ref` identifies safe evidence, not raw payload authority.
- `builder_field_id` identifies UI-neutral field semantics.
- `beacon_id`, `beacon_revision_id`, `extracted_snapshot_id` and `override_id` remain Beacon-owned references.
- `parser_attempt_id` and `parser_compatibility_profile_id` remain Parser-owned references.
- `correlation_id` and `causation_id` connect catalog validation to Beacon/Web outcomes.

Identifiers do not expose raw Avito payloads, cookies, sessions, credentials, provider internals or unnecessary personal data.

## 8. Evidence and catalog approval boundary

A filter definition may be approved only when future exact evidence establishes:

- provider/category/geography scope;
- source URL/profile and extraction context;
- filter label/name as observed;
- normalized project filter concept;
- provider parameter mapping where safe and approved;
- value type and normalization semantics;
- option/range semantics;
- dependency/incompatibility semantics;
- multivalue semantics;
- known unsupported/lossy/ambiguous cases;
- evidence date, source, limitations and refresh requirement.

Evidence can be official or primary/accepted reference evidence as allowed by policy. If evidence is stale, missing, contradictory or unsupported, the catalog item is not approved for editing.

## 9. Builder boundary

Builder semantics are UI-neutral. Future Web/Telegram/MAX surfaces may render them differently, but all must preserve the same server-side catalog and Beacon validation.

Rules:

- builder field exists only if derived from approved `BuilderFieldDefinition`;
- field display does not grant editability;
- draft value is not Beacon override until Beacon accepts it;
- client-side validation is advisory;
- server validation uses catalog version and Beacon revision references;
- unsupported or ambiguous field prevents silent activation;
- hidden or disabled fields cannot be submitted as trusted authority;
- builder cannot bypass entitlements or Beacon ownership.

## 10. Beacon dependency

Beacon Management owns source URL, extracted snapshot, overrides, effective configuration, revisions and lifecycle.

Filter Catalog & Builder supplies:

- catalog version references;
- approved filter definitions/options;
- validation results;
- compatibility warnings;
- builder field semantics.

Rules:

- catalog does not create Beacon revisions;
- catalog does not accept extracted snapshots;
- catalog does not activate, pause, resume, archive or delete Beacons;
- Beacon override acceptance uses catalog definitions but remains Beacon authority;
- historical Beacon revisions keep the catalog/evidence references they were validated against;
- catalog supersession does not rewrite historical Beacon revisions.

## 11. Parser dependency

Avito Parser Adapter supplies normalized extraction and compatibility evidence. It does not approve filter editability.

Rules:

- parser observation is evidence input, not catalog authority alone;
- parser malformed/incomplete/ambiguous/restricted outcome cannot approve a filter;
- repeated/multivalue provider parameters must not be collapsed silently;
- internal endpoint/embedded-state behavior is not stable contract;
- parser compatibility profile change may make catalog definitions stale or blocked;
- exact provider request/probe behavior remains future proof/implementation scope.

## 12. Web Cabinet dependency

Web Cabinet may render catalog-backed builder forms only after this playbook is accepted and later exact tasks approve UI/screen details.

Rules:

- Web Cabinet does not invent filter definitions;
- Web Cabinet does not own catalog versions;
- Web Cabinet draft state is not business state;
- Web Cabinet screen map and analytics remain OD-014;
- UI labels, localization and validation messages remain future decisions;
- Web Cabinet sends commands to Beacon, not direct catalog/Beacon table writes.

## 13. Entitlements and interval dependency

Entitlements & Billing owns effective rights, tariff limits and allowed intervals.

Rules:

- Filter Catalog does not select tariff limits;
- Filter Catalog does not select allowed monitoring intervals;
- OD-003 remains open for exact interval rules;
- builder visibility may later consume entitlement decisions but cannot duplicate entitlement state;
- tariff/payment UI remains outside this module.

## 14. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `RegisterFilterEvidenceCommand` | Attach safe evidence reference for candidate catalog work |
| `ProposeFilterDefinitionCommand` | Propose one filter definition from approved evidence |
| `ApproveFilterDefinitionCommand` | Approve definition only after evidence and policy gates |
| `DeprecateFilterDefinitionCommand` | Mark definition obsolete/stale without rewriting history |
| `CreateFilterCatalogVersionCommand` | Publish immutable catalog version |
| `ValidateBuilderDraftCommand` | Validate draft values against catalog and Beacon context |
| `ExplainFilterCapabilityQuery` | Explain support/unsupported/stale/ambiguous status |
| `ListBuilderFieldsQuery` | Produce UI-neutral builder fields for a category/geography/context |
| `MapBuilderDraftToBeaconOverridesCommand` | Produce Beacon override candidate for Beacon-owned acceptance |
| `GetCatalogVersionQuery` | Read one catalog version and provenance |
| `ListCatalogWarningsQuery` | Read stale/changed/unsupported warnings |
| `RecordCatalogCompatibilityOutcomeCommand` | Attach compatibility check outcome after future proof task |

Mutation-capable inputs require common contract metadata, actor/service scope where applicable, idempotency key and normalized fingerprint.

## 15. Public output families

| Output family | Meaning |
|---|---|
| `FilterEvidenceOutcome` | accepted-reference, rejected, stale, unsupported, ambiguous or blocked |
| `FilterDefinitionOutcome` | proposed, approved, rejected, deprecated, superseded or blocked |
| `FilterCatalogVersionOutcome` | created, replayed, rejected, superseded or conflict |
| `BuilderFieldListOutcome` | produced, partial, empty-supported-set, blocked, stale or ambiguous |
| `BuilderDraftValidationOutcome` | valid, invalid, unsupported, stale, conflict, ambiguous or blocked |
| `BeaconOverrideCandidateOutcome` | prepared, rejected, unsupported, stale, ambiguous or conflict |
| `FilterCapabilityExplanationOutcome` | explained, partially-explained, unsupported, stale or ambiguous |
| `CatalogCompatibilityOutcome` | compatible, changed-compatible, changed-breaking, unsupported, stale or unknown |

Outputs remain framework, frontend, provider, persistence and route neutral.

## 16. Mandatory outcome classes

At minimum:

- `FILTER_EVIDENCE_MISSING`;
- `FILTER_EVIDENCE_STALE`;
- `FILTER_UNSUPPORTED`;
- `FILTER_AMBIGUOUS`;
- `FILTER_DEFINITION_APPROVED`;
- `FILTER_DEFINITION_DEPRECATED`;
- `CATALOG_VERSION_CREATED`;
- `CATALOG_VERSION_SUPERSEDED`;
- `BUILDER_FIELDS_PRODUCED`;
- `BUILDER_FIELD_POLICY_BLOCKED`;
- `BUILDER_DRAFT_VALID`;
- `BUILDER_DRAFT_INVALID`;
- `BUILDER_DRAFT_NOT_AUTHORITY`;
- `BEACON_OVERRIDE_CANDIDATE_PREPARED`;
- `BEACON_ACCEPTANCE_REQUIRED`;
- `CATALOG_COMPATIBILITY_BREAKING`;
- `CATALOG_RECONCILIATION_REQUIRED`.

Exact wire codes, option values, UI labels and category identifiers are not selected.

## 17. False-success prohibition

None of the following may become clean catalog/builder success:

- Avito UI label observed once without accepted evidence;
- internal endpoint parameter treated as stable public contract;
- parser success treated as supported editability;
- visible Web field treated as Beacon override acceptance;
- client-side validation treated as server acceptance;
- repeated/multivalue parameters collapsed silently;
- range value accepted without unit/boundary semantics;
- category/geography-specific filter treated as global;
- stale/contradictory provider evidence treated as current;
- unsupported filter silently ignored while activating Beacon;
- catalog supersession rewriting historical Beacon revisions;
- OD-009 filled by implementation default;
- raw provider payload stored as ordinary fixture/log;
- direct table edit or direct provider call by catalog/builder.

## 18. Security, privacy and retention

- Filter catalog evidence uses minimized safe references and fingerprints.
- Raw provider payloads are not ordinary logs, fixtures or public docs.
- URL parameters can contain personal/sensitive search intent and must be minimized/redacted in reports.
- External strings never become shell commands.
- Builder inputs are untrusted.
- Error messages do not leak internal provider payloads, foreign object existence or stack traces.
- Retention/deletion/archive/compaction remain OD-013.
- Catalog evidence refresh does not authorize live provider calls without exact task.

## 19. Observability semantics

Future minimum safe signals:

- catalog version;
- filter definition/capability identifiers;
- evidence reference class and date;
- category/geography/provider-surface scope;
- validation outcome class;
- builder draft id and Beacon context reference;
- stale/unsupported/ambiguous warning class;
- compatibility-profile change class;
- owning module called;
- safe reason code and latency;
- no raw provider payload, credentials, cookies or unnecessary personal data.

A rendered builder, successful parser extraction or green validation indicator does not prove Beacon activation or future scan success.

## 20. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Beacon public commands and revision references;
- Parser normalized extraction evidence and compatibility profile references;
- Web Cabinet UI-neutral field consumption;
- Admin & Support safe catalog explanations;
- PostgreSQL/SQLAlchemy/Psycopg after physical schema approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- OpenTelemetry boundary after applicable instrumentation task.

Deferred/blocked:

- exact filter lists/options/categories;
- exact URL parameter mapping;
- evidence refresh cadence;
- visual builder screen composition;
- frontend framework/component implementation;
- persistence schema/migrations;
- provider probes/live calls;
- services/deploy/runtime.

No catalog runtime is introduced by this playbook.

## 21. Fake dependencies and test doubles

Future approved fakes may model:

- `FilterEvidenceGateway`;
- `FilterCatalogRepository`;
- `FilterCompatibilityClassifier`;
- `BuilderFieldProjector`;
- `BuilderDraftValidator`;
- `BeaconOverrideCandidateMapper`;
- `BeaconReadGateway`;
- `ParserEvidenceGateway`;
- `EntitlementDecisionReader`;
- `WebPresentationGateway`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic categories, filters, options, ranges, evidence references, Beacons and drafts only. They do not prove real Avito behavior, supported filters, UI correctness, provider permission, persistence or production safety.

## 22. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-OWNER-FOREIGN-BEACON-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-CHANGED-BREAKING-001`;
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-FILTER-EVIDENCE-MISSING-001`;
- `FX-FILTER-EVIDENCE-STALE-001`;
- `FX-FILTER-DEFINITION-APPROVED-001`;
- `FX-FILTER-DEFINITION-REJECTED-001`;
- `FX-FILTER-MULTIVALUE-PRESERVED-001`;
- `FX-FILTER-RANGE-UNIT-REQUIRED-001`;
- `FX-FILTER-CATEGORY-SCOPE-REQUIRED-001`;
- `FX-FILTER-DEPENDENCY-BLOCKED-001`;
- `FX-FILTER-OD009-BLOCKED-001`;
- `FX-BUILDER-FIELD-PRODUCED-001`;
- `FX-BUILDER-DRAFT-NOT-AUTHORITY-001`;
- `FX-BUILDER-CLIENT-VALIDATION-NOT-AUTHORITY-001`;
- `FX-BUILDER-BEACON-OVERRIDE-CANDIDATE-001`;
- `FX-CATALOG-VERSION-IMMUTABLE-001`;
- `FX-CATALOG-SUPERSESSION-NO-HISTORY-REWRITE-001`;
- `FX-CATALOG-COMPATIBILITY-BREAKING-001`;
- `FX-CATALOG-RAW-PAYLOAD-REDACTED-001`;
- `FX-CATALOG-NO-PROVIDER-CALL-001`.

Run 24 creates no fixture files and executes no tests.

## 23. Acceptance Matrix coverage

Run 24 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-DATA-002`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004`;
- `AM-REF-001`–`AM-REF-004`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, frontend, catalog implementation, parser probes, Avito calls, exact filter lists, migrations, API routes and deployment remain future gates and are not passed by this documentation run.

## 24. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral filter catalog records;
- implement synthetic deterministic catalog validation tests;
- integrate Parser evidence references;
- integrate Beacon override-candidate mapping through public contracts;
- integrate Web Cabinet builder field projections;
- add immutable catalog version persistence after schema/migration approval;
- add compatibility classification after approved evidence-refresh task;
- add observability, idempotency and redaction evidence.

## 25. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create exact supported filter list or options;
- close OD-009 by assumption;
- create frontend, pages, routes, API handlers or UI components;
- create tables, migrations, ORM models or physical schemas;
- install dependencies or create lockfiles;
- call Avito, Telegram, MAX or any provider;
- create parser implementation or provider probes;
- edit Beacon configuration directly;
- rewrite historical Beacon revisions;
- treat parser observation as supported editability;
- invent category taxonomy, URL mapping, range units or dependency graph;
- create fixture data files or executable tests;
- store raw provider payloads, cookies, secrets or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 26. Report and handoff requirements

Any future implementation/proof task touching Filter Catalog & Builder must report:

- exact GitHub SHA and paths;
- module playbook version used;
- evidence references and dates used;
- created/changed files and hashes;
- whether product-code, migrations, dependency files, database, runtime, frontend, API routes, fixture files, parser probes or provider calls were created;
- exact tests and outputs;
- filter evidence, idempotency, redaction and compatibility evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 27. Roadmap after this playbook

1. Synchronize exact Run 24 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Perform final independent documentation audit across all Runs 1–24.
4. Publish final governance acceptance only if audit proves readiness.
5. Synchronize final governance SHA and stop; product-code remains not started.

This playbook is a prerequisite only and does not authorize implementation.

## 28. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `FILTER-HISTORY-0001` | 2026-07-08 | Run 24 created Filter Catalog & Builder Module Playbook v1.0 and fixed evidence-bound filter definitions, immutable catalog versions, builder validation, Beacon/Web/Parser separation, OD-009 blocking and false-success boundaries without implementation. | Public GitHub `main`; Run 24 publication commit; no runtime artifacts. |
