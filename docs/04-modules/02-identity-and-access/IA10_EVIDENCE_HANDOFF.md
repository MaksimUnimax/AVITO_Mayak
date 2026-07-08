# Маяк Авито — Identity & Access IA-10 evidence handoff

Status:
- Module: 02-identity-and-access
- IA-10 status: HANDOFF_ONLY / NO_PRODUCT_FEATURES
- Source of truth branch: main
- Accepted IA-01 SHA: f75e6ac0c98773f1885e97653df0714e64d05e88
- Accepted IA-05 SHA: 9bdd992070b12163a197a14519bc482f7eadbe2a
- Handoff created at SHA: 9bdd992070b12163a197a14519bc482f7eadbe2a

## 1. Accepted implementation evidence
- IA-01 summary: introduced the initial semantic identity-and-access contract package with immutable pydantic primitives, provider-neutral enums, safe synthetic fixture IDs, and boundary/contract/unit checks for account, identity, contact, credential, role, session, challenge, and link semantics.
- IA-01 changed paths:
  - `src/mayak/modules/identity_and_access/__init__.py`
  - `src/mayak/modules/identity_and_access/contracts.py`
  - `src/mayak/modules/identity_and_access/fixtures.py`
  - `tests/architecture/test_identity_and_access_boundaries.py`
  - `tests/contract/test_identity_and_access_imports.py`
  - `tests/unit/test_identity_and_access_contracts.py`
- IA-05 summary: extended the semantic contract surface with actor-context validation, audit references, role and target scopes, and role-assignment decision semantics, while expanding safety checks and fixture coverage.
- IA-05 changed paths:
  - `src/mayak/modules/identity_and_access/__init__.py`
  - `src/mayak/modules/identity_and_access/contracts.py`
  - `src/mayak/modules/identity_and_access/fixtures.py`
  - `tests/architecture/test_identity_and_access_boundaries.py`
  - `tests/contract/test_identity_and_access_imports.py`
  - `tests/unit/test_identity_and_access_contracts.py`

## 2. Semantic contract boundary
- account_id boundary: `account_id` remains the internal immutable account boundary.
- provider identity is not account: Telegram/MAX provider identity links to an account and does not replace `account_id`.
- contact point remains contact-only: `ContactPoint` is a contact channel with verification state; phone requiredness remains open.
- credential reference has no raw secret material: `CredentialReference` stores only a reference, not password, token, code, or secret content.
- actor context validation semantics: `ActorContext` captures validation state with explicit semantic outcomes, not runtime authentication mechanics.
- role assignment / role scope / target scope semantics: role assignment remains server-authorized and scoped; `RoleScope` and `TargetScope` are separate semantic primitives.
- audit reference safety: `AuditReference` records safe reference values only and excludes raw payload or secret material.

## 3. Checks evidence
- IA-01 checks from accepted report: architecture boundary test, package import/contract test, and unit contract test were added for forbidden runtime imports, export surface, frozen/forbid models, semantic enums, contact-only behavior, and fixture-ID stability.
- IA-05 checks from accepted report: the same test surfaces were extended for actor-context validation, role/target scope semantics, audit-reference safety, provider-display authority rejection, and expanded forbidden import roots.
- Note that this handoff task changes docs only.

## 4. Explicitly not implemented
- no auth runtime
- no password hashing
- no credential store
- no raw credentials / one-time codes / provider tokens
- no sessions/cookies/JWT/OAuth
- no Telegram/MAX SDK calls
- no provider endpoints
- no bots/Mini App/Web Cabinet/Admin UI
- no DB schema / ORM / migrations
- no Docker/CI/CD/deploy/runtime services
- no OD-006/OD-007/OD-008/OD-013 closure

## 5. Roadmap state after IA-10
- IA-01 accepted
- IA-05 accepted
- IA-02 not allowed: provider verification contract gate missing
- IA-03 blocked
- IA-04 blocked
- IA-06 blocked
- IA-07 not allowed
- IA-08 blocked
- IA-09 blocked
- IA-10 handoff created

## 6. Next safe decision points
- provider verification contract boundary for IA-02/IA-07
- OD-006/OD-007/OD-008/OD-013 remain open
- physical schema/migration gate remains closed
- product-code/runtime remains prohibited until separate accepted gates
