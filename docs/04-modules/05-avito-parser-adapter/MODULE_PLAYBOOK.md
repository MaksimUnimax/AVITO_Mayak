# Маяк Авито — Avito Parser Adapter Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 16 of 24
**Дата:** 2026-07-07
**Модуль:** `05-avito-parser-adapter`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Beacon Management Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Windows Egress Agent Runbook v1.0, Reference Registry v1.0/v1.1, Avito Reference Policy v1.0, Avito Reference Evidence v1.0, Target Model v0.1 and Architecture Module Map v0.1 only as DRAFT context, and OPEN_DECISIONS.md.
**Primary implementation evidence:** `AVITO-PRIMARY-PARSER-001`, repository `Duff89/parser_avito`, exact commit `48441c352e36919abef13c436f41a3a62636da17`.
**Не является:** parser implementation, Avito permission, official consumer-search API contract, live request task, endpoint probe, supported-filter catalog, route design, retry/rate policy, executable test, database schema, migration, runtime configuration or permission to implement.

---

## 1. Назначение

Avito Parser Adapter является внешней границей между недоверенным Avito/search transport outcome и внутренними transport-neutral contracts Маяка.

Модуль:

- классифицирует transport/provider/response state;
- извлекает и нормализует search configuration evidence;
- извлекает и нормализует listing candidates;
- сохраняет provenance, reference profile and warnings;
- возвращает explicit usable, rejected, unavailable, malformed, incomplete, restricted, unsupported or ambiguous outcomes.

Он не решает, существует ли «новое объявление», не создаёт Beacon, не выбирает route, не планирует scan и не отправляет notification.

## 2. Границы и non-ownership

Avito Parser Adapter owns semantic authority for:

- parser request classification;
- parser/reference compatibility profile;
- source/response extraction semantics within an approved evidence scope;
- normalized search-configuration outcome;
- normalized listing-candidate outcome;
- explicit parser warnings and failure/ambiguity reasons;
- safe adapter-attempt evidence references;
- mapping provenance from external evidence to normalized output.

It does not own:

- `Beacon`, source URL storage, extracted-snapshot acceptance, overrides, effective configuration, revision or lifecycle;
- Account, identity, role, entitlement, tariff or payment state;
- Egress route, agent, lease, health, quarantine, fallback or transport credentials;
- ScanRun, schedule, baseline, diff, listing observation/history or “new listing” decision;
- NotificationEvent, outbox or provider delivery;
- Filter Catalog definitions/options or supported-editability decisions;
- cookies, sessions, proxy configuration or route policy;
- raw provider retention policy while OD-013 remains open.

No foreign module may mutate parser-owned compatibility/evidence state directly; Parser Adapter may not mutate foreign business state directly.

## 3. Source-of-truth and evidence hierarchy

For Avito-dependent behavior use:

1. public GitHub `main` and approved governance;
2. current approved architecture/contracts/security/quality/operations documents;
3. `REFERENCE_REGISTRY_v1.0.md` for Avito reference IDs;
4. `AVITO_REFERENCE_POLICY_v1.0.md`;
5. `AVITO_REFERENCE_EVIDENCE_v1.0.md`;
6. exact official evidence within its exact product/scope;
7. exact primary implementation reference behavior within its exact commit;
8. future separately approved `proof_only` evidence;
9. exact implementation task after all gates.

Official Avito Ads evidence applies only to Avito Ads. It does not prove consumer classified-search API, URL/filter semantics, endpoint stability, automation permission, listing fields or safe cadence.

## 4. Confirmed decisions

1. All Avito URLs, HTML, parameters, embedded state, response bodies, headers and errors are external/untrusted.
2. A normalized adapter outcome is not a raw provider/HTTP/framework object.
3. Transport success is not parser success. Parser success is not scan/business success.
4. No request sent, route failure, explicit rejection, restriction/CAPTCHA, malformed/incomplete response, stale/unsupported evidence and ambiguity never become a clean empty listing result.
5. Parser Adapter cannot create, activate, pause, edit or delete a Beacon.
6. Parser Adapter cannot write Scan/listing history or decide baseline/diff/newness.
7. Parser Adapter cannot create notifications or call Telegram/MAX directly.
8. Source URL remains Beacon-owned evidence and is not rewritten by parser output.
9. Extracted snapshot acceptance belongs to Beacon Management; Parser only returns a normalized extraction outcome.
10. Repeated/multivalue parameters must not be silently collapsed or overwritten.
11. External strings must never be interpolated into shell execution.
12. Raw provider payloads and sensitive access material are excluded from ordinary contracts, logs, reports and fixtures.
13. Any parser mapping is tied to an explicit reference/compatibility profile and cannot silently outlive contradictory evidence.
14. Provider/reference changes require compatibility classification before dependent acceptance.
15. DRAFT target-model examples are not implementation defaults.

