# Маяк Авито — Telegram Adapter Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 20 of 24
**Дата:** 2026-07-08
**Модуль:** `09-telegram-adapter`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Identity & Access Module Playbook v1.0, Notification Delivery Module Playbook v1.0, Egress Routing Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, Telegram Reference Policy v1.0, current official Telegram Bot API and Mini Apps documentation rechecked for Run 20, and OPEN_DECISIONS.md.
**Не является:** bot implementation, BotFather action, webhook deployment, getUpdates polling loop, Mini App implementation, provider SDK choice, credential/token policy, physical database schema, migration, live provider call, runtime configuration, endpoint/domain/certificate/port setup, notification worker, message template catalog or permission to implement.

---

## 1. Назначение

Telegram Adapter владеет provider-specific boundary between Telegram surfaces and internal project contracts.

Модуль отвечает на вопросы:

- как Telegram inbound updates become verified, normalized adapter events;
- как Telegram user/chat/update/message identifiers remain external provider identifiers;
- как команды, кнопки, deep links and Mini App launch data are classified before business dispatch;
- как outbound Notification attempts are mapped to Telegram Bot API requests and provider outcomes;
- как webhook or `getUpdates` mode is treated as an explicit operational decision, not an implementation default;
- как duplicate/replayed/ambiguous Telegram provider effects are preserved and reconciled;
- как provider-specific UI adaptation is separated from Account, Beacon, Scan, Egress and Notification ownership.

Модуль не создаёт аккаунты напрямую, не владеет generic notification outbox, не создаёт Beacons, не рассчитывает baseline/diff, не выбирает Egress route и не доставляет сообщения вне accepted Notification contracts.

## 2. Границы и владение

Telegram Adapter owns semantic mutation authority for:

- Telegram provider identity mapping records;
- Telegram bot/update intake records;
- Telegram webhook/getUpdates receipt evidence after mode approval;
- Telegram update replay/deduplication state;
- Telegram command/callback/deep-link normalization;
- Telegram Mini App launch-data validation result references;
- Telegram-specific delivery request mapping;
- Telegram provider outcome mapping;
- Telegram provider-side message/callback correlation references;
- Telegram-specific safe diagnostics and adapter read models.

It does not own:

- internal `Account`, account merge, roles, sessions or credentials;
- tariff, subscription, entitlement grant or payment state;
- Beacon source URL, configuration, revision or lifecycle;
- Parser extraction, Avito provider evidence or listing candidates;
- Scan runs, observations, baseline, difference or listing state;
- Egress routes, agents, leases or transport state;
- generic Notification source intake, outbox, delivery attempts or delivery lifecycle;
- MAX provider mapping;
- Admin/Support work items;
- Web Cabinet screens or web sessions;
- Filter Catalog definitions;
- Telegram bot token raw material or provider secrets;
- provider payload retention while OD-013 remains unresolved.

Only Telegram Adapter may authorize Telegram-provider mapping state. It must use public contracts of Identity & Access, Notification Delivery, Beacon Management and other owning modules and must never write their internal records directly.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Accepted Identity & Access and Notification Delivery playbooks.
4. Telegram Reference Policy v1.0 and current official Telegram documentation for exact provider behavior.
5. This playbook.
6. Future exact implementation task and accepted evidence.
7. Runtime evidence for one exact release/environment/provider operation.

Official Telegram Bot API and Mini Apps documentation were rechecked for Run 20 only to preserve provider-evidence boundaries. This playbook records adapter semantics and does not create a provider account, token, webhook, API call, SDK, endpoint, Mini App or runtime.

## 4. Confirmed decisions

