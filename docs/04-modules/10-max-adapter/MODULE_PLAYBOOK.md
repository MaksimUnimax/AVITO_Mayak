# Маяк Авито — MAX Adapter Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 21 of 24
**Дата:** 2026-07-08
**Модуль:** `10-max-adapter`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Notification Delivery Module Playbook v1.0, Egress Routing Module Playbook v1.0, Telegram Adapter Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, MAX Reference Policy v1.0, current official MAX API/Webhook/Long Polling/Mini App/partner documentation rechecked for Run 21, and OPEN_DECISIONS.md.
**Не является:** MAX bot implementation, partner enrollment, moderation submission, webhook subscription, Long Polling loop, Mini App implementation, provider SDK choice, credential/token policy, physical database schema, migration, live provider call, runtime configuration, endpoint/domain/certificate/port setup, notification worker, message template catalog, legal opinion or permission to implement.

---

## 1. Назначение

MAX Adapter владеет provider-specific boundary between MAX platform surfaces and internal project contracts.

Модуль отвечает на вопросы:

- как MAX eligibility/moderation gates отделяются от product requirements;
- как MAX inbound events become verified, normalized adapter events;
- как Webhook production boundary and Long Polling development/test boundary are preserved;
- как MAX user/chat/message/update-related identifiers remain external provider identifiers;
- как commands, buttons, callbacks, contact requests and Mini App launch data are classified before business dispatch;
- как outbound Notification attempts are mapped to MAX API requests and provider outcomes;
- как provider duplicate/retry/unknown-effect cases are preserved and reconciled;
- как MAX-specific UI adaptation is separated from Account, Beacon, Scan, Egress, Notification and Telegram ownership.

Модуль не создаёт аккаунты напрямую, не владеет generic notification outbox, не создаёт Beacons, не рассчитывает baseline/diff, не выбирает Egress route и не доставляет сообщения вне accepted Notification contracts.

## 2. Границы и владение

MAX Adapter owns semantic mutation authority for:

- MAX provider identity mapping records;
- MAX eligibility/moderation evidence references;
- MAX bot/event intake records;
- MAX Webhook receipt evidence after mode/operations approval;
- MAX Long Polling marker evidence for allowed development/test contexts;
- MAX event replay/deduplication state;
- MAX command/callback/button/deep-link normalization;
- MAX contact-request verification result references where later approved;
- MAX Mini App launch-data validation result references;
- MAX-specific delivery request mapping;
- MAX provider outcome mapping;
- MAX provider-side message/callback correlation references;
- MAX-specific safe diagnostics and adapter read models.

It does not own:

- internal `Account`, account merge, roles, sessions or credentials;
- tariff, subscription, entitlement grant or payment state;
- Beacon source URL, configuration, revision or lifecycle;
- Parser extraction, Avito provider evidence or listing candidates;
- Scan runs, observations, baseline, difference or listing state;
- Egress routes, agents, leases or transport state;
- generic Notification source intake, outbox, delivery attempts or delivery lifecycle;
- Telegram provider mapping;
- Admin/Support work items;
- Web Cabinet screens or web sessions;
- Filter Catalog definitions;
- MAX bot token raw material or provider secrets;
- provider payload retention while OD-013 remains unresolved;
- legal qualification for partner eligibility.

Only MAX Adapter may authorize MAX-provider mapping state. It must use public contracts of Identity & Access, Notification Delivery, Beacon Management and other owning modules and must never write their internal records directly.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted Identity & Access, Notification Delivery and Telegram Adapter playbooks.
4. MAX Reference Policy v1.0 and current official MAX documentation for exact provider behavior.
5. This playbook.
6. Future exact implementation task and accepted evidence.
7. Runtime evidence for one exact release/environment/provider operation.

