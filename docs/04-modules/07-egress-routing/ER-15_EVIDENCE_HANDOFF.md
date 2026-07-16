# Маяк Авито — Module 07 Egress Routing ER-15 Full Evidence/Handoff

## 1. Metadata

- module: `07-egress-routing`
- roadmap step: `ER-15`
- status: docs-only evidence/handoff for accepted semantic scope
- current handoff base: `833e39632446e00e1889975343443a0ea4d12f8d`
- latest accepted Egress semantic/code SHA: `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- source-of-truth playbook: `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`
- source-of-truth owner capture: `docs/04-modules/07-egress-routing/OWNER_EGRESS_DECISIONS_CAPTURE_v1.0.md`
- source-of-truth readme: `docs/04-modules/07-egress-routing/README.md`
- this document is evidence only and does not authorize runtime, persistence, deploy, provider access, or direct mutation of Parser, Scan, Notification, Beacon, Admin, or provider state

## 2. Purpose and scope

- summarize the accepted Module 07 semantic and evidence state
- preserve the accepted prerequisite ancestry that leads into ER-15
- preserve the full accepted Egress chain from `0f90ef7081e6f810d38e5dea76254d4e10f8bed4` to `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- preserve the exact route-proof statuses carried in synthetic evidence
- preserve the exact safety declarations carried by the handoff
- keep the module complete only in governance, semantic, contracts, synthetic-tests, fail-closed-gates, and evidence scope
- keep the module not production-ready and not runtime-ready

## 3. Accepted prerequisites

These six prerequisite SHAs are the accepted ancestors that precede the Egress chain start at `0f90ef7081e6f810d38e5dea76254d4e10f8bed4`:

- `e8587107fd6cd3675b3e69f1ce75ffa0c846cc3c` - `docs: bootstrap project governance and source documents`
- `fb55ec29708cb0f4de745504393fb02afb62ce3a` - `docs: accept Run 18 Egress Routing playbook`
- `bbe0691465e1b951980b33e5ee0ba2b0d9ab8127` - `er-01: capture egress owner decisions`
- `9e5a7b05bc211282b59462be4148568321f0482e` - `er-01: capture egress owner decisions`
- `9f80cd6877b7a53860cee2a2ff034aa8edaf7d49` - `er-01: restore literal owner decision capture`
- `4dfaec36be7997beaf06777befb9e997f80f3ef9` - `er-01: complete literal owner capture correction`

These prerequisites confirm ancestry only. They do not imply runtime readiness, provider approval, or production proof.

## 4. Accepted Egress chain

The full accepted Egress chain for ER-15 is:

- `0f90ef7081e6f810d38e5dea76254d4e10f8bed4` - `er-01: fix final literal owner capture mismatch`
- `9d1560057680f8d5f53921bb1b5632793e135e6f` - `nd-01: capture notification owner decisions`
- `97ceaec577231ec3cb1d45130f844a7c9f3f7716` - `er-02: add egress semantic contracts and fixtures`
- `cb30fffc20417b13153513043e973b2cbac93bce` - `er-02: correct canonical egress enum matrix`
- `d50f36640a81e1b081f08cfb101e6abcae63b394` - `er-02: enforce exact ambiguous outcome reconciliation`
- `d1e15cac1067a22da6594a43654e312eee627308` - `er-03: add agent and route registration boundary`
- `6153356ac24786cfc4233ae597103ec923e82984` - `er-03: restore canonical package exports`
- `ac62a3fac3050b5d9bd3cc28d5cb07791c60830f` - `er-03: enforce same-agent route ownership`
- `9a9a34dc0c5c88ac45d192355abb3ed215eb2adc` - `er-05a: add server route selection boundary`
- `ac432b43599ca217129d1ebf7fbf273f4caef182` - `er-05b: add policy-based fallback boundary`
- `8a696d231bf138ee3dc17ebba9f8338b6f83a0a5` - `er-06a: add route lease authorization boundary`
- `38539f16833af9a3ec67c7fb99cc15f2bb92e00b` - `er-06b: add transport assignment commitment boundary`
- `4096cc7fd6e0d9e5e04dbbb53fd344e400c15424` - `er-06b: separate request identity from safe request reference`
- `2c6dbb40a85c5e39068d484e11d0d97371e34b67` - `er-06c: add first dispatch attempt boundary`
- `1c166971083f9d419aa7e881061333ed7979af52` - `er-06d: add dispatch replay decision boundary`
- `c70921cd3298f250864792e1c2456e4a00de1fca` - `er-06e: add unknown dispatch reconciliation boundary`
- `31f7db5455f64915ddd76b0a5544900219e79472` - `nd-01: correct notification owner capture`
- `38322db2b5facc31f54cb9183f4fb672b053bef5` - `nd-02: add notification source intake semantics`
- `f76b03e99a5753f27991c86056ae0e0936d22afa` - `nd-03: add notification eligibility semantics`
- `e6e1973cd3a20a96fffd24be1e6e72583a1925d0` - `nd-03: correct exports and eligibility precedence`
- `fa349e23acd35e630f4e8ae594fca1c215d1ba61` - `er-06f: add resolved dispatch reconciliation boundary`
- `5e5940e0b5916c7f936a01b0e4a5072353a7074c` - `nd-04: add generic notification outbox semantics`
- `0b3c661f8f1f4bf9c984e28927bb8c6b2f807726` - `nd-05: add multi-channel delivery plan semantics`
- `f5b18cbdafef834c7c11024dcdfb244f017bcfc7` - `er-07a: add transport outcome commitment boundary`
- `ef3bb52d5c9b3bc4b275a454b7282e56933c440e` - `er-07b: add transport availability outcome boundary`
- `ec0c019053fe8a28aa2804fff3ad3d8577d3eccb` - `er-07b: enforce exact reconciliation status type`
- `30f2982fb0eecade9407d5bf0e4cd5dd6546a9dc` - `er-07c: add transport response presence outcome boundary`
- `a805fa8ff34e1c790484f821d19e475342dce7b4` - `er-07c: enforce exact nested transport records`
- `bd1e4a8ad73d196d34323c561a3cde43bcd636f4` - `er-07d: add transport response failure outcome boundary`
- `e5c1bc81bc1cf4916fb755c584172dd5c37eb85f` - `er-07d: complete safe response negative matrix`
- `c4c11bde77e80cf58b0da1ed1a10ab8a7ee8a990` - `er-07e: add policy fallback transport outcome boundary`
- `d9f3a1504690363e8b3ba0e90570242913a0beba` - `er-07e: satisfy differential static gates`
- `2034c2efeef2786fb1f8edc72b771b7946de3f55` - `er-07b: enforce exact nested transport records`
- `ffedb3a14f13110ef5e3471168c1eb0d6f71693a` - `er-07b: restore assignment dispatch architecture gates`
- `05f1427768dcd7e23bdbf47c8149908de0f72498` - `nd-06: add notification attempt outcome semantics`
- `35b35245ea70929b401290f6876e1e1ca190a487` - `nd-06: enforce provider outcome start state gate`
- `2024015c6bb6ee9ad3a3836b12e1a6ab79230e2e` - `nd-07: add notification deduplication semantics`
- `d220c0c525c1a071652b81b5af47239daf05cf50` - `nd-07: enforce exact channel class type`
- `05f5a4efefdcfca8a05c7504645033fbd9f5e68a` - `nd-08: add no-new status policy semantics`
- `62ecf572f8897395f80e8b3d7d38484f4dac7d25` - `nd-08: enforce upstream provenance gates`
- `4d8fdc2b6649115e50baf1729cc7933058df2820` - `nd-08: remove static boundary evasion`
- `2a09a302f2a2f6ae0a91d9c3b4a7fc29213761e8` - `nd-09: add external recovery policy semantics`
- `e49f3c850a35eb083af9361c0e2cc9dffbf2c575` - `nd-09: correct same-problem replay status`
- `0e021a75bcbeedb935990cd5e6018c5696214a5a` - `nd-10: add listing card payload boundary`
- `ab6050844cb850d781ae6993082d70c48c71085f` - `nd-10: enforce listing card output invariants`
- `bedb27612429f04f8be5b3f27500e14bd1f4a85e` - `nd-11: add batch partial outcome semantics`
- `38e7dd4d59f271bf579b2d8892106a48097bfbd3` - `nd-11: correct replayed failure retry policy`
- `911287645121414d872d6774c8a176956d48864f` - `er-08a: add transport restriction signal boundary`
- `c965b0480128ca259805cadeed98908666c394db` - `er-08a: fix restriction signal lint`
- `15207864e0d304f43ac50602f77f57143b89aed6` - `nd-11: satisfy batch static type gate`
- `32fa7929c97f0518625f3b5777920dfae4d5d453` - `er-08b: add restriction evaluation gate`
- `61ea3bdf7bb3281445dee0651591adad1ecb54a8` - `er-08b: add restriction evaluation gate`
- `ecd68c216292627bf357bd86e0777a54b0892238` - `er-09a: add session secret gate`
- `668c52f4a91e146de99d2d504815170b3bc03552` - `er-09a: store source capability`
- `0971796a7fc1d22dd57950541216100699f6ce83` - `er-10a: add browser windows fallback gate`
- `3728540cf4801c50761d67f5ffad55b5c9217bea` - `er-10a: revalidate session secret gate`
- `201747d74d8bd99b9c893e87ae570fad8b794b7c` - `er-11a: add development bridge gate`
- `47b46447abcce62864473553d1a5ecdce9999bc9` - `er-12a: add safe diagnostic gate`
- `6cd8af542c4c3e07ff08ac2b40f9848971b0ac6b` - `er-12a: remove import-order suppression`
- `6c9c0aaa3bcb12195a68b6bd6262ef365c91ca17` - `er-13a: add proof-only gate`
- `69fd43905550c9dd94f6be45965ba67e72418882` - `nd-12: add notification read model semantics`
- `0178d5661b7bd1b81e65676491ae6fce46ab00a9` - `er-13a: establish canonical test package layout`
- `a05b71818fde3a43066714098e1b9eed43fdf9dd` - `nd-12: export notification read model semantics`
- `fa06c5e502910d5fbdd2efe9f168f870726a34b9` - `er-14a: add persistence runtime gate`

