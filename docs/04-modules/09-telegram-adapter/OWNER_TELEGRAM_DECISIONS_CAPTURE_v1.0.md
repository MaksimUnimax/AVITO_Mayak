# Маяк Авито — Telegram Adapter Owner Decisions Capture v1.0

## 1. Metadata

- date: `2026-07-19`
- module: `09-telegram-adapter`
- roadmap step: `TG-01`
- technical task: `TG01-GOVERNANCE-CAPTURE-20260719-017`
- status: `APPROVED_OWNER_INPUT_PENDING_INDEPENDENT_GITHUB_ACCEPTANCE`
- expected base: `ca974aaedc77f34c8b2ded04aae3e7c38add57fc`
- source-of-truth playbook: `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md`
- this document is governance capture only and is not product code, provider runtime, persistence, deployment or permission to implement

## 2. Purpose and authority

This document freezes the owner-provided Telegram Adapter decisions that may be used by later exact semantic tasks only after independent acceptance of the publishing commit.

The internal project `account_id` is the authoritative user identity. Telegram user, chat, message, callback, update and bot identifiers remain external provider identifiers. Telegram Adapter owns Telegram-specific verification, mapping and normalization only. It must use public contracts of Identity & Access, Beacon Management, Scan Orchestration, Egress Routing, Notification Delivery, Entitlements & Billing, Web Cabinet and other owning modules and must never mutate their internal state directly.

This capture does not close an open decision by implication and does not override public GitHub `main`.

## 3. Existing Telegram bot identity and protected secret evidence

Owner-provided and previously accepted redacted evidence:

- bot created: `yes`
- bot username: `@signalings_bot`
- Telegram numeric bot ID: `8664835407`
- numeric bot ID is external Telegram provider metadata and is not an internal `account_id`
- protected token reference: `/etc/avito-mayak/secrets/telegram_bot_token`
- token file owner/group: `root:root`
- token file mode: `0600`
- token file size evidence: `46` bytes
- token value: `NOT_READ_NOT_PRINTED`
- public bot metadata reference: `/etc/avito-mayak/telegram-bot.conf`
- public metadata owner/group: `root:root`
- public metadata mode: `0644`
- public metadata size evidence: `65` bytes

Bot creation through BotFather is already completed as an owner provisioning action. Creating another bot, repeating BotFather setup, changing commands/description, configuring a Mini App, rotating/revoking/deleting the token or changing the protected secret is forbidden without a separate exact owner task.

The existence of the bot and protected token does not authorize token consumption, Telegram API calls, `getMe`, webhook configuration, `getUpdates`, Mini App, provider runtime, deployment or any live proof.

## 4. Token and secret handling

The raw bot token must never be:

- pasted into ChatGPT or a CLI/Codex prompt or report;
- read, printed, hashed, fingerprinted, encoded, copied or transmitted by an agent;
- committed to Git;
- stored in fixtures, logs, screenshots, URLs, query parameters, environment dumps or ordinary reports;
- moved, replaced, rotated, revoked or deleted without an exact owner task.

Before an accepted runtime/proof gate, only redacted file-presence metadata may be checked: path existence, owner, group, mode and non-zero size. Any future runtime use must consume a protected secret reference through an approved operations/security mechanism.

## 5. User identity and account linking

The authoritative user is the internal `account_id`.

- `telegram_user_id` is an external provider identifier.
- `telegram_chat_id` is an external provider chat identifier.
- Telegram username, display name, avatar, language, phone, chat title and group membership are not account keys or merge authority.
- Telegram Adapter must not create an Account row directly.
- Telegram Adapter must not maintain a separate Telegram-only user database.
- Telegram Adapter must not merge accounts.
- `/start` may request account resolution, linking or account-creation flow only through Identity & Access public contracts.
- Identity & Access owns account creation semantics, identity-link challenges, authorization and merge policy.
- Missing, conflicting or weak identity evidence must produce rejected, blocked, challenge-required or ambiguous outcomes rather than a silent merge.

`OD-006`, `OD-007` and `OD-008` remain open where their exact phone-login, phone requirement and account-merge rules are not already governed elsewhere.

## 6. Telegram as the first practical channel

Telegram is the first practical channel for notifications and user control.

This decision means Telegram Adapter may be prepared first as a provider-specific channel boundary. Notification Delivery remains generic and owns generic eligibility, outbox, attempts and delivery lifecycle. MAX remains a separate future adapter. Web Cabinet remains a separate UI/session surface. This decision does not disable future channels and does not close `OD-012`.

## 7. Provider mode direction

Owner direction:

- production/staging target: webhook;
- local/development proof may use `getUpdates` only after an exact proof task;
- webhook and `getUpdates` are mutually exclusive for the same bot and environment;
- mode transition, drop-pending behavior, polling offset rules, acknowledgement point and reconciliation behavior require separate exact operations/security decisions.

No environment receives a live provider mode from this capture. No endpoint, domain, TLS certificate, port, polling loop, cursor, service or provider call is authorized.

## 8. Webhook authenticity

If webhook mode is selected later, provider authenticity verification is mandatory.

A future exact task must use official/provider-evidence-backed verification, protected secret references and safe comparison rules. Missing or mismatched authenticity evidence is not business success. HTTP acknowledgement is not business success. The webhook secret must not appear in URLs, logs, reports, fixtures or Git.

This capture does not create a webhook endpoint or configure Telegram.

## 9. Telegram input is untrusted

Commands, message text, callback data, button labels, deep-link payloads, provider profile fields, update structure and future Mini App launch data are untrusted provider input until validated.

Receiving an update through webhook or `getUpdates` does not make its business meaning trusted. Unsupported or disallowed update types must be ignored safely or rejected explicitly without business effect. Duplicate/replayed input must not create a second business effect. Conflicting replay/fingerprint evidence must remain conflict or ambiguity.

## 10. Buttons and callback data

Telegram buttons are not executable commands and callback data is not authorization.

Required future semantic flow:

Telegram callback received → provider/update structure validated → verified Telegram identity resolved through Identity & Access to internal `account_id` → owning module checks authorization, ownership and action scope → destructive or sensitive action requires explicit confirmation → owning module performs the action only after its own accepted gate.

Callback data must be bounded, replay-safe and idempotent. A future format may be opaque, signed or server-resolved and may expire where required. Raw `account_id`, raw `beacon_id`, secrets, payment identifiers and authorization decisions must not be embedded as trusted callback authority.

Delete Beacon, change source URL, unlink identity, disable a channel and payment/tariff-sensitive actions require server-side ownership checks and confirmation. Telegram Adapter must not mutate Beacon, Identity or Entitlements state directly.

## 11. Deep links

Deep-link payloads are untrusted.

Future allowed purposes may include onboarding, linking Telegram to an existing internal account through Identity & Access, opening Beacon or listing-result context, returning from Web Cabinet and opening a future Mini App context.

Sensitive deep links must use a future approved opaque, signed or one-time short-lived payload. Raw `account_id`, raw `beacon_id`, email, phone, payment ID, secret or token material must not be placed in a deep link. A deep link is never authorization by itself. Exact payload format remains a future gate.

## 12. Commands, messages and Avito-link intent

The exact command catalog, button labels, conversation flow and callback/deep-link encoding remain future UI/adapter decisions.

Current semantic intent direction may include:

- start or link Telegram;
- help;
- list my Beacons;
- Beacon status;
- create Beacon from a candidate Avito source URL;
- Beacon settings;
- update interval or status-notification preference;
- pause or resume Beacon;
- request Beacon deletion with confirmation;
- tariff or limits;
- open full listing result;
- toggle no-new status notification.

Telegram Adapter may classify message text or an Avito link only as an untrusted candidate intent. Beacon Management owns Avito source validation, Beacon creation, lifecycle, configuration revision, patch-based settings update and ownership/limit checks. Telegram Adapter does not parse Avito business semantics and does not create a Beacon directly.

## 13. Chat surfaces

Version 1 supports private chat only.

Groups, supergroups, channels, forum topics, business connections, shared chats and multi-user chat ownership remain future gates. Telegram Adapter must not infer account ownership from a chat title, membership or group role and must not expose private Beacon/listing data to a group or channel by default.

## 14. Mini App boundary

Mini App is deferred and is not the first mandatory implementation step. It may later support full listing results, listing details, Beacon settings/status and richer onboarding.

`initDataUnsafe` is never trusted for authentication or authorization. A future backend must receive raw `Telegram.WebApp.initData` and validate it server-side under accepted official rules. `auth_date` freshness, hosting, frontend, URL, screens, Web Cabinet integration and BotFather Mini App configuration remain future decisions. Validated Telegram identity remains an external provider identity and still requires Identity & Access resolution.

This capture does not implement or configure a Mini App.

## 15. Telegram presentation of listings and status

Notification Delivery preserves the full approved safe listing-card reference set for one notification effect. Telegram Adapter may later render a Telegram-friendly summary, compact list, pagination or buttons after an exact UI/template gate.

Twenty separate messages must not be sent by default for twenty listings. Telegram rendering must not discard listing references at the adapter boundary.

