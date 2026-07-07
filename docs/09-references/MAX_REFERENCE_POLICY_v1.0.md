# Маяк Авито — MAX Reference Policy

**Версия:** 1.0
**Статус:** APPROVED documentation policy
**Дата:** 2026-07-07
**Основание:** Reference Registry v1.1, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Security and Privacy Model v1.0, Data Model v1.0, Fixture Registry v1.0, Acceptance Matrix v1.1, Reference Regression Policy v1.0, OPEN_DECISIONS.md.
**Не является:** MAX bot implementation, partner enrollment, moderation application, webhook deployment, Mini App implementation, SDK choice, credential policy, legal opinion or permission to call MAX.

---

## 1. Назначение

Policy defines how future project documents and tasks may rely on current official MAX behavior. It prevents Telegram analogy, undocumented payload assumptions and unverified client data from becoming provider facts or account authority.

## 2. Covered scope

- partner eligibility and moderation gates;
- API HTTPS/authentication/result boundaries;
- production Webhook and development/test Long Polling;
- Webhook TLS, acknowledgement, retry and secret-header behavior;
- Update/marker evidence limitations;
- Mini App launch-data validation;
- outbound message result and ambiguity;
- time-sensitive July 2026 endpoint/certificate transition;
- privacy/data minimization;
- evidence gates for future MAX Adapter, Identity, Notification Delivery, Operations and Web Cabinet playbooks.

## 3. Authoritative references

Current records:

- `MAX-OFFICIAL-API-OVERVIEW-001`;
- `MAX-OFFICIAL-WEBHOOK-001`;
- `MAX-OFFICIAL-LONG-POLLING-001`;
- `MAX-OFFICIAL-MINI-APP-VALIDATION-001`;
- `MAX-OFFICIAL-PARTNER-ONBOARDING-001`.

Only exact scopes in Reference Registry v1.1 are authoritative. Telegram behavior, community SDKs, examples, old screenshots or memory cannot fill MAX evidence gaps.

## 4. Adoption and eligibility gate

Current official documentation states that partner access is available to Russian-resident legal entities, individual entrepreneurs and self-employed persons; bot creation requires a verified partner profile, and user access follows moderation.

Therefore:

- project eligibility is `UNPROVEN` until owner-specific lawful evidence is separately accepted;
- no personal/legal documents or partner credentials belong in public Git, prompts or ordinary reports;
- bot availability, approval and moderation are not assumed;
- inability to prove eligibility blocks MAX implementation planning but does not alter the target product model;
- this policy does not interpret law or decide organizational form.

## 5. Time-sensitive API transition

Official pages retrieved on 7 July 2026 require, by 19 July 2026:

- redirecting API requests from `platform-api.max.ru` to `platform-api2.max.ru`;
- adding the stated Ministry certificate to the relevant trust list.

They also state that token-in-query is no longer supported and the `Authorization` header must be used.

Consequences:

- `platform-api2.max.ru` is the current documented target for future planning, subject to immediate revalidation;
- no project request, trust-store change or certificate installation is performed by Run 11;
- Run 21 must revalidate after the 19 July 2026 deadline and record the effective current domain/certificate rule;
- a stale endpoint/certificate assumption is a blocking reference regression, not a retryable business error.

## 6. Token and request boundary

- MAX access token is a secret and never belongs in Git, prompts, reports, fixtures, logs or query strings.
- Token acquisition, storage, rotation and revocation remain deferred.
- Future calls use HTTPS and explicit HTTP status/error normalization.
- 401, 429, 503 and malformed responses remain explicit provider outcomes; they do not become success or empty result.
- Official request-rate statements are provider evidence, not an automatically adopted project budget.

## 7. Inbound update modes

Current MAX documentation distinguishes:

- Webhook as the production mechanism;
- Webhook or Long Polling for development/test;
- modes are mutually exclusive.

Therefore:

- production MAX Adapter planning must use Webhook unless current official evidence changes;
- Long Polling cannot be accepted as production fallback by analogy or convenience;
- active Webhook disables Long Polling;
- this policy creates no endpoint, domain, TLS, port, worker or polling process.

