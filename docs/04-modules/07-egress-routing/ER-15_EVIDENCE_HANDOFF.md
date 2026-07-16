# ER-15 Evidence Handoff

## 1. Metadata

- module: `07-egress-routing`
- roadmap step: `ER-15`
- status: docs-only evidence/handoff for accepted semantic scope
- latest accepted Egress semantic/code SHA: `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- current handoff base: `4cf497a8602ed934c8b00747d634e3b0df4d6e5f`
- source-of-truth playbook: `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`
- source-of-truth owner capture: `docs/04-modules/07-egress-routing/OWNER_EGRESS_DECISIONS_CAPTURE_v1.0.md`
- source-of-truth readme: `docs/04-modules/07-egress-routing/README.md`
- this document is evidence only and does not authorize runtime, persistence, deploy, provider access, or direct mutation of Parser, Scan, Notification, Beacon, Admin, or provider state

## 2. Purpose and scope

- summarize the accepted Module 07 semantic and evidence state
- preserve the exact accepted SHA chain for this handoff
- preserve the exact route-proof statuses carried in synthetic evidence
- preserve the exact safety declarations carried by the handoff
- record the required validation, cleanup, commit, push, and reporting gates
- keep OD-009, OD-010, OD-011, and OD-013 open or blocked

## 3. Preflight basis

- GitHub `main` is the source of truth for this handoff
- the verified preflight base before editing was `6fa3dd2a314587ad354073ab5ae79ecec1b272d2`
- the verified preflight branch was `main`
- the verified preflight worktree was clean
- the verified accepted Egress semantic/code SHA is `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- no live Avito/provider calls were made
- no runtime, persistence, Windows/browser, proxy/VPN/tunnel, or deploy change is authorized by this handoff

## 4. Accepted SHA chain

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

Each SHA above is intended to remain an accepted ancestor in the documented chain.

## 5. Exact route proof statuses

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

## 6. Exact safety declarations

- `NO_PUBLIC_INBOUND`
- `NO_PRIMARY_DATABASE`
- `SECRET_REFERENCE_ONLY`
- `NO_AGENT_FALLBACK`
- `NO_POLICY`
- `RECONCILIATION_AMBIGUOUS`
- `PRODUCTION_READINESS: NOT_PROVEN`
- `PROVIDER_ACCESS_PERMISSION: NOT_INFERRED`
- `NO_LIVE_AVITO_CALLS`
- `NO_LIVE_PROVIDER_CALLS`
- `NO_RUNTIME_MUTATION`
- `NO_PERSISTENCE_MUTATION`
- `NO_WINDOWS_BROWSER_PROXY_TUNNEL_VPN_CHANGES`
- `NO_DEPLOY_CHANGES`
- `NO_RAW_PROVIDER_PAYLOAD_RETENTION`
- `NO_BROWSER_COOKIES_SESSIONS_CREDENTIALS`
- `NO_FORBIDDEN_PATH_CHANGES`

These 17 declarations are carried as safety boundaries only and do not authorize any hidden runtime or provider behavior.

## 7. Ownership boundaries

- Parser owns extraction, normalization, and parser-side business semantics only
- Scan owns scan intent, work claims, run state, and listing state only
- Notification owns delivery semantics, outbox/read-model semantics, and delivery outcomes only
- Beacon owns Beacon source-of-truth state only
- Admin owns protected policy requests only
- Provider behavior is external evidence only
- Egress Routing does not own account, entitlement, pricing, transport-host, or provider-permission state

## 8. Open decisions and blocked gates

| Decision | Status |
|---|---|
| `OD-009` | `OPEN` |
| `OD-010` | `OPEN` |
| `OD-011` | `OPEN` |
| `OD-013` | `OPEN` |

The module remains blocked for supported first-stage filters, country-wide support, safe monitoring cadence, and retention/deletion of route, lease, request, outcome, audit, and diagnostic evidence.

## 9. Live traffic and environment boundaries

- live Avito traffic is not claimed
- live provider traffic is not claimed
- raw provider payload retention is not authorized
- cookies, sessions, secrets, credentials, and private browser profiles are not inferred or retained
- public unauthenticated inbound exposure is not selected
- the agent remains a replaceable execution dependency with no primary database access
- no runtime, persistence, deploy, or browser/proxy/VPN/tunnel topology change is authorized here

## 10. Accepted semantic scope

- route selection is server-side and explainable
- a lease is bounded authorization for one declared purpose and scope
- transport success is not Parser success
- Parser success is not Scan success
- unknown dispatch or send state is reconcile-first and is never blindly retried
- quarantine blocks new affected work and preserves history
- automatic unquarantine is prohibited unless a later explicit policy proves it
- foreign resources do not become project resources by visibility or convenience

## 11. Source-of-truth and ancestry validation

- `origin/main` must equal `6fa3dd2a314587ad354073ab5ae79ecec1b272d2` before any correction that claims to be exact
- each SHA in the accepted chain must satisfy `git merge-base --is-ancestor <sha> HEAD`
- the handoff must remain subordinate to GitHub source-of-truth and accepted governance
- if the base does not match, the task must stop immediately with `STOP_BASE_MISMATCH`
- rebase, merge, cherry-pick, reset, amend, squash, and force-push are forbidden

