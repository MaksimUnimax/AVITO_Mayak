# Маяк Авито — Module 07 Egress Routing ER-15 Full Evidence/Handoff

## Metadata

- date: 2026-07-16
- module: 07-egress-routing
- roadmap step: ER-15
- latest accepted Egress semantic/code SHA: fa06c5e502910d5fbdd2efe9f168f870726a34b9
- original ER-15 handoff base: 4cf497a8602ed934c8b00747d634e3b0df4d6e5f
- initial ER-15 publication: 6fa3dd2a314587ad354073ab5ae79ecec1b272d2
- first corrective publication: 833e39632446e00e1889975343443a0ea4d12f8d
- current corrective base: 53f908cdb8276e8831710b3b34dd84b4628e4f95

## Executive summary

- this document is evidence-only and records the accepted ER-15 lineage for Module 07 Egress Routing
- it preserves the exact prerequisite ancestry, accepted Egress chain, ownership boundaries, route-status evidence, and safety declarations
- it keeps the module complete only in governance, semantic contracts, synthetic fixtures/tests, fail-closed gates, and evidence-handoff scope
- it does not claim production readiness, runtime readiness, live Avito execution, provider access, or deploy authorization

## Current GitHub and parallel-work state

- `origin/main` resolves to `53f908cdb8276e8831710b3b34dd84b4628e4f95`
- this corrected handoff is aligned to that current corrective base
- the accepted ER-15 handoff work in this checkout is limited to the evidence file itself
- `parallel-main` module-08 work only: `16ec547eef68b800d17afd95e2a33274c5e68d5c`, `d02b2ac0bf3845394f4c1b0677cf438e41b9818f`, `65afae19c25aa90bb2c9ceba68402f0a19e69f19`, `4cf497a8602ed934c8b00747d634e3b0df4d6e5f`, `6fa3dd2a314587ad354073ab5ae79ecec1b272d2`, `833e39632446e00e1889975343443a0ea4d12f8d`, `53f908cdb8276e8831710b3b34dd84b4628e4f95`

## Accepted prerequisites

- `79c550e6a5a9ed68c4aaadebb219aaad4e8afa63`
- `5d278bfde42657d61a002e3e165d99330bdbb3ec`
- `81b4754a2097503542d84fcb153d0f08817e30be`
- `d4dee6489b26f61c81c5e9841b7f8769a5fa6795`
- `8a7daf5270c634e27e54507a69cf33e94cd50450`
- `408f62f7833a9fbbc8c188938dd24fd07ad00b8f`

## Complete accepted Egress SHA chain

- `0f90ef7081e6f810d38e5dea76254d4e10f8bed4`
- `d50f36640a81e1b081f08cfb101e6abcae63b394`
- `ac62a3fac3050b5d9bd3cc28d5cb07791c60830f`
- `ER-04: no implementation commit; route technology remains gated`
- `9a9a34dc0c5c88ac45d192355abb3ed215eb2adc`
- `ac432b43599ca217129d1ebf7fbf273f4caef182`
- `8a696d231bf138ee3dc17ebba9f8338b6f83a0a5`
- `4096cc7fd6e0d9e5e04dbbb53fd344e400c15424`
- `2c6dbb40a85c5e39068d484e11d0d97371e34b67`
- `1c166971083f9d419aa7e881061333ed7979af52`
- `c70921cd3298f250864792e1c2456e4a00de1fca`
- `fa349e23acd35e630f4e8ae594fca1c215d1ba61`
- `f5b18cbdafef834c7c11024dcdfb244f017bcfc7`
- `ffedb3a14f13110ef5e3471168c1eb0d6f71693a`
- `a805fa8ff34e1c790484f821d19e475342dce7b4`
- `e5c1bc81bc1cf4916fb755c584172dd5c37eb85f`
- `d9f3a1504690363e8b3ba0e90570242913a0beba`
- `c965b0480128ca259805cadeed98908666c394db`
- `61ea3bdf7bb3281445dee0651591adad1ecb54a8`
- `668c52f4a91e146de99d2d504815170b3bc03552`
- `3728540cf4801c50761d67f5ffad55b5c9217bea`
- `201747d74d8bd99b9c893e87ae570fad8b794b7c`
- `6cd8af542c4c3e07ff08ac2b40f9848971b0ac6b`
- `6c9c0aaa3bcb12195a68b6bd6262ef365c91ca17`
- `0178d5661b7bd1b81e65676491ae6fce46ab00a9`
- `fa06c5e502910d5fbdd2efe9f168f870726a34b9`