## 8. Webhook endpoint and authenticity

Current official constraints include:

- HTTPS on port 443;
- trusted certificate or documented accepted certificate, matching domain and complete chain;
- no self-signed certificate;
- HTTP 200 within 30 seconds;
- configured secret delivered in `X-Max-Bot-Api-Secret`;
- official recommendation to verify that header.

Project policy strengthens this boundary:

- future Webhook must configure and verify the secret unless a stricter accepted provider-authentication mechanism supersedes it;
- missing/mismatched secret is rejected before business dispatch;
- acknowledgement occurs only after the adapter’s defined durable acceptance point;
- UI/client state never substitutes for server verification;
- endpoint/TLS ownership requires a separate operations decision and task.

## 9. Webhook retries, duplicates and unsubscribe

Official documentation reports up to 10 retry attempts with increasing intervals and automatic unsubscribe after eight hours without successful response.

Consequences:

- duplicate webhook delivery is expected;
- exactly-once delivery must not be claimed;
- duplicate handling uses internal idempotency and provider/event evidence;
- a future adapter must detect subscription loss and expose explicit degraded/unsubscribed state;
- a timeout/non-200 is delivery failure, not proof that the event was not processed internally;
- blind replay of downstream business effects is prohibited.

The policy does not adopt provider retry intervals as internal retry configuration.

## 10. Update identity and deduplication gap

The generic MAX `Update` page enumerates event types but does not establish one universal stable update identifier equivalent to Telegram `update_id`.

Therefore:

- do not invent a global MAX update ID;
- Long Polling `marker` is a cursor, not business/event identity;
- a future MAX Adapter playbook must document event-specific identities that are actually present in current official schemas, plus normalized fingerprint and scope;
- where safe identity is absent, duplicate/unknown effect remains explicit and requires reconciliation;
- same evidence/fingerprint may reuse the original outcome; incompatible replay is conflict/ambiguity.

## 11. Long Polling marker rules

For allowed development/test use:

- `marker` points to the next expected update;
- advancing it marks previous updates read;
- marker advances only after durable adapter acceptance;
- interruption before durable acceptance must preserve replay capability;
- passing no marker/current documented null behavior must not be used as a complete-history assumption;
- polling frequency, timeout and event-retention assumptions remain deferred.

## 12. Mini App trust boundary

- MAX launch parameters are untrusted until the official `WebAppData` validation algorithm succeeds on the backend.
- Validation uses the documented canonicalization and HMAC-SHA-256 construction derived from bot token and `WebAppData`.
- Client-visible fields and `window.WebApp.initData` are transport input, not authorization by themselves.
- The future playbook must define a maximum `auth_date` age; this policy does not invent it.
- Validation failure/staleness yields explicit unauthenticated/rejected outcome before any business action.
- Validated MAX user ID is an external identity reference and links to internal `account_id` only through Identity & Access.
- Name, username, photo, phone/contact or chat metadata cannot merge accounts automatically.

## 13. Provider identifiers and data ownership

- MAX user/chat/message/callback/update-related identifiers are external provider identities.
- MAX Adapter owns provider mapping and verified ingress/egress translation only.
- Identity & Access owns account/identity linkage.
- Notification Delivery owns intent/outbox/delivery lifecycle.
- MAX Adapter must not write business tables directly or create a second user database.
- Weak-signal linking and automatic merge remain prohibited.

OD-006–OD-008 remain open.

## 14. Outbound message/result semantics

- A successful `POST /messages` response may confirm the documented API operation/result; it does not by itself prove human read or final user-visible delivery.
- Explicit HTTP/provider rejection remains rejection.
- Transport interruption after a possible external effect is `AMBIGUOUS`/reconcile-first.
- Notification resend requires idempotency and evidence that duplicate user-visible effect is prevented or detectable.
- Provider message objects/IDs may be stored only in the approved scoped mapping/delivery model.

SDK, retry schedule, rate budget, template rendering and final delivery/read semantics remain deferred.

## 15. Supported surfaces and non-adoption

Official MAX documentation includes chat/channel events, buttons, callbacks, bots and Mini Apps. Run 11 does not automatically adopt them.

