# Маяк Авито — Reference Registry

**Версия:** 1.1
**Статус:** APPROVED documentation registry
**Дата:** 2026-07-07
**Основание:** Reference Registry v1.0, Source of Truth Policy, Contract Change Policy v1.0, Security and Privacy Model v1.0, Reference Regression Policy v1.0, Acceptance Matrix v1.1, OPEN_DECISIONS.md.
**Не является:** provider API specification, credential store, implementation guide, legal opinion, traffic authorization or archived copy of third-party content.

---

## 1. Version relationship

This document is the current cross-provider index. It incorporates all detailed Avito records and evidence gaps from `REFERENCE_REGISTRY_v1.0.md` without rewriting them, and adds Telegram/MAX official records for Run 11.

A consumer resolving an Avito `reference_id` reads v1.0. A consumer resolving a Telegram/MAX `reference_id` reads this document. Both files form one versioned registry package; they are not parallel competing layouts.

Canonical lifecycle statuses remain `CURRENT`, `STALE`, `SUPERSEDED`, `WITHDRAWN`, `UNAVAILABLE` and `DISPUTED`. A URL without authority, retrieval date, scope, status and limitations is insufficient evidence.

## 2. Inherited Avito records

The following v1.0 records remain unchanged and current only in their declared scope:

- `AVITO-OFFICIAL-ADS-HELP-001`;
- `AVITO-OFFICIAL-ADS-SDK-PY-001`;
- `AVITO-OFFICIAL-ADS-TECHDOC-001` (`UNAVAILABLE`);
- `AVITO-PRIMARY-PARSER-001`.

All consumer-search evidence gaps listed by v1.0 remain open. Run 11 does not change Avito evidence or OD-009–OD-011.

## 3. Telegram official records

### TELEGRAM-OFFICIAL-BOT-API-001

- **Provider:** Telegram.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** Telegram Bot API documentation.
- **URL:** `https://core.telegram.org/bots/api`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Effective identity:** page reported Bot API 10.1, dated 11 June 2026.
- **Scope:** HTTPS Bot API request/response semantics, Update identity, webhook/getUpdates delivery, webhook secret header and identifier storage requirements.
- **Status:** `CURRENT`.
- **Claims supported:**
  - Bot API is HTTPS-based and authenticated by a bot token;
  - API responses expose explicit `ok` success/failure semantics;
  - webhook and `getUpdates` are mutually exclusive;
  - updates are retained for no longer than 24 hours before receipt;
  - `update_id` is a provider update identifier useful for duplicate/order handling;
  - webhook delivery retries non-2xx responses;
  - `secret_token` is delivered as `X-Telegram-Bot-Api-Secret-Token` when configured;
  - webhook-response shortcut calls do not expose whether the invoked Bot API request succeeded;
  - Telegram user/chat identifiers may require 64-bit-safe storage.
- **Claims not supported:** project webhook hosting, endpoint URL, retry budget, SDK choice, final human read/delivery, automatic identity merge, group/channel scope or credential provisioning.
- **Limitations:** provider behavior may change; `update_id` does not replace internal account/Beacon/idempotency boundaries.
- **Affected documents:** `TELEGRAM_REFERENCE_POLICY_v1.0.md`; future Runs 13, 19, 20 and 23 playbooks.
- **Fixture links:** `FX-SEC-PROVIDER-VERIFY-001`, `FX-IDEMP-REPLAY-SAME-001`, `FX-EXT-REJECTED-001`, `FX-EXT-UNAVAILABLE-001`, `FX-EXT-AMBIGUOUS-001`, `FX-REF-CURRENT-001`.
- **Acceptance rows:** `AM-SEC-004`, `AM-IDEMP-001`, `AM-EXT-001`–`AM-EXT-004`, `AM-REF-001`–`AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** Bot API version/change log update, webhook/update behavior change, Run 20 planning, final documentation audit.

### TELEGRAM-OFFICIAL-MINI-APPS-001

- **Provider:** Telegram.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** Telegram Mini Apps documentation.
- **URL:** `https://core.telegram.org/bots/webapps`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** Mini App launch surfaces, `initData`, `initDataUnsafe`, HMAC validation and `auth_date` freshness.
- **Status:** `CURRENT`.
- **Claims supported:**
  - server use must rely on validated `Telegram.WebApp.initData`;
  - `initDataUnsafe` must not be trusted;
  - integrity can be checked with the documented HMAC-SHA-256 algorithm derived from the bot token and `WebAppData`;
  - `auth_date` can be checked to reject stale launch data;
  - Mini Apps can be launched through documented buttons/menu/deep-link surfaces.
