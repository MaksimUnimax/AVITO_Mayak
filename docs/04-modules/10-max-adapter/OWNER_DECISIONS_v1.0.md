Маяк Авито — MAX Adapter Owner Decisions v1.0
1. Metadata

version: 1.0

date: 2026-07-19

module: 10-max-adapter

roadmap step: MX-01

technical task: MX-01-MAX-OWNER-DECISION-CAPTURE-20260719-01

governance classification: APPROVED owner decision capture

status: APPROVED_OWNER_INPUT_PENDING_INDEPENDENT_GITHUB_ACCEPTANCE

expected base: 9fff874f97ca74536e62a01ee2b6811c61c5cd8f

source-of-truth playbook: docs/04-modules/10-max-adapter/MODULE_PLAYBOOK.md

scope: documentation/governance-only

this document is not product code, provider runtime, persistence, deployment, provider permission evidence or permission to implement

2. Purpose and authority

This document freezes the owner-provided MAX Adapter decisions required for Module 10 roadmap step MX-01.

These decisions may be used by later exact semantic tasks only after the publishing commit is independently verified and accepted against public GitHub main.

This document records owner product direction. It does not claim new official MAX provider facts, partner eligibility, verified-profile status, bot availability, moderation acceptance, token availability, provider permission or production readiness.

Public GitHub main, approved governance and the current Module 10 playbook remain the source of truth. This capture does not close any numbered open decision by implication.

3. Module boundary

MAX Adapter owns MAX-specific verification, mapping, normalization and provider-outcome semantics at the boundary between MAX platform surfaces and internal project contracts.

MAX Adapter does not own:

internal Account, account_id, account creation, account merge, roles, credentials, sessions or authorization;

tariff, subscription, payment or entitlement state;

Beacon source validation, Beacon creation, Beacon configuration or Beacon lifecycle;

Parser extraction or Avito provider evidence;

Scan baseline, difference, observations, listing state or recovery decisions;

Egress route, lease, agent or transport state;

generic Notification outbox, generic delivery attempt lifecycle, eligibility or final generic delivery state;

Telegram provider mapping or Telegram payload semantics;

Web Cabinet screens, web sessions or Mini App frontend;

Admin and Support mutation authority;

raw MAX token material, webhook secrets, private keys or provider credentials.

MAX Adapter must use public contracts of Identity & Access, Notification Delivery, Beacon Management, Scan Orchestration, Egress Routing, Entitlements & Billing, Telegram Adapter, Web Cabinet, Admin and other owning modules. It must never write those modules' internal state directly.

4. Owner decision 1 — MAX is a future and secondary channel

MAX is a future and secondary project channel.

Telegram remains the first practical channel for notifications and user control.

This decision means:

MAX must not block the MVP;

MAX must not displace Telegram as the first practical provider adapter;

Notification Delivery remains provider-neutral and generic;

Telegram Adapter and MAX Adapter remain separate provider-specific boundaries;

Telegram provider payloads and MAX provider payloads must not be merged into one provider payload contract;

future MAX support remains conditional on accepted eligibility, moderation, credential, runtime, delivery, privacy, security and UX gates.

This decision does not close OD-012 and does not disable future channels.

5. Owner decision 2 — eligibility, profile, bot and moderation remain unproven

MAX partner eligibility, partner or verified-profile status, bot creation and moderation status are unproven and blocked until safe accepted evidence exists.

The project must not assume that:

the owner satisfies MAX partner eligibility;

a required partner or verified profile exists;

a MAX bot can be created;

moderation has been submitted or accepted;

a bot token or provider credential exists;

production provider access has been granted.

Future accepted evidence may use only safe status or redacted reference forms.

The public repository, ChatGPT prompts, CLI reports, fixtures and ordinary logs must not contain:

raw tokens;

webhook secrets;

private keys;

legal or personal provider documents;

credentials;

unnecessary personal data;

real raw provider payloads.

This decision does not create a partner profile, bot, moderation submission, token, provider permission or runtime.

6. Owner decision 3 — first scope is personal chat only

The first MAX scope is personal chat between one user and the bot.

Groups and channels remain blocked until a separate exact owner decision and later accepted contracts define permissions, membership, admin rights, recipient semantics, privacy and authorization.

The personal-chat scope does not authorize:

group delivery;

channel delivery;

group callbacks;

channel callbacks;

multi-user ownership;

account resolution from group membership;

account resolution from chat title, username, display name, avatar or profile metadata.

max_user_id, max_chat_id, max_message_id, callback identifiers and other MAX identifiers remain external provider identifiers.