The MAX Adapter playbook must explicitly choose:

- private dialog versus chat/channel surfaces;
- supported update types;
- callbacks/buttons/deep links/Mini App surfaces;
- moderation-approved user journeys;
- unsupported event behavior;
- required provider permissions.

Unsupported surfaces must fail closed or be ignored without unauthorized effects.

## 16. Privacy and minimization

Run 11 does not authorize collection of phone numbers, contact requests, private message archives, channel/member inventories or unnecessary profile data.

Future storage must be limited to approved fields with provider scope, internal account linkage, redaction, provenance and retention. Raw tokens, webhook secrets, launch payloads and unnecessary message content are prohibited in ordinary logs/reports/fixtures.

OD-007 and OD-013 remain open.

## 17. Failure and ambiguity classes

The adapter must distinguish:

- eligibility/moderation not proven;
- request/update not received;
- webhook authenticity failure;
- TLS/endpoint/subscription failure;
- structurally invalid or unsupported update;
- duplicate/unknown update identity;
- accepted normalized update;
- provider explicit rejection/authentication/rate/unavailable result;
- malformed/incomplete response;
- ambiguous external effect;
- stale endpoint/certificate/reference evidence.

None may become fabricated success, empty business result or unauthorized account action.

## 18. Required fixtures and acceptance rows

Applicable fixtures include:

- `FX-SEC-PROVIDER-VERIFY-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-INTERRUPT-UNKNOWN-001`;
- `FX-EXT-SUCCESS-001`;
- `FX-EXT-REJECTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-CHANGED-BREAKING-001`;
- `FX-REF-UNSUPPORTED-001`.

Applicable Acceptance Matrix rows include `AM-CONTRACT-001`–`003`, `AM-IDEMP-001`–`002`, `AM-INTERRUPT-002`, `AM-SEC-001`–`004`, `AM-EXT-001`–`004`, `AM-REF-001`–`004`, and ownership/data rows where account scope is used.

Run 11 creates no executable fixture files.

## 19. Currentness and revalidation

Revalidation is mandatory:

- immediately after/on the 19 July 2026 API transition before any dependent planning;
- before Run 21 MAX Adapter playbook acceptance;
- before Run 13/23 relies on MAX identity/Mini App behavior;
- when eligibility, moderation, domain, certificate, authorization, webhook, retry, Update or validation behavior changes;
- when official source becomes unavailable/contradictory;
- before any implementation task and during final documentation audit.

Known relevant change invalidates `CURRENT` in affected scope. Missing evidence remains blocked; it is not filled from Telegram analogy.

## 20. Open decisions and non-decisions

This policy does not decide:

- whether project owner satisfies partner eligibility;
- partner profile, bot name, moderation submission or launch timing;
- webhook domain/TLS/port ownership;
- SDK/framework/library;
- token/secret storage product;
- exact `auth_date` freshness threshold;
- universal event identity where official evidence lacks one;
- supported dialog/chat/channel/callback/Mini App surfaces;
- commands/buttons/deep-link UX;
- account-linking, phone or merge policy;
- internal retry/backoff/rate budgets;
- provider payload retention;
- final delivery/read guarantees.

OD-006–OD-008 and OD-012–OD-014, plus all other OD-001–OD-014, remain open.

## 21. Explicit prohibitions

Run 11 does not authorize MAX partner registration, identity/eligibility evidence collection, bot creation, moderation action, token generation, webhook subscription, API requests, Long Polling, trust-store/certificate change, Mini App hosting, executable tests, SDK installation, service/container/port creation, product-code, migration, database, Dockerfile, CI/CD, deploy or production infrastructure.

## 22. Acceptance criteria

Policy is accepted when official evidence and the July transition are recorded, eligibility is a proven gate rather than assumption, production Webhook and Long Polling boundaries are explicit, webhook/Mini App trust is server-verified, duplicate/identity gaps remain explicit, Telegram analogy is forbidden, privacy is minimized, open decisions remain open and no implementation/runtime artifact is created.

## 23. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial MAX official-evidence, eligibility, transition, webhook/replay, Mini App validation, delivery and privacy policy. |
