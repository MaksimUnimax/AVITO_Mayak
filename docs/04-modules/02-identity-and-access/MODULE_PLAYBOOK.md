# Маяк Авито — Identity & Access Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 13 of 24
**Дата:** 2026-07-07
**Модуль:** `02-identity-and-access`
**Основание:** Architecture Baseline v1.1, Platform & Contracts Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Technical Baseline v1.0, Acceptance Matrix v1.1, Target Model v0.1 and OPEN_DECISIONS.md.
**Не является:** product-code, auth implementation, password policy, session technology, database schema, migration, provider integration, bot, Mini App, Web Cabinet implementation, credential store, runtime configuration or permission to implement.

---

## 1. Назначение

Identity & Access владеет внутренней account boundary, проверяемыми способами идентификации, контактными точками, credential references, server-authorized roles, sessions and account-linking challenges.

Модуль обеспечивает единый `account_id` для Telegram, MAX and future Web Cabinet so that customer state is not duplicated by channel adapters or UI surfaces.

## 2. Границы и non-ownership

Identity & Access owns:

- `Account`;
- `AccountIdentity`;
- `ContactPoint`;
- `CredentialReference`;
- `RoleAssignment`;
- `AuthSession`;
- `AuthChallenge`;
- `IdentityLinkChallenge`;
- safe authentication/authorization audit references.

It does not own:

- tariffs, entitlements, subscriptions or payments;
- Beacons, source URLs or Beacon configuration revisions;
- Avito parser state;
- scan/listing history;
- egress routes or agents;
- notification events, outbox or delivery attempts;
- Telegram/MAX provider payload mapping;
- Admin & Support work items;
- Web Cabinet presentation state;
- Filter Catalog definitions.

Adapters, Web Cabinet and Admin may ask Identity & Access for verified actor/account/role facts through approved contracts, but they do not become identity owners.

## 3. Confirmed decisions

1. `account_id` is the immutable internal account boundary.
2. Telegram identity, MAX identity, email, phone and local credentials link to an account; none replaces `account_id`.
3. Bot-first entry creates or resolves an account through a verified provider identity.
4. Phone is a contact point with verification state, not a primary key.
5. Automatic account merge by username, display name, avatar, phone, email or weak correlation is forbidden.
6. Linking a second messenger requires a one-time, short-lived, server-created challenge and explicit confirmation.
7. Role assignment is server-authorized and audited; UI flags, provider usernames or chat names are not authorization.
8. Credential material, one-time codes and provider payloads are excluded from common contracts, ordinary logs, fixtures and reports.
9. Protected mutation requires contract validation, verified actor context, authorization, ownership/scope validation, idempotency, commit point and audit outcome.

## 4. Open decisions and blockers

The playbook does not resolve:

- `OD-006` — exact phone+password and recovery policy;
- `OD-007` — when phone is required, if ever;
- `OD-008` — merge policy for two accounts and whether merge can be undone;
- `OD-013` — retention of history, logs and personal data;
- exact session TTL;
- exact identifier encoding;
- password hashing algorithm and credential-store product;
- email delivery provider;
- phone verification provider;
- rate-limit values;
- admin role taxonomy beyond documented server-assigned role boundary;
- exact browser cookie/token/session implementation.

Open means blocked for implementation defaults. Future task may only implement a subset that avoids unresolved decisions.

## 5. Authoritative state

| Record | Purpose | Required boundary |
|---|---|---|
| `Account` | Internal customer/operator boundary | one internal owner of account-scoped state |
| `AccountIdentity` | Link between account and provider/local identity | provider identity is not account |
| `ContactPoint` | Email/phone/contact channel and verification state | phone requiredness remains OD-007 |
| `CredentialReference` | Reference to protected credential material | raw credential value never enters ordinary state |
| `RoleAssignment` | Server-side role in explicit scope | UI/provider display data does not authorize |
| `AuthSession` | Future session state | exact technology and TTL deferred |
| `AuthChallenge` | Email/phone/login/recovery challenge lifecycle | raw one-time code excluded from ordinary logs |
| `IdentityLinkChallenge` | One-time proof for linking identities | merge policy remains OD-008 |

## 6. Public input families

Exact Python and wire schemas remain future task scope. Semantic contract families:

| Input family | Purpose |
|---|---|
| `ResolveProviderIdentityRequest` | Resolve or create account from a verified Telegram/MAX provider identity |
| `RegisterEmailIdentityRequest` | Start future email identity registration after email-policy gates |
| `RegisterPhoneContactRequest` | Register/verify phone contact without making it primary key |
| `StartIdentityLinkChallengeRequest` | Create a short-lived challenge to link a second identity |
| `CompleteIdentityLinkChallengeRequest` | Verify and attach second identity to same account |
| `StartAuthChallengeRequest` | Start email/phone/recovery/login challenge where policy allows |
| `CompleteAuthChallengeRequest` | Complete a challenge and return authorized outcome |
| `CreateAuthSessionRequest` | Create a future session for a verified actor |
| `ValidateActorContextRequest` | Validate caller identity for protected operations |
| `AssignRoleRequest` | Server-authorized role assignment in explicit scope |
| `RevokeRoleRequest` | Server-authorized role revocation in explicit scope |
| `PrepareAccountMergeRequest` | Prepare merge only after OD-008 is resolved |
| `ExecuteAccountMergeRequest` | Execute merge only under approved policy and audit gates |

Mutation-capable inputs require idempotency key, verified actor context and authorization where applicable.

## 7. Public output families

| Output family | Meaning |
|---|---|
| `AccountResolutionOutcome` | existing account, newly created account, rejected or ambiguous |
| `IdentityLinkChallengeOutcome` | created, expired, completed, rejected or already-linked |
| `AuthChallengeOutcome` | created, completed, expired, rejected or rate-limited |
| `ActorContextValidationOutcome` | verified, unauthenticated, forbidden, ambiguous or stale |
| `RoleAssignmentOutcome` | assigned, unchanged replay, rejected, revoked or conflict |
| `SessionOutcome` | created, refreshed, revoked, expired or invalid |
| `AccountMergeAssessment` | blocked, safe-to-present, conflict, unsupported or approved-ready |
| `AccountMergeOutcome` | completed, rejected, partial/blocked, reconcile-required |

Outputs do not imply transport, cookie, JWT, OAuth, provider SDK or database implementation.

## 8. Authorization and role boundary

- Server-side role assignment is authoritative.
- `client` role may be created for normal first provider entry.
- Admin/operator roles are never derived from username, phone, provider display name, chat title or client-supplied flag.
- Protected operator action requires actor identity, role scope, target scope and audit evidence.
- Other modules must call Identity & Access or an approved auth service for verified actor context; they must not parse provider payloads as authorization.

## 9. Identity linking

Required semantics:

1. user is verified in one existing channel or session;
2. user requests linking another identity;
3. server creates `IdentityLinkChallenge` with target provider and expiration;
4. challenge token contains no permanent account identifier in cleartext;
5. second provider ingress is verified by that provider adapter;
6. challenge completion is idempotent;
7. result links exactly one identity to the account or returns explicit failure;
8. audit records safe actor, target and outcome references.

Automatic merge and silent linking are prohibited.

## 10. Account merge

Run 13 does not approve account merge implementation.

Before merge can be implemented, OD-008 must define:

- proof required for both accounts;
- primary account selection;
- reversible/irreversible boundary;
- tariff/Beacon/notification consequences;
- conflict handling;
- audit and customer notification;
- rollback or roll-forward policy.

Until then, two accidentally created accounts may only be detected and shown as a protected support/workflow problem, not merged automatically.

## 11. Credential and challenge safety

- Raw passwords, one-time codes and provider tokens do not enter common contracts, audit records, fixtures or ordinary logs.
- Credential storage is represented only as `CredentialReference` until a separate implementation task selects and proves safe mechanics.
- Challenge attempts require rate-limit policy before implementation.
- Recovery cannot rely only on phone possession because phone can be reassigned.
- Email confirmation and phone confirmation are contact verification methods, not proof of all account ownership by themselves.

## 12. Sessions

Future sessions must preserve:

- internal `account_id` scope;
- verified actor category;
- issued/revoked/expired semantic states;
- server-side authorization checks for protected actions;
- revocation and audit boundary;
- no duplicate user database in Web Cabinet.

Exact session technology, cookie/token format, TTL, refresh policy and storage remain deferred.

## 13. Dependencies

Allowed after exact implementation gates:

- Platform & Contracts common primitives;
- Pydantic v2 for serialization/validation boundaries;
- FastAPI only at API entrypoint transport boundary;
- SQLAlchemy/Psycopg/Alembic only after database gates;
- PostgreSQL authoritative records after physical schema approval;
- pytest/pytest-asyncio/RESpx for deterministic tests;
- standard cryptographic primitives only after a security implementation task names exact algorithms and libraries.

Forbidden leakage:

- provider SDK types in Identity public contracts;
- Telegram/MAX raw payload as account authority;
- ORM/session objects in public interfaces;
- Web Cabinet cookie/session types as domain contracts;
- raw credential values in tests or reports;
- foreign user database in adapters or Web Cabinet.

## 14. Fake dependencies and test doubles

Future fakes may model:

- `ProviderIdentityVerifier`;
- `ContactPointVerifier`;
- `CredentialHasher` as an interface only;
- `ChallengeCodeGenerator` returning safe synthetic values;
- `ActorContextVerifier`;
- `AuthorizationPolicy`;
- `IdentityRepository`;
- `SessionStore`;
- `AuditSink`;
- `Clock`;
- `IdGenerator`.