A MAX provider identifier is never an internal account_id, account ownership proof or authorization decision.

Identity & Access remains the authority for account resolution, identity linking, account creation semantics, authorization and account merge policy.

7. Owner decision 4 — Mini App is a future validation and handoff boundary only

MAX Mini App is a future server-side validation and handoff boundary only.

Module 10 does not implement:

Mini App screens;

Mini App frontend;

Web Cabinet screens;

client-side account authority;

hosting;

launch URLs;

final UX composition;

provider configuration;

runtime endpoints.

Future raw MAX WebAppData or equivalent launch data remains untrusted client input.

A future accepted backend task must validate raw launch evidence server-side under accepted official rules before it can produce a verified external MAX identity reference.

Validated MAX identity remains an external provider identity and must still pass through Identity & Access account-resolution and authorization contracts.

Mini App launch context is not authorization and does not permit direct mutation of Account, Beacon, Notification, Entitlements or other owning-module state.

The maximum accepted auth_date age and related freshness policy remain future security and product decisions.

8. Owner decision 5 — no phone or contact request in the first scope

The first MAX scope must not request phone or contact data through MAX.

The first MAX scope must not:

ask the user to share a phone number or contact;

use phone or contact as an account key;

merge accounts by phone or contact;

store contact data in fixtures, prompts or ordinary logs;

treat a manually forwarded or manually entered contact as provider-verified identity;

invent a phone-required policy;

invent retention or deletion policy for phone or contact data.

Phone requiredness remains open under OD-007.

Account merge policy remains open under OD-008.

Retention and deletion of personal and provider data remain open under OD-013.

Any future contact-sharing adoption requires a separate exact owner decision, privacy boundary, trust rule, retention policy and provider-verifiable evidence rule.

9. Owner decision 6 — common product intents, separate untrusted MAX payloads

MAX commands, callbacks, buttons and deep links may later normalize into product intents that are also understood by internal modules.

The provider payload remains MAX-specific and untrusted.

MAX Adapter must not copy Telegram callback, button, command or deep-link payload formats as MAX authority.

The following are not authorization:

a MAX command;

a callback payload;

a button click;

a deep-link parameter;

a client-visible identifier;

provider profile data;

a chat identifier;

Mini App launch context.

A future allowed flow must preserve:

MAX provider input received → MAX-specific structure and provider evidence validated → replay and deduplication evaluated → verified external MAX identity resolved through Identity & Access → owning module evaluates authorization, ownership and action scope → owning module performs an accepted business mutation.

MAX Adapter may normalize an intent but must not:

create or mutate a Beacon directly;

create or merge an Account;

decide entitlement grants;

decide generic Notification eligibility;

mutate Scan or Egress state;

execute a destructive business action by itself.

Exact command catalog, callback format, button UX and deep-link format remain future gates.

10. Owner decision 7 — Webhook direction and Long Polling restriction

The current production update-delivery direction is Webhook.

This is a governance direction only.

It does not create or authorize:

a Webhook subscription;

a Webhook endpoint;

a domain;

TLS configuration;

a certificate;

a port;

a listener;

a service;

a queue or worker;

provider credentials;

a provider call;

production runtime.

Long Polling may be considered only for a separately approved development or test context.

Long Polling is not a production fallback.

Active Webhook and Long Polling are mutually exclusive for the same bot and environment.

This capture does not create a polling loop, marker storage, scheduler, service or mode transition.

A future Long Polling marker is a provider cursor only. It is not business identity or a universal event idempotency key and must not advance before a future approved durable safe-processing point.

Endpoint ownership, domain, TLS, certificate, port, authenticity verification, acknowledgement point, mode transition and allowed development/test environments remain future operations and security gates.

11. Owner decision 8 — provider acceptance is not final business success

A MAX provider accepted response means only the accepted provider result class supported by future verified provider evidence.

It does not prove:

human read;

human click;

final user-visible delivery;

business success;

generic Notification delivery success;

successful account or Beacon mutation.

MAX Adapter returns an explicit provider-specific result, failure or ambiguity outcome.

Notification Delivery remains the authority that accepts provider outcomes into the generic notification lifecycle.

An unknown, interrupted or possible-send-without-result effect is reconciliation-first.

Unknown effect is not success.

Unknown effect is not proven failure unless evidence establishes failure.

Unknown or ambiguous provider effect must never be blindly retried.

Blind retry must not create a duplicate user-visible effect.

Provider rejection, authentication failure, unavailability, rate limitation, malformed response and ambiguity remain explicit outcomes and must not be collapsed into clean success.