- **Claims not supported:** project freshness window, session lifetime, account-linking UX, phone collection, Mini App hosting, authorization policy or automatic trust of user/profile fields.
- **Limitations:** exact adopted launch surfaces and freshness threshold remain module-playbook decisions.
- **Affected documents:** `TELEGRAM_REFERENCE_POLICY_v1.0.md`; future Runs 13, 20 and 23 playbooks.
- **Fixture links:** `FX-SEC-PROVIDER-VERIFY-001`, `FX-SEC-SECRET-REDACTION-001`, `FX-REF-CURRENT-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-SEC-001`, `AM-SEC-004`, `AM-REF-001`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** Mini Apps validation algorithm/surface change, Run 13/20/23 planning, final audit.

### TELEGRAM-OFFICIAL-BOT-FEATURES-001

- **Provider:** Telegram.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** Telegram Bot Features documentation.
- **URL:** `https://core.telegram.org/bots/features`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** commands, inline mode and deep-link capability identity.
- **Status:** `CURRENT`.
- **Claims supported:** Telegram provides documented deep links and bot interaction surfaces.
- **Claims not supported:** adoption of inline/group/channel/business/guest features or use of deep-link payload as authenticated account identity.
- **Limitations:** a deep-link parameter is untrusted input until validated by project contracts.
- **Affected documents:** `TELEGRAM_REFERENCE_POLICY_v1.0.md`; future Telegram/Web Cabinet playbooks.
- **Fixture links:** `FX-CONTRACT-MISSING-META-001`, `FX-SEC-PROVIDER-VERIFY-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-CONTRACT-001`, `AM-SEC-004`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** deep-link format/surface change or dependent playbook planning.

## 4. MAX official records

### MAX-OFFICIAL-API-OVERVIEW-001

- **Provider:** MAX.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** MAX developer API overview.
- **URL:** `https://dev.max.ru/docs-api`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** HTTPS API, Authorization header, response codes, production webhook requirement, Long Polling limitation and July 2026 endpoint/certificate transition notice.
- **Status:** `CURRENT`.
- **Claims supported:**
  - API uses HTTPS and explicit HTTP statuses including 429 and 503;
  - token-in-query is no longer supported; Authorization header is required;
  - production update delivery uses Webhook; Long Polling is development/test only; modes cannot be simultaneous;
  - official notice requires redirecting requests from `platform-api.max.ru` to `platform-api2.max.ru` and adding the stated trust certificate by 19 July 2026;
  - HTTP/self-signed webhook support ended from 25 May 2026 according to the current page.
- **Claims not supported:** project endpoint provisioning, certificate installation, SDK choice, safe retry rate, final delivery/read, eligibility satisfaction or runtime readiness.
- **Limitations:** time-sensitive transition must be revalidated immediately before Run 21 implementation planning.
- **Affected documents:** `MAX_REFERENCE_POLICY_v1.0.md`; future Runs 19, 21 and 23 playbooks.
- **Fixture links:** `FX-EXT-REJECTED-001`, `FX-EXT-UNAVAILABLE-001`, `FX-REF-CHANGED-BREAKING-001`, `FX-REF-CURRENT-001`.
- **Acceptance rows:** `AM-EXT-002`, `AM-EXT-003`, `AM-REF-001`, `AM-REF-003`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** 19 July 2026 transition, domain/certificate/auth change, Run 21 planning, final audit.

### MAX-OFFICIAL-WEBHOOK-001

- **Provider:** MAX.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** MAX `POST /subscriptions` documentation.
- **URL:** `https://dev.max.ru/docs-api/methods/POST/subscriptions`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** webhook subscription, HTTPS/TLS/port requirements, response deadline, retries, unsubscribe behavior and secret header.
- **Status:** `CURRENT`.
- **Claims supported:**
  - active Webhook disables Long Polling;
  - endpoint must use HTTPS on port 443 with a trusted certificate/full chain;
  - endpoint must return HTTP 200 within 30 seconds;
  - failed delivery is retried up to 10 times with increasing intervals and may cause automatic unsubscribe after eight hours without success;
  - configured secret is sent in `X-Max-Bot-Api-Secret` and official docs recommend validating it.
- **Claims not supported:** exactly-once delivery, a universal stable event ID, project endpoint/secret creation, internal retry schedule or server ownership.
- **Limitations:** webhook retries imply duplicate processing risk; generic Update documentation does not establish one universal dedup identifier.
- **Affected documents:** `MAX_REFERENCE_POLICY_v1.0.md`; future Notification Delivery and MAX Adapter playbooks.
- **Fixture links:** `FX-SEC-PROVIDER-VERIFY-001`, `FX-IDEMP-REPLAY-SAME-001`, `FX-INTERRUPT-UNKNOWN-001`, `FX-EXT-AMBIGUOUS-001`.
- **Acceptance rows:** `AM-SEC-004`, `AM-IDEMP-001`, `AM-INTERRUPT-002`, `AM-EXT-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** webhook retry/secret/TLS change, Run 21 planning, final audit.

### MAX-OFFICIAL-LONG-POLLING-001

- **Provider:** MAX.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** MAX `GET /updates` documentation.
- **URL:** `https://dev.max.ru/docs-api/methods/GET/updates`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** development/test Long Polling and marker semantics.
- **Status:** `CURRENT`.
- **Claims supported:** Long Polling is not for production; `marker` points to the next expected update and advancing it marks previous updates read.
- **Claims not supported:** marker as a stable event/idempotency identifier, production polling, storage duration or safe polling frequency for this project.
- **Limitations:** marker is a cursor; it must not be treated as business identity.
- **Affected documents:** `MAX_REFERENCE_POLICY_v1.0.md`; future MAX Adapter playbook.
- **Fixture links:** `FX-IDEMP-REPLAY-SAME-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-IDEMP-001`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** mode/marker semantics change or Run 21 planning.