Official MAX API, Webhook, Long Polling, Mini App validation and partner documentation were rechecked for Run 21 only to preserve provider-evidence boundaries. This playbook records adapter semantics and does not create a partner profile, bot, token, webhook, API call, SDK, endpoint, Mini App, certificate, trust-store change or runtime.

## 4. Confirmed decisions

1. MAX user/chat/message/update-related IDs are external provider identifiers and never replace internal `account_id`, `beacon_id`, `notification_outbox_item_id` or `notification_attempt_id`.
2. MAX Adapter owns provider-specific mapping and normalization only.
3. Identity & Access owns account resolution, identity linking, role/session/authorization and merge policy.
4. Notification Delivery owns generic outbox, delivery attempts, delivery lifecycle and acceptance of provider outcome into generic notification state.
5. MAX Adapter may request account resolution only after provider identity is verified under MAX rules and project contracts.
6. Automatic account merge by username, display name, avatar, phone/contact, chat title, group membership or weak correlation is forbidden.
7. MAX partner eligibility, verified profile and moderation are explicit gates; project eligibility is not assumed.
8. MAX production update delivery uses Webhook under current official evidence; Long Polling is development/test only and not production fallback.
9. Active Webhook and Long Polling are mutually exclusive.
10. MAX Webhook endpoint requirements, including HTTPS/443/TLS/full chain and `X-Max-Bot-Api-Secret` verification, are operations/security gates, not Run 21 runtime permission.
11. MAX Long Polling `marker` is a cursor, not business identity or universal event idempotency key.
12. MAX generic `Update` evidence does not prove one universal stable update identifier equivalent to Telegram `update_id`.
13. Deep-link/callback/button/message/contact/Mini App payloads are untrusted input until validated by provider and project contracts.
14. MAX Mini App launch data requires server-side validation using official `WebAppData` rules before it can provide a verified external identity reference.
15. MAX API success confirms only the documented provider operation/result class; it does not prove human read, click, final user-visible delivery or business success.
16. Unknown MAX send/update effect is reconcile-first and is never blindly retried.
17. Unsupported update/surface types are ignored safely or rejected explicitly without business effect.
18. MAX adapter diagnostics and records exclude raw tokens, webhook secrets, private keys, unnecessary personal data and raw provider payloads by default.
19. Run 21 does not decide command catalog, button UX, Mini App screens, chat/channel support, retry values, rate budgets, token storage or retention.
20. Open decisions and provider-specific defaults receive no fabricated values.
21. Run 21 creates no bot, token, webhook, Long Polling loop, endpoint, provider call, SDK, queue, worker, database table, migration, service, port, certificate, trust-store change or runtime.

## 5. Open decisions and blockers

Run 21 does not resolve:

- `OD-006` — exact phone+password and recovery policy where MAX identity might later link to Web Cabinet;
- `OD-007` — when phone is required, if ever;
- `OD-008` — account merge policy;
- `OD-012` — future channels beyond Telegram/MAX;
- `OD-013` — retention/deletion of provider payloads, adapter records, delivery logs and personal data;
- `OD-014` — future Web Cabinet screen composition where MAX Mini App handoff may interact with web UI;
- whether the project owner satisfies MAX partner eligibility;
- partner profile, bot name, moderation submission or launch timing;
- endpoint/domain/TLS/port/certificate ownership;
- Webhook operations topology;
- Long Polling allowed development/test environments;
- MAX bot token storage, rotation, revocation and delivery;
- exact supported update types and chat/channel surfaces;
- command catalog and button/callback UX;
- deep-link parameter formats;
- contact-request adoption and phone trust policy;
- Mini App launch surfaces and screens;
- maximum accepted Mini App `auth_date` age;
- provider retry count, delay, backoff and rate budgets;
- provider payload retention and redaction granularity;
- adapter persistence schema, indexes and constraints;
- exact SDK/library choice and transport implementation.

Open means blocked. No implementation, test, fixture, runtime, bot, token, webhook, endpoint, provider call, certificate, trust-store, moderation or UI task may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, queues, wire schemas or provider payloads.