1. Telegram user/chat/message/update IDs are external provider identifiers and never replace internal `account_id`, `beacon_id`, `notification_outbox_item_id` or `notification_attempt_id`.
2. Telegram Adapter owns provider-specific mapping and normalization only.
3. Identity & Access owns account resolution, identity linking, role/session/authorization and merge policy.
4. Notification Delivery owns generic outbox, delivery attempts, delivery lifecycle and acceptance of provider outcome into generic notification state.
5. Telegram Adapter may request account resolution only after provider identity is verified under Telegram rules and project contracts.
6. Automatic account merge by username, display name, avatar, phone, chat title, group membership or weak correlation is forbidden.
7. Deep-link parameters, callback data, commands, message text and Mini App start parameters are untrusted input until validated by project contracts.
8. `initDataUnsafe` is never trusted for server-side authentication or authorization; server validation uses raw `Telegram.WebApp.initData` under official rules.
9. Webhook and `getUpdates` are mutually exclusive provider modes. Run 20 does not select a mode for any environment.
10. Webhook authenticity requires provider-evidence-backed verification such as `X-Telegram-Bot-Api-Secret-Token` when webhook mode is selected by a future task.
11. `Update.update_id` may support provider-scope replay/order handling but does not replace internal idempotency or correlation.
12. Telegram Bot API `ok=true` confirms only the API method result class returned by Telegram; it does not prove human read, click, final user-visible delivery or business success.
13. Telegram webhook-response shortcut cannot be treated as confirmed delivery unless a future reconciliation design proves result capture and safety.
14. Unknown send/update effect is reconcile-first and is never blindly retried.
15. Unsupported update types are ignored safely or rejected explicitly without business effect.
16. Telegram adapter diagnostics and records exclude raw bot tokens, secrets, private keys, unnecessary personal data and raw provider payloads by default.
17. Run 20 does not decide command catalog, button UX, Mini App screens, chat-surface support, retry values, rate budgets, token storage or retention.
18. Open decisions and provider-specific defaults receive no fabricated values.
19. Run 20 creates no bot, token, webhook, endpoint, provider call, SDK, queue, worker, database table, migration, service, port, certificate or runtime.

## 5. Open decisions and blockers

Run 20 does not resolve:

- `OD-006` — exact phone+password and recovery policy where Telegram identity might later link to Web Cabinet;
- `OD-007` — when phone is required, if ever;
- `OD-008` — account merge policy;
- `OD-012` — future channels beyond Telegram/MAX;
- `OD-013` — retention/deletion of provider payloads, adapter records, delivery logs and personal data;
- `OD-014` — future Web Cabinet screen composition where Telegram Mini App handoff may interact with web UI;
- webhook versus `getUpdates` per environment;
- endpoint/domain/TLS/port/certificate ownership;
- Telegram bot account creation and BotFather process;
- bot token storage, rotation, revocation and delivery;
- exact supported update types and chat surfaces;
- command catalog and button/callback UX;
- deep-link parameter formats;
- Mini App launch surfaces and screens;
- maximum accepted Mini App `auth_date` age;
- provider retry count, delay, backoff and rate budgets;
- provider payload retention and redaction granularity;
- adapter persistence schema, indexes and constraints;
- exact SDK/library choice and transport implementation.

Open means blocked. No implementation, test, fixture, runtime, bot, token, webhook, endpoint, provider call or UI task may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, queues, wire schemas or provider payloads.

| Record | Purpose | Required boundary |
|---|---|---|
| `TelegramProviderIdentity` | External Telegram user/chat identity reference | not internal account authority by itself |
| `TelegramAccountLinkReference` | Link between provider identity and internal account after Identity contract approval | owned with Identity handoff; no weak merge |
| `TelegramUpdateIntakeRecord` | One provider update receipt/reference | provider identity, bot scope and fingerprint |
| `TelegramUpdateDeduplicationRecord` | Duplicate/replay protection for provider updates | scoped to bot/provider identity and normalized update |
| `TelegramCommandEnvelope` | Normalized command/callback/deep-link intent | untrusted until contract validation |
| `TelegramMiniAppValidationResult` | Server-side validation result for raw `initData` | no trust in `initDataUnsafe` |
| `TelegramOutboundRequest` | Adapter mapping of one Notification attempt to Telegram request intent | not generic outbox authority |
| `TelegramProviderOutcome` | Explicit Telegram result/failure/ambiguity mapping | not delivery success until Notification accepts it |
| `TelegramReconciliationRecord` | Evidence resolving unknown provider effect | no blind retry |
| `TelegramAdapterReadModel` | Safe projection for diagnostics/support | not mutation authority |

## 7. Semantic identifiers and scope

- `telegram_bot_ref` identifies the logical bot/provider scope without exposing token material.
- `telegram_update_id` identifies Telegram update scope and must be scoped to bot/provider identity.
- `telegram_user_id`, `telegram_chat_id` and `telegram_message_id` are external provider identifiers.
- `telegram_callback_query_id`, `telegram_inline_query_id` and related provider IDs remain provider-specific.
- `telegram_delivery_request_id` identifies adapter-side request mapping under one Notification attempt.
- `correlation_id` and `causation_id` connect Identity, Notification and adapter evidence.

