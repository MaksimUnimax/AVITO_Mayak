Маяк Авито — Module 10 MAX Adapter Full Evidence and Handoff v1.0

status: final evidence/handoff for accepted governance, semantic contracts and synthetic deterministic tests scope

date: 2026-07-19

module: 10-max-adapter

roadmap step: MX-10

technical task: MX-10-MAX-MODULE-EVIDENCE-HANDOFF-20260719-01

latest accepted semantic/test SHA: 16c744f3e5479081b4ebe93fc95735016627198a

source-of-truth playbook: docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md

owner decision capture: docs/04-modules/10-max-adapter/OWNER_DECISIONS_v1.0.md

open-decision register: docs/00-governance/OPEN_DECISIONS.md

MX-10-MAX-MODULE-EVIDENCE-HANDOFF-20260719-01

1. Executive summary

Module 10 is complete only inside the current accepted governance, provider-boundary semantic contracts, synthetic deterministic fixtures/tests and evidence scope.

The module defines a transport-neutral but MAX-provider-specific boundary.

It does not implement a MAX bot, partner enrollment, moderation, credential handling, provider SDK, provider call, Webhook endpoint, Long Polling loop, Mini App frontend, persistence, queue, worker, service, scheduler, infrastructure bot, partner enrollment, moderation, credential handling, provider SDK, provider call, or deployment.

MAX remains a future and secondary channel.

Telegram remains the first practical channel.

MAX eligibility, verified profile, bot availability, moderation, credential availability and production provider access remain unproven and blocked.

The first MAX product surface remains personal chat only.

Groups and channels remain blocked.

MAX provider identities remain external references and are not internal account authority.

Identity & Access remains responsible for account resolution, linking, authorization and merge policy.

Notification Delivery remains responsible for the generic outbox, generic attempts, retry policy and generic delivery lifecycle.

MAX provider acceptance is not human read, click, final user-visible delivery or business success.

Unknown provider effect remains reconcile-first and must not be blindly retried.

No raw provider payload, real WebAppData, token, secret, private key, contact data, unnecessary personal data or legal/personal provider document is stored in the accepted artifacts.

This module is not production-ready.

Physical persistence and live provider integration remain blocked.

Upon independent acceptance of the MX-10 handoff commit, roadmap steps MX-00 through MX-10 are complete for the current semantic scope only.

2. Accepted SHA chain
Step	Accepted SHA	Commit subject	Accepted result
MX-01	a193d9f197272bfeeadd59dd0900abd5d6df8943	mx-01: correct MAX inline code delimiters	Governance-safe capture of eight owner decisions after append-only serialization corrections
MX-02	0a815fc53a2c67c3c9db990f9fdddb016b03118c	mx-02: add MAX semantic contract skeleton	Twelve authoritative records and initial provider-boundary invariants
Parallel main	abd5a5a2fa037a560b164bf2ab31f72ce622f4c5	tg-06: add telegram intent normalization boundary	Telegram-only parallel change preserved without becoming a Module 10 step
MX-03	8cc4173523a2278e4c9b3c8eb2a2b18efd4ec49f	mx-03: add MAX update intake semantics	Inbound update admission, intake and deduplication semantics
MX-04	8d0442690728b150f403556a861c1990b947a8e3	mx-04: add MAX input normalization semantics	Command, callback, button and deep-link normalization semantics
MX-05	1c4a4ec38ad5cb6058eecc70e63d405945f884a7	mx-05: add MAX Mini App validation semantics	Future server-side Mini App validation and Identity handoff boundary
MX-06	4f5c2f80e5eb6843ff0539f6beb80e6cc1cc53de	mx-06: add MAX outbound mapping semantics	Generic Notification attempt to MAX request/outcome mapping semantics
MX-07	6733806fc600e693d8fd19354cda8d05ee855cf7	mx-07: add MAX reconciliation semantics	Unknown-effect and reconcile-first semantics
MX-08	3ab2b7fb90046e1a67fa888f72c097d15e488c44	mx-08: add MAX safe read model semantics	Authorized safe diagnostics/read-model projection semantics
MX-09	189194177f543d7d35a67d9b3c77a61b8265c0af	mx-09: add MAX synthetic contract tests	Synthetic fixture manifest and deterministic contract tests
MX-09 correction	16c744f3e5479081b4ebe93fc95735016627198a	mx-09: correct MAX architecture import guard	Exact reusable import/runtime boundary guard with real negative controls