Fakes use synthetic identities and contacts only and never prove provider production behavior.

## 15. Required fixtures and test vectors

Minimum fixture IDs:

- `FX-IA-PROVIDER-FIRST-TELEGRAM-001`;
- `FX-IA-PROVIDER-FIRST-MAX-001`;
- `FX-IA-SAME-PROVIDER-REPLAY-001`;
- `FX-IA-WEAK-SIGNAL-NO-MERGE-001`;
- `FX-IA-LINK-CHALLENGE-CREATED-001`;
- `FX-IA-LINK-CHALLENGE-EXPIRED-001`;
- `FX-IA-LINK-CHALLENGE-REPLAY-001`;
- `FX-IA-LINK-FOREIGN-ACCOUNT-REJECTED-001`;
- `FX-IA-PHONE-CONTACT-OPTIONAL-001`;
- `FX-IA-EMAIL-CHALLENGE-CODE-REDACTED-001`;
- `FX-IA-ROLE-ASSIGNMENT-AUTHORIZED-001`;
- `FX-IA-ROLE-ASSIGNMENT-FORBIDDEN-001`;
- `FX-IA-SESSION-REVOKED-001`;
- `FX-IA-MERGE-BLOCKED-OD008-001`.

Run 13 creates no fixture files.

## 16. Acceptance Matrix coverage

Run 13 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-DATA-001`;
- `AM-DATA-006`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-004`;
- module-playbook adoption gates from Acceptance Matrix section 9.

Rows requiring runtime state, locks, provider verification, migrations, sessions or reconciliation execution remain future gates.

## 17. Allowed future changes

A later exact task may:

- create Identity & Access package skeleton inside the approved layout;
- define semantic contract classes after Platform primitives exist;
- implement synthetic account/identity/contact fixtures;
- implement validation and authorization order tests;
- implement provider-verified identity resolution only through Telegram/MAX adapter contracts;
- add database schema only after physical model and migration gates;
- add password/session/challenge implementation only after OD and security gates.

## 18. Forbidden changes

Without new accepted decisions/tasks, this module must not:

- close OD-006, OD-007 or OD-008 by assumption;
- make phone mandatory by default;
- merge accounts by weak signal;
- create credential storage, password hashing, session cookie, JWT or OAuth flow;
- create bots, provider endpoints, Mini Apps or Web Cabinet screens;
- own tariffs, Beacons, parser, notification or provider adapter state;
- create product-code, dependency file, lockfile, executable tests, fixture files, migrations, database, Docker/CI/CD, service, port, deploy or runtime configuration.

## 19. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `IA-01` | Identity semantic contracts and synthetic fixtures | `NOT_STARTED` | Platform primitives and exact task |
| `IA-02` | Account/provider identity resolution | `NOT_STARTED` | Telegram/MAX adapter verification contracts |
| `IA-03` | Contact point verification model | `BLOCKED` | OD-007 and provider/contact evidence |
| `IA-04` | Auth challenge lifecycle | `BLOCKED` | OD-006, rate-limit and credential policy |
| `IA-05` | Role assignment and actor context | `NOT_STARTED` | exact authorization scope task |
| `IA-06` | Session semantics | `BLOCKED` | session technology and TTL decision |
| `IA-07` | Identity linking challenge | `NOT_STARTED` | provider adapters and exact task |
| `IA-08` | Account merge | `BLOCKED` | OD-008 |
| `IA-09` | Persistence and migrations | `BLOCKED` | physical schema and migration gates |
| `IA-10` | Full evidence/handoff | `NOT_STARTED` | applicable subtasks complete |

## 20. Task packet requirements

A future task must include exact paths, stable ID, parent SHA, allowed/forbidden scope, idempotency, rollback, fixtures, matrix rows, static/runtime checks, evidence format, final marker and prohibition on unrelated module work.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook.

## 21. Acceptance criteria

The playbook is acceptable only when:

- account/identity/contact/credential/session/challenge ownership is explicit;
- Telegram, MAX, Web Cabinet and Admin are not identity owners;
- OD-006, OD-007 and OD-008 remain open;
- weak-signal merge is prohibited;
- credential/challenge/session details are gated;
- contracts remain transport/provider/framework/ORM neutral;
- fixtures and matrix coverage are named;
- roadmap does not authorize implementation;
- no code, dependency, lock, test, fixture file, migration, database, Docker/CI/CD, deploy/runtime, service, port or sensitive access material is created;
- GitHub publication and exact server synchronization are independently verified.

## 22. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### IA-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 13 initial Identity & Access account, identity, contact, credential-reference, role, session, challenge and account-linking boundaries defined.
- OD-006, OD-007 and OD-008 remain unresolved.
- No implementation artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
