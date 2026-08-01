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