| Record | Purpose | Required boundary |
|---|---|---|
| `MaxProviderIdentity` | External MAX user/chat identity reference | not internal account authority by itself |
| `MaxAccountLinkReference` | Link between provider identity and internal account after Identity contract approval | owned with Identity handoff; no weak merge |
| `MaxEligibilityEvidenceReference` | Reference to accepted partner/moderation evidence | no legal/personal data in public repo |
| `MaxUpdateIntakeRecord` | One provider update receipt/reference | provider scope and normalized fingerprint |
| `MaxUpdateDeduplicationRecord` | Duplicate/replay protection where event identity/fingerprint is sufficient | no invented universal update id |
| `MaxCommandEnvelope` | Normalized command/callback/button/deep-link intent | untrusted until contract validation |
| `MaxContactValidationResult` | Future validated contact-sharing result where approved | not automatic account merge or phone policy |
| `MaxMiniAppValidationResult` | Server-side validation result for raw `WebAppData` | no client-side trust |
| `MaxOutboundRequest` | Adapter mapping of one Notification attempt to MAX request intent | not generic outbox authority |
| `MaxProviderOutcome` | Explicit MAX result/failure/ambiguity mapping | not delivery success until Notification accepts it |
| `MaxReconciliationRecord` | Evidence resolving unknown provider effect | no blind retry |
| `MaxAdapterReadModel` | Safe projection for diagnostics/support | not mutation authority |

## 7. Semantic identifiers and scope

- `max_bot_ref` identifies the logical MAX bot/provider scope without exposing token material.
- `max_update_reference` identifies the provider update evidence available for one event family; it is not assumed globally stable.
- `max_marker` is a Long Polling cursor and not business identity.
- `max_user_id`, `max_chat_id` and `max_message_id` are external provider identifiers.
- `max_callback_reference` and related provider IDs remain provider-specific.
- `max_delivery_request_id` identifies adapter-side request mapping under one Notification attempt.
- `correlation_id` and `causation_id` connect Identity, Notification and adapter evidence.

Identifiers do not reveal raw tokens, private keys, webhook secrets, full provider payloads or unnecessary personal data. Exact internal encoding remains future task scope.

## 8. Eligibility and moderation boundary

MAX partner and bot availability is a prerequisite gate, not a project assumption.

Rules:

- no partner profile or moderation state is created by this playbook;
- no legal/person documents are stored in public Git, prompts or ordinary reports;
- bot availability and user access are not assumed until accepted evidence exists;
- eligibility evidence may only be represented by safe references and statuses;
- inability to prove eligibility blocks MAX implementation planning but does not alter the target product model;
- this playbook is not a legal opinion and does not select organizational form.

## 9. Inbound update boundary

MAX inbound processing has the following semantic sequence after an allowed mode/environment is selected:

```text
provider event received through Webhook or allowed Long Polling
→ provider-scope authenticity/mode gate
→ raw payload structural classification
→ event family identity/fingerprint recorded
→ duplicate/replay/idempotency evaluation
→ MAX-specific normalization
→ Identity/Notification/Beacon public contract dispatch only if allowed
→ explicit adapter outcome
```

Rules:

- webhook payload is not trusted until provider-authenticity checks pass;
- Long Polling payload is not trusted merely because it came from polling;
- unsupported event type produces safe ignored/rejected outcome;
- provider display names, usernames, phone/contact, chat titles and avatars are not account keys;
- client-visible buttons and callback payloads are not authorization;
- duplicate update replay returns/references original adapter outcome without second business effect;
- incompatible replay/fingerprint mismatch is conflict or ambiguity, not a new action;
- absence of a universal stable event identifier keeps ambiguity explicit.

## 10. Webhook boundary

Run 21 does not create a Webhook subscription. If a future task selects it, the adapter must define:

- endpoint ownership and environment boundary;
- HTTPS/domain/certificate/port gate;
- full TLS chain/trust-store/certificate decision;
- secret generation, storage and verification policy;
- constant-time comparison for `X-Max-Bot-Api-Secret` or stricter approved mechanism;
- durable acceptance/acknowledgement point;
- duplicate webhook delivery idempotency;
- automatic unsubscribe/degraded-state handling;
- drop-pending and mode-transition behavior;
- safe failure response semantics;
- no raw token/secret in URL, logs, reports or fixtures.

HTTP `200` acknowledgement is not business success. Non-200/timeout retry behavior is expected provider behavior and must not produce duplicate business effects.

## 11. Long Polling boundary

Run 21 does not create a polling loop. If a future task selects Long Polling, it is allowed only where current evidence and operations policy permit development/test usage.

The adapter must define:

- allowed environment class;
- polling ownership and scheduler/worker boundary;
- marker persistence and advancement after durable adapter acceptance point;
- replay after interruption;
- mode transition from/to Webhook;
- timeout/limit/interval values after approved policy;
- no process-local marker as source of truth;
- no production fallback by convenience.

Passing no marker or `null` does not prove complete history. `marker` advancement marks previous provider updates read and therefore must not happen before safe internal processing.

## 12. Mini App boundary

Run 21 does not implement MAX Mini App screens. If a future task uses MAX Mini Apps:

- client-visible launch fields are display/input context only and are not trusted;
- backend receives raw `WebAppData` evidence from the launch URL/client boundary;
- validation follows official extraction/canonicalization/HMAC rules or later accepted official mechanism;
- `auth_date` freshness threshold must be selected by future security/product policy;
- validation failure, stale data or missing hash yields explicit unauthenticated/rejected result;
- validated MAX user ID remains an external provider identity reference;
- account linking still uses Identity & Access policies and challenges;
- Mini App UI state does not bypass server-side authorization.

## 13. Contact and phone boundary

Official MAX contact-sharing mechanics may later provide verified contact evidence, but Run 21 does not adopt phone collection.

Rules:

- phone requiredness remains OD-007;
- contact request adoption requires separate product/security/privacy decision;
- contact hash validation does not merge accounts automatically;
- forwarded or manually shared contact data without provider-verifiable hash is not equivalent;
- phone/contact data is personal data and retention remains OD-013;
- no contact data belongs in fixtures, prompts or ordinary logs.

## 14. Outbound delivery boundary

MAX Adapter maps a Notification attempt to MAX provider request semantics.

It may consume from Notification Delivery:

- `notification_outbox_item_id`;
- `notification_attempt_id`;
- target/channel reference;
- safe message/card references;
- delivery purpose and correlation;
- idempotency/fingerprint;
- adapter policy references.

It returns to Notification Delivery:

- explicit provider request classification;
- provider response/result reference;
- MAX message/callback correlation where available;
- accepted-success, accepted-failure or ambiguity class;
- retry/reconciliation recommendation under policy;
- safe reason/evidence references.

Rules:

- adapter does not create generic outbox items;
- adapter does not mark generic Notification delivery success by itself;
- provider successful result is mapped to provider accepted result, not human read/ack;
- HTTP/provider rejection, authentication failure, rate limit, transport failure and malformed response remain explicit failures;
- possible-send-without-result remains ambiguous/reconcile-first;
- provider message IDs may be stored only in approved scoped mapping/delivery state.

