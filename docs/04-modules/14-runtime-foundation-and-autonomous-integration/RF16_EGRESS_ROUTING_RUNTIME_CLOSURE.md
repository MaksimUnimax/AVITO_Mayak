# RF16 Egress Routing durable runtime corrective closure

Technical ID: `RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01`
Expected base: `151b1956ac059166a6c8b5a960196a5fd344103e`
Previous candidate: `151b1956ac059166a6c8b5a960196a5fd344103e`
Previous hosted failures: `30783243880` and `30784771463`; jobs/artifacts were independently verified absent for `30784771463`.

## Previous publication and root cause

The first corrective hosted failure (`30783243880`) was the canonical
file-backed-secret/bootstrap boundary failure. The next hosted candidate
(`30784771463`) failed earlier: `.github/workflows/ci-rf16-acceptance.yml`
contained `with: {ref: ${{ github.sha }}}`; the YAML loader rejected the
workflow before job graph creation. Its five-transition classification is
`HARNESS_WORKFLOW_SYNTAX_DEFECT`, not PostgreSQL failure or external access.

## Corrective facts

This corrective uses block YAML checkout pinned to the trigger candidate SHA,
the canonical file-backed Mayak bootstrap, external expected-SHA and exact
Alembic-head verification, raw independently checkable observations, accepted
Module-07 selection facts, measured restart/expiry/concurrency boundaries,
strict protocol/parser/simulator matrices, an immutable frozen verifier
registry and an independent meta-gate. No schema or migration is changed.

The committed closure is source/package closure only. Final hosted run/job/
artifact identities and exact hosted counts belong in the executor/controller
report and workflow artifacts, not in a post-run evidence-only commit.

Hosted run/job/artifact, strict-verifier count, tamper count, package digest,
and PostgreSQL/Python/uv identities are intentionally `PENDING` until the
single post-publication hosted run completes. No hosted success is implied.

External residual: `WINDOWS_LIVE_PROOF_OPERATOR_ONLY_CONTINUE`.
Production readiness is not claimed.

`PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