## Accepted artifact inventory

- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`
- `docs/04-modules/07-egress-routing/OWNER_EGRESS_DECISIONS_CAPTURE_v1.0.md`
- `docs/04-modules/07-egress-routing/README.md`
- `docs/04-modules/07-egress-routing/ER-15_EVIDENCE_HANDOFF.md`
- `src/mayak/modules/egress_routing/*`
- `tests/contract/test_egress_routing_*`
- `tests/unit/test_egress_routing_*`
- `tests/architecture/test_egress_routing_boundaries.py`

## Owner decisions captured

- the primary route direction is a Linux/server reference-style outbound route
- the browser-extension route is evidence-only and serves as a proof route, not a production-scale SaaS route
- Windows-specific fallback behavior remains separately bounded and does not become production ownership here
- live Avito traffic, endpoint probing, CAPTCHA solving or bypass, and production-scale proof are not authorized by the captured governance

## Accepted ownership and semantic scope

- Egress Routing owns logical route, agent, lease, readiness, health, quarantine, selection, and transport state only
- Parser owns extraction, normalization, and parser-side business semantics only
- Scan owns scan intent, work claims, run state, and listing state only
- Notification owns delivery semantics, outbox/read-model semantics, and delivery outcomes only
- Beacon owns Beacon source-of-truth state only
- Admin owns protected policy requests only
- provider behavior is external evidence only
- Egress Routing does not own account, entitlement, pricing, transport-host, or provider-permission state

## Agent and route registration boundary

- route and agent registration remain inside Egress ownership
- same-agent route ownership is enforced as a semantic boundary
- canonical package exports keep the module surface explicit
- registration does not imply runtime authorization, live provider access, or production readiness

## Route selection and policy-based fallback

- route selection is server-side and explainable
- the Linux/server reference-style route remains the primary candidate but is not proven
- the Russian residential route remains future allowed and provider unselected
- policy-based fallback stays bounded and evidence-driven
- fallback does not authorize blind retry, route switching by other modules, or live traffic

## Route lease and assignment lifecycle

- lease authorization is bounded by declared purpose and scope
- transport assignment commitment is separate from request identity
- request identity, safe request references, and lease state remain distinct
- lease renewal or reassignment is not a runtime or deploy authorization

## Dispatch, replay, idempotency and reconciliation

- first dispatch attempts remain explicit and bounded
- replay semantics are exact and idempotent
- unknown dispatch or send state is reconcile-first
- blind retry is prohibited
- reconciliation preserves evidence rather than collapsing it into success

## Transport outcome classification

- transport availability, response presence, and failure are separate outcomes
- nested transport records remain transport evidence
- transport success is not parser success
- failure and negative-matrix evidence remain explicit and do not collapse into empty success

## Parser and Scan handoff boundary

- Egress Routing hands transport evidence and safe request references to Parser and Scan
- parser success is not scan success
- transport success is not parser success
- this handoff does not claim parser-side mutation, scan-side mutation, or downstream runtime behavior

## CAPTCHA, restriction and quarantine

- restriction evaluation remains a gate, not runtime authorization
- quarantine blocks new affected work and preserves history
- CAPTCHA solving or bypass is not executed
- live Avito proof remains gated elsewhere and is not inferred here

## Cookies, sessions and secrets

- session secret handling remains gated
- cookies, sessions, tokens, credentials, and personal browser profiles are not retained or inferred
- source capability storage remains reference-only
- no raw provider payloads are placed in Git

## Browser-extension and Windows fallback

- the browser-extension route is owner-provided proof evidence, not a SaaS-scale production route
- Windows Browser Agent remains a fallback family that is not implemented
- Windows VM Browser Worker remains a fallback family that is not implemented
- browser-extension evidence does not expand to general browser automation authorization

## Development owner bridge

- the owner development bridge is development-only and not production
- it is explicit-owner-consent only
- it does not authorize live traffic, runtime changes, or deploy changes

## Safe observability and diagnostics

- safe diagnostics stay bounded to evidence use
- proof-only gates remain proof-only
- observability does not expose raw provider payloads or secret material
- diagnostics do not expand ownership or runtime authority

## Route families and exact proof statuses

- Linux/server reference-style route: `PRIMARY_CANDIDATE_UNPROVEN`
- Russian residential route: `FUTURE_ALLOWED_PROVIDER_UNSELECTED`
- Owner development bridge: `DEVELOPMENT_ONLY_NOT_PRODUCTION`
- Windows Browser Agent: `FALLBACK_FAMILY_NOT_IMPLEMENTED`
- Windows VM Browser Worker: `FALLBACK_FAMILY_NOT_IMPLEMENTED`
- Browser Extension route: `OWNER_PROVIDED_AVITO_PROOF_NOT_SAAS_SCALE`
- Live Avito proof: `NOT_EXECUTED`
- Production route: `NOT_SELECTED`
- Production readiness: `NOT_PROVEN`

## Live proof-only gate

- live Avito proof is not executed
- no endpoint probing or CAPTCHA solving or bypass is authorized here
- proof remains synthetic and evidence-only
- live provider execution is not claimed

## Persistence/runtime/deploy fail-closed gates

- the persistence runtime gate remains closed
- runtime service and deploy are fail-closed
- database schema or migration changes are not authorized here
- production readiness remains not proven

## Remaining open decisions and dependencies

- `OD-009`: `OPEN`
- `OD-010`: `OPEN`
- `OD-011`: `OPEN`
- `OD-013`: `OPEN`
- route-default encoding, geography assumption, cadence and threshold selection, and retention and deletion policy remain dependent on these decisions

## Explicit non-ownership

- Parser, Scan, Notification, Beacon, and Admin semantics remain separate ownership domains
- provider behavior remains external evidence only
- Egress Routing does not own account, entitlement, pricing, host, credentials, or provider-permission state
- this handoff does not expand into runtime service, deploy, or production execution ownership

## Verification evidence

| Check | Observed result | Status |
|---|---|---|
| scoped Ruff | `All checks passed!` | PASS |
| scoped mypy | `Success: no issues found in 64 source files` | PASS |
| lint-imports | `Contracts: 3 kept, 0 broken.` | PASS |
| scoped Egress pytest | `2344 passed in 5.73s` | PASS |
| full pytest | `3477 passed in 9.50s` | PASS |
| git diff --check | clean | PASS |

## Exact safety declarations

- `LIVE_AVITO_TRAFFIC: NONE`
- `ENDPOINT_PROBING: NONE`
- `CAPTCHA_SOLVING_OR_BYPASS: NONE`
- `BROWSER_AUTOMATION_EXECUTED: NONE`
- `WINDOWS_AGENT_IMPLEMENTATION: NONE`
- `BROWSER_EXTENSION_IMPLEMENTATION: NONE`
- `NATIVE_HOST_OR_INSTALLER: NONE`
- `PROXY_VPN_TUNNEL_CONFIGURATION: NONE`
- `PROVIDER_SELECTED: NONE`
- `RAW_PROVIDER_PAYLOADS_IN_GIT: NONE`
- `REAL_AVITO_FIXTURES: NONE`
- `COOKIES_SESSIONS_TOKENS_CREDENTIALS: NONE`
- `PERSONAL_BROWSER_PROFILE_ACCESS: NONE`
- `DATABASE_SCHEMA_OR_MIGRATIONS: NONE`
- `RUNTIME_SERVICE_OR_DEPLOY: NONE`
- `PRODUCTION_READINESS: NOT_PROVEN`
- `PROVIDER_ACCESS_PERMISSION: NOT_INFERRED`

## Final accepted module state

> Module 07 is complete only in the accepted governance, semantic contracts,
> synthetic fixtures/tests, fail-closed gates, and evidence-handoff scope.
>
> Module 07 is not production-ready or runtime-ready.