## 15. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `RecordMaxEligibilityEvidenceCommand` | Attach safe eligibility/moderation evidence reference after owner-approved proof |
| `IngestMaxWebhookUpdateCommand` | Accept/reject one provider update through Webhook |
| `RecordMaxLongPollingBatchCommand` | Record a development/test Long Polling batch and marker evidence after approval |
| `NormalizeMaxCommandCommand` | Convert command/callback/button/deep-link input to a project command envelope |
| `ValidateMaxContactShareCommand` | Validate contact-sharing evidence only after product/privacy approval |
| `ValidateMaxMiniAppDataCommand` | Validate raw MAX WebAppData and return provider identity reference |
| `ResolveMaxIdentityCommand` | Ask Identity & Access to resolve/link verified MAX identity |
| `MapNotificationAttemptToMaxCommand` | Build provider request intent from a Notification attempt |
| `RecordMaxProviderOutcomeCommand` | Attach explicit MAX provider outcome to the adapter request |
| `ReconcileMaxProviderEffectCommand` | Resolve unknown inbound/outbound MAX effect |
| `GetMaxAdapterEventQuery` | Read safe adapter event/intake projection |
| `ExplainMaxAdapterDecisionQuery` | Explain eligibility, authenticity, replay, normalization and outcome decision |

Mutation-capable inputs require mandatory common contract metadata, authorization scope where applicable, idempotency key and normalized fingerprint.

## 16. Public output families

| Output family | Meaning |
|---|---|
| `MaxEligibilityOutcome` | proven, unproven, rejected, expired, blocked or unsupported |
| `MaxUpdateIntakeOutcome` | accepted, replayed, rejected, unsupported, duplicate, ambiguous or blocked |
| `MaxAuthenticityOutcome` | verified, missing-secret, mismatched-secret, not-applicable, rejected or blocked |
| `MaxCommandNormalizationOutcome` | normalized, ignored, unsupported, invalid, ambiguous or blocked |
| `MaxContactValidationOutcome` | verified, rejected, unsupported, policy-blocked or ambiguous |
| `MaxMiniAppValidationOutcome` | verified, rejected, stale, malformed, missing-hash or blocked |
| `MaxIdentityResolutionOutcome` | resolved-account, new-account-requested, link-challenge-required, rejected or ambiguous |
| `MaxOutboundMappingOutcome` | request-prepared, blocked, unsupported-target, invalid-content or ambiguous |
| `MaxProviderOutcomeResult` | provider-accepted, provider-rejected, auth-failed, unavailable, rate-limited, malformed, ambiguous or blocked |
| `MaxReconciliationOutcome` | resolved-no-effect, resolved-effect, remains-ambiguous, subscription-degraded or manual-review-required |
| `MaxAdapterReadResult` | authorized safe provider-adapter projection |

Outputs remain framework, SDK, persistence, queue and provider transport neutral.

## 17. Mandatory outcome classes

At minimum:

- `ELIGIBILITY_UNPROVEN`;
- `MODERATION_NOT_ACCEPTED`;
- `NOT_RECEIVED`;
- `AUTHENTICITY_FAILED`;
- `TLS_OR_ENDPOINT_FAILED`;
- `UNSUPPORTED_UPDATE`;
- `DUPLICATE_OR_UNKNOWN_IDENTITY`;
- `NORMALIZED_UPDATE_ACCEPTED`;
- `CONTACT_VALIDATION_BLOCKED`;
- `MINI_APP_VALIDATION_FAILED`;
- `IDENTITY_RESOLUTION_BLOCKED`;
- `PROVIDER_REQUEST_NOT_SENT`;
- `PROVIDER_ACCEPTED`;
- `PROVIDER_REJECTED`;
- `PROVIDER_AUTH_FAILED`;
- `PROVIDER_UNAVAILABLE`;
- `RATE_LIMITED_OR_RESTRICTED`;
- `MALFORMED_OR_UNUSABLE_RESPONSE`;
- `PROVIDER_EFFECT_AMBIGUOUS`;
- `SUBSCRIPTION_DEGRADED_OR_UNSUBSCRIBED`;
- `RECONCILIATION_REQUIRED`.

Exact wire codes and provider payload fields are not selected.

## 18. False-success prohibition

None of the following may become clean business success or notification delivery success:

- partner eligibility or moderation not proven;
- missing or mismatched webhook secret where webhook mode requires it;
- TLS/endpoint/subscription failure;
- unsupported update type;
- Long Polling marker advanced before durable acceptance;
- no universal event identity where one is required;
- unvalidated callback/button/deep-link/message/contact payload;
- unvalidated MAX Mini App launch data;
- provider display name, username, phone/contact or chat title match;
- contact hash evidence used as account merge;
- provider successful response without Notification acceptance of provider outcome;
- request may have been sent but result is unknown;
- provider explicit rejection/authentication failure/rate limit;
- malformed/incomplete response;
- ambiguous MAX effect;
- Egress transport success without MAX provider outcome;
- reconciliation incomplete.

## 19. Identity & Access dependency

MAX Adapter supplies verified provider identity evidence to Identity & Access. Identity owns account resolution, account creation semantics, linking and authorization.

Rules:

- `max_user_id` is not `account_id`;
- `max_chat_id` is not account ownership;
- username, first/last name, phone/contact, avatar and chat title are not merge keys;
- linking another identity requires Identity-owned challenge semantics;
- OD-006, OD-007 and OD-008 remain unresolved;
- adapter cannot create a second user database;
- protected actions require server-side actor context and role/ownership checks.

## 20. Notification Delivery dependency

Notification Delivery owns source events, outbox items, attempts and generic delivery lifecycle. MAX Adapter maps one approved attempt to MAX provider request/outcome.

Rules:

- MAX Adapter does not create generic notification events;
- MAX Adapter does not create outbox work;
- provider accepted result is returned to Notification for acceptance;
- provider failure or ambiguity is explicit;
- retry/reconciliation uses Notification idempotency and provider evidence;
- delivery history cannot include raw token/secret or unnecessary payload.

## 21. Egress dependency

If MAX provider calls later use Egress or platform transport evidence, MAX Adapter must preserve route/transport correlation but does not own Egress state.

Rules:

- adapter does not choose private route independently;
- adapter does not mutate route health/quarantine;
- Egress transport success is not MAX provider success;
- ambiguous Egress state remains explicit;
- exact transport/route technology remains Egress/operations scope.

## 22. Telegram Adapter separation

Telegram Adapter and MAX Adapter are separate provider modules.

Rules:

- Telegram behavior is not evidence for MAX;
- MAX behavior is not evidence for Telegram;
- provider IDs are not interchangeable;
- shared generic notification state belongs to Notification Delivery;
- shared account identity belongs to Identity & Access;
- provider-specific callback, Mini App, webhook and message semantics remain in their own adapters.

## 23. Security, privacy and retention

- MAX bot token is a secret and never appears in Git, prompts, ordinary reports, fixtures, URLs or logs.
- Webhook secret material is represented only by safe references/classes.
- Raw provider payloads are not ordinary logs or fixtures.
- Store only approved provider IDs and minimized fields required by contracts.
- Private message archives, group/channel member inventories, contact requests, phone numbers and unnecessary profile content are not collected by default.
- Logs use safe IDs, outcome classes, reason codes, provider scope and correlation IDs.
- External strings never become shell commands.
- Retention, deletion, archive and compaction remain OD-013.
- A retention/deletion implementation cannot be invented by agents.

## 24. Observability semantics

Future minimum safe signals:

- provider bot scope reference;
- eligibility/moderation state class;
- update/request/attempt identities;
- update type and supported/unsupported class;
- authenticity validation result;
- replay/dedup/idempotency result;
- normalized command family;
- Mini App validation class;
- contact-validation class where approved;
- account-resolution outcome class;
- outbound provider result class;
- subscription degraded/unsubscribed state;
- retry/reconciliation state;
- safe reason code and latency;
- no raw token, secret, private payload, legal/personal documents or unnecessary personal data.

A verified partner profile, green webhook endpoint, polling response, provider successful response or Egress transport success does not prove internal business success.

