# Маяк Авито — дорожная карта

**Версия:** 1.10
**Статус:** APPROVED planning baseline

`[x]` accepted; `[~]` active; `[ ]` not started; `[!]` blocked.

- `[x] A0.1–A0.6` Product/model/governance bootstrap accepted.
- `[x] A0.7` TASK-001 technical environment evidence accepted; remote supervision introduced.
- `[x] A0.8` Architecture Foundation: Architecture Baseline, Environment Isolation Policy and Security/Privacy Model accepted.
- `[x] A0.9` Common Contract Foundation: Contract Package, Error and Idempotency Policy and Contract Change Policy accepted.
- `[x] A0.10` Data Model and Migration/Compatibility Policy accepted.
- `[x] A0.11` Quality Foundation: Test Strategy, Fixture Registry, Acceptance Matrix and Reference Regression Policy accepted.
- `[~] A0.12` Operations and external-reference documentation active:
  - `[x] Run 6` Environment Matrix and Observability/Alerting baseline accepted;
  - `[x] Run 7` Backup/Recovery and Deployment/Release boundaries accepted;
  - `[x] Run 8` Windows Egress Agent runbook accepted;
  - `[x] Run 9` Avito reference registry, policy and evidence accepted;
  - `[ ] Run 10` Telegram and MAX reference policies.
- `[ ] A0.13` Thirteen module playbooks.
- `[ ] A0.14` Final independent documentation audit and stop.

Product implementation is forbidden until required documentation gates are accepted. A module cannot start without approved boundaries, owner, contracts, data/compatibility rules, fake dependencies, fixtures, acceptance checks and applicable operations/reference evidence. Avito Ads evidence is not a consumer-search authorization. Primary implementation references do not replace official provider contracts. CLI reports never replace independent GitHub acceptance.