### MAX-OFFICIAL-MINI-APP-VALIDATION-001

- **Provider:** MAX.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** MAX Mini App validation documentation.
- **URL:** `https://dev.max.ru/docs/webapps/validation`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** `WebAppData`, `window.WebApp.initData`, HMAC-SHA-256 validation and `auth_date` field.
- **Status:** `CURRENT`.
- **Claims supported:** launch data must be validated; the official page defines extraction, canonicalization and HMAC-SHA-256 verification using the bot token and `WebAppData`; `auth_date` is Unix time.
- **Claims not supported:** project freshness window, session/account linking, phone trust, hosting or authorization.
- **Limitations:** client-visible launch fields remain untrusted until server validation succeeds.
- **Affected documents:** `MAX_REFERENCE_POLICY_v1.0.md`; future Runs 13, 21 and 23 playbooks.
- **Fixture links:** `FX-SEC-PROVIDER-VERIFY-001`, `FX-SEC-SECRET-REDACTION-001`, `FX-REF-CURRENT-001`.
- **Acceptance rows:** `AM-SEC-001`, `AM-SEC-004`, `AM-REF-001`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** validation algorithm/data shape change or dependent playbook planning.

### MAX-OFFICIAL-PARTNER-ONBOARDING-001

- **Provider:** MAX.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** MAX bot preparation/onboarding documentation.
- **URL:** `https://dev.max.ru/docs/chatbots/bots-coding/prepare`.
- **Retrieved at:** `2026-07-07T13:32:54+02:00`.
- **Scope:** partner eligibility, verified profile and bot moderation gates.
- **Status:** `CURRENT`.
- **Claims supported:** access is currently documented for Russian-resident legal entities, individual entrepreneurs and self-employed persons; bot creation requires a verified partner profile; user access follows successful moderation.
- **Claims not supported:** project owner eligibility, approval outcome, legal interpretation, account creation or production availability.
- **Limitations:** this is a blocking adoption gate until separately evidenced for the project owner; no personal/legal evidence belongs in public Git.
- **Affected documents:** `MAX_REFERENCE_POLICY_v1.0.md`; future MAX Adapter and operations planning.
- **Fixture links:** `FX-REF-MISSING-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-REF-002`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** eligibility/moderation terms change, owner adoption decision, Run 21 planning.

## 5. Cross-provider constraints

- Telegram facts are not evidence for MAX, and MAX facts are not evidence for Telegram.
- Provider identifiers are external identities, not internal `account_id`.
- Username, display name, avatar, phone or deep-link payload cannot merge accounts automatically.
- Webhook/Mini App input remains untrusted until provider-specific verification succeeds.
- Duplicate/retry behavior requires internal idempotency and commit-point rules; provider retry is not exactly-once delivery.
- API acceptance is not proof of human read or final user-visible delivery unless current evidence explicitly says so.
- Raw tokens, webhook secrets, launch payloads and unnecessary personal content are prohibited in Git, prompts, logs, reports and fixtures.

## 6. Evidence gaps after Run 11

Run 11 does not establish:

- project eligibility or moderation approval for MAX;
- actual bot ownership, tokens or provider accounts;
- project webhook hosting, domain, TLS, ports or secret delivery;
- provider SDK/library selection;
- exact adopted chat/group/channel/Mini App surfaces;
- account-linking UX or freshness windows;
- project retry/backoff/rate budgets;
- universal MAX event dedup identifier;
- final delivery/read guarantees;
- retention of provider identifiers/payloads;
- phone/contact collection or automatic identity merge.

These gaps block dependent acceptance; they do not prove capability absence.

## 7. Change control and prohibitions

A provider-reference change follows Contract Change Policy and Reference Regression Policy: identify old/new source, status, changed scope, compatibility, affected documents/fixtures, security/privacy impact and open decisions. Historical records are not silently rewritten.

This registry authorizes no provider traffic, bot/account creation, token handling, endpoint probing, credential storage, executable fixture/test, service, port, certificate installation, product-code, migration, database, Docker, CI/CD, deploy or production infrastructure.

## 8. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Detailed Avito official/primary records and consumer-search evidence gaps. |
| 1.1 | 2026-07-07 | Current cross-provider index incorporating v1.0 and adding Telegram/MAX official records, limitations and revalidation gates. |