MX-01 technical-task identity is recorded in ADR-0023 and the canonical owner-decision document.

The final accepted MX-01 commit does not contain and was not required to contain a commit-message Technical-ID trailer.

Historical commits were not amended to manufacture missing trailers.

All Module 10 implementation and test commits above are ancestors of 16c744f3e5479081b4ebe93fc95735016627198a.

The Telegram parallel-main commit is preserved as a separate provider-module change and is not presented as MAX implementation authority.

No Module 10 commit rewrote unrelated parallel history.

No accepted Module 10 step used rebase, merge, cherry-pick, reset, amend, squash or force-push.

3. Accepted artifact inventory
Artifact	Step	Accepted role	Explicit non-authority
docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md	MX-00 through MX-10	Approved documentation playbook and ownership boundary	Not runtime or provider permission
docs/04-modules/10-max-adapter/OWNER_DECISIONS_v1.0.md	MX-01	Eight governance-safe owner decisions	Not proof of provider eligibility or production access
docs/00-governance/DECISION_LOG_APPEND_ONLY.md	MX-01	Append-only governance trace for owner-decision capture and serialization corrections	Not runtime configuration
src/mayak/modules/max_adapter/contracts.py	MX-02 through MX-08	Provider-specific semantic records, enums and validation matrices	Not ORM, wire payload, SDK or runtime
src/mayak/modules/max_adapter/__init__.py	MX-02 through MX-04	Stable package export surface and module identifier	No import-time provider side effect
tests/fixtures/max_adapter_semantic_vectors.json	MX-09	Synthetic-only deterministic fixture manifest	No recorded provider payload or real WebAppData
tests/contract/test_max_adapter_semantic_contract_exports.py	MX-09	Deterministic export, identity and enum evidence	No provider integration
tests/unit/test_max_adapter_semantic_contracts.py	MX-09	Contract validators and state-matrix evidence	No persistence, network or provider call
tests/architecture/test_max_adapter_semantic_boundaries.py	MX-09 correction	Exact production file/class/import/runtime boundary guard	Static evidence only, not runtime security implementation

Logical records remain logical records.

They are not physical tables, ORM models, queues, provider wire schemas, provider SDK objects or live transport requests.

4. Public semantic contract surface

The accepted authoritative record count is twelve:

MaxProviderIdentity

MaxAccountLinkReference

MaxEligibilityEvidenceReference

MaxUpdateIntakeRecord

MaxUpdateDeduplicationRecord

MaxCommandEnvelope

MaxContactValidationResult

MaxMiniAppValidationResult

MaxOutboundRequest

MaxProviderOutcome

MaxReconciliationRecord

MaxAdapterReadModel

The accepted supporting enum count is fifteen:

MaxEligibilityState

MaxUpdateIntakeState

MaxUpdateAdmissionState

MaxUpdateSourceKind

MaxUpdateStructuralClass

MaxUpdateDeduplicationState

MaxCommandSourceKind

MaxCommandSurfaceKind

MaxCommandNormalizationState

MaxContactValidationState

MaxMiniAppValidationState

MaxOutboundRequestState

MaxProviderOutcomeState

MaxRetryRecommendation

MaxReconciliationState

The accepted contracts export count is twenty-seven.

The accepted package export count is twenty-eight, including MODULE_ID.

The module identifier remains exactly 10-max-adapter.

All public records use frozen, extra-forbidden and whitespace-stripping Pydantic contract configuration.

No public contract grants runtime, persistence, authorization, retry-execution or provider-call authority.

