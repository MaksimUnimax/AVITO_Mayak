# RF16 Egress Routing durable runtime corrective closure

Technical ID: `RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01`
Expected base: `441eb4c86cc6e19eae2e0c826713209d653c3a3d`
Previous candidate: `441eb4c86cc6e19eae2e0c826713209d653c3a3d`
Previous hosted run/job: `30783243880` / `91591837769`

## Previous publication and root cause

The original RF16 partial publication preceded a complete source-level
production/evidence audit. The independently proven first failure was
`FileNotFoundError: secret path is not a regular file:
/run/secrets/mayak_database_migration_password`. PostgreSQL 18, the exact
candidate checkout, Python 3.14.6, uv 0.11.31 and frozen sync had passed.
The workflow created roles/schema and invoked `alembic/env.py`, whose canonical
`create_migration_engine -> build_migration_url -> resolve_secret_file` path
had no required file-backed secret or complete `MAYAK_DATABASE_*` boundary.
The workflow also invented `RF16_DSN` instead of reusing the accepted Mayak
bootstrap contract.

## Corrective facts

This candidate reuses the canonical file-backed Mayak bootstrap, requires an
explicit trusted lease validity input, adapts the accepted Module-07 selection
port, makes replay/conflict/terminal mutation fail closed, strictly validates
typed protocol messages, persists simulator replay across a process-equivalent
restart, emits raw PostgreSQL observations, and builds only the allowlisted
transport-neutral agent artifact. No schema or migration is changed.

Hosted run/job/artifact, strict-verifier count, tamper count, package digest,
and PostgreSQL/Python/uv identities are intentionally `PENDING` until the
single post-publication hosted run completes. No hosted success is implied.

External residual: `WINDOWS_LIVE_PROOF_OPERATOR_ONLY_CONTINUE`.
Production readiness is not claimed.

`PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
