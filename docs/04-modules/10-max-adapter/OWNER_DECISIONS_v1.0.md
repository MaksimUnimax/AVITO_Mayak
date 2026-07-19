# Маяк Авито — MAX Adapter Owner Decisions v1.0
## 1. Metadata

Version: 1.0

Date: 2026-07-19

Module: `10-max-adapter`

Roadmap step: `MX-01`

Technical task: `MX-01-MAX-OWNER-DECISION-CAPTURE-20260719-01`

Governance classification: APPROVED owner decision capture

Status: APPROVED_OWNER_INPUT_PENDING_INDEPENDENT_GITHUB_ACCEPTANCE

Source-of-truth playbook: `docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md`

Scope: documentation/governance-only

This document is not product code, provider runtime, persistence, deployment, provider permission evidence or permission to implement.

## 2. Purpose and authority

This document freezes the eight owner-provided MAX Adapter decisions required for Module 10 roadmap step MX-01.

These decisions may be used by later exact semantic tasks only after the publishing and corrective commits are independently verified and accepted against public GitHub main.

This document records owner product direction. It does not claim MAX partner eligibility, verified-profile status, bot availability, moderation acceptance, token availability, provider permission or production readiness.

Public GitHub main, approved governance and the current Module 10 playbook remain the source of truth. No numbered open decision is closed by implication.

## 3. Module boundary

MAX Adapter owns MAX-specific verification, identity references, event intake, replay/deduplication classification, command/callback/button/deep-link normalization, future Mini App validation boundary, outbound provider-request mapping, provider-outcome mapping and safe adapter diagnostics.

MAX Adapter does not own:

- internal Account, account_id, account creation, account merge, roles, credentials, sessions or authorization;

- tariffs, payments, subscriptions or entitlement grants;

- Beacon source validation, creation, configuration or lifecycle;

- Parser extraction or Avito provider evidence;

- Scan baseline, observations, differences, listing state or recovery decisions;

- Egress route, lease, agent or transport state;

- generic Notification outbox, eligibility, attempt lifecycle or final generic delivery state;

- Telegram provider mapping or Telegram payload semantics;

- Web Cabinet screens, web sessions or Mini App frontend;

- Admin and Support mutation authority;

- raw MAX tokens, webhook secrets, private keys or provider credentials.

MAX Adapter must use public contracts of owning modules and must never mutate their internal state directly.

## 4. Owner decisions
### 4.1. MAX is a future and secondary channel

MAX is a future and secondary project channel.

Telegram remains the first practical channel for notifications and user control.

MAX must not block the MVP or displace Telegram.

Notification Delivery remains provider-neutral and generic.

Telegram Adapter and MAX Adapter remain separate provider-specific boundaries.

Telegram payload formats are not MAX payload authority.

Future MAX support remains conditional on accepted eligibility, moderation, credential, runtime, delivery, privacy, security and UX gates.

### 4.2. Eligibility, profile, bot and moderation remain unproven

MAX partner eligibility, partner or verified-profile status, bot creation, moderation status, token availability and production provider permission are unproven and blocked until safe accepted evidence exists.

The project must not assume that:

- the owner satisfies MAX partner eligibility;

- a required partner or verified profile exists;

- a MAX bot can be created;

- moderation has been submitted or accepted;

- a bot token or provider credential exists;

- production provider access has been granted.

Allowed evidence is limited to safe status references, redacted provider references, secret-presence evidence and moderation-status references. Raw tokens, credentials, private keys, legal or personal provider documents, unnecessary personal data and real raw provider payloads are forbidden in Git, prompts, reports, fixtures and ordinary logs.

### 4.3. First scope is personal chat only

The first MAX scope is personal chat between one user and the bot.

Groups and channels remain blocked until a separate exact owner decision and accepted permission, membership, admin-right, recipient, privacy and authorization boundaries exist.

Group membership, chat title, username, avatar, display name and provider profile metadata are not internal identity or account ownership.

MAX user, chat, message, update, callback and bot identifiers remain external provider identifiers.

A MAX provider identifier is never an internal account_id, account ownership proof or authorization decision.

Identity & Access remains the authority for account resolution, linking, creation semantics, authorization and merge policy.

### 4.4. Mini App is a future validation and handoff boundary only

MAX Mini App is a future server-side validation and handoff boundary only.

Module 10 does not implement Mini App screens, frontend, Web Cabinet screens, hosting, launch URLs, final UX composition, provider configuration or runtime endpoints.

Raw MAX WebAppData or equivalent launch data remains untrusted client input.

A future accepted backend task must validate raw launch evidence server-side under accepted official rules.

Validated MAX identity remains an external provider identity and must pass through Identity & Access.

Mini App launch context is not authorization.

The maximum accepted auth_date age and related freshness policy remain future decisions.

### 4.5. No phone or contact request in the first scope

The first MAX scope must not:

- request phone or contact data through MAX;

- use phone or contact as an account key;