5. MX-01 governance evidence

The accepted owner decisions are:

MAX is a future and secondary channel; Telegram remains first practical.

MAX eligibility, profile, bot and moderation remain unproven until safe evidence exists.

First MAX scope is personal chat only; groups and channels remain blocked.

MAX Mini App is a future server-side validation and handoff boundary only.

Phone/contact is not requested in the first MAX scope.

MAX inputs may map to common product intents but remain separate provider-specific untrusted inputs.

Production direction is Webhook under current evidence; Long Polling is development/test only and is not production fallback.

Provider acceptance is not human read or final business success; unknown effect is reconcile-first.

The initial capture technical task is MX-01-MAX-OWNER-DECISION-CAPTURE-20260719-01.

Append-only serialization corrections are recorded by ADR-0024, ADR-0025 and ADR-0026 under MX-01-MAX-OWNER-DECISION-SERIALIZATION-CORRECTION-20260719-01.

These decisions do not prove provider permission or production readiness.

6. MX-02 semantic skeleton evidence

MX-02 established the provider-specific semantic boundary without importing or mutating Identity, Notification or Telegram internals.

MAX provider identifiers remain external identifiers.

An account-link reference must agree with the verified MAX provider identity.

Proven eligibility requires safe evidence reference.

Verified Mini App identity requires server-side validation evidence.

Ambiguous provider outcome requires reconciliation and RECONCILE_FIRST.

No raw provider payload, token, contact value or provider runtime was introduced.

7. MX-03 inbound update and deduplication evidence

Inbound MAX provider data remains untrusted.

Webhook input is not trusted before authenticity evidence.

Long Polling input is not trusted merely because polling supplied it.

Production Webhook and development/test Long Polling are mutually exclusive.

Long Polling is not production fallback.

A polling marker is a cursor and is not business identity.

No universal stable MAX update identifier was invented.

Unsupported update families are safely ignored or rejected.

Replay does not create a second business effect.

Fingerprint conflict and identity ambiguity remain explicit.

No listener, endpoint, polling loop, persistence or provider call exists.

8. MX-04 command and interaction normalization evidence

Commands, callbacks, buttons and deep links remain separate MAX-specific untrusted inputs.

Telegram payload format is not MAX authority.

Client-visible callback or button payload is not authorization.

Deep-link data is not authorization.

Only personal-chat scope may normalize under the current owner decision.

Groups, channels and unknown surfaces remain blocked or unsupported.

MAX Adapter does not execute business actions.

MAX Adapter does not mutate Beacon or Account.

Exact command catalog, callback format, button UX and deep-link format remain open.

9. MX-05 Mini App validation evidence

Raw MAX WebAppData remains untrusted.

Server-side validation is mandatory for a verified result.

Verified result requires validation evidence and external MAX provider identity.

Non-verified result cannot carry a trusted provider identity.

Validated identity remains external and must pass through Identity & Access.

Mini App launch context is not authorization.

The accepted contracts contain no raw WebAppData value and no token material.

The auth-date freshness threshold remains unresolved.

No frontend, screen, launch URL, runtime endpoint or validation implementation exists.

10. MX-06 outbound mapping evidence

One generic Notification attempt may be represented as one MAX provider request intent.

The mapping consumes only safe generic Notification references and approved adapter-policy evidence.

MAX Adapter does not create a generic outbox.

MAX Adapter does not mutate a generic Notification attempt.

MAX Adapter does not decide the generic delivery lifecycle.

Provider acceptance is not human read, click, business success or final user-visible delivery proof.

Provider rejection, authentication failure, unavailability, rate limitation, malformed result, ambiguity and blocked state remain explicit.

Retry and reconciliation remain recommendations under Notification policy.

No live send, SDK, token, rendering implementation or provider request payload schema exists.

11. MX-07 unknown-effect and reconciliation evidence

Unknown effect is not success.

Unknown effect is not proven failure without evidence.

Ambiguous effect is reconciliation-first.

Blind retry is forbidden.

