# Маяк Авито — Telegram Reference Policy

**Версия:** 1.0
**Статус:** APPROVED documentation policy
**Дата:** 2026-07-07
**Основание:** Reference Registry v1.1, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Security and Privacy Model v1.0, Data Model v1.0, Fixture Registry v1.0, Acceptance Matrix v1.1, Reference Regression Policy v1.0, OPEN_DECISIONS.md.
**Не является:** bot implementation, webhook deployment, Mini App implementation, provider SDK choice, credential policy, legal opinion or permission to call Telegram.

---

## 1. Назначение

Policy defines how future project documents and tasks may rely on Telegram official behavior. It prevents unverified payloads, display names, deep-link parameters or memory from becoming trusted identity or business facts.

## 2. Covered scope

- Bot API request/result semantics;
- inbound updates through webhook or `getUpdates`;
- provider update identity and replay handling;
- webhook authenticity header;
- bot/user/chat identifiers;
- commands, buttons, deep links and Mini App launch surfaces;
- Mini App launch-data validation;
- outbound API result and ambiguity;
- privacy/data minimization;
- evidence lifecycle for future Telegram Adapter, Identity, Notification Delivery and Web Cabinet playbooks.

This policy does not select which surfaces the first product release adopts.

## 3. Authoritative references

Current records:

- `TELEGRAM-OFFICIAL-BOT-API-001`;
- `TELEGRAM-OFFICIAL-MINI-APPS-001`;
- `TELEGRAM-OFFICIAL-BOT-FEATURES-001`.

Only exact scope declared in Reference Registry v1.1 is authoritative. Community libraries, samples, old screenshots, payloads from memory and analogy with MAX cannot approve behavior.

## 4. Bot token and request boundary

- A Telegram bot token is a secret and never belongs in Git, prompts, reports, fixtures, ordinary logs or URLs recorded by the project.
- Token acquisition, storage, rotation, revocation and delivery remain deferred to Security/Operations and Telegram Adapter playbooks.
- Bot API uses HTTPS and explicit `ok`/error results, but transport/library implementation is not selected here.
- Provider error text or codes are external/untrusted diagnostics and must be normalized without exposing secrets.

## 5. Inbound update modes

Telegram documents two mutually exclusive modes: webhook and `getUpdates`.

- An active webhook excludes `getUpdates`.
- Incoming updates are not kept by Telegram longer than 24 hours before receipt.
- A future Telegram Adapter playbook must select one allowed mode for each environment and document transition/drop-pending behavior.
- This policy does not provision an endpoint, domain, certificate, port, worker or polling loop.

A mode switch is an operational change requiring state/replay analysis. It cannot be inferred from whichever mode is easier to implement.

## 6. Webhook authenticity and acknowledgement

If webhook is selected later:

- `secret_token` must be configured unless a stricter accepted provider-authentication mechanism supersedes it;
- the adapter must verify `X-Telegram-Bot-Api-Secret-Token` using constant-time comparison before trusting payload content;
- missing or mismatched secret produces explicit rejection with no business effect;
- HTTP acknowledgement is emitted only after the adapter reaches its defined durable acceptance/commit point;
- Telegram retries non-2xx webhook delivery, so duplicate reception is expected and must be idempotent;
- supported public ports and certificate behavior are provider facts, not permission to create project ingress.

Provider IP allowlisting alone is not accepted as the only authenticity control unless current official evidence and a new security decision support it.

## 7. Update identity, order and replay

- `Update.update_id` is the provider update identifier in Telegram scope.
- It may be used to ignore repeated updates and restore ordering after out-of-order delivery.
- Scope must include the bot/provider identity; an `update_id` from another bot is not the same event.
- The internal adapter records the provider identity and normalized request fingerprint before business dispatch.
- Duplicate update with same semantic fingerprint returns/reuses the original adapter outcome and causes no second business effect.
- Same provider identity with incompatible fingerprint is an explicit conflict/ambiguity, never a new action.
- A gap, old update or out-of-order update is not automatic evidence of data loss or success; it requires the playbook-defined reconciliation behavior.

`update_id` does not replace `message_id`, `correlation_id`, internal `account_id`, `beacon_id` or command idempotency keys.

## 8. `getUpdates` cursor rules

If `getUpdates` is selected for an allowed non-webhook environment:

- offset confirmation follows the official “highest update plus one” semantics;
- offset advances only after the adapter-defined durable acceptance point;
- advancing the offset before durable acceptance is forbidden;
- replay after interruption must not create a second business effect;
- polling interval, timeout and operational limits remain deferred.

## 9. Mini App trust boundary

- Client-visible `initDataUnsafe` is never trusted for authentication, authorization, ownership or account linking.
- The backend receives raw `Telegram.WebApp.initData` and performs the official validation algorithm.
- Hash verification uses the documented HMAC-SHA-256 construction derived from the bot token and constant `WebAppData`.
- The future playbook must choose and document a maximum accepted `auth_date` age; this policy does not invent one.
- Validation failure or stale data yields an explicit unauthenticated/rejected result before any business action.
- Validated Telegram user ID is still an external identity reference and must be linked to an internal `account_id` only through Identity & Access policy.
- Username, first/last name, language, photo, chat title and other display data are not account keys.