## 25. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity & Access provider identity contracts;
- Notification Delivery outbox/attempt contracts;
- Egress correlation where applicable;
- MAX Reference Policy and current official MAX provider evidence;
- PostgreSQL/SQLAlchemy/Psycopg after physical schema approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- HTTPX only if an exact adapter implementation task selects it within the Technical Baseline.

Deferred/blocked:

- provider SDK/library choice;
- Webhook runtime mode and endpoint;
- Long Polling development/test loop;
- partner enrollment, bot creation and moderation;
- token/secret storage product;
- endpoint/domain/TLS/port/certificate/trust-store setup;
- Mini App hosting and frontend;
- command catalog and templates;
- retry/backoff/rate values;
- persistence schema/migrations;
- services/deploy/runtime.

No provider runtime is introduced by this playbook.

## 26. Fake dependencies and test doubles

Future approved fakes may model:

- `MaxEligibilityEvidenceGateway`;
- `MaxWebhookRequestVerifier`;
- `MaxUpdateSource`;
- `MaxMarkerStore`;
- `MaxUpdateDeduplicationStore`;
- `MaxMiniAppDataVerifier`;
- `MaxContactShareVerifier`;
- `MaxProviderIdentityGateway`;
- `IdentityAccountResolver`;
- `NotificationAttemptReader`;
- `NotificationOutcomeSink`;
- `MaxProviderClientFake`;
- `EgressCorrelationReader`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic provider IDs, updates, markers, commands, Mini App data, contact payloads, accounts, notification attempts and provider outcomes only. They do not prove MAX live behavior, eligibility, moderation, token validity, webhook reachability, Mini App hosting or production delivery.