Identifiers do not reveal raw tokens, private keys, secret headers, full provider payloads or unnecessary personal data. Exact internal encoding remains future task scope.

## 8. Inbound update boundary

Telegram inbound update processing has the following semantic sequence after an allowed mode is selected:

```text
provider update received or polled
→ provider-scope authenticity/mode gate
→ raw payload structural classification
→ provider update identity/fingerprint recorded
→ duplicate/replay/idempotency evaluation
→ Telegram-specific normalization
→ Identity/Notification/Beacon public contract dispatch only if allowed
→ explicit adapter outcome
```

Rules:

- webhook payload is not trusted until provider-authenticity checks pass;
- `getUpdates` payload is not trusted merely because it arrived from polling; it still requires structural and contract validation;
- unsupported update type produces safe ignored/rejected outcome;
- provider display names, usernames, language, chat titles and avatars are not account keys;
- client-visible buttons and callback payloads are not authorization;
- duplicate update replay returns/references original adapter outcome without second business effect;
- incompatible replay/fingerprint mismatch is conflict or ambiguity, not a new action.

## 9. Webhook boundary

Run 20 does not select webhook mode. If a future task selects it, the adapter must define:

- endpoint ownership and environment boundary;
- HTTPS/domain/certificate/port gate;
- `secret_token` generation, storage and verification policy;
- constant-time comparison for `X-Telegram-Bot-Api-Secret-Token` or stricter approved mechanism;
- durable acceptance/acknowledgement point;
- duplicate webhook delivery idempotency;
- drop-pending and mode-transition behavior;
- safe failure response semantics;
- no raw token/secret in URL, logs, reports or fixtures.

HTTP acknowledgement is not business success. A non-2xx retry by Telegram is expected provider behavior and must not produce duplicate business effects.

## 10. `getUpdates` boundary

Run 20 does not select polling mode. If a future task selects it, the adapter must define:

- allowed environment class;
- polling ownership and scheduler/worker boundary;
- offset advancement only after durable adapter acceptance point;
- replay after interruption;
- mode transition from/to webhook;
- drop-pending behavior;
- timeout/limit/interval values after approved policy;
- no process-local cursor as source of truth.

Calling `getUpdates` with offset higher than an update confirms provider-side receipt semantics. The project must not advance offset before it can safely replay or reject the internal effect.

## 11. Mini App boundary

Run 20 does not implement Mini App screens. If a future task uses Telegram Mini Apps:

- frontend-visible `initDataUnsafe` is display/input context only and is not trusted;
- backend receives raw `Telegram.WebApp.initData`;
- validation follows official Telegram data-check-string/HMAC rules or later accepted official mechanism;
- `auth_date` freshness threshold must be selected by future security/product policy;
- validation failure, stale data or missing hash yields explicit unauthenticated/rejected result;
- validated Telegram user ID remains an external provider identity reference;
- account linking still uses Identity & Access policies and challenges;
- Mini App UI state does not bypass server-side authorization.

## 12. Outbound delivery boundary

Telegram Adapter maps a Notification attempt to Telegram provider request semantics.

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
- Telegram message/callback correlation where available;
- accepted-success, accepted-failure or ambiguity class;
- retry/reconciliation recommendation under policy;
- safe reason/evidence references.

Rules:

- adapter does not create generic outbox items;
- adapter does not mark generic Notification delivery success by itself;
- `ok=true` is mapped to provider accepted result, not human read/ack;
- `ok=false`, HTTP failure, transport failure and malformed response remain explicit failures;
- possible-send-without-result remains ambiguous/reconcile-first;
- webhook-response shortcut is not used as confirmed delivery without accepted reconciliation design.

## 13. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `IngestTelegramUpdateCommand` | Accept/reject one provider update under selected mode |
| `ValidateTelegramWebhookRequestCommand` | Verify webhook authenticity before payload trust |
| `RecordTelegramPollingBatchCommand` | Record a `getUpdates` batch and cursor evidence after mode approval |
| `NormalizeTelegramCommandCommand` | Convert command/callback/deep-link input to a project command envelope |
| `ValidateTelegramMiniAppInitDataCommand` | Validate raw Mini App initData and return provider identity reference |
| `ResolveTelegramIdentityCommand` | Ask Identity & Access to resolve/link verified Telegram identity |
| `MapNotificationAttemptToTelegramCommand` | Build provider request intent from a Notification attempt |
| `RecordTelegramProviderOutcomeCommand` | Attach explicit Telegram provider outcome to the adapter request |
| `ReconcileTelegramProviderEffectCommand` | Resolve unknown inbound/outbound Telegram effect |
| `GetTelegramAdapterEventQuery` | Read safe adapter event/intake projection |
| `ExplainTelegramAdapterDecisionQuery` | Explain authenticity, replay, normalization and outcome decision |

