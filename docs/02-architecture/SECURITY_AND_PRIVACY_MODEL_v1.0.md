# Маяк Авито — Security and Privacy Model

**Версия:** 1.0  
**Статус:** APPROVED documentation baseline  
**Дата:** 2026-07-07  
**Основание:** target model v0.1, ADR-0001 through ADR-0006, TASK-001 accepted evidence.  
**Не является:** implementation design, secrets-manager choice, authorization library choice, retention schedule, legal opinion or production security certification.

---

## 1. Purpose

Этот документ фиксирует framework-independent security and privacy requirements для будущих contracts, data model, adapters, operations and module playbooks.

Он не разрешает implementation and does not select security products or cryptographic libraries.

## 2. Trust boundaries

| Boundary | Incoming data | Required future treatment |
|---|---|---|
| Client interface | Commands, forms, links, button actions | Untrusted until server-side authorization and validation |
| Telegram/MAX | Webhooks, Mini App payloads, external identities | Verify authenticity and freshness by official provider rules |
| Avito source | Search pages, parameters, listing fields and response failures | Treat as external/untrusted; never convert incomplete result into a clean empty result |
| Admin/support | Privileged human actions | Server-side authorization, audit and least-privilege policy |
| Egress route | Route state, health and parser transport outcome | Isolated dependency; no false-success state |
| Internal module boundary | Commands/events/read models | Only approved contracts; no direct foreign-state mutation |
| Runtime and secrets | Configuration, tokens, passwords, keys | Never expose through source, ordinary logs or task reports |

## 3. Mandatory security invariants

### 3.1. Identity and access

- Internal `account_id` is the stable account identity.
- Telegram, MAX, email, phone and browser identities do not become equivalent automatically.
- Identity merge requires explicit proof of control over both sides, an audited protected operation and separate approved policy.
- Role checks occur server-side for every protected action; hidden UI is not authorization.
- Moderator access is read-only for foreign customer data unless a separate approved role policy changes this.
- Administrator access must not expose raw secrets, passwords, tokens or one-time codes.

### 3.2. Credentials and tokens

- Passwords are stored only as durable password hashes.
- Raw passwords, tokens, one-time codes and private keys must not be emitted into ordinary logs, reports, fixtures, source files or UI.
- One-time and authentication artifacts require bounded lifetime, replay protection and auditable state; exact values remain an open contract/security design item.
- Future secret delivery, rotation, revocation and storage mechanism are open decisions and cannot be implied by host availability.

### 3.3. External payload integrity

- Telegram, MAX webhook and Mini App payloads require provider-specific cryptographic validation before trusted use.
- Replay, duplicate delivery, timeout and repeated user action require idempotency handling.
- External URL, template or parameter values must not be passed directly into shell commands.
- Parser result ambiguity, CAPTCHAs, access denial, malformed structures and route failures must become explicit error/warning states, not a fabricated empty result.

### 3.4. Audit

At minimum, future audit requirements cover:

- role and access changes;
- ban/unban actions;
- entitlement and manual-access changes;
- protected account merge actions;
- Beacon configuration changes;
- route and critical operational changes;
- security-sensitive administrative actions.

Audit records must not contain raw secrets or unnecessary personal content.

## 4. Privacy and data minimization

The product collects and displays only data necessary for the defined monitoring function.

Current target-model limits include:

- do not collect or show phone numbers, seller information, full descriptions, view counts or hidden technical fields as normal client-card data;
- a phone number is not a primary account key and must not be used for automatic identity merge;
- personal data and logs require separate retention decisions;
- metrics and observability must not carry passwords, tokens, codes, full phone numbers or private message contents.

Any expansion of collected data needs a documented product, legal, privacy and security review before implementation.

## 5. Logging and evidence rules

- Security-relevant events must be observable without disclosing secrets.
- Task reports contain proof boundaries, not credentials, raw keys, raw external payloads or foreign host internals.
- Fixtures and test vectors use synthetic or redacted data unless an approved reference-evidence policy explicitly governs a safe alternative.
- A production incident workflow, retention period, log destination and alert channel are not selected by this document.

## 6. Security gates before implementation

Before a module accepts implementation work, its playbook and task must identify:

1. owner of protected state;
2. inbound trust boundary;
3. authorization rule;
4. validation and idempotency rule;
5. audit requirement;
6. logging/redaction rule;
7. fake dependency and safe test vector;
8. failure and rollback behavior;
9. relevant open decisions;
10. evidence required for external provider behavior.

## 7. Explicit open decisions

This baseline does not decide:

- concrete authentication/session protocol;
- password-hashing algorithm parameters;
- secrets-management product;
- encryption-at-rest implementation;
- data retention periods;
- breach/incident procedure;
- exact administrator permission matrix;
- legal basis and privacy notice text;
- phone-login policy;
- detailed account-merge and reversal policy;
- provider-specific verification implementation;
- key rotation schedule.

## 8. Prohibited shortcuts

- automatic account merge by username, avatar, phone or other weak correlation;
- client-side-only authorization;
- logging tokens, passwords, codes or raw secrets;
- shell interpolation of external values;
- treating a failed or partial parser result as no listings;
- use of foreign shared-host resources as project-owned security infrastructure;
- creating a security implementation before contracts, data policy and environment gates are accepted.

## 9. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый framework-independent security/privacy baseline without selecting implementation technology or secrets/deployment design. |
