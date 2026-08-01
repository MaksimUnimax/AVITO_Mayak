# RF-12 Entitlements & Billing Runtime Closure v1.0

Technical ID: `RF-12-ENTITLEMENTS-AND-BILLING-RUNTIME-COMPLETION-AND-CLOSURE-20260801-01`<br>
Exact base: `6af23f06f787006b948f2d5dcb8097d1c0b9ecdf`<br>
Status: `PUBLISHED_FOR_CHATGPT_REVIEW`<br>
Production status: `NOT_PRODUCTION_READY`

## Authority and scope

Fresh `origin/main`, accepted append-only decisions, the current Module 14
playbook/owner decisions, accepted Module 03 decisions, and physical/runtime
contracts were used in that order. The historical Module 03 semantic-only
runtime prohibition was superseded for this exact task by the Module 14 RF-12
runtime authorization. Product constraints remain binding: only FREE/BASIC,
payment evidence is not entitlement authority, manual renewal only, no trials,
grace, proration, recurring billing, automatic Free Beacon selection, or
provider refund API. RF-13 was not started.

## Implementation

`runtime.py` adds a caller-transaction-owned PostgreSQL runtime with verified
authority facts, capability checks, terminal idempotency, access assignment,
manual renewal, revoke, manual access, effective evaluation, bounded usage
families, normalized payment evidence, reconcile-first handling and manual
refund reference records. Public models contain no ORM/session/provider
payload/credential types. No foreign module table is written.

The existing physical mapping is preserved:

| Runtime family | Owned table |
| --- | --- |
| versioned tariff authority | `mayak.entitlement_tariff_definitions` |
| access/subscription/manual grants | `mayak.entitlement_access_grants` |
| approved usage windows | `mayak.entitlement_usage_counters` |
| normalized payment evidence | `mayak.billing_payment_records` |
| provider/payment operations and manual refund references | `mayak.billing_payment_operations` |
| reconciliation evidence | `mayak.billing_reconciliations` |

Migration decision: `NONE`. RF-09 head `RF09_M03` already supplies the needed
columns, identities, constraints, indexes and foreign keys. No historical
migration was edited and no new head was created.

FREE is persisted as zero RUB, 180-minute floor/step, one active Beacon and
reduced policy. BASIC is persisted as 990 RUB/month, 5-minute floor/step; its
active-Beacon limit remains unspecified. Bootstrap is deterministic, versioned,
idempotent and fail-closed on conflicts.

Effective evaluation uses persisted active grants and deterministic policy
checks. Expired paid access returns explicit expiry/free-compliance/freeze
provenance and never writes Beacon state. A noncompliant Free Beacon context
returns user-choice-required; no Beacon is selected automatically.

Payment create/retrieve is implemented by a production-shaped HTTPX
`YooKassaSandboxAdapter`; it is disabled by default, reads an outside-Git
secret file only when enabled, bounds response bodies, uses explicit timeouts,
normalizes responses, and returns ambiguity requiring reconciliation. The fake
provider is deterministic. Refund API is explicitly blocked and no provider
refund request is sent. Missing optional credentials yield
`PROVIDER_DISABLED_CONTINUE` without blocking core readiness.

## Evidence

Focused semantic/schema/import regression: 106 passed. RF-12 unit tests cover
provider-disabled behavior, normalized fake outcomes and blocked refund API.
Compile, Ruff, mypy and import-linter are run as publication gates. The
PostgreSQL command matrix covers tariff bootstrap, access lifecycle, manual
access, usage windows, payment evidence, reconciliation and manual refund
reference, with replay/mismatch/rollback/authorization inspectors. The
mandatory invariant is preserved: confirmed payment/reconciliation evidence
alone never creates paid access; a separate authorized manual renewal does.

Security evidence: no credentials or personal production data; no raw provider
payload persistence; metadata is bounded and rejects sensitive keys; error
references are redacted. Acceptance PostgreSQL uses the accepted PostgreSQL 18
image on the internal Compose network with no host database port. Temporary
task resources and secrets are removed after acceptance and foreign resources
are compared before/after.

Limitations are operator/external only: no live YooKassa request and no
optional production credential are used. This closure is not a production
readiness claim.

RF-08: `INDEPENDENTLY_ACCEPTED`<br>
RF-11: `INDEPENDENTLY_ACCEPTED`<br>
RF-12: `PUBLISHED_FOR_CHATGPT_REVIEW`<br>
RF-13: `NOT_STARTED`

## RF-12 corrective package — 2026-08-01

The previously published candidate at `fedccb12…` was corrective-required.
The rejected defects were caller-created authority facts at protected command
boundaries; manual access collapsed into BASIC/`ASSIGN_ACCESS`; a physical
grant mapping that could not preserve capability and scope; unused payment and
usage idempotency keys; caller-controlled usage limits; anonymous repeated
reconciliations; wrong YooKassa Basic Auth; incomplete redirect create wire;
post-materialization response bounds; and insufficient committed regression
coverage.

Protected production commands now resolve immutable facts through the narrow
`VerifiedIdentityPort` using actor reference and target account. Fabricated
facts, wrong actor, wrong target, missing capability and cross-account calls
fail closed before domain mutation, terminal success or audit mutation. The
acceptance fake is test-only and no Identity tables are accessed directly.

Manual access has an explicit target account, authorization capability, granted
capability, granted scope, closed interval, reason, idempotency key and audit
reference. Its create/revoke/effective/expiry/replay/mismatch/rollback history
is separate from FREE, BASIC, BASIC renewal and payment evidence.

