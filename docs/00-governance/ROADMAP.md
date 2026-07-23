# Маяк Авито — дорожная карта

**Версия:** 4.0
**Статус:** `MODULE_14_RF02_ACTIVE`
**Дата:** 2026-07-23

`[x]` independently accepted; `[~]` active; `[ ]` not started; `[!]` blocked.

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
- `[~] RF-02` Current-main governance reconciliation.
  - `[x] RF-02-01` Current-main reconciliation audit published and accepted at `59f86084bbc17386070dde34485aba6c1706712c`.
  - `[~] RF-02-02` Primary governance reconciliation.
  - `[ ] RF-02 remaining` Current decisions, manifest, indexes and final RF-02 closure.
- `[ ] RF-03` Thirteen-module integration inventory.
- `[ ] RF-04` Runtime architecture and physical data model.
- `[ ] RF-05` Existing-server environment record.
- `[ ] RF-06` Toolchain and dependency proof.
- `[ ] RF-07` CI quality gates.
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
