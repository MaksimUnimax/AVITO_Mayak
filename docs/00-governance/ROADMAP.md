# Маяк Авито — дорожная карта

**Версия:** 4.0
**Статус:** `MODULE_14_RF06_TOOLCHAIN_BOOTSTRAP_PUBLISHED_PENDING_ACCEPTANCE`
**Дата:** 2026-07-23

`[x]` independently accepted; `[~]` active; `[ ]` not started; `[c]` repository-content complete/published for independent acceptance; `[!]` blocked.

## Historical documentation foundation

The A0 documentation route is preserved as accepted project history:

- `[x] A0.1–A0.6` Product/model/governance bootstrap.
- `[x] A0.7` Environment evidence and remote supervision.
- `[x] A0.8` Architecture Foundation.
- `[x] A0.9` Common Contract Foundation.
- `[x] A0.10` Data Model and Migration/Compatibility Policy.
- `[x] A0.11` Quality Foundation.
- `[x] A0.12` Operations and provider-reference documentation.
- `[x] A0.13` Technical Baseline.
- `[x] A0.14` Telegram and MAX reference policies.
- `[x] A0.15` Module playbooks 01–13.
- `[x] A0.16` Final documentation audit and historical acceptance cycle.

Historical A0 completion does not mean that the Module 14 runtime is implemented, deployed or production-ready.

## Module 14 — Runtime Foundation & Autonomous Integration

- `[x] RF-00` Current state, GitHub and server verification.
- `[x] RF-01` Governance capture and Module 14 playbook.
- `[x] RF-02` Current-main governance reconciliation — independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
  - `[x] RF-02-01` Current-main reconciliation audit accepted at `59f86084bbc17386070dde34485aba6c1706712c`.
  - `[x] RF-02-02` Primary governance reconciliation accepted at `63de1f4c62e1b72626f20278dbba9eef190b6a99`.
  - `[x] RF-02-03` Current decision register reconciliation accepted at `f7733447f5f10cc3f3702c8f863accb4d9403c05`.
  - `[x] RF-02-04` Documentation manifest reconciliation accepted at `8d3ff83198d90f062906925d6f4becf66c81ed9a`.
  - `[x] RF-02-05` Applicable documentation indexes reconciliation accepted at `34db47cbbffd7f31a918963b181e3048229307be`.
  - `[x] RF-02-06` Module registry and playbook gate reconciliation accepted at `ae4181ab06fd0cae45ef5d7d8be55d796b8f7ac5`.
  - `[x] RF-02-07` Closure evidence and status transition independently accepted at `c92e9299e5c0bd11ea18362673a8ac342b835483`.
- `[c] RF-03` Thirteen-module integration inventory — repository-content complete; closure published for independent acceptance.
  - `[x] RF-03-01` Thirteen-module completion matrix independently accepted through corrective SHA `23e73707b14b220da98beade93ee2d13021ba1b9`.
  - `[c] RF-03-02` Cross-module runtime gap matrix — repository-content complete and independently accepted through `061757c4cfd9c5c4ea466539c4a92499e5b269d5`.
  - `[c] RF-03-03` Cross-module consistency audit — repository-content complete and independently accepted at `e8a38a1ce3e506f5d880129bb9781802cd69f48b`.
  - `[c] RF-03-04` Closure evidence and status transition — repository-content complete; published for independent acceptance.