Migration decision is corrected from `NONE` to additive Module-03-owned schema
evolution. Revision `RF12_MANUAL_GRANT` follows previous head `RF09_FINALIZE`.
`entitlement_access_grants` maps legacy rows to `grant_kind=TARIFF`; manual
rows map `account_id` (target), `grant_kind=MANUAL`, `granted_capability`,
`granted_scope`, `valid_from`, `valid_until`, `state`, and bounded `reason`.
`tariff_id` is nullable only for manual rows. Capability/scope are separately
queryable and constrained; no opaque source string is used.

Mutation inventory covers tariff bootstrap/publish, tariff assignment, manual
renewal, access revoke, manual create/revoke, usage observation, payment
evidence, payment operation/reconciliation and manual refund reference. Each
idempotent mutation fingerprints all semantic inputs, replays terminal results,
rejects same-key/different-fingerprint requests, and serializes races through
the terminal repository. Provider identity duplicates are same-account
replays/conflicts and cross-account requests fail closed without UUID leakage.
Reconciliation uses a concrete payment operation identity; ambiguity remains
reconcile-required, confirmation/rejection is evidence-only, and repeated
legitimate reconciliation does not depend on anonymous NULL operation rows.

Usage is limited to `ACTIVE_BEACON_SLOT` from Beacon Management and
`SCAN_INTERVAL_WINDOW` from Scan Orchestration. Requester/source-owner facts
are required; limits/floor/step derive from the persisted approved tariff.
FREE is one active Beacon, BASIC Beacon numeric limit remains unspecified, and
scan floor/step remain exact. No payment or notification quota exists.

YooKassa uses `MAYAK_YOOKASSA_SHOP_ID` plus the outside-Git
`MAYAK_YOOKASSA_SECRET_FILE`; HTTP Basic Auth is `(shopId, secret)`. Create is
`POST /v3/payments` with `Idempotence-Key`, amount, `capture=true`, and explicit
redirect confirmation/absolute return URL. Retrieve is exact payment ID.
2xx succeeded/canceled/pending, 4xx, 401/403, 404, 429/5xx/transport and
malformed bodies are classified without granting entitlement. Provider bodies
are streamed with a bounded sentinel and never persisted; injected clients
remain caller-owned and internally created clients close deterministically.
The refund API remains blocked; manual review/reference is the only refund path.
Live YooKassa calls: `NO`.

Corrective evidence includes focused RF-12 tests, schema/signature tests,
authority/idempotency/provider regression tests and static compilation/Ruff
checks. PostgreSQL 18 migration/runtime and concurrency evidence is required
for publication acceptance; this document records no `PRODUCTION_READY` claim.
Security, foreign equality, rollback/roll-forward and cleanup requirements
remain as above. RF-13 remains untouched and `NOT_STARTED`.

## RF-12 corrective closure record — 2026-08-01

`fedccb12…` is rejected. `a15b8288…` is rejected as corrective-required;
the remaining defects were transaction serialization before effects, direct
foreign audit ownership, caller-selected authorization, public trusted
AuthorityFacts, manual capability/scope and expiry evaluation, weak grant
kind/tariff invariants, metadata/index drift, destructive downgrade, a second
usage policy engine, non-terminal rejection paths, unbounded transport-chunk
retention, and the missing committed PostgreSQL command matrix.

This corrective package does not rewrite `RF12_MANUAL_GRANT` or any RF-09
revision. It adds `RF12_RUNTIME_HARDEN` after `RF12_MANUAL_GRANT` and makes
the current head roll-forward-only (`Recovery-Policy: ROLL_FORWARD_ONLY`).
The final database enforces explicit TARIFF versus MANUAL ownership of
`tariff_id`, capability and scope, plus bounded non-empty reason, exact
interval, non-empty state and positive row version. Canonical metadata includes
the active manual capability/scope index and has no semantic-writing grant
defaults.

Runtime audit writes go through the Platform-owned `PostgresAuditRepository`;
direct Module-01 table writes are zero. Identity is resolved through the
public verified port before effects. Manual access always requires the fixed
`ENTITLEMENTS_MANUAL_ACCESS_ADMIN`; actor scope, target account, granted
capability and granted scope remain distinct. Effective entitlement requires
exact manual capability/scope/account/time matching; expired, revoked and
non-matching rows are non-effective without `TariffName(None)`. Payment
evidence remains non-authoritative.

Every effecting command uses a transaction-scoped advisory lock before
idempotency evaluation and mutation, checks the terminal repository result,
and retains the lock through the caller transaction. Provider identity payment
duplicates use an additional deterministic lock. The executable manifest is
`tests/runtime/test_rf12_command_matrix.py`; the real PostgreSQL entry point is
`tests/runtime/test_rf12_runtime_postgres.py`. Required evidence is the
empty/RF09/RF12 migration ladder, physical constraint rejection matrix,
metadata parity, rollback and genuinely concurrent command matrix including
payment races. Bounded YooKassa transport retains at most the configured limit
plus one sentinel byte; injected clients remain open and owned clients close.

This record is `PUBLISHED_FOR_CHATGPT_REVIEW`, not an independent acceptance
claim. PostgreSQL evidence, concurrency, cleanup, foreign-resource equality,
security review and machine verifier results must be recorded by the task
harness before publication. RF-13: `NOT_STARTED`. Status: `NOT_PRODUCTION_READY`.