## 27. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-INTERRUPT-UNKNOWN-001`;
- `FX-EXT-SUCCESS-001`;
- `FX-EXT-REJECTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-SEC-PROVIDER-VERIFY-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-PERSONAL-MINIMIZATION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-CHANGED-BREAKING-001`;
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-MAX-ELIGIBILITY-UNPROVEN-BLOCKED-001`;
- `FX-MAX-MODERATION-NOT-ACCEPTED-001`;
- `FX-MAX-WEBHOOK-SECRET-VALID-001`;
- `FX-MAX-WEBHOOK-SECRET-MISSING-001`;
- `FX-MAX-WEBHOOK-SECRET-MISMATCH-001`;
- `FX-MAX-WEBHOOK-TLS-ENDPOINT-BLOCKED-001`;
- `FX-MAX-WEBHOOK-RETRY-DUPLICATE-001`;
- `FX-MAX-SUBSCRIPTION-UNSUBSCRIBED-001`;
- `FX-MAX-LONGPOLLING-PROD-BLOCKED-001`;
- `FX-MAX-LONGPOLLING-MARKER-AFTER-COMMIT-001`;
- `FX-MAX-LONGPOLLING-MARKER-PRECOMMIT-BLOCKED-001`;
- `FX-MAX-UPDATE-NO-UNIVERSAL-ID-AMBIGUOUS-001`;
- `FX-MAX-UPDATE-FINGERPRINT-REPLAY-001`;
- `FX-MAX-UNSUPPORTED-UPDATE-IGNORED-001`;
- `FX-MAX-COMMAND-NORMALIZED-001`;
- `FX-MAX-CALLBACK-UNTRUSTED-001`;
- `FX-MAX-CONTACT-POLICY-BLOCKED-001`;
- `FX-MAX-CONTACT-HASH-NOT-MERGE-001`;
- `FX-MAX-MINIAPP-WEBAPPDATA-VALID-001`;
- `FX-MAX-MINIAPP-WEBAPPDATA-REJECTED-001`;
- `FX-MAX-MINIAPP-AUTHDATE-STALE-BLOCKED-001`;
- `FX-MAX-IDENTITY-RESOLVE-VERIFIED-001`;
- `FX-MAX-WEAK-MERGE-FORBIDDEN-001`;
- `FX-MAX-OUTBOUND-OK-NOT-READ-001`;
- `FX-MAX-OUTBOUND-REJECTED-001`;
- `FX-MAX-OUTBOUND-AMBIGUOUS-RECONCILE-001`;
- `FX-MAX-TOKEN-REDACTION-001`;
- `FX-MAX-RETENTION-OD013-BLOCKED-001`;
- `FX-MAX-NOTIFICATION-BOUNDARY-001`;
- `FX-MAX-EGRESS-SUCCESS-NOT-PROVIDER-SUCCESS-001`;
- `FX-MAX-TELEGRAM-ANALOGY-FORBIDDEN-001`.

Run 21 creates no fixture files and executes no tests.

## 28. Acceptance Matrix coverage

Run 21 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-DATA-002`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004`;
- `AM-EXT-001`–`AM-EXT-004`;
- `AM-REF-001`–`AM-REF-004`;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, database, webhook, Long Polling, Mini App, provider call, bot, certificate/trust-store, moderation and notification-delivery executions remain future gates and are not passed by this documentation run.

## 29. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral MAX adapter records/contracts;
- implement synthetic deterministic update validation/dedup/normalization rules;
- implement official Mini App WebAppData validation after selecting exact security parameters;
- integrate Identity & Access account-resolution contracts;
- integrate Notification Delivery outbox/attempt contracts;
- add provider client adapter only after credential/runtime/eligibility gates;
- add Webhook mode only after operations/security decisions;
- add Long Polling only for approved development/test scope;
- add observability, idempotency and reconciliation evidence;
- add approved read models with provenance.

## 30. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create tables, migrations, ORM models or physical schemas;
- create queues, brokers, workers, schedulers or services;
- install dependencies or create lockfiles;
- create MAX partner profile, bot, moderation submission, token, webhook subscription, Long Polling loop or Mini App;
- send MAX API requests or receive live provider updates;
- create provider SDK dependency;
- select endpoint/domain/TLS/port/certificate/trust-store;
- select command catalog, callback payload format, deep-link format or Mini App screens;
- select retry counts, delays, backoff or rate limits;
- invent account merge, phone requirement or session behavior;
- invent retention/deletion policy;
- treat MAX provider IDs as internal account IDs;
- treat raw client Mini App data as trusted;
- treat provider success as human read or final notification delivery;
- retry ambiguous provider send blindly;
- write Identity, Notification, Beacon, Scan, Egress, Entitlement, Telegram or Admin state directly;
- store raw provider payloads, tokens, cookies, secrets, legal/personal documents or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 31. Report and handoff requirements

Any future implementation/proof task touching MAX Adapter must report:

- exact GitHub SHA and paths;
- module playbook version used;
- official MAX evidence version/date used;
- created/changed files and hashes;
- whether product-code, migrations, dependency files, database, runtime, bot, webhook, Long Polling, Mini App, certificate/trust-store or provider calls were created;
- exact tests and outputs;
- eligibility/authenticity/idempotency/reconciliation evidence;
- token/secret and personal-data redaction evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 32. Roadmap after this playbook

1. Synchronize exact Run 21 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Run 22 — Admin & Support Module Playbook.
4. Run 23 — Web Cabinet Module Playbook.
5. Run 24 — Filter Catalog & Builder Module Playbook.
6. Final independent documentation audit and explicit owner decision before any product-code track.

This playbook is a prerequisite only and does not authorize implementation.

## 33. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `MAX-HISTORY-0001` | 2026-07-08 | Run 21 created MAX Adapter Module Playbook v1.0 and fixed provider-specific eligibility, inbound, Mini App, contact, identity, outbound and reconciliation boundaries without implementation. | Public GitHub `main`; Run 21 publication commit; current official MAX API/Webhook/Long Polling/Mini App/partner documentation rechecked; no runtime artifacts. |