## 5. Exact reference observations and rejected inheritance

At `AVITO-PRIMARY-PARSER-001` commit `48441c352e36919abef13c436f41a3a62636da17`, the reviewed implementation was observed to:

- accept configured Avito URLs;
- read first-page HTML;
- consume embedded `loaderData.data`, `searchCore`, `context` and `catalog`;
- derive later-page parameters;
- use `https://www.avito.ru/web/1/js/items` for later pages;
- normalize result models and locally filter;
- keep local `listing id + price` history;
- handle request failures/restriction-like statuses;
- replace an earlier repeated parameter value in current normalization behavior.

These are implementation observations only. Run 16 explicitly rejects automatic inheritance of:

- internal endpoint or embedded-state stability;
- local SQLite/global history;
- direct parser-to-notification coupling;
- local single-user TOML authority;
- repeated-value loss;
- phone extraction;
- unrestricted details/views collection;
- reference retry/cookie/proxy choices;
- reference-specific dependencies;
- production or legal suitability.

No reference source code is copied by this playbook.

## 6. Open decisions and blockers

Run 16 does not resolve:

- `OD-009` — exact supported editable filters by category;
- `OD-010` — country-wide/market support;
- `OD-011` — safe/allowed monitoring frequency;
- `OD-013` — retention of raw/normalized provider evidence, logs and personal data;
- official consumer-search API availability;
- legal/compliance permission for automation;
- exact access strategy and provider surface;
- stability or permitted use of embedded structures/internal endpoints;
- exact URL allowlist, canonicalization, redirect and DNS policy;
- exact request headers, cookies, sessions, authentication or consent policy;
- exact route technology and route-selection/fallback policy;
- exact timeout, response-size, pagination and concurrency limits;
- retry count, delay, backoff, rate limit and circuit breaker;
- CAPTCHA/restriction operational handling beyond explicit failure classification;
- exact stable listing identity and required provider fields;
- price/currency/unit normalization rules;
- category/geography/filter mapping schema;
- exact empty-result usability criteria;
- exact partial-page acceptance policy;
- exact raw payload fingerprint and retention mechanism;
- exact parser compatibility-profile lifecycle;
- exact storage/persistence for adapter attempt evidence.

Open means blocked. No implementation agent may guess these values.

## 7. Authoritative semantic records

These are logical contract concepts, not approved tables or storage formats.

| Record | Purpose | Boundary |
|---|---|---|
| `ParserCompatibilityProfile` | Evidence/reference identity and supported extraction scope | versioned; invalidated by relevant change |
| `ParserRequestEnvelope` | Normalized adapter request metadata and safe source/revision references | no raw secret or arbitrary command |
| `TransportOutcomeReference` | Explicit Egress outcome consumed by parser | transport success alone is insufficient |
| `ParserAttemptOutcome` | Explicit attempt/result classification | no fabricated empty success |
| `NormalizedSearchExtraction` | Candidate geography/category/filter/context extraction | Beacon decides acceptance |
| `NormalizedListingCandidate` | Minimal listing candidate with field provenance/quality | Scan decides observation/business semantics |
| `ParserWarning` | Unsupported, uncertain, lossy or stale-evidence warning | never silently discarded |
| `ParserEvidenceReference` | Safe reference/fingerprint/counts/version | raw retention separately gated |
| `ParserReadModel` | Rebuildable diagnostics/projection | not provider or business authority |

## 8. Use-case families

### 8.1. Beacon preparation analysis

```text
Beacon-owned source reference
→ approved Egress transport request/outcome
→ parser response classification
→ normalized search extraction + warnings + evidence profile
→ Beacon Management acceptance/rejection decision
```

