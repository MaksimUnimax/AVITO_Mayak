# Маяк Авито — Module 05 Avito Parser Adapter APA-12 Evidence/Handoff

## 1. Metadata

- status: final evidence/handoff for accepted semantic/contracts/tests scope;
- date: 2026-07-12;
- module: 05-avito-parser-adapter;
- latest accepted module SHA before handoff: `b149abc372ff66005493938d58368824af7e81a7`;
- source-of-truth playbook path: `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md`;
- docs-only handoff;
- no runtime/provider/DB/UI/deploy authorization;
- module is not a production-ready Avito parser.

## 2. Accepted prerequisites

Verified ancestor SHAs for the module dependencies and adjacent handoff chain:

- Module 01: `79c550e6a5a9ed68c4aaadebb219aaad4e8afa63`;
- Module 02: `5d278bfde42657d61a002e3e165d99330bdbb3ec`;
- Module 03 semantic: `81b4754a2097503542d84fcb153d0f08817e30be`;
- Module 04 semantic/evidence: `d4dee6489b26f61c81c5e9841b7f8769a5fa6795`;
- Module 06 handoff: `408f62f7833a9fbbc8c188938dd24fd07ad00b8f`.

These prerequisites confirm ancestry only. They do not imply that any foreign runtime scope is complete.

## 3. Accepted Module 05 SHA chain

| Step | Accepted/final SHA | Subject/evidence |
|---|---|---|
| APA-01 governance capture | `7a11bd49266b347c88cca1ea2e6a5ddb7a8e1b3d` | `docs: capture parser adapter owner decisions` |
| APA-02 semantic contracts | `9fc2e416161352c6d20e5e2590d537bde18ca3f4` | `initial 5abeb2a75ef7e4448f4a337b557d83fb43d17543 plus accepted boundary refinement` |
| APA-03 compatibility profile | `e6d180bc83e35bdf791f3e76794ffbfaa16c397f` | `parser compatibility profile semantics` |
| APA-04 source URL boundary | `fa02f69efda71f780b0937198483e4b49e33014d` | `source URL boundary semantics` |
| APA-05 transport classification | `402bce7336a55e81b3073fc198c3072680af6ada` | `transport/response classification semantics` |
| APA-06 search configuration | `cef009f5e337210f5a499d841c093bdc5b770782` | `search configuration extraction semantics` |
| APA-07 multivalue normalization | `d1521c63c8686435ff22f516a549aa023b990785` | `multivalue-safe normalization` |
| APA-08 listing candidate | `4a595d228babf0599694f8ff84677f8e86a0d9b4` | `listing candidate normalization` |
| APA-09 ordering/Scan handoff | `6e3aeed23a5416006a902e932073113911ea330f` | `ordering and Scan handoff semantics` |
| APA-10 pagination/partial | `766ab41f81ce86074401b478e987e789afcb2d5d` | `original 48196c30f407102acdec36317a165e120e4fe36a plus empty-page equality correction` |
| APA-11 privacy/observability | `b149abc372ff66005493938d58368824af7e81a7` | `original 4ebdee56e4bfcca2198224c901673fe2a71a830a, canonical enum correction 09df5302ced92c83729394c733ba475b4644fc20, literal ASCII/root-cause correction b149abc372ff66005493938d58368824af7e81a7` |

Each SHA above was checked with `git merge-base --is-ancestor <sha> HEAD`.

## 4. Accepted semantic scope

The evidence supports these boundaries:

- transport success is not parser success;
- parser success is not Scan/business success;
- failure, restriction, CAPTCHA, malformed, incomplete, stale and ambiguous outcomes do not collapse into clean empty;
- source URL remains Beacon-owned evidence;
- parser does not mutate Beacon;
- compatibility profile does not turn internal Avito structure into an official API;
- response/profile claims are evidence-bound;
- repeated and multivalue parameters are preserved;
- listing candidates are transport-neutral and field-level provenance-aware;
- phone, seller, rating and description are optional and evidence-gated;
- absence of an optional field does not break clean candidate handling;
- observed order is preserved;
- newest/newness decision belongs to Scan;
- pagination has per-page outcomes;
- batch processing does not hide partial, restricted or ambiguous pages;
- safe diagnostic evidence is limited to IDs, fingerprints, counts, profile references, field availability and redacted reason codes;
- raw provider payload retention is denied by default;
- sensitive access material is not stored;
- `OD-013` remains open.