- merge accounts by phone or contact;

- store contact data in fixtures, prompts or ordinary logs;

- treat manually forwarded or entered contact data as provider-verified identity;

- invent phone-required, retention or deletion policy.

Future contact sharing requires a separate exact owner decision, privacy boundary, trust rule, retention policy and provider-verifiable evidence rule.

### 4.6. Common product intents, separate untrusted MAX payloads

MAX commands, callbacks, buttons and deep links may later normalize into common internal product intents.

MAX provider payload remains separate, MAX-specific and untrusted.

Telegram callback, command, button and deep-link formats must not be copied as MAX authority.

A command, callback payload, button click, deep-link parameter, client-visible identifier, chat identifier or Mini App launch context is not authorization.

Business action requires server-side identity resolution, ownership and authorization by the owning module.

MAX Adapter may normalize an intent but must not create or mutate a Beacon, create or merge an Account, grant entitlement, decide generic Notification eligibility or execute a destructive business action.

Exact command catalog, callback format, button UX and deep-link format remain future gates.

### 4.7. Webhook direction and Long Polling restriction

The current production update-delivery direction is Webhook under current accepted evidence.

This governance direction does not create or authorize a Webhook subscription, endpoint, domain, TLS configuration, certificate, port, listener, service, queue, worker, credential, provider call or production runtime.

Long Polling may be considered only for a separately approved development or test context.

Long Polling is not a production fallback.

Active Webhook and Long Polling are mutually exclusive for the same bot and environment.

A future Long Polling marker is a provider cursor only; it is not business identity or a universal event idempotency key.

Mode transition, authenticity verification, acknowledgement point and marker advancement remain future operations and security gates.

### 4.8. Provider acceptance is not final business success

A MAX provider accepted result does not prove human read, human click, final user-visible delivery, generic Notification success or business success.

MAX Adapter returns an explicit provider-specific success, failure or ambiguity outcome.

Notification Delivery remains the authority that accepts provider outcomes into the generic delivery lifecycle.

Unknown, interrupted or possible-send-without-result effect is reconciliation-first.

Unknown effect is not success.

Unknown effect is not proven failure unless evidence establishes failure.

Unknown or ambiguous provider effect must never be retried blindly.

Provider rejection, authentication failure, unavailability, rate limitation, malformed response and ambiguity must remain explicit outcomes.

## 5. Data minimization

Raw MAX payloads are not ordinary logs or fixtures by default.

Future minimized semantic records may contain only contract-required safe references, classifications, fingerprints, safe reason codes and correlation or causation identifiers after separate accepted gates.

Forbidden by default:

- raw MAX bot token;

- webhook secret;

- private key;

- credentials;

- full raw provider payload retention;

- private-message archives;

- unnecessary profile data;

- phone or contact data;

- legal or personal provider documents;

- unbounded retention.

## 6. Open decisions preserved

The following remain OPEN where applicable:

- OD-006 — exact phone/password login and recovery policy;

- OD-007 — whether and when phone is required;

- OD-008 — account merge and cancellation policy;

- OD-012 — future channels beyond Telegram and MAX;

- OD-013 — retention and deletion of logs, history, provider records and personal data;

- OD-014 — future Web Cabinet screens, analytics depth and UI interaction.

Also blocked until separate exact gates: MAX eligibility, profile state, bot creation, moderation, token lifecycle, supported update types, group/channel support, command catalog, callback/button/deep-link formats, Mini App screens and freshness threshold, Webhook topology and authenticity, Long Polling environments, marker persistence, retry budgets, provider SDK, physical schema, runtime and deployment topology.

Open means blocked. No later task may invent these values.

## 7. Explicitly blocked implementation

This owner decision capture does not authorize:

- product or runtime source code;

- semantic Python contracts;

- tests or fixtures;

- real provider payloads or provider SDK;

- partner enrollment, profile creation, bot creation or moderation submission;

- token handling or MAX API calls;

- Webhook subscription or endpoint;

- Long Polling loop;

- Mini App frontend;

- physical database schema, ORM models, migrations or persistence;

- queue, worker, scheduler or service;

- endpoint, domain, TLS, certificate, port or listener;

- Docker, CI/CD or deployment;

- direct mutation of Identity, Notification, Beacon, Scan, Egress, Entitlements, Telegram, Web Cabinet, Admin or Support state.

## 8. Roadmap consequence

After this document, ADR-0023 and the append-only corrective ADR are published and independently verified and accepted:

MX-01 governance capture is complete;

later exact semantic MAX Adapter tasks may use these owner decisions without inventing product policy;

MX-02 may be considered only after a fresh GitHub main, parallel-main, Module 10 playbook, Identity & Access and Notification Delivery dependency verification;

MX-02 still requires a separate exact task;

no runtime, provider, secret, persistence, database, migration, queue, worker, Mini App, Webhook, Long Polling or deployment gate opens automatically.

This document does not authorize the CLI executor to select the next roadmap step.
