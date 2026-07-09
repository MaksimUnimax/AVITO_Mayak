# Mayak Avito - Beacon Management BM-12 Evidence/Handoff

**Status:** APPROVED evidence/handoff
**Module:** `04-beacon-management`
**Current accepted module SHA:** `f3e786392f9d1ce18382fbcce3c24389b1980379`
**Scope:** docs-only evidence/handoff for module 04. No source code, test, runtime, DB, UI, parser, or deploy changes.

## Accepted prerequisites

- module 01 final SHA: `79c550e6a5a9ed68c4aaadebb219aaad4e8afa63`
- module 02 final SHA: `5d278bfde42657d61a002e3e165d99330bdbb3ec`

## Accepted module 04 step log

| Step | Accepted SHA | Local evidence |
|---|---|---|
| BM-01 governance capture | `0258bc0d2761feac741bd4696baf2254ce5324c3` | `ADR-0016` and `OWNER_DECISIONS_CAPTURE_v1.0.md` capture the owner decisions for Beacon Management. |
| BM-02 semantic contracts and synthetic fixtures | `bdcf48e2a14a2f6a49fca34942ca803dfd9c1760` | `git log` shows `bm-02: add beacon semantic contracts`. |
| BM-03 account ownership and authorization | `7d75776cef450138612111258d640584fc3e550b` | `git log` shows the BM-03 add/harden commit chain. |
| BM-04 source URL preservation and preparation boundary | `744b2aef75d81095c45973f75c7b54c37211670e` | `git log` shows the BM-04 add/harden commit chain. |
| BM-05 parser outcome and extracted snapshot acceptance boundary | `1b4037efc1d1ff8b051025dcd5a3d08f8e6dbcbd` | `git log` shows `bm-05: add parser snapshot acceptance boundary`. |
| BM-06 structured overrides and effective configuration assembler | `0ee6c56ecc20789a1d8caecf3f4eccfdd61799d6` | `git log` shows the BM-06 add/harden commit chain. |
| BM-07 current configuration and revision/storage policy | `cbebe0e85682860ba3607df9e06142a271095db7` | `git log` shows `bm-07: add current config storage policy semantics`. |
| BM-08 entitlement-gated lifecycle | `410dd9d42ef59fb4534f9e12b8033db3979ebf5e` | `git log` shows `bm-08: add entitlement gated lifecycle semantics`. |
| BM-09 Beacon History / Archive / Delete / Permanent Delete | `f3e786392f9d1ce18382fbcce3c24389b1980379` | `git show --name-only` confirms the two BM-09 test files changed in this commit. |

## BM-09 evidence

- commit: `f3e786392f9d1ce18382fbcce3c24389b1980379`
- parent: `164dd1372cc58846572bb1d25cd35b4f26ce3f08`
- changed paths:
  - `tests/contract/test_beacon_management_bm09_history_contracts.py`
  - `tests/unit/test_beacon_management_bm09_history_semantics.py`
- targeted checks passed
- full repo ruff/mypy failures are pre-existing baseline debt outside BM-09, proven by evidence task `BM04-BM09-CHECK-BASELINE-EVIDENCE-20260709-003`

## Current semantic boundaries

- account-owned Beacon
- source URL preservation
- parser snapshot acceptance safety
- structured overrides
- patch-based save and last-write-wins
- current working configuration and no unbounded user-facing revision clutter
- entitlement-gated activation, resume, and freeze
- History / Archive / Delete / Permanent Delete semantics

## Remaining gated work

- BM-10 is gated by the Scan Orchestration contract.
- BM-11 is gated by physical schema and migration decisions.
- Parser implementation remains gated.
- Filter Catalog implementation remains gated.
- Notification Delivery remains gated.
- Telegram, MAX, Web, and Admin UI remain gated.
- DB, persistence, migrations, runtime, and deploy remain gated.

## Explicit non-ownership

- no Parser Adapter implementation
- no ScanRun/listing history ownership
- no Notification outbox/delivery ownership
- no Entitlements tariff/payment authority duplication
- no Identity/session/role ownership
- no Admin/Web/Telegram/MAX UI ownership

## Known project debt

- full repo ruff baseline has pre-existing E501/I001 failures outside BM-09
- full repo mypy baseline has pre-existing failures in Entitlements & Billing and related tests outside BM-09
- BM-09 targeted files are clean

## Next safe state

- BM-01 through BM-09 are complete for the current semantic scope.
- BM-10 must not start until the Scan Orchestration contract gate is accepted.
- BM-11 must not start until the physical schema and migration gates are accepted.
- After BM-12, module 04 is evidence/handoff complete for the current semantic scope.

## Do not

- edit source code
- edit tests
- add executable tests
- add parser/runtime/DB/UI implementation
- close open decisions by assumption
- invent missing SHAs
- claim live Avito/Telegram/MAX evidence
- claim production readiness
- claim DB/migrations/deploy exist

## Verification basis

- Module playbook: `docs/04-modules/04-beacon-management/MODULE_PLAYBOOK.md`
- Governance decision log: `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`
- Open decisions: `docs/00-governance/OPEN_DECISIONS.md`
- Module history evidence: git log for module 04 paths and BM-09 commit metadata