Mutation-capable inputs require mandatory common contract metadata, authorization scope where applicable, idempotency key and normalized fingerprint.

## 14. Public output families

| Output family | Meaning |
|---|---|
| `TelegramUpdateIntakeOutcome` | accepted, replayed, rejected, unsupported, duplicate, ambiguous or blocked |
| `TelegramAuthenticityOutcome` | verified, missing-secret, mismatched-secret, not-applicable, rejected or blocked |
| `TelegramCommandNormalizationOutcome` | normalized, ignored, unsupported, invalid, ambiguous or blocked |
| `TelegramMiniAppValidationOutcome` | verified, rejected, stale, malformed, missing-hash or blocked |
| `TelegramIdentityResolutionOutcome` | resolved-account, new-account-requested, link-challenge-required, rejected or ambiguous |
| `TelegramOutboundMappingOutcome` | request-prepared, blocked, unsupported-target, invalid-content or ambiguous |
| `TelegramProviderOutcomeResult` | provider-accepted, provider-rejected, unavailable, rate-limited, malformed, ambiguous or blocked |
| `TelegramReconciliationOutcome` | resolved-no-effect, resolved-effect, remains-ambiguous or manual-review-required |
| `TelegramAdapterReadResult` | authorized safe provider-adapter projection |

Outputs remain framework, SDK, persistence, queue and provider transport neutral.

## 15. Mandatory outcome classes

At minimum:

- `NOT_RECEIVED`;
- `AUTHENTICITY_FAILED`;
- `UNSUPPORTED_UPDATE`;
- `DUPLICATE_UPDATE`;
- `NORMALIZED_UPDATE_ACCEPTED`;
- `MINI_APP_VALIDATION_FAILED`;
- `IDENTITY_RESOLUTION_BLOCKED`;
- `PROVIDER_REQUEST_NOT_SENT`;
- `PROVIDER_ACCEPTED`;
- `PROVIDER_REJECTED`;
- `PROVIDER_UNAVAILABLE`;
- `RATE_LIMITED_OR_RESTRICTED`;
- `MALFORMED_OR_UNUSABLE_RESPONSE`;
- `PROVIDER_EFFECT_AMBIGUOUS`;
- `RECONCILIATION_REQUIRED`.

Exact wire codes and provider payload fields are not selected.

## 16. False-success prohibition

None of the following may become clean business success or notification delivery success:

- missing or mismatched webhook secret where webhook mode requires it;
- raw Mini App `initDataUnsafe` without server validation;
- unvalidated deep-link/start/callback payload;
- unsupported update type;
- duplicate update with incompatible fingerprint;
- provider display name or username match;
- `ok=true` without Notification acceptance of provider outcome;
- webhook-response shortcut without result capture;
- request may have been sent but result is unknown;
- provider explicit rejection;
- provider unavailable/rate limited;
- malformed/incomplete response;
- ambiguous Telegram effect;
- Egress transport success without Telegram outcome;
- reconciliation incomplete.

## 17. Identity & Access dependency

Telegram Adapter supplies verified provider identity evidence to Identity & Access. Identity owns account resolution, account creation semantics, linking and authorization.

Rules:

- `telegram_user_id` is not `account_id`;
- `telegram_chat_id` is not account ownership;
- username, first/last name, language, phone, avatar and chat title are not merge keys;
- linking another identity requires Identity-owned challenge semantics;
- OD-006, OD-007 and OD-008 remain unresolved;
- adapter cannot create a second user database;
- protected actions require server-side actor context and role/ownership checks.

## 18. Notification Delivery dependency

Notification Delivery owns source events, outbox items, attempts and generic delivery lifecycle. Telegram Adapter maps one approved attempt to Telegram provider request/outcome.

Rules:

- Telegram Adapter does not create generic notification events;
- Telegram Adapter does not create outbox work;
- provider accepted result is returned to Notification for acceptance;
- provider failure or ambiguity is explicit;
- retry/reconciliation uses Notification idempotency and provider evidence;
- delivery history cannot include raw token/secret or unnecessary payload.