12. Identity and ownership preservation

The internal project account_id remains the authoritative project user identity.

MAX user, chat, message, update, callback, bot and delivery identifiers remain external provider identifiers.

MAX Adapter may request Identity & Access resolution only after future accepted MAX-specific verification rules have produced sufficient provider evidence.

MAX Adapter must not:

create an internal Account directly;

maintain a MAX-only user database;

merge accounts;

infer identity from username, display name, avatar, phone, contact, chat title or group membership;

use max_chat_id as account ownership;

bypass Identity & Access challenges or authorization.

OD-006, OD-007 and OD-008 remain open where their exact login, phone and merge policies are not governed elsewhere.

13. Notification and business ownership preservation

Notification Delivery owns:

generic source-event intake;

generic eligibility;

outbox;

channel plan;

notification attempts;

generic deduplication;

generic delivery lifecycle;

acceptance of provider outcome into generic notification state.

MAX Adapter may later map one approved Notification attempt to one MAX-specific request intent and return one explicit MAX provider outcome.

MAX Adapter does not create generic outbox work and does not mark generic Notification delivery success by itself.

Beacon Management owns source validation, Beacon creation, configuration and lifecycle.

Scan Orchestration owns baseline, observations, differences, listing state and recovery facts.

Egress Routing owns route and transport state.

Entitlements & Billing owns tariff, subscription, payment and entitlement authority.

Telegram Adapter owns Telegram-specific provider mapping.

Web Cabinet owns web screens and sessions.

Admin and Support retain their own authority.

14. Data minimization and blocked retention

Raw MAX payloads are not ordinary logs or fixtures by default.

Future minimized semantic records may contain only contract-required safe references, classifications, fingerprints, safe reason codes, provider correlation references and correlation or causation identifiers after separate accepted gates.

Forbidden by default:

raw MAX bot token;

webhook secret;

private key;

full raw provider payload retention;

private-message archives;

unnecessary profile data;

phone or contact data;

legal or personal provider documents;

unbounded retention;

credentials in reports, prompts, URLs, logs, screenshots, fixtures or Git.

OD-013 remains open. This document does not select physical storage, retention, deletion, archive or compaction policy.

15. Explicitly blocked implementation

This owner decision capture does not authorize:

source code;

semantic Python contracts;

tests or fixtures;

real provider payloads;

provider SDK or library selection;

partner enrollment;

verified-profile creation;

bot creation;

moderation submission;

token handling;

MAX API calls;

Webhook subscription;

Webhook endpoint;

Long Polling loop;

Mini App frontend;

runtime;

physical database schema;

ORM models;

migrations;

persistence;

queue;

worker;

scheduler;

service;

endpoint;

domain;

TLS;

certificate;

port;

listener;

Docker;

CI/CD;

deployment;

direct mutation of Identity, Notification, Beacon, Scan, Egress, Entitlements, Telegram, Web Cabinet, Admin or Support state.

16. Open decisions preserved

This capture closes no numbered open decision by assumption.

The following remain open where applicable:

OD-006 — exact phone and password login and recovery policy;

OD-007 — whether and when phone is required;

OD-008 — account merge and cancellation policy;

OD-012 — future channels beyond Telegram and MAX;

OD-013 — retention and deletion of logs, history, provider records and personal data;

OD-014 — future Web Cabinet screens, analytics depth and UI interaction.

Also remaining as future exact gates:

owner MAX partner eligibility;

partner or verified-profile state;

bot creation and bot identity;

moderation submission and acceptance;

token availability, storage, rotation, revocation and deletion;

supported MAX update types;

exact chat and channel support;

command catalog;

callback and button payload formats;

deep-link formats;

Mini App screens and freshness threshold;

Webhook topology and authenticity mechanism;

Long Polling development and test environments;

marker persistence and advancement;

retry count, delay, backoff and rate budgets;

provider SDK or transport implementation;

physical schema and indexes;

runtime and deployment topology.

Open means blocked. No later task may invent these values.

17. Consequences and next admissible step

After this document and matching ADR-0023 are published and the publishing commit is independently verified and accepted:

MX-01 governance capture is complete;

later exact semantic MAX Adapter tasks may use these owner decisions without inventing product policy;

MX-02 may be considered only after a fresh GitHub main, parallel-main, Module 10 playbook, Identity & Access contract and Notification Delivery contract verification;

MX-02 still requires a separate exact task;

no runtime, provider, secret, persistence, database, migration, queue, worker, Mini App, Webhook, Long Polling or deployment gate is opened automatically.

This document does not authorize the CLI executor to select the next roadmap step.