## 10. Deep links and interaction surfaces

Telegram officially supports commands, buttons, deep links and multiple Mini App launch surfaces. Project adoption is narrower:

- deep-link/start parameters are untrusted opaque input until validated by a project contract;
- a deep-link parameter never authenticates or merges an account by itself;
- initial supported private-chat/group/channel/inline/business/guest/Mini App surfaces remain deferred to the Telegram Adapter playbook;
- unsupported update types must be ignored safely or rejected explicitly without leaking data;
- a client UI button is not server-side authorization.

## 11. Provider identifiers and data ownership

- Telegram user/chat/message/update IDs are external provider identifiers.
- IDs must be stored in a representation safe for the provider’s documented numeric range.
- Identity & Access owns account/identity linkage; Telegram Adapter owns provider mapping state only.
- Telegram Adapter must not create a second user database or mutate Identity, Beacon, Entitlement or Notification tables directly.
- Automatic merge by username, phone, name, avatar, chat membership or weak correlation is prohibited.

OD-006–OD-008 remain open.

## 12. Outbound message/result semantics

- Bot API `ok=true` confirms the API method’s documented result, not necessarily human read or final user-visible delivery.
- Explicit `ok=false`, HTTP/transport failure and malformed response remain explicit failures.
- If the request may have reached Telegram but no trustworthy result was received, outcome is `AMBIGUOUS`/reconcile-first; blind resend is prohibited.
- Telegram’s webhook-response shortcut cannot prove whether the invoked Bot API method succeeded and therefore cannot be used as a confirmed delivery path without an accepted reconciliation design.
- Notification Delivery owns intents, outbox and delivery lifecycle; Telegram Adapter only maps provider request/outcome.

Retry count, delay, backoff and rate budgets require current provider evidence plus an approved adapter/delivery playbook.

## 13. Privacy and minimization

Current documentation does not authorize collection of phone numbers, contact requests, private message archives, group-member lists or unnecessary profile content.

Allowed future storage is limited to fields required by approved contracts and playbooks, with:

- internal `account_id` separation;
- provider identity scope;
- redaction of tokens/secrets;
- minimized payload/audit data;
- explicit retention/provenance;
- safe deletion/reconciliation rules after OD-013 is decided.

Raw webhook/Mini App payloads are not ordinary logs or fixtures.

## 14. Failure and ambiguity classes

The adapter must distinguish:

- request/update not received;
- authenticity validation failed;
- structurally invalid/unsupported update;
- duplicate update;
- accepted normalized update;
- provider explicit rejection;
- provider unavailable/rate limited;
- malformed/incomplete response;
- ambiguous external effect;
- stale/missing reference evidence.

None may be converted into fabricated success, empty business result or unauthorized account action.

## 15. Required fixtures and acceptance rows

Applicable existing fixtures include:

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
- `FX-REF-UNSUPPORTED-001`.

Applicable Acceptance Matrix rows include `AM-CONTRACT-001`–`003`, `AM-IDEMP-001`–`002`, `AM-INTERRUPT-002`, `AM-SEC-001`–`004`, `AM-EXT-001`–`004`, `AM-REF-001`–`004`, and ownership/data rows where identity/account scope is used.

Run 11 creates no executable fixture files.

## 16. Currentness and revalidation

Revalidate immediately:

- before Run 20 Telegram Adapter playbook acceptance;
- before Run 13 or Run 23 relies on Telegram Mini App/account-linking behavior;
- when Bot API or Mini Apps change validation, update identity, webhook, delivery or supported surfaces;
- when an official source becomes unavailable/contradictory;
- before any implementation task and during final documentation audit.

A known relevant change invalidates `CURRENT` for affected scope. Missing evidence produces a blocked/unsupported state, not analogy or memory-based behavior.

## 17. Open decisions and non-decisions

This policy does not decide:

- webhook versus `getUpdates` per environment;
- endpoint/domain/TLS/port ownership;
- SDK/framework/library;
- token/secret storage product;
- exact `auth_date` freshness threshold;
- supported chat/group/channel/inline/business/guest surfaces;
- bot commands, button UX or Mini App screens;
- account-linking UX, phone requirement or merge policy;
- retry/backoff/rate budgets;
- provider payload retention;
- notification templates or final delivery/read semantics.

OD-006–OD-008, OD-012–OD-014 and all other OD-001–OD-014 remain open.

## 18. Explicit prohibitions

Run 11 does not authorize Telegram bot creation, BotFather actions, tokens, webhook registration, provider calls, polling, Mini App hosting, executable tests, SDK installation, service/container/port/certificate creation, product-code, migration, database, Dockerfile, CI/CD, deploy or production infrastructure.

## 19. Acceptance criteria

Policy is accepted when official evidence is recorded, inbound trust and replay boundaries are explicit, external identity is separated from internal ownership, Mini App data is server-validated, delivery ambiguity remains explicit, privacy is minimized, open decisions remain open and no implementation/runtime artifact is created.

## 20. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial Telegram official-evidence, authenticity, replay, Mini App validation, delivery and privacy policy. |