The idempotency reference remains required to prevent duplicate user-visible effect.

Resolution may prove no effect, effect, continuing ambiguity, subscription degradation or manual-review requirement.

Generic Notification success/failure and retry policy remain Notification Delivery authority.

No reconciliation execution, provider lookup, retry engine or manual-review workflow exists.

12. MX-08 safe diagnostics and read-model evidence

The read model is an authorized safe projection only.

User, support and admin audiences remain explicit.

Authorization evidence is required.

Only opaque safe references, safe reason codes, classifications and correlation/causation references are exposed.

Raw provider payload, raw WebAppData, token, secret, private key, phone/contact, legal document, private-message content, display-name inventory, username inventory, avatar inventory and chat-title inventory are excluded.

No retention policy is invented while OD-013 remains open.

The read model has no mutation, provider-call, retry, reconciliation, Identity-linking, Notification-state or UI authority.

No projection builder, query handler, support UI or admin UI exists.

13. MX-09 synthetic fixture and test evidence

The fixture manifest is synthetic-only.

The accepted manifest SHA-256 is:

7b9bce228502d58d8d2dc607e9837a7012ce8ad26807adc13dcf8adca89bdd49

The accepted fixture vector count is fifty-three.

The accepted MX-09 test-node increase is one hundred thirty-four.

The accepted full suite result after MX-09 and its correction is:

3811 passed

The fixture manifest contains no raw provider payload, raw WebAppData, token, secret, phone/contact, real provider identity or personal/legal data.

The deterministic tests cover:

exact exports and enum values;

all twelve authoritative records;

model immutability and unknown-field rejection;

identity-reference consistency;

eligibility matrices;

inbound intake and deduplication matrices;

personal-chat and blocked group/channel normalization;

no-contact first-scope policy;

Mini App validation matrices;

outbound request and provider-outcome matrices;

reconcile-first matrices;

safe read-model projection;

false-success prohibition;

no-blind-retry prohibition;

duplicate-effect prevention;

Identity and Notification ownership;

Telegram/MAX provider separation;

sensitive-data minimization.

The corrected architecture guard uses exact import allowlists.

It rejects unknown standard-library imports, unknown third-party imports, foreign project-module imports and forbidden relative imports.

Its negative and safe controls invoke the same reusable guard used for production sources.

The accepted production MAX package contains only:

src/mayak/modules/max_adapter/__init__.py

src/mayak/modules/max_adapter/contracts.py

14. Compatibility with Modules 01 through 09
Owning module	Compatibility preserved by MAX Adapter
01 Platform & Contracts	Uses common metadata/reference types and stable module boundary; no platform mutation
02 Identity & Access	MAX identity remains external; account resolution, linking, authorization and merge remain Identity authority
03 Entitlements & Billing	MAX provider input cannot grant tariff, entitlement, payment or subscription state
04 Beacon Management	MAX may normalize an intent but cannot create or mutate Beacon state
05 Avito Parser Access	MAX does not validate Avito URLs, parse listings or store raw Avito/provider payloads
06 Scan Orchestration	MAX does not calculate baseline, anchors, differences, listing state or recovery
07 Egress Routing	MAX does not choose Egress routes, leases, agents or transport state
08 Notification Delivery	Notification owns generic outbox, attempts, retry policy and generic delivery lifecycle
09 Telegram Adapter	Telegram and MAX payloads, identities and normalization remain separate provider-specific boundaries

Future Web Cabinet owns screens and web sessions.

Future Admin & Support owns operational UI and work-item execution.

MAX safe read models do not create UI or mutation authority.

15. Security and privacy evidence

The accepted Module 10 artifacts contain no:

raw MAX bot token;

webhook secret;

private key;

provider credential;

real raw MAX provider payload;

real Mini App WebAppData;

real phone/contact data;

private-message archive;

unnecessary profile data;

legal or personal provider document;

live provider response body.

Safe references are opaque.

Provider identity does not imply internal account authority.

Client-visible input does not imply authorization.