Phone, seller, rating and description may be shown only if approved upstream Parser/Scan/Notification contracts already provide them as safe facts. Telegram Adapter does not fetch, parse or enrich Avito data and must not fail a notification merely because optional fields are absent.

## 16. No-new, unavailable and recovery messages

Telegram may later render optional no-new status notifications when the user enables the generic Notification preference. Notification Delivery owns eligibility and frequency policy. Telegram Adapter does not choose the frequency. The captured current minimum is not more frequent than once per hour when enabled.

If Telegram channel is enabled, Telegram may later render one material problem-status effect when Avito, route or parser availability becomes unavailable or materially changes, and one recovery-result effect after recovery. Telegram Adapter does not decide Scan recovery, retry a scan, choose an Egress route or emit the same problem on every scan interval.

## 17. Beacon management intents

Telegram may later normalize pause, resume, settings and delete requests.

- pause/resume requires current account and ownership checks through owning modules;
- source URL and settings changes go through Beacon Management;
- tariff/payment-sensitive actions go through Entitlements, Web Cabinet or approved payment flows;
- deletion requires explicit confirmation;
- callback data is never permission;
- Telegram Adapter does not mutate Beacon state directly.

## 18. Outbound provider semantics

Telegram Adapter maps one approved Notification attempt to a Telegram-specific provider request intent and maps provider result/failure/ambiguity back to a Telegram provider outcome.

- Notification Delivery owns generic outbox, attempts and delivery lifecycle.
- Telegram Bot API `ok=true` means provider accepted the method result; it does not prove human read, click, final delivery or business success.
- Egress transport success does not prove Telegram provider success.
- HTTP acknowledgement does not prove business success.
- Unknown or interrupted send/update effect is reconciliation-first and must never be retried blindly.
- Provider rejection, unavailability, rate limitation, malformed response and ambiguity remain explicit.
- Telegram Adapter does not mark generic Notification delivery success by itself.

## 19. Data minimization, diagnostics and retention

Raw Telegram payloads are not ordinary logs or fixtures by default.

Allowed future minimized records may include provider bot scope reference, Telegram update/user/chat/message identifiers where contractually required, update type class, authenticity result, replay/deduplication result, normalized intent family, provider outcome class, safe reason code, correlation/causation IDs and redacted evidence references.

Forbidden by default:

- raw bot token or webhook secret;
- private keys;
- full raw Telegram update retention;
- private-message archives;
- group-member lists;
- unnecessary profile data;
- contact requests or phone numbers;
- unbounded retention.

Retention, deletion, archive and compaction remain blocked by `OD-013`. This capture does not close `OD-013` and does not authorize a physical storage policy.

## 20. Explicitly blocked implementation

This capture does not authorize:

- source code, handlers, provider clients or Telegram SDK/library selection;
- tests or real provider fixtures;
- Telegram API calls, `getMe`, webhook or `getUpdates`;
- BotFather reconfiguration, token consumption, token rotation/revocation/deletion or secret changes;
- Mini App frontend, hosting or configuration;
- command catalog, callback payload format, deep-link format or message-template catalog;
- database schema, ORM models, migrations or persistence;
- queue, worker, scheduler, service or runtime;
- endpoint, domain, TLS, certificate, port or listener;
- Docker, CI/CD or deploy;
- raw provider payload storage;
- direct mutation of Identity, Beacon, Scan, Egress, Notification, Entitlements, MAX or Web state.

Only later exact roadmap tasks may open narrowly defined semantic or implementation scope.

## 21. Open decisions preserved

This capture closes no numbered open decision by assumption.

- `OD-006`, `OD-007` and `OD-008` remain open for exact login/phone/merge policy not already governed elsewhere.
- `OD-012` remains open for future channels beyond Telegram/MAX.
- `OD-013` remains open for retention/deletion.
- `OD-014` remains open for future Web Cabinet screen composition and Telegram/Web/Mini App interaction.
- exact command catalog, callback format, deep-link format, supported update matrix, webhook endpoint topology, `getUpdates` operating values, Mini App `auth_date` threshold, retry/backoff/rate values, provider SDK/library, physical schema and runtime topology remain future gates.

## 22. Consequences and next admissible step

After this document, the matching append-only ADR and the matching OPEN_DECISIONS update are published and independently accepted:

- `TG-01` governance capture is complete;
- later exact semantic Telegram tasks may use these owner decisions without inventing product policy;
- `TG-02` may be considered next only after a fresh GitHub/parallel-main/playbook/dependency check and a separate exact task;
- provider runtime, secrets, Telegram API, webhook, `getUpdates`, Mini App, schema, persistence, templates, workers and deploy remain blocked.