This chain is the accepted ancestry record for ER-15. It is factual evidence only and does not authorize runtime behavior.

## 5. Accepted artifact inventory

- `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`
- `docs/04-modules/07-egress-routing/OWNER_EGRESS_DECISIONS_CAPTURE_v1.0.md`
- `docs/04-modules/07-egress-routing/README.md`
- `docs/04-modules/07-egress-routing/ER-15_EVIDENCE_HANDOFF.md`
- `src/mayak/modules/egress_routing/*`
- `tests/contract/test_egress_routing_*`
- `tests/unit/test_egress_routing_*`
- `tests/architecture/test_egress_routing_boundaries.py`

These artifacts bound the current accepted semantic and synthetic-test scope for Module 07.

## 6. ER-01 governance capture evidence

- the owner decision capture establishes the primary route direction as a Linux/server reference-style outbound route
- the browser-extension route is evidence-only and may serve only as a fallback or proof route
- browser, provider, and Windows-specific behaviors are bounded by separate evidence and are not production claims
- live Avito traffic, provider access, CAPTCHA solving, and production-scale proof are not authorized by the governance capture

## 7. ER-02 canonical contracts evidence

- the canonical egress enum matrix and synthetic fixture set define the accepted outcome vocabulary
- ambiguous, restricted, fallback, unavailable, and reconcile-first states remain distinct
- transport success is not collapsed into Parser success
- failure and ambiguity do not become clean empty outcomes

## 8. ER-03 route registration and ownership evidence

- route and agent registration remain within Egress Routing ownership
- same-agent route ownership is enforced as a semantic boundary
- canonical package exports keep the module surface explicit
- Egress Routing owns logical route, agent, lease, readiness, health, quarantine, selection, and transport state only

## 9. ER-04 server-side selection and route-technology gate evidence

- `ER-04` remains `BLOCKED`
- the route-technology decision gate is closed to implementation
- priority, fallback, rate, and cadence choices remain unresolved
- connectivity topology, ports, tunnel/VPN/proxy, credentials, and capability mappings remain unresolved
- there is no accepted `ER-04` implementation commit in the chain

## 10. ER-05 and ER-06 lease/assignment/dispatch evidence

- lease authorization is bounded by declared purpose and scope
- transport assignment commitment is separate from request identity
- dispatch attempts carry safe request references, not primary business state
- policy-based fallback remains controlled and bounded
- fallback does not authorize blind retry or route switching by other modules

## 11. ER-07 transport and parser boundary evidence

- transport availability, response presence, and failure states remain explicit
- nested transport records are preserved as transport evidence
- parser integration does not convert transport success into parser success
- response failure evidence remains separate from parser extraction evidence

## 12. ER-08 idempotency and reconciliation evidence

- replay semantics remain exact and bounded
- unknown dispatch is handled reconcile-first
- reconciliation status types remain explicit and fail closed
- dispatch resolution does not become blind retry

## 13. ER-09 to ER-10 gate evidence

- restriction evaluation remains a gate, not a runtime authorization
- session secret handling remains gated
- source capability storage remains gated
- browser windows fallback remains gated
- development bridge usage remains explicit-owner-consent only

## 14. ER-11 to ER-14 gate evidence