## 12. Content validation

- the changed path must remain exactly one existing file: `docs/04-modules/07-egress-routing/ER-15_EVIDENCE_HANDOFF.md`
- `docs/04-modules/07-egress-routing/MODULE_07_FULL_EVIDENCE_HANDOFF_v1.0.md` must remain untouched
- `docs/04-modules/07-egress-routing/README.md` must remain untouched
- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md` must remain untouched
- `pyproject.toml`, `uv.lock`, `src/**`, and `tests/**` must remain untouched
- the handoff must keep the exact route proof statuses, exact open decisions, and exact safety declarations
- the handoff must continue to forbid live Avito/provider calls and any runtime or persistence mutation

## 13. Literal validation

- all SHA values in this document are literal 40-hex strings where expected
- the accepted Egress semantic/code SHA literal is `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- the current handoff base literal is `4cf497a8602ed934c8b00747d634e3b0df4d6e5f`
- the preflight base literal is `6fa3dd2a314587ad354073ab5ae79ecec1b272d2`
- the route-proof labels remain literal and synthetic
- the safety declarations remain literal and declarative
- no Unicode, secret, token, cookie, or provider payload literal is required for this handoff

## 14. Generated-artifact cleanup

- after checks, remove only untracked `__pycache__` directories, `.pyc` files, `*.egg-info` directories, and tool caches
- do not delete tracked files or touch forbidden paths
- if cleanup would affect any path outside those artifact classes, stop
- the final worktree must be clean after cleanup and before push

## 15. Required checks

- `ruff`
- `mypy`
- `lint-imports`
- scoped pytest for the Egress Routing surface
- full `pytest`
- `git diff --check`
- `git status --short`

All checks are required to pass before commit.

## 16. Scoped pytest boundary

- the scoped pytest run must target the Egress Routing contract, unit, and architecture surfaces
- the scoped run must not add new runtime behavior
- the scoped run must not depend on live Avito/provider traffic
- the scoped run must fail closed if any forbidden path or hidden runtime dependency is introduced

## 17. Pre-push gate

- `origin/main` must be re-verified against the expected base before commit and again before push
- the worktree must remain clean except for the intended doc change
- all checks from section 15 must pass
- cleanup from section 14 must be complete
- the accepted SHA chain and exact safety declarations must still be present in the handoff
- if any gate fails, do not push

## 18. Commit requirements

- commit subject must be exactly `er-15: correct module 07 evidence handoff`
- commit must include only the allowed doc change
- no amend, squash, rebase, merge, cherry-pick, reset, or force-push is allowed
- the commit must remain a fast-forward descendant of the expected base
- the commit must not introduce generated artifacts or forbidden path changes

## 19. Push requirements

- push only fast-forward to `main`
- do not force-push
- do not create a merge commit
- do not rewrite published history
- stop immediately if the push is not fast-forward

## 20. Post-push verification

- fetch `origin/main` again after push
- verify `origin/main` equals the new commit SHA
- verify the commit is an ancestor of the pushed remote tip
- verify the branch remains `main`
- verify the repository is still on the intended source-of-truth chain

## 21. Clean worktree requirement

- the final worktree must be fully clean
- no untracked artifact directories may remain
- no untracked `.pyc`, `__pycache__`, `*.egg-info`, or tool cache entries may remain
- the only acceptable final state is a clean repository with the intended commit applied

## 22. Report requirements

The final report for this task must contain:

- the new workspace path
- preflight SHAs
- the single changed path
- ancestry validation results
- content validation results
- literal validation results
- all check results
- cleanup actions
- the commit SHA
- the push result
- post-push `origin/main`
- the final clean-status result

## 23. Failure conditions

- if the base mismatches, stop with `STOP_BASE_MISMATCH`
- if the worktree is dirty, stop with `STOP_DIRTY_WORKTREE`
- if any required check fails, report `FAIL`
- if any forbidden path changes, stop
- if any live call or runtime mutation is introduced, stop
- if the push is not fast-forward, stop

## 24. Non-authorization reminder

This handoff does not authorize runtime, persistence, Windows/browser, proxy/VPN/tunnel, deploy, provider-access, or database changes.

## 25. Exact acceptance criteria

- accepted Egress semantic/code SHA is `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- `OD-009`, `OD-010`, `OD-011`, and `OD-013` remain open or blocked
- no live Avito/provider calls were made
- no runtime, persistence, Windows/browser, proxy/VPN/tunnel, or deploy changes were made
- the exact route proof statuses are present
- the exact 17 safety declarations are present
- the single allowed path is the only changed path
- required checks pass
- generated artifacts are cleaned up
- commit and fast-forward push complete
- final worktree is clean

## 26. Handoff completeness statement

- this document is evidence-only
- this document does not create code, tests, runtime, persistence, deploy, or provider permission
- this document does not rewrite module 07 playbook or README history
- this document remains a handoff record for the accepted semantic and evidence state only

## 27. Final status

This handoff is complete only when the preflight base matches, all checks pass, cleanup is complete, the commit is created with the exact subject, the push is fast-forward only, and the repository ends clean.