Parser does not create the Beacon or accept the snapshot.

### 8.2. Scan listing extraction

```text
Scan-owned run request + immutable Beacon revision reference
→ approved Egress transport request/outcome
→ parser page classification
→ normalized listing candidates + pagination/partial evidence
→ Scan Orchestration observation/baseline/diff decision
```

Parser does not store listing history or decide newness/price-change notification.

## 9. Public input families

Exact Python/wire schemas remain future task scope.

| Input family | Purpose |
|---|---|
| `AnalyzeAvitoSearchSourceRequest` | Analyze one Beacon-owned source reference under an explicit compatibility profile |
| `ParseAvitoSearchConfigurationRequest` | Extract normalized geography/category/filter/context candidates from a usable response |
| `ParseAvitoListingPageRequest` | Extract normalized listing candidates from one explicitly identified page response |
| `ParseAvitoListingBatchRequest` | Process independently classified page units with per-unit outcomes |
| `RevalidateParserCompatibilityRequest` | Compare current evidence/profile identity before dependent use |
| `ExplainParserOutcomeQuery` | Read safe outcome/provenance/warnings without raw sensitive payload |

Every request must carry or inherit:

- `contract_name` and `contract_version`;
- `message_id`, `correlation_id`, `causation_id` where applicable;
- logical producer;
- `account_id` and `beacon_id` when the operation is Beacon-scoped;
- immutable `configuration_revision_id` for scan extraction;
- parser compatibility/reference profile ID;
- safe source/transport outcome reference;
- idempotency key and normalized fingerprint for retryable/external-effect request orchestration;
- declared purpose: preparation or scan;
- bounded requested page/unit scope.

## 10. Public output families

| Output family | Meaning |
|---|---|
| `SearchSourceAnalysisOutcome` | usable, rejected, unavailable, restricted, malformed, incomplete, unsupported or ambiguous |
| `SearchConfigurationExtractionOutcome` | normalized candidate extraction, warnings, profile and evidence references or explicit failure |
| `ListingPageParseOutcome` | normalized listing candidates plus explicit page/result classification |
| `ListingBatchParseOutcome` | per-page/item outcomes with succeeded/failed/ambiguous counts |
| `ParserCompatibilityOutcome` | current, stale, changed-compatible, changed-breaking, missing, unavailable or disputed |
| `ParserOutcomeExplanation` | safe read-only provenance, reason codes and warnings |

A usable empty listing set is valid only when a future approved compatibility profile proves that:

- request was sent through an approved route;
- response was explicit and usable;
- required structure was present and validated;
- no restriction/CAPTCHA/malformed/incomplete/ambiguous signal exists;
- evidence is current for that scope;
- the parser can distinguish genuine empty from failure.

Until then, empty is not assumed clean.

## 11. Parser attempt outcome classes

At minimum:

- `NOT_SENT`;
- `TRANSPORT_UNAVAILABLE`;
- `TRANSPORT_AMBIGUOUS`;
- `RESPONSE_RECEIVED_UNCLASSIFIED`;
- `USABLE_RESPONSE`;
- `EXPLICIT_REJECTION`;
- `RATE_OR_ACCESS_RESTRICTED`;
- `CAPTCHA_OR_CHALLENGE`;
- `MALFORMED_RESPONSE`;
- `INCOMPLETE_RESPONSE`;
- `UNSUPPORTED_STRUCTURE`;
- `REFERENCE_STALE`;
- `REFERENCE_MISSING`;
- `REFERENCE_DISPUTED`;
- `PARTIAL`;
- `RESULT_AMBIGUOUS`.

Exact wire codes and HTTP mappings are not selected.

## 12. Compatibility/reference profile

A future `ParserCompatibilityProfile` must identify:

- profile ID and semantic version;
- applicable `reference_id` records;
- exact primary-reference commit where used;
- retrieval/effective dates;
- authority class and scope;
- response/page structure fingerprints or safe selectors after proof;
- supported extraction claims;
- unsupported claims;
- required fields and completeness rules;
- warning/error mappings;
- fixture IDs and Acceptance Matrix rows;
- revalidation triggers;
- lifecycle: current/stale/superseded/withdrawn/unavailable/disputed;
- compatibility classification for each change.