## 19. Egress dependency

If Telegram provider calls later use Egress or platform transport evidence, Telegram Adapter must preserve route/transport correlation but does not own Egress state.

Rules:

- adapter does not choose private route independently;
- adapter does not mutate route health/quarantine;
- Egress transport success is not Telegram provider success;
- ambiguous Egress state remains explicit;
- exact transport/route technology remains Egress/operations scope.

## 20. Security, privacy and retention

- Telegram bot token is a secret and never appears in Git, prompts, ordinary reports, fixtures, URLs or logs.
- Webhook secret/token material is represented only by safe references/classes.
- Raw provider payloads are not ordinary logs or fixtures.
- Store only approved provider IDs and minimized fields required by contracts.
- Private message archives, group member lists, contact requests, phone numbers and unnecessary profile content are not collected by default.
- Logs use safe IDs, outcome classes, reason codes, provider scope and correlation IDs.
- External strings never become shell commands.
- Retention, deletion, archive and compaction remain OD-013.
- A retention/deletion implementation cannot be invented by agents.

## 21. Observability semantics

Future minimum safe signals:

- provider bot scope reference;
- update/request/attempt identities;
- update type and supported/unsupported class;
- authenticity validation result;
- replay/dedup/idempotency result;
- normalized command family;
- Mini App validation class;
- account-resolution outcome class;
- outbound provider result class;
- retry/reconciliation state;
- safe reason code and latency;
- no raw token, secret, private payload or unnecessary personal data.

A green webhook endpoint, successful polling loop, provider response, `ok=true` or Egress transport success does not prove internal business success.

## 22. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Identity & Access provider identity contracts;
- Notification Delivery outbox/attempt contracts;
- Egress correlation where applicable;
- Telegram Reference Policy and current official Telegram provider evidence;
- PostgreSQL/SQLAlchemy/Psycopg after physical schema approval;
- pytest/pytest-asyncio and approved fakes for deterministic tests;
- HTTPX only if an exact adapter implementation task selects it within the Technical Baseline.

Deferred/blocked:

- provider SDK/library choice;
- webhook/getUpdates runtime mode;
- bot creation and BotFather configuration;
- token/secret storage product;
- endpoint/domain/TLS/port/certificate setup;
- Mini App hosting and frontend;
- command catalog and templates;
- retry/backoff/rate values;
- persistence schema/migrations;
- services/deploy/runtime.

No provider runtime is introduced by this playbook.

## 23. Fake dependencies and test doubles

Future approved fakes may model:

- `TelegramWebhookRequestVerifier`;
- `TelegramUpdateSource`;
- `TelegramUpdateDeduplicationStore`;
- `TelegramMiniAppInitDataVerifier`;
- `TelegramProviderIdentityGateway`;
- `IdentityAccountResolver`;
- `NotificationAttemptReader`;
- `NotificationOutcomeSink`;
- `TelegramProviderClientFake`;
- `EgressCorrelationReader`;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic provider IDs, updates, commands, Mini App data, accounts, notification attempts and provider outcomes only. They do not prove Telegram live behavior, token validity, webhook reachability, Mini App hosting or production delivery.