- safe diagnostic evidence remains bounded
- proof-only gates remain proof-only
- canonical test package layout is accepted as a packaging boundary
- persistence runtime remains blocked
- no runtime gate in this chain authorizes production execution

## 15. Exact route proof statuses

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

## 16. Exact safety declarations

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

## 17. Ownership boundaries

- Parser owns extraction, normalization, and parser-side business semantics only
- Scan owns scan intent, work claims, run state, and listing state only
- Notification owns delivery semantics, outbox/read-model semantics, and delivery outcomes only
- Beacon owns Beacon source-of-truth state only
- Admin owns protected policy requests only
- Provider behavior is external evidence only
- Egress Routing does not own account, entitlement, pricing, transport-host, or provider-permission state

## 18. Open decisions and blocked gates

| Decision | Governance state | Implementation effect |
|---|---|---|
| `OD-009` | `OPEN` | blocked from route-default encoding |
| `OD-010` | `OPEN` | blocked from geography assumption |
| `OD-011` | `OPEN` | blocked from cadence and threshold selection |
| `OD-013` | `OPEN` | blocked from retention and deletion policy |

These decisions remain unresolved and the module remains blocked for their associated route, lease, request, outcome, audit, and diagnostic evidence policies.

## 19. Live traffic and environment boundaries

- live Avito traffic is not claimed
- live provider traffic is not claimed
- raw provider payload retention is not authorized
- cookies, sessions, secrets, credentials, and private browser profiles are not inferred or retained
- public unauthenticated inbound exposure is not selected
- the agent remains a replaceable execution dependency with no primary database access
- no runtime, persistence, deploy, or browser/proxy/VPN/tunnel topology change is authorized here

## 20. Accepted semantic scope

- route selection is server-side and explainable
- a lease is bounded authorization for one declared purpose and scope
- transport success is not Parser success
- Parser success is not Scan success
- unknown dispatch or send state is reconcile-first and is never blindly retried
- quarantine blocks new affected work and preserves history
- automatic unquarantine is prohibited unless a later explicit policy proves it
- foreign resources do not become project resources by visibility or convenience

## 21. Source-of-truth and ancestry evidence

- GitHub `main` is the source of truth for this handoff
- the accepted ancestry for ER-15 is recorded in the chain above
- the current published base for this handoff is `833e39632446e00e1889975343443a0ea4d12f8d`
- the latest accepted Egress semantic/code SHA is `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- the handoff remains subordinate to accepted governance and source-of-truth ancestry

## 22. Content boundary evidence

- this handoff remains evidence-only
- this handoff does not introduce runtime, persistence, deploy, provider, or database authorization
- this handoff does not change module playbook, README, source code, or tests as part of the handoff record
- the accepted scope remains limited to the documented evidence boundary

## 23. Literal evidence

- all SHA values in this document are literal 40-hex strings where expected
- the accepted Egress semantic/code SHA literal is `fa06c5e502910d5fbdd2efe9f168f870726a34b9`
- the current handoff base literal is `833e39632446e00e1889975343443a0ea4d12f8d`
- the route-proof labels remain literal and synthetic
- the safety declarations remain literal and declarative
- no secret, token, cookie, or provider payload literal is required for this handoff

## 24. Module completeness evidence

- the module is complete only inside governance, semantic, contracts, synthetic-tests, fail-closed-gates, and evidence scope
- the module is not production-ready
- the module is not runtime-ready
- the module does not claim live provider behavior or operational readiness

## 25. Non-authorization evidence

- this handoff does not authorize runtime changes
- this handoff does not authorize persistence changes
- this handoff does not authorize deploy changes
- this handoff does not authorize Windows/browser topology changes
- this handoff does not authorize proxy, VPN, or tunnel changes
- this handoff does not authorize provider-access changes
- this handoff does not authorize database changes

## 26. Remaining gates and blockers

- `ER-04` remains blocked
- `OD-009`, `OD-010`, `OD-011`, and `OD-013` remain open
- exact route technology, connectivity topology, ports, tunnel/VPN/proxy, credentials, capability mappings, priority/fallback, lease/heartbeat/readiness thresholds, retries, rate limits, cookies/sessions, and retention remain blocked
- production readiness remains unproven
- runtime readiness remains absent

## 27. Final handoff state

This handoff captures the accepted Module 07 Egress Routing evidence state for ER-15. It is complete only in governance, semantic, contracts, synthetic-tests, fail-closed-gates, and evidence scope, and it remains not production-ready and not runtime-ready.