A profile does not convert an internal provider structure into an official public contract.

## 13. Source URL boundary

- Beacon Management owns the submitted URL and its persistence.
- Parser receives only a safe reference or bounded value required for an approved request.
- Source URL is untrusted input.
- Exact host/path/query/redirect validation policy remains blocked until approved.
- No source URL, query value, header or extracted parameter may become a shell command or arbitrary filesystem/network target.
- Parser output never overwrites the Beacon source URL.
- Canonicalization/equivalence cannot be guessed.

## 14. Egress Routing dependency

Parser Adapter consumes future Egress contracts; it does not own route selection or execution.

Required semantic sequence:

```text
parser request accepted
→ route/lease decision by Egress Routing
→ dispatch/send outcome
→ usable response or explicit transport outcome
→ parser classification/normalization
```

Rules:

- route/agent/lease IDs are semantic references, not host/IP aliases;
- parser does not choose fallback independently;
- heartbeat/alive route is not request success;
- `SENT_SUCCESS_RESPONSE` is not parser success until content validation completes;
- route failure/restriction/ambiguity remains explicit;
- unknown send state is reconcile-first and not blindly retried;
- cookies/session/request identity behavior remains separately gated;
- no Windows/server/network configuration is created by Run 16.

## 15. Response validation and completeness

A future usable-response classifier must prove, for the active profile:

- correct intended provider/product/scope;
- bounded response size and content handling;
- expected response class/content type where evidence supports it;
- required structural markers and completeness;
- absence of known restriction/CAPTCHA/challenge indicators;
- no contradictory error/body/status evidence;
- safe parsing limits and cancellation;
- parser profile currentness;
- explicit unsupported/unknown fields;
- safe evidence fingerprint/provenance.

HTML status `200`, parseable JSON, non-empty body or a recognized substring alone is insufficient.

## 16. Search configuration extraction

A normalized extraction may expose candidates for:

- geography/context;
- category/context;
- price bounds;
- structured filter keys and values;
- multivalue parameters;
- sort/pagination context where evidence permits;
- unsupported/uncertain parameters;
- normalization warnings;
- source/reference/profile provenance.

Rules:

- all values remain evidence-bound, not universal provider facts;
- repeated values are preserved as a collection and never silently replaced;
- extraction does not declare a filter user-editable; Filter Catalog/OD-009 owns that decision;
- country-wide support is not inferred; OD-010 remains open;
- exact parameter names/types/mappings require current evidence and fixtures;
- loss, conflict or ambiguity produces warning/failure, not silent normalization;
- Beacon Management decides whether to accept the extraction snapshot.

## 17. Listing normalization

A future `NormalizedListingCandidate` is minimal and evidence-bound. Potential field families include only those proven by the active profile and needed by Scan/Notification boundaries:

- provider listing reference candidate;
- title candidate;
- normalized price candidate plus raw-safe provenance;
- listing URL/reference;
- preview/image reference candidate;
- geography/category candidates;
- relevant exposed parameters;
- extraction timestamp/correlation;
- field-level availability/quality/warnings.

Run 16 does not declare any provider field stable or mandatory globally.

By default exclude:

- phone;
- seller contact/profile details;
- full description;
- views/analytics;
- hidden technical fields not required by approved contracts;
- raw HTML/provider payload;
- cookies/session material;
- unnecessary personal data.

Scan Orchestration owns listing observations, identity acceptance, baseline/diff and history. Parser merely returns candidates with provenance and uncertainty.

## 18. Pagination and partial outcomes

The primary reference’s later-page endpoint is an observation, not an approved contract.

Future pagination design must define:

- evidence/profile scope;
- page/continuation identity;
- maximum pages/items/bytes/time;
- ordering and duplicate semantics;
- per-page transport and parser outcomes;
- stop conditions;
- partial result policy;
- interrupted/ambiguous state;
- compatibility change behavior.

A batch never returns generic success when pages differ. Each page/unit has an explicit outcome. Partial usable data cannot erase a failed, restricted or ambiguous unit.

## 19. Beacon Management handoff

Parser returns `SearchConfigurationExtractionOutcome` with:

- source-reference correlation;
- profile/reference identity;
- normalized candidate snapshot;
- multivalue preservation evidence;
- unsupported/uncertain parameter evidence;
- warnings and failure class;
- safe response/provenance fingerprint;
- explicit usability classification.