## 24. Required fixtures and test vectors

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
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-TG-WEBHOOK-SECRET-VALID-001`;
- `FX-TG-WEBHOOK-SECRET-MISSING-001`;
- `FX-TG-WEBHOOK-SECRET-MISMATCH-001`;
- `FX-TG-GETUPDATES-OFFSET-AFTER-COMMIT-001`;
- `FX-TG-GETUPDATES-OFFSET-PRECOMMIT-BLOCKED-001`;
- `FX-TG-UPDATE-DEDUP-REPLAY-001`;
- `FX-TG-UPDATE-FINGERPRINT-CONFLICT-001`;
- `FX-TG-UNSUPPORTED-UPDATE-IGNORED-001`;
- `FX-TG-COMMAND-NORMALIZED-001`;
- `FX-TG-DEEPLINK-UNTRUSTED-001`;
- `FX-TG-CALLBACK-UNTRUSTED-001`;
- `FX-TG-MINIAPP-INITDATA-VALID-001`;
- `FX-TG-MINIAPP-INITDATAUNSAFE-REJECTED-001`;
- `FX-TG-MINIAPP-AUTHDATE-STALE-BLOCKED-001`;
- `FX-TG-IDENTITY-RESOLVE-VERIFIED-001`;
- `FX-TG-WEAK-MERGE-FORBIDDEN-001`;
- `FX-TG-OUTBOUND-OK-NOT-READ-001`;
- `FX-TG-OUTBOUND-REJECTED-001`;
- `FX-TG-OUTBOUND-AMBIGUOUS-RECONCILE-001`;
- `FX-TG-WEBHOOK-RESPONSE-SHORTCUT-NOT-DELIVERY-001`;
- `FX-TG-TOKEN-REDACTION-001`;
- `FX-TG-RETENTION-OD013-BLOCKED-001`;
- `FX-TG-NOTIFICATION-BOUNDARY-001`;
- `FX-TG-EGRESS-SUCCESS-NOT-PROVIDER-SUCCESS-001`.

Run 20 creates no fixture files and executes no tests.

## 25. Acceptance Matrix coverage

Run 20 documentation coverage:

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

Runtime, database, webhook, polling, Mini App, provider call, bot and notification-delivery executions remain future gates and are not passed by this documentation run.

## 26. Allowed future changes

A later exact task may, after all gates:

- create module package skeleton inside the approved layout;
- define transport-neutral Telegram adapter records/contracts;
- implement synthetic deterministic update validation/dedup/normalization rules;
- implement official Mini App initData validation after selecting exact security parameters;
- integrate Identity & Access account-resolution contracts;
- integrate Notification Delivery outbox/attempt contracts;
- add provider client adapter only after credential/runtime gates;
- add webhook or getUpdates mode only after operations/security decisions;
- add observability, idempotency and reconciliation evidence;
- add approved read models with provenance.

## 27. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create product code;
- create tables, migrations, ORM models or physical schemas;
- create queues, brokers, workers, schedulers or services;
- install dependencies or create lockfiles;
- create Telegram bot, BotFather configuration, token, webhook, polling loop or Mini App;
- send Telegram API requests or receive live provider updates;
- create provider SDK dependency;
- select webhook/getUpdates for an environment;
- select endpoint/domain/TLS/port/certificate;
- select command catalog, callback payload format, deep-link format or Mini App screens;
- select retry counts, delays, backoff or rate limits;
- invent account merge, phone requirement or session behavior;
- invent retention/deletion policy;
- treat Telegram provider IDs as internal account IDs;
- treat `initDataUnsafe` as trusted;
- treat `ok=true` as human read or final notification delivery;
- retry ambiguous provider send blindly;
- write Identity, Notification, Beacon, Scan, Egress, Entitlement or MAX state directly;
- store raw provider payloads, tokens, cookies, secrets or unnecessary personal data;
- use foreign host resources, containers, queues, databases, ports, services, certificates or credentials;
- create CI/CD, Docker, deploy, runtime configuration, ports, listeners or production infrastructure.

## 28. Report and handoff requirements

Any future implementation/proof task touching Telegram Adapter must report:

- exact GitHub SHA and paths;
- module playbook version used;
- official Telegram evidence version/date used;
- created/changed files and hashes;
- whether product-code, migrations, dependency files, database, runtime, bot, webhook, polling, Mini App or provider calls were created;
- exact tests and outputs;
- authenticity/idempotency/reconciliation evidence;
- token/secret and personal-data redaction evidence;
- known limitations and open decisions left unresolved.

A handoff cannot override public GitHub `main`.

## 29. Roadmap after this playbook

1. Synchronize exact Run 20 published SHA on `/opt/avito-mayak`.
2. Independently verify publication scope, SHA, clean worktree and no prohibited artifacts.
3. Run 21 — MAX Adapter Module Playbook.
4. Run 22 — Admin & Support Module Playbook.
5. Run 23 — Web Cabinet Module Playbook.
6. Run 24 — Filter Catalog & Builder Module Playbook.
7. Final independent documentation audit and explicit owner decision before any product-code track.

This playbook is a prerequisite only and does not authorize implementation.

## 30. Append-only history

| ID | Date | Change | Evidence |
|---|---|---|---|
| `TG-HISTORY-0001` | 2026-07-08 | Run 20 created Telegram Adapter Module Playbook v1.0 and fixed provider-specific inbound, Mini App, identity, outbound and reconciliation boundaries without implementation. | Public GitHub `main`; Run 20 publication commit; current official Telegram Bot API and Mini Apps documentation rechecked; no runtime artifacts. |