The fixture and test scope is synthetic and deterministic.

No network is required by accepted semantic tests.

16. Forbidden artifact absence

The accepted Module 10 scope contains no:

MAX partner-profile creation;

MAX bot creation;

moderation submission;

token storage or rotation implementation;

Webhook subscription;

Webhook endpoint;

Long Polling loop;

Mini App frontend;

Web Cabinet screen;

provider SDK;

provider HTTP client;

live provider call;

physical database schema;

ORM model;

migration;

queue;

broker;

worker;

scheduler;

service;

listener;

runtime configuration;

port;

domain;

TLS or certificate configuration;

Docker change;

CI/CD change;

deployment change;

dependency or lockfile change.

17. Remaining open decisions

The following numbered decisions remain open where applicable:

OD-006 — exact phone/password and recovery policy;

OD-007 — whether phone is ever required;

OD-008 — account merge policy;

OD-012 — channels beyond Telegram/MAX;

OD-013 — retention/deletion periods for history, logs and personal data;

OD-014 — future Web Cabinet screen composition and analytics depth.

Module-specific unresolved decisions include:

whether the owner satisfies MAX partner eligibility;

verified-profile requirements;

bot creation and naming;

moderation submission and acceptance;

credential availability and storage;

production provider access;

endpoint/domain/TLS/port/certificate ownership;

Webhook operations topology and acknowledgement point;

approved Long Polling development/test environments;

supported provider update families;

future group/channel support;

command catalog;

button/callback UX and payload format;

deep-link parameter format;

future contact-sharing adoption;

maximum accepted Mini App auth-date age;

Mini App launch surfaces and screens;

provider retry count, delays, backoff and rate budgets;

provider payload retention/redaction granularity;

adapter persistence schema, indexes and constraints;

provider SDK/library and transport implementation.

Open means blocked.

No future task may invent these values.

18. Runtime and provider gates still blocked

A future runtime step requires separate accepted evidence and exact authorization for at least:

MAX partner eligibility.

Verified profile or equivalent provider prerequisite.

Bot creation and moderation status.

Secret-presence and credential-storage policy.

Exact provider documentation revalidation.

Provider SDK or direct transport choice.

Personal-chat recipient and authorization rules.

Webhook endpoint ownership and security controls.

Long Polling development/test environment policy, if used.

Durable intake, deduplication and marker-advancement commit point.

Persistence schema and migration gate.

Notification runtime integration.

Retry, reconciliation and rate-policy values.

Logging, redaction, retention and deletion policy.

Operations, monitoring, deployment and rollback evidence.

This handoff authorizes none of those runtime steps.

19. Parallel-main and publication evidence

GitHub main remained the source of truth.

Every Module 10 publish used an exact expected-base gate.

The Telegram parallel-main commit between MX-02 and MX-03 was preserved and independently scoped.

Module 10 did not rewrite parallel history.

Historical MX-01 commits were not amended to add commit trailers that were not part of their accepted publication.

No accepted step pushed over a changed main.

No accepted step used rebase, merge, cherry-pick, reset, amend, squash or force-push.

Project publication used the project-specific deploy key with IdentitiesOnly=yes.

No private key content was exposed.

20. Final semantic acceptance statement

The latest accepted semantic/test SHA before this handoff is:

16c744f3e5479081b4ebe93fc95735016627198a

At that SHA:

governance capture is present;

twelve authoritative records are present;

fifteen supporting enums are present;

twenty-seven contracts exports are present;

twenty-eight package exports are present;

fifty-three synthetic fixture vectors are present;

the corrected reusable architecture boundary guard is present;

the full deterministic test suite reports 3811 passed;

no provider runtime, persistence, dependency, infrastructure or secret artifact is authorized or present in Module 10 scope.

Upon independent GitHub acceptance of the commit adding this document, Module 10 roadmap steps MX-00 through MX-10 are complete for the accepted governance/semantic/synthetic-test/evidence scope.

This completion does not authorize MAX production implementation.