Beacon Management alone:

- accepts/rejects the extracted snapshot;
- stores source/snapshot/override/revision state;
- applies ownership/authorization/entitlement rules;
- activates or changes a Beacon.

## 20. Scan Orchestration handoff

Parser receives a scan-owned request containing an immutable `beacon_id` + `configuration_revision_id` reference and returns explicit page/batch outcomes.

Parser does not:

- schedule the run;
- decide due time or interval;
- create authoritative run state;
- persist listing history;
- decide baseline, new listing or price-change event;
- enqueue notification;
- silently select a newer Beacon revision.

Run 17 must preserve parser outcome and revision provenance in authoritative scan/listing state.

## 21. Idempotency, retries and reconciliation

External request orchestration is retry-sensitive even when the provider operation is read-like because duplicate traffic, restriction and ambiguous send state matter.

Required rules:

- same key + same request + known terminal outcome returns original outcome reference where policy/storage exists;
- same key + different fingerprint returns `IDEMPOTENCY_MISMATCH`;
- missing key for retryable external attempt is rejected before effect;
- unknown dispatch/send state is `EXTERNAL_AMBIGUOUS`/reconcile-first;
- parser does not retry because a library default exists;
- retry count/delay/backoff/rate limits require explicit evidence and approval;
- retry cannot bypass route restriction, authorization, compatibility or evidence gates;
- partial batch retries identify exact units and preserve previous outcomes;
- no success event is emitted before parser outcome commit point if an authoritative attempt record is later introduced.

## 22. Error semantics

