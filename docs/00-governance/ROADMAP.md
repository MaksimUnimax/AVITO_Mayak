# Маяк Авито — дорожная карта

**Версия:** 2.6
**Статус:** APPROVED planning baseline

`[x]` accepted; `[~]` published/active; `[ ]` not started; `[!]` blocked.

- `[x] A0.1–A0.6` Product/model/governance bootstrap.
- `[x] A0.7` TASK-001 environment evidence and remote supervision.
- `[x] A0.8` Architecture Foundation v1.0.
- `[x] A0.9` Common Contract Foundation.
- `[x] A0.10` Data Model and Migration/Compatibility Policy.
- `[x] A0.11` Quality Foundation.
- `[x] A0.12` Operations and Avito reference documentation:
  - `[x] Run 6` Environment Matrix and Observability;
  - `[x] Run 7` Backup/Recovery and Deployment/Release;
  - `[x] Run 8` Windows Egress Agent boundaries;
  - `[x] Run 9` Avito reference registry, policy and evidence.
- `[x] A0.13` Technical Foundation:
  - `[x] Run 10` Technical Baseline package and exact server synchronization accepted.
- `[x] A0.14` Remaining provider references:
  - `[x] Run 11` Telegram and MAX reference policies plus cross-provider registry v1.1; exact server synchronization accepted at `642655a523af3591b1a024c39efa6978a064b2b8`.
- `[~] A0.15` Thirteen module playbooks:
  - `[x] Run 12` Platform & Contracts; accepted at `728b9062126fd7c2e816dde3a1a3ed9d42431cf2`;
  - `[x] Run 13` Identity & Access; accepted at `bcc33aa7120d60f977819319195000ab3a27a2c7`;
  - `[x] Run 14` Entitlements & Billing; accepted at `2346ccbbeaa8f1be18281fdf16fbec75cdb5052e`;
  - `[x] Run 15` Beacon Management; accepted at `2a73078c42cb03ef89d62b6161752f2069d35129`;
  - `[~] Run 16` Avito Parser Adapter published; exact server synchronization/acceptance pending;
  - `[ ] Run 17` Scan Orchestration & Listing State;
  - `[ ] Run 18` Egress Routing;
  - `[ ] Run 19` Notification Delivery;
  - `[ ] Run 20` Telegram Adapter;
  - `[ ] Run 21` MAX Adapter;
  - `[ ] Run 22` Admin & Support;
  - `[ ] Run 23` Web Cabinet;
  - `[ ] Run 24` Filter Catalog & Builder.
- `[ ] A0.16` Final independent documentation audit and stop.

Product implementation remains forbidden until the receiving module has an accepted playbook, current references where applicable, isolated toolchain proof and exact implementation task.

An accepted playbook is a prerequisite, not an automatic instruction to create code, dependencies, database, migrations, parser/provider calls, services or runtime.