- `[x] RF-04` Runtime architecture and physical data model — accepted through `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
  - `[x] RF-04-01` Physical data model — accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`.
  - `[x] RF-04-02` Transaction and outbox boundaries — accepted through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`.
  - `[x] RF-04-03` Runtime process and package model — accepted at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`.
  - `[x] RF-04-04` Migration and schema evolution plan — accepted at `39f65b3f2de9668be188aec6f16b777d04f23135`.
  - `[x] RF-04-05` Runtime topology candidate — accepted through `9062d613d64ded16c9758ea33ae7cfe04c267990`.
  - `[x] RF-04-06` Configuration and secrets boundary — accepted at `0d0efe27018fa01e1248e8939a026a3e590d622b`.
  - `[x] RF-04-07` Closure and status transition — accepted through `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
- `[x] RF-05` Existing-server environment record — independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`; repository-content complete; `NOT_PRODUCTION_READY`.
  - `[x] RF-05-01` Read-only host and allocation baseline.
  - `[x] RF-05-02` Service identity and isolation evidence.
  - `[x] RF-05-03` Filesystem boundaries and permissions evidence.
  - `[x] RF-05-04` Environment allocation record validation.
  - `[x] RF-05-05` Repository evidence and closure — accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`; `NOT_PRODUCTION_READY`.
- `[~] RF-06` Toolchain and dependency proof — RF-06-01 and RF-06-02 accepted; RF-06-03 corrective dependency expansion, lock and clean sync published pending independent acceptance; runtime stopped.
  - `[x] RF-06-01` Toolchain and dependency baseline — accepted through corrective SHA `f77a1d85d7c8b8fd1f2e60694729d1b7c3a1598c`.
    - `[x] RF-06-01-C01` UV candidate freshness correction — accepted through the corrective chain.
  - `[x] RF-06-02` Bootstrap and executable verification — independently accepted at `4c28354bceaf8325084d8ffd99a31e662c518a71`.
  - `[c] RF-06-03` Dependency expansion, lock and clean sync corrective chain published for independent acceptance.
    - `[c]` OpenTelemetry coupled-prerelease correction.
    - `[c]` OpenTelemetry import-topology correction.
    - `[x]` Quality baseline and FC-08 classification.
    - `[c]` FC-08 historical-boundary correction and publication.
  - `[!] RF-06-04` Closure blocked pending RF-06-03 acceptance.
- `[ ] RF-07` CI quality gates — blocked pending RF-06-03 acceptance.
- `[ ] RF-08` Container and Compose foundation.
- `[ ] RF-09` PostgreSQL and Alembic foundation.
- `[ ] RF-10` Platform & Contracts runtime.
- `[ ] RF-11` Identity & Access runtime.
- `[ ] RF-12` Entitlements & Billing runtime.
- `[ ] RF-13` Beacon Management runtime.
- `[ ] RF-14` Avito Parser Adapter runtime.
- `[ ] RF-15` Scan Orchestration & Listing State runtime.
- `[ ] RF-16` Egress Routing runtime.
- `[ ] RF-17` Notification Delivery runtime.
- `[ ] RF-18` Telegram Adapter runtime.
- `[ ] RF-19` MAX Adapter runtime.
- `[ ] RF-20` Admin & Support runtime.
- `[ ] RF-21` Web Cabinet runtime.
- `[ ] RF-22` Filter Catalog & Builder runtime.
- `[ ] RF-23` Cross-module API and command wiring.
- `[ ] RF-24` Synthetic end-to-end vertical slices.
- `[ ] RF-25` Security, privacy and supply-chain verification.
- `[ ] RF-26` Observability, backup and recovery.
- `[ ] RF-27` Deployment on the existing server.
- `[ ] RF-28` Automated final regression and failure drills.
- `[ ] RF-29` Operator acceptance pack.
- `[ ] RF-30` Final evidence handoff.

## Execution rules

- GitHub `main` is checked before every task.
- One CLI task performs one atomic scope.
- CLI never chooses the next roadmap step.
- A task may mutate only exact allowed paths and resources.
- Parallel-main change stops publication.
- Missing optional provider credentials disable that provider and do not stop unrelated work.
- Runtime mutation requires the applicable RF prerequisite and exact task.
- The existing project server is the authorized runtime host.
- Foreign resources must not be altered or reused.
- Public ingress and production launch remain blocked.
- `READY_FOR_OPERATOR_ACCEPTANCE` is achieved only after RF-30 acceptance.
- Module 14 must not claim `PRODUCTION_READY`.
