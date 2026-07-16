# ER-15 Evidence Handoff

module: `07-egress-routing`
roadmap step: `ER-15`
latest accepted Egress semantic/code SHA: `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
current handoff base: `4cf497a8602ed934c8b00747d634e3b0df4d6e5f`

This document is evidence-only. It does not authorize route runtime, persistence, deploy, provider access, or any direct mutation of Parser, Scan, Notification, Beacon, Admin, or provider state.

## Prerequisite and accepted Egress SHA chain

Ordered chain preserved for this handoff:

1. `e858710` - `docs: bootstrap project governance and source documents`
1. `fb55ec2` - `docs: accept Run 18 Egress Routing playbook`
1. `bbe0691465e1b951980b33e5ee0ba2b0d9ab8127` - `er-01: capture egress owner decisions`
1. `9e5a7b05bc211282b59462be4148568321f0482e` - `er-01: capture egress owner decisions`
1. `cb30fffc20417b13153513043e973b2cbac93bce` - `er-02: correct canonical egress enum matrix`
1. `fa06c5e502910d5fbdd2efe9f168f870726a34b9` - latest accepted Egress semantic/code SHA
1. `16ec547eef68b800d17afd95e2a33274c5e68d5c` - `nd-13: add security privacy suppression semantics`
1. `d02b2ac0bf3845394f4c1b0677cf438e41b9818f` - `nd-14: add deferred runtime gate semantics`
1. `65afae19c25aa90bb2c9ceba68402f0a19e69f19` - `nd-15: add module 08 evidence handoff`
1. `4cf497a8602ed934c8b00747d634e3b0df4d6e5f` - current handoff base and parallel-main ND-15 marker correction

## Exact route proof statuses

Route proof is not production-proven. The exact proof statuses preserved in Module 07 synthetic evidence are:

| Fixture | Route family | Exact proof status |
|---|---|---|
| `FX-ER-AGENT-REGISTRATION-BLOCKED-001` | `LINUX_REFERENCE_STYLE_ROUTE` | `proof-gated`, `not-production-ready` |
| `FX-ER-REGISTERED-NOT-READY-001` | `RUSSIAN_RESIDENTIAL_ROUTE` | `provider-unselected` |
| `FX-ER-HEARTBEAT-NOT-READINESS-001` | `OWNER_DEVELOPMENT_BRIDGE_ROUTE` | `development-only`, `heartbeat-not-readiness` |
| `FX-ER-RELEASE-MISMATCH-BLOCKS-001` | `WINDOWS_BROWSER_AGENT_ROUTE` | `proof-gated`, `fallback-blocked` |
| `FX-ER-CAPABILITY-UNSUPPORTED-001` | `WINDOWS_VM_BROWSER_WORKER_ROUTE` | `proof-gated`, `capability-unsupported` |
| `FX-ER-CAPABILITY-EVIDENCE-STALE-001` | `BROWSER_EXTENSION_ROUTE` | `owner-evidence-only`, `not-production-scale-proof` |

Evidence status values preserved by the module are `CURRENT`, `STALE`, `MISSING`, `DISPUTED`, `UNPROVEN`, and `WITHDRAWN`.

## Exact safety declarations

- `NO_PUBLIC_INBOUND`: required by the module boundary and preserved as a safety declaration.
- `NO_PRIMARY_DATABASE`: required by the agent boundary and preserved as a safety declaration.
- `SECRET_REFERENCE_ONLY`: required for route/assignment payloads and preserved as a safety declaration.
- `NO_AGENT_FALLBACK`: the Egress module remains the selection authority.
- `NO_POLICY`: no arbitrary route selection is allowed without approved policy.
- `RECONCILIATION_AMBIGUOUS`: ambiguous dispatch or transport requires reconciliation, not blind retry.
- `PRODUCTION_READINESS: NOT_PROVEN`
- `PROVIDER_ACCESS_PERMISSION: NOT_INFERRED`

## Ownership boundaries

- Parser owns extraction, normalization, and parser-side business semantics only. It does not own route selection, transport dispatch, or Egress state mutation.
- Scan owns scan intent, work claims, run state, and listing state only. It does not own route selection or transport dispatch.
- Notification owns delivery semantics, outbox/read-model semantics, and delivery outcomes only. It does not own route authorization, route selection, or provider permission inference.
- Beacon owns Beacon source-of-truth state only. It does not own route, lease, transport, or provider state.
- Admin owns protected policy requests only. It does not own runtime route selection or direct Egress writes.
- Provider behavior is external evidence only. It does not authorize access permission, and raw provider payload retention remains blocked while OD-013 is unresolved.

## Gate status

| Gate | Status | Basis |
|---|---|---|
| proof-only | `REQUIRED` | Live proof is allowed only under a separate owner-approved `proof_only` task. |
| persistence | `BLOCKED` | Physical schema, migrations, and OD-013 remain unresolved. |
| runtime | `BLOCKED` | Exact connectivity, secret, OS/runtime, and deployment approvals are not passed. |
| deploy | `BLOCKED` | No runtime artifact or deployment is authorized by this handoff. |

## Open decisions

| Decision | Status |
|---|---|
| `OD-009` | `OPEN` |
| `OD-010` | `OPEN` |
| `OD-011` | `OPEN` |
| `OD-013` | `OPEN` |

These decisions remain unresolved for supported first-stage filters, country-wide support, safe monitoring cadence, and retention/deletion of route, lease, request, outcome, audit, and diagnostic evidence.

## Boundaries on proof and data handling

- Live Avito proof is not claimed here.
- Raw payload retention is not authorized here.
- Cookies, sessions, secrets, credentials, and private browser profiles are not inferred or retained by this handoff.
- Public unauthenticated inbound exposure is not selected.
- The agent remains a replaceable execution dependency with no primary database access.

## Readiness statement

- `PRODUCTION_READINESS: NOT_PROVEN`
- `PROVIDER_ACCESS_PERMISSION: NOT_INFERRED`
- The module remains evidence-bound until the open decisions and blocked gates are independently resolved.