## 5. Accepted contracts and artifacts

Main contract families evidenced for Module 05:

- compatibility/profile lifecycle;
- parser request/outcome;
- source analysis boundary;
- transport/response evidence classification;
- search configuration candidates;
- multivalue candidates;
- listing-card candidates;
- ordering and Scan handoff;
- pagination/page/batch evidence;
- privacy/diagnostic boundary.

Package and test boundaries referenced by the accepted scope:

- `src/mayak/modules/avito_parser_adapter/contracts.py`;
- `src/mayak/modules/avito_parser_adapter/fixtures.py`;
- package export boundary;
- contract/unit/architecture tests.

This handoff does not name any runtime parser implementation.

## 6. Synthetic fixture evidence

- fixtures are synthetic;
- real Avito HTML/JSON is absent;
- real listing data is absent;
- cookies, sessions and tokens are absent;
- raw provider payload is absent;
- APA-02 through APA-11 fixture families cover positive, blocked, ambiguous, partial and safety outcomes;
- APA-11 contains 16 privacy/observability fixture IDs;
- fixture `FX-APA11-COOKIE-SESSION-TOKEN-BLOCKED-001` uses only semantic classifications, not real access values.

## 7. Corrective evidence

### APA-10

- original SHA: `48196c30f407102acdec36317a165e120e4fe36a`;
- defect: nonempty `page_outcomes` was accepted when `empty` evidence observations were present;
- corrective SHA: `766ab41f81ce86074401b478e987e789afcb2d5d`;
- итог: unconditional exact tuple equality.

### APA-11

- original SHA: `4ebdee56e4bfcca2198224c901673fe2a71a830a`;
- defect 1: surrogate Enum members and dynamic `_member_map_` mutation;
- correction: `09df5302ced92c83729394c733ba475b4644fc20`;
- defect 2: Unicode-confusable `ＳＥＳＳＩＯＮ` and hex-obfuscated strings from an over-broad lexical architecture ban;
- root-cause correction: `b149abc372ff66005493938d58368824af7e81a7`;
- итог:
  - literal `SESSION = "SESSION"`;
  - no dynamic Enum mutation;
  - no Unicode confusable;
  - AST-level architecture protection;
  - semantic classification is allowed;
  - real session runtime remains forbidden.

## 8. Verification evidence

Current-run verification results recorded before writing this handoff:

- `git fetch` on `origin main` completed successfully with the GitHub SSH deploy key and `IdentitiesOnly=yes`;
- `HEAD` and `origin/main` were both `b149abc372ff66005493938d58368824af7e81a7`;
- branch was `main`;
- worktree was clean before edits;
- `HEAD` subject was `apa-11: use literal ascii session semantics`;
- `docs/04-modules/05-avito-parser-adapter/MODULE_PLAYBOOK.md` was present;
- `docs/00-governance/OPEN_DECISIONS.md` was present;
- `OD-009`, `OD-010`, `OD-011` and `OD-013` were open, not closed by assumption;
- backup ref `backup/APA-12-FULL-EVIDENCE-HANDOFF-20260712-001-before` was created locally and points to `b149abc372ff66005493938d58368824af7e81a7`.

Ancestor checks for prerequisites:

- Module 01 ancestor check: exit `0`;
- Module 02 ancestor check: exit `0`;
- Module 03 ancestor check: exit `0`;
- Module 04 ancestor check: exit `0`;
- Module 06 ancestor check: exit `0`.

Accepted SHA chain verification:

- APA-01 through APA-11 accepted SHAs each satisfied `git merge-base --is-ancestor <sha> HEAD`.

Tool results for the current run:

- Module 05 targeted pytest: `53 passed in 24.42s`;
- Ruff: `All checks passed!`;
- Mypy: exit `0`;
- Import boundaries: `Contracts: 3 kept, 0 broken.`;
- Full pytest: `581 passed in 75.16s (0:01:15)`.

Static document checks required by the task:

- exact path: satisfied;
- UTF-8: satisfied;
- no secrets: satisfied;
- no raw provider data: satisfied;
- no real Avito URLs or listing data: satisfied;
- all SHA values are 40 hex chars: satisfied;
- latest accepted SHA is `b149abc372ff66005493938d58368824af7e81a7`: satisfied;
- `OD-013` is OPEN: satisfied;
- live traffic is NONE: satisfied;
- production readiness is denied: satisfied;
- no executable, code or test changes in this handoff: satisfied.

## 9. Explicit non-ownership

Module 05 does not own:

- Beacon lifecycle, storage or revisions;
- Egress route, lease, fallback or credentials;
- ScanRun, baseline, anchors, diff, newness or history;
- NotificationEvent, outbox or delivery;
- Filter Catalog definitions or editability;
- account, identity, roles, tariffs or billing;
- Admin, Web, Telegram or MAX UI;
- DB, schema or migrations;
- scheduler, worker or deploy runtime.

## 10. Remaining gates

Open or blocked items remaining after the accepted semantic scope:

- official consumer-search API not proven;
- legal/access permission not proven;
- live Avito calls remain blocked;
- endpoint probing remains blocked;
- internal endpoint stability not proven;
- exact URL, redirect and DNS policy blocked;
- Egress runtime integration blocked;
- exact headers, cookies, session and auth policy blocked;
- retry, rate, backoff and circuit-breaker blocked;
- CAPTCHA operational handling blocked;
- `OD-009` editable filters open;
- `OD-010` country-wide support open;
- `OD-011` safe cadence open;
- `OD-013` retention open;
- exact field mapping/profile revalidation requires current evidence;
- listing detail enrichment blocked;
- phone/contact enrichment blocked;
- live pagination blocked;
- exact pagination limits blocked;
- persistence/DB/migrations blocked;
- logging/telemetry runtime blocked;
- Admin/Web/Telegram/MAX UI blocked;
- Docker/CI/CD/deploy/services blocked.

## 11. Live traffic and sensitive-data declaration

- `LIVE_AVITO_TRAFFIC: NONE;`
- `ENDPOINT_PROBING: NONE;`
- `BROWSER_AUTOMATION: NONE;`
- `RAW_PROVIDER_PAYLOADS_IN_GIT: NONE;`
- `REAL_AVITO_FIXTURES: NONE;`
- `COOKIES_SESSIONS_TOKENS_CREDENTIALS: NONE;`
- `PHONE_OR_OTHER_ACTUAL_PERSONAL_DATA: NONE;`
- `DATABASE_OR_MIGRATIONS: NONE;`
- `RUNTIME_SERVICE_OR_DEPLOY: NONE;`

## 12. Current accepted state

- APA-01 through APA-11 are complete only in the allowed governance, semantic, contracts and synthetic-tests scope;
- APA-12 is docs-only evidence/handoff;
- Module 05 is not implemented as a production parser/runtime;
- live/provider/runtime work requires separate gates and task packets;
- there is no next step for Module 05 without new owner, evidence or gate decisions;
- this module is ready for handoff to other modules only as a semantic contract source.

## 13. Prohibited claims avoided

This handoff does not claim:

- production-ready;
- live-tested against Avito;
- official Avito API available;
- automation legally approved;
- internal endpoint stable;
- phone extraction implemented;
- listing details enrichment implemented;
- pagination runtime implemented;
- DB/persistence implemented;
- raw retention approved;
- `OD-013` closed;
- Egress/Scan/Notification runtime integrated;
- UI implemented;
- deployed.