Applicable categories:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`/`FORBIDDEN` where caller scope applies;
- `NOT_FOUND` for permitted missing references;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `RATE_LIMITED`;
- `EXTERNAL_UNAVAILABLE`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

Errors include safe correlation, profile/reference identity, source category, retry class and redacted details. They do not expose credentials, cookies, raw tokens, private route details, full raw payloads or foreign-account data.

## 23. Security, privacy and evidence minimization

- No credentials, cookies, sessions, private keys or tokens in Git, contracts, fixtures, logs or reports.
- No browser-profile or foreign-host data access.
- No arbitrary command/script execution payload.
- External strings never reach shell interpolation.
- Response handling must be bounded against oversized/malformed/adversarial input after exact design.
- Logs use safe IDs, counts, classifications, fingerprints and redacted reason codes.
- Raw payload retention is prohibited by default until OD-013 and exact evidence policy are approved.
- Personal data collection is minimized to approved listing-card needs.
- Provider evidence capture must follow Reference Policy and copyright/data-minimization boundaries.
- A parser success cannot authorize account, Beacon, route or notification mutation by itself.

## 24. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Beacon Management source/revision contracts;
- Egress Routing transport contracts after Run 18 acceptance;
- Scan Orchestration request/outcome contracts after Run 17 acceptance;
- Reference Registry/Policy/Evidence package;
- HTTPX as selected-with-gate default client after Python 3.14 compatibility proof;
- Pydantic v2 at serialized/external boundaries;
- pytest, pytest-asyncio and RESpx for future deterministic tests;
- OpenTelemetry boundary after applicable instrumentation gate.

Deferred/blocked:

- exact parser libraries;
- HTML/JSON parsing libraries;
- browser automation;
- headless browser;
- proxy/VPN/session/cookie tooling;
- CAPTCHA services;
- provider SDK/internal endpoint client;
- persistence technology for attempt evidence;
- live traffic and route configuration.

Reference-specific libraries never become core dependencies merely because the reference uses them.

## 25. Fake dependencies and test doubles

Future approved fakes may model:

- `ReferenceProfileProvider`;
- `EgressTransportGateway`;
- `ResponseClassifier`;
- `SearchStateExtractor`;
- `SearchConfigurationNormalizer`;
- `ListingNormalizer`;
- `EvidenceFingerprintProvider`;
- `ParserAttemptRepository` only after persistence approval;
- `Clock`;
- `IdGenerator`;
- `SafeDiagnosticSink`.

Fakes use synthetic URLs, HTML/JSON fragments, listings, routes and profiles only. They do not prove current Avito behavior.

## 26. Required fixtures and test vectors

Minimum fixture IDs:

- `FX-APA-PROFILE-CURRENT-001`;
- `FX-APA-PROFILE-STALE-BLOCKS-001`;
- `FX-APA-PROFILE-MISSING-BLOCKS-001`;
- `FX-APA-PROFILE-BREAKING-CHANGE-001`;
- `FX-APA-NOT-SENT-001`;
- `FX-APA-ROUTE-UNAVAILABLE-001`;
- `FX-APA-TRANSPORT-AMBIGUOUS-001`;
- `FX-APA-EXPLICIT-REJECTION-001`;
- `FX-APA-RATE-RESTRICTED-001`;
- `FX-APA-CAPTCHA-BLOCKS-001`;
- `FX-APA-MALFORMED-HTML-001`;
- `FX-APA-MISSING-REQUIRED-STATE-001`;
- `FX-APA-INCOMPLETE-CONTEXT-001`;
- `FX-APA-UNSUPPORTED-STRUCTURE-001`;
- `FX-APA-GENUINE-EMPTY-PROVEN-001`;
- `FX-APA-FALSE-EMPTY-PROHIBITED-001`;
- `FX-APA-MULTIVALUE-PRESERVED-001`;
- `FX-APA-REPEATED-VALUE-LOSS-REGRESSION-001`;
- `FX-APA-UNSUPPORTED-FILTER-WARNING-001`;
- `FX-APA-COUNTRYWIDE-OD010-BLOCKED-001`;
- `FX-APA-LISTING-MINIMAL-001`;
- `FX-APA-LISTING-FIELD-UNCERTAIN-001`;
- `FX-APA-PHONE-EXCLUDED-001`;
- `FX-APA-RAW-PAYLOAD-REDACTED-001`;
- `FX-APA-EXTERNAL-STRING-NO-SHELL-001`;
- `FX-APA-IDEMPOTENT-REPLAY-001`;
- `FX-APA-IDEMPOTENCY-MISMATCH-001`;
- `FX-APA-PAGINATION-PARTIAL-001`;
- `FX-APA-BEACON-NO-MUTATION-001`;
- `FX-APA-SCAN-NO-HISTORY-MUTATION-001`.

Run 16 creates no fixture files and executes no tests.

## 27. Acceptance Matrix coverage

Run 16 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-004`, `AM-TECH-005`, `AM-TECH-007`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-BATCH-001`;
- `AM-DATA-003`–`AM-DATA-007` where applicable;
- `AM-SEC-001`–`AM-SEC-003`;
- `AM-EXT-001`–`AM-EXT-004`;
- `AM-AVITO-001`;
- `AM-EGRESS-001`;
- `AM-REF-001`–`AM-REF-004`;
- `AM-MIG-008`–`AM-MIG-009` where applicable;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime/provider/route/parser executions remain future gates and are not passed by this documentation run.

## 28. Allowed future changes

A later exact task may, after all gates:

- create parser-adapter package skeleton inside the approved layout;
- define transport-neutral parser request/outcome models;
- add synthetic compatibility-profile and response fixtures;
- implement deterministic response classification/extraction/normalization;
- prove multivalue preservation and false-empty prevention;
- integrate with accepted Beacon/Scan/Egress contracts;
- add bounded HTTPX behavior after compatibility and provider/access approval;
- add persistence only if an approved data/migration packet requires it;
- add observability with redaction and safe provenance.

## 29. Forbidden changes

Without new accepted evidence/decisions/tasks, this module must not:

- send live Avito requests or probe endpoints;
- treat Avito Ads API as consumer-search evidence;
- declare internal endpoint/embedded structures stable;
- choose supported filters, markets or cadence;
- choose cookies, sessions, headers, retries, proxy/VPN or CAPTCHA handling;
- collapse repeated filter values;
- convert failures/restrictions/ambiguity into empty success;
- collect phone, seller details, full descriptions or views by default;
- retain raw payloads without OD-013 policy;
- mutate Beacon, route, scan/listing or notification state;
- copy reference source with unclear reuse permission;
- add reference-specific dependencies to core;
- create product-code, dependency file, lockfile, executable test, fixture data file, migration, database, Docker/CI/CD, service, port, deploy or runtime configuration.

## 30. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `APA-01` | Semantic request/outcome contracts and synthetic fixtures | `NOT_STARTED` | exact implementation task and Platform primitives |
| `APA-02` | Compatibility profile and evidence revalidation | `BLOCKED` | exact proof/evidence task and current references |
| `APA-03` | Source URL validation/request boundary | `BLOCKED` | legal/access, URL/redirect/DNS policy |
| `APA-04` | Transport/response classification | `BLOCKED` | Run 18 Egress contracts and exact limits |
| `APA-05` | Search configuration extraction | `BLOCKED` | current profile, OD-009/OD-010 and mapping fixtures |
| `APA-06` | Multivalue-safe normalization | `NOT_STARTED` | synthetic contracts/fixtures and exact rules |
| `APA-07` | Minimal listing normalization | `BLOCKED` | field identity/mapping evidence and Scan contract |
| `APA-08` | Pagination and partial outcomes | `BLOCKED` | endpoint/access evidence and bounded policy |
| `APA-09` | Privacy, observability and reconciliation | `BLOCKED` | OD-013 and operations/evidence policy |
| `APA-10` | Full evidence/handoff | `NOT_STARTED` | applicable subtasks complete |

## 31. Task packet requirements

A future task must include:

- exact paths and parent SHA;
- stable task/iteration ID;
- exact compatibility/reference profile identity;
- allowed/forbidden provider scope;
- URL/request/redirect/DNS boundary;
- Egress contract and transport outcome classes;
- response completeness/classification rules;
- config/listing mappings and field provenance;
- multivalue semantics;
- page/batch limits and partial policy;
- idempotency, retry and reconciliation;
- privacy/redaction/raw-retention boundary;
- fixtures and matrix rows;
- isolated toolchain/dependency proof;
- no-live-traffic or separately approved proof-only scope;
- evidence/report format and exact final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 32. Report and handoff

A future implementation/proof report must include:

- task/iteration ID and exact commit SHA;
- changed paths and dependency/lock identity;
- compatibility profile/reference IDs, exact commits and retrieval status;
- request/route/transport/parser outcome evidence;
- response classification and completeness evidence;
- configuration/listing normalization and multivalue evidence;
- per-page/partial/ambiguous evidence;
- idempotency/reconciliation evidence;
- Beacon/Scan/Egress ownership-boundary evidence;
- privacy/redaction/sensitive-access confirmation;
- fixtures, Acceptance Matrix rows and exact results;
- live provider traffic statement (`NONE` unless separately authorized);
- prohibited-artifact check;
- blockers and next safe task;
- exact final marker for independent review.

## 33. Acceptance criteria

The playbook is acceptable only when:

- parser ownership and non-ownership are explicit;
- official, primary-reference and project-decision authority are separated;
- exact primary-reference commit is recorded;
- internal Avito structures/endpoints are not declared stable;
- source-analysis and scan-parse use cases are distinct;
- transport, parser and scan/business success are distinct;
- failure/restriction/CAPTCHA/malformed/incomplete/stale/ambiguous outcomes cannot become empty success;
- multivalue preservation is explicit;
- Beacon, Egress, Scan, Notification and Filter Catalog boundaries are explicit;
- stable fields, filters, markets, cadence, retries, sessions and retention are not guessed;
- contracts, idempotency, reconciliation, partial results, privacy, fakes, fixtures and matrix rows are named;
- roadmap remains blocked where evidence/decisions are missing;
- no code, live request, endpoint probe, dependency, lock, test, fixture file, migration, database, cookie/session/proxy config, Docker/CI/CD, deploy/runtime, service, port or sensitive access material is created;
- GitHub publication and exact server synchronization are independently verified.

## 34. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### APA-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 16 initial evidence-bound Avito Parser Adapter ownership and public contract families defined.
- Exact primary implementation evidence `AVITO-PRIMARY-PARSER-001` at commit `48441c352e36919abef13c436f41a3a62636da17` recorded without promoting it to official contract.
- Transport/parser/scan success separation, false-empty prohibition, multivalue preservation and module boundaries fixed.
- OD-009, OD-010, OD-011 and OD-013 remain unresolved.
- No parser implementation, provider request, endpoint probe, database, runtime or infrastructure artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
