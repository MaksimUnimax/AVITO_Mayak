# Telegram Adapter Module — Full Evidence and Handoff v1.0

## 1. Metadata

- date: `2026-07-21`
- module: `09-telegram-adapter`
- roadmap step: `TG-16`
- technical task: `TG16-TELEGRAM-ADAPTER-FULL-EVIDENCE-HANDOFF-20260721-121`
- expected base: `ff139200ace791f2826dd19d6b50365b120fc9cb`
- latest accepted semantic/test SHA: `ff139200ace791f2826dd19d6b50365b120fc9cb`
- scope: governance + semantic contracts + synthetic deterministic tests + architecture/static boundaries + evidence only

## 2. Source-of-truth records

- playbook: `docs/04-modules/09-telegram-adapter/MODULE_PLAYBOOK.md`
- playbook blob: `90a63f982d93c527e64b0c648d5efb795183c573`
- playbook version/status/Run: `1.0` / `APPROVED documentation playbook` / `20 of 24`
- owner decision capture: `docs/04-modules/09-telegram-adapter/OWNER_TELEGRAM_DECISIONS_CAPTURE_v1.0.md`
- owner capture blob: `2b0523691ffc412df8fe9a8ec18836f3e5d6804b`
- open decisions: `docs/00-governance/OPEN_DECISIONS.md`
- open decisions blob: `df2d024ec54f84b53eca519681f82b062b9e4d7c`

## 3. Executive summary

TG-00–TG-15 are accepted. TG-00 has no commit and records accepted current-state, infrastructure and parallel-main verification. TG-16 is the final docs-only handoff. The module is complete only in accepted semantic/documentation scope. No Telegram provider runtime, API integration, persistence or deployment exists or is authorized.

## 4. Accepted SHA chain

| Step | Accepted commit | Exact subject |
|---|---|---|
| TG-00 | no commit | accepted current-state/infrastructure/parallel-main verification |
| TG-01 | `9fff874f97ca74536e62a01ee2b6811c61c5cd8f` | `tg-01: capture telegram owner decisions` |
| TG-02 | `21106dec6a9d8834fa67144fea54de96878e39ca` | `tg-02: add telegram identity boundary` |
| TG-03 | `e84e45968b5f7e140158a26e8681070c912d085b` | `tg-03: check every telegram import alias` |
| TG-04 | `98472ace88fa5edee265c0957a1b1e6d9e7f27d5` | `tg-04: close telegram import guard gaps` |
| TG-05 | `ca1df7f9b4afb7c10ecc19f24d797905475a82f7` | `tg-05: enforce canonical evidence modes` |
| TG-06 | `abd5a5a2fa037a560b164bf2ab31f72ce622f4c5` | `tg-06: add telegram intent normalization boundary` |
| TG-07 | `f140f484c92da07777c9aeb7721690b10907180a` | `tg-07: add telegram callback validation boundary` |
| TG-08 | `4622b255551f4ddeec4cc6d839a4a008f28c1bb6` | `tg-08: complete verified identity mismatch evidence` |
| TG-09 | `78ea359e4d5b01eed5c229d6605f852271551b37` | `tg-09: bind mini app validation to provider identity` |
| TG-10 | `b727bc1a74458d76bff7a090d06db4cb039aed87` | `tg-10: add private chat surface admission boundary` |
| TG-11 | `0c3619849a485bc48acacc311302d34bf41a8f7b` | `tg-11: add outbound notification attempt mapping boundary` |
| TG-12 | `2a1b4af87790f11237b437ebe52cc8e614778ea7` | `tg-12: add telegram display projection boundary` |
| TG-13 | `704914342712a44bacf12b105d15545531a0144d` | `tg-13: add telegram provider outcome boundary` |
| TG-14 | `ab9af6d2b2f6476eddb3ea089d23e107367406a1` | `tg-14: add telegram security privacy retention boundary` |
| TG-15 | `ff139200ace791f2826dd19d6b50365b120fc9cb` | `tg-15: add telegram runtime gate boundary` |

Every committed SHA in the table is an ancestor of `ff139200ace791f2826dd19d6b50365b120fc9cb`; each exact subject was verified from Git metadata.

## 5. Corrected and rejected history

The following are initial, intermediate or corrective history, not accepted roadmap entries: TG-03 `13dbb7c` and `d221fe5`; TG-04 `04febb5` and `cafef29`; TG-05 `be8dfb3`; TG-07 `8dd9685` and `82c90bc`; TG-08 `56bb33c`, `8d0682a` and `8c9c28a`; TG-09 `b27609a`; and TG-12 `d9b0ffa`. Their subjects describe preliminary or correction work and they are never marked accepted here. TG-14 and TG-15 acceptance is represented only by the exact SHAs in the accepted table; parallel-main refreshes and any STOP_BASE_MISMATCH task are safety evidence, not roadmap acceptance commits. No missing SHA or task result is inferred.

## 6. Accepted artifact inventory

The inventory below is derived from the expected-base checkout. Each row is `path | Git blob SHA | local SHA-256`.

### Production source

| Path | Git blob SHA | SHA-256 |
|---|---|---|
| `src/mayak/modules/telegram_adapter/__init__.py` | `c568854a1eeaede93b6b0b9e7fba416d76bc18e5` | `ed794e18b3ba7de2473bb8c3474f4219c204cafcc979a7c71fc1b6b79e16cbf4` |
| `src/mayak/modules/telegram_adapter/contracts.py` | `5f5a8ef681881a43d07097dcb80dfc3e633c404e` | `83ee5955436daec2c5729b384fe05c3fb119ed12040d42106d63130529a07448` |

### Telegram unit, contract and architecture tests

| Path | Git blob SHA | SHA-256 |
|---|---|---|
| `tests/unit/test_telegram_adapter_callback_validation_contracts.py` | `6ef13efedb2ec8e43131420d04bd7c53c4b29860` | `683f80719f1afebe33e7565b31df93c1f9c954ea9bbff59340d412dac155e328` |
| `tests/unit/test_telegram_adapter_chat_surface_contracts.py` | `5b75dcbaf6b937247cfc14aaed01d13bcb2e31cb` | `e4353f6da17a33342b49151feed8aa735205992a01d50ee80f4081967d576159` |
| `tests/unit/test_telegram_adapter_deep_link_validation_contracts.py` | `caf25dea85584e8adab842342c4123f0398dd871` | `9f39cc4eadab5b836c6f7267cdbb2fdab2412841eed5b0ad18c7d683cf282049` |
| `tests/unit/test_telegram_adapter_display_projection_contracts.py` | `39455dc39c5bacf5f8e6f1155171425c006a82c8` | `4fd1eda68adcd0697bbd6169f5da75ea25d3e8143e95a93c5211dc146f861a80` |
| `tests/unit/test_telegram_adapter_existing_bot_operational_gate_contracts.py` | `344af16e1ebc510da16e40cd9226b317fea5b574` | `29ab74241a302aa0f2c36d6e8dd5e46e6eab98d64673cbf1b13200f63551b957` |
| `tests/unit/test_telegram_adapter_identity_contracts.py` | `8587b731ca324143103daea3fc9462aaa7c4ba3f` | `0babf29fcf244db8e1a4dd4abf969ce750d3e709968da4f232950aa8a82a3505` |
| `tests/unit/test_telegram_adapter_intent_normalization_contracts.py` | `bcc7eaae781b31e0bf214a0b681844e0e093b995` | `aa7158cfe07ccdaa5df3d261a3f9e71063268554cb98ee5dfe1286a4485f0c9a` |
| `tests/unit/test_telegram_adapter_mini_app_validation_contracts.py` | `eae7504374fbb3d486168f69f7eb407a84b99aab` | `fea89324d19ed4b22041ead7dac34a29d91fd668c74a4cab34eeef18a3b7211c` |
| `tests/unit/test_telegram_adapter_outbound_mapping_contracts.py` | `62d9858d2d7ab711baff726bd1a706cf9cb8f4db` | `ff873851f3f99a8825b672487458be1f31cab25dfbcd5c9b8e36781a130639ae` |
| `tests/unit/test_telegram_adapter_provider_mode_contracts.py` | `7753fe51d83231d64e9c17ee50a94d12b1dbe297` | `aa704fb1ab925a0c7e0ace6bb91c0b3eacd2c900fe0b6be07456308830878910` |
| `tests/unit/test_telegram_adapter_provider_outcome_contracts.py` | `4b218afa0971a95315a518a1ccd814ee4571098a` | `0691df1aad73567d596393f28b373733b6a5b680ef051233e97bfebe2d9ad878` |
| `tests/unit/test_telegram_adapter_runtime_gates.py` | `bb71feb258d8a39a5c5f89fa9aebad5541ae8a33` | `f70c5648ba17c9860d49cdcccdf9aa797ad0d7566db64e0fe137937e3da85f26` |
| `tests/unit/test_telegram_adapter_security_privacy_contracts.py` | `4fcc92cfde170d669c0165c60b8fd97fe7be91b9` | `1cab36d6e18fc5361a5f590c3653ed4ce43e2fef6658cad82e0bc0d9457738c0` |
| `tests/unit/test_telegram_adapter_update_intake_contracts.py` | `278cb090be3f5e988eeeae1e943185c1e59db57a` | `a51338c0d470404388d2e7ff3f9a39531c30c2db4b95d950814be84a3c429c3f` |
| `tests/contract/test_telegram_adapter_callback_validation_exports.py` | `4bd03f770e2460e9ad19755b20bee457f7e5a74b` | `4079e5792596a9cc62145acb0279886bfb5816b7f226db2282685d604e2cffde` |
| `tests/contract/test_telegram_adapter_chat_surface_exports.py` | `5afc6392d84507c7b288c1dc168a0bce8994cffb` | `cba75aa61a9822943b40c04d37240dd4d158345c3cc20923890f7c0330798d71` |
| `tests/contract/test_telegram_adapter_deep_link_validation_exports.py` | `f5f39122b63efce07dee14ae0d5e009e484b2a62` | `ed4e0bb6f0c318b4c43351d8950f97c8fc5ff6b6a9de6afcb8628030f178178e` |
| `tests/contract/test_telegram_adapter_display_projection_exports.py` | `a49426f1cf6ad42ea4b412e397765e15e034d79d` | `09d10c48fb6d9562a3894c5ff994ccc267857883d80fb096b0e0b545e8a994ee` |
| `tests/contract/test_telegram_adapter_existing_bot_operational_gate_exports.py` | `f6395555375df44ed0c6a11c3427063ebd9feea7` | `c483b2af2247c3cbdaa3390e06fc3d5c65b75b3cc43ac15cc954c4db484c3121` |
| `tests/contract/test_telegram_adapter_imports.py` | `9e8aee4052bdc1caaf8f57e6fa168af6e8578aa4` | `2b7e0e701eeb2cf7441d55bb1a419ab7b86458e7f933f65ffa8bbc5a38ed5a26` |
| `tests/contract/test_telegram_adapter_intent_normalization_exports.py` | `29316dd1caa92489ea196054e43c6ebff9bf9052` | `73ac690d317761c8cc5fbe6e319b11e30bbe04607562310f7b5490ce17e4e495` |
| `tests/contract/test_telegram_adapter_mini_app_validation_exports.py` | `b10a382518e6a15f882638c4e33c21b8c31f8364` | `d71677d2f7b70c2f4ad44ec25434a5589af5f8cb998ecee34d90ab68b3294bc5` |
| `tests/contract/test_telegram_adapter_outbound_mapping_exports.py` | `94f33e47d1d2fd81daa2a2a6a731bb67768ba984` | `9e95855f96862113a906918437ca24619186efd4d5e82c0820b9ec8a358ed64c` |
| `tests/contract/test_telegram_adapter_provider_mode_exports.py` | `945369a9132939528b5c0c67b39bf878ea25e32c` | `7bcc529885be9a84b227727f67dcf66299e72a22a2ef9f9e60c8c5e7fdd15b34` |
| `tests/contract/test_telegram_adapter_provider_outcome_exports.py` | `a9b5deb46ec89bd422ccac3f18d210bdfca8933c` | `db3439c36c495bc7d388006c4c77cbc85a9e2f32e5beae46b3c82cf75667c422` |
| `tests/contract/test_telegram_adapter_runtime_gate_exports.py` | `069961c7724f34986f6a706b94040eb8888f8b28` | `3107f71692301d88ff86965c1c55f0eb37085ea78483129de9d8904b460c6e49` |
| `tests/contract/test_telegram_adapter_security_privacy_exports.py` | `5b9af65bc020c3d71b159718d00eef20e6d4066e` | `b64af853bbb7d3d6fba379c597bbc696b2c3409b45cbacb7af35e4199bac8274` |
| `tests/contract/test_telegram_adapter_update_intake_imports.py` | `bba063ce4caa31061509e5eae9c685611c0f866a` | `59794daee6c0012fed8596df296db42e71414c2c4301848ed111bf4d4617c9c0` |
| `tests/architecture/test_telegram_adapter_callback_validation_boundaries.py` | `31588310b9152af1afc56311127d25593a216f70` | `8360ecf08c8ae77eca9a1b57dfe6e37f203f23c4592a1dea963994c278cb723d` |
| `tests/architecture/test_telegram_adapter_chat_surface_boundaries.py` | `8d17c2d053e32e67a1ae812446b2afc11eb4f6ed` | `bd47a3d8ea24d19a6eb30f8dd784ec37b37c2204745d80743e3f260ba69c94f0` |
| `tests/architecture/test_telegram_adapter_deep_link_validation_boundaries.py` | `c0bd4e3840f052f1eed6039e4b20fe2541bf734b` | `fedf1ae34551a34bc6c362a48e39c7ade2b14e77cae52f07c2e31a2ebf376f8f` |
| `tests/architecture/test_telegram_adapter_display_projection_boundaries.py` | `e66a0fb26bde5e2b510600c17b84891ecaedf712` | `574d626aa3336c79af7f08615610420cc298f7a968dc21631b93cfef0044920f` |
| `tests/architecture/test_telegram_adapter_existing_bot_operational_gate_boundaries.py` | `c889ac11ce3746d1a481ba4e098fd1081daa517d` | `069dbfb4292c6cffd6f7687b010fe668405cc218ec9798f085d0bc324107ebb1` |
| `tests/architecture/test_telegram_adapter_import_boundaries.py` | `9388792800689d8a80a09e9678cd7c7339de2174` | `065dfbf797a6196b5c127350999b19c1730a52de28ded59e8e9416de3a4950d5` |
| `tests/architecture/test_telegram_adapter_intent_normalization_boundaries.py` | `9ab6df2520214a61ffbdceafb9150223cd72ee45` | `d369d7ae4d0e1f7195cc3bacbd4755a33d8d25cad1c7e282e4034707a51c70a8` |
| `tests/architecture/test_telegram_adapter_mini_app_validation_boundaries.py` | `22c847b3a42cd56cc6a5d601a7d134c72e00f59a` | `382c0e4c57061aab2cd8a1fb6df1c5f8f95bace8967274ec244b0e180326f412` |
| `tests/architecture/test_telegram_adapter_outbound_mapping_boundaries.py` | `d0c811da8fb34feb62e1fe4ba3f8681ede9f790e` | `0b110552c1a2652d37abb1c8fd9d424a11702f4a2ed34bf9bbf195f76f87746e` |
| `tests/architecture/test_telegram_adapter_provider_mode_boundaries.py` | `0c9c122a8319c66c7e4bc00282cd928867394aed` | `6a83785f3c0171783d048bed3ca1dcdd1c2259031beb6cc04809c6b187e00357` |
| `tests/architecture/test_telegram_adapter_provider_outcome_boundaries.py` | `d7a917a036cb34339de13b30d5b8f6b55f13eb74` | `9b8dfde1621ce286794bab20fe998e727e8dd329182976357349f4716ed785dc` |
| `tests/architecture/test_telegram_adapter_runtime_gate_boundaries.py` | `430412f93c3a6b8e9ad0918a7c8ecfd7f6b90ae6` | `3daf3f9a8d0853bd377c69836d1181c9906025c83fe0e6465dedcc4bc0bfc1b8` |
| `tests/architecture/test_telegram_adapter_security_privacy_boundaries.py` | `36db27f5f4e2f32dfd1a39009bdb9d31c84f428f` | `acfe9fe4ffef9970bc519980f1ccc08f940bb9628bd12aa73bb0ea011873ce6e` |
| `tests/architecture/test_telegram_adapter_update_intake_boundaries.py` | `9ab99f34d7c027ff721d6374838b887a741f32bc` | `8c1ce7ca099ea24001170716cff6c7def3e431978dd75ad52d624b26551f96f2` |

Artifact inventory count: 47 artifacts: 44 source/test files (2 source, 14 unit, 14 contract, 14 architecture) plus the three complete-file governance artifacts above.

## 7. Public semantic surface

The accepted surface covers provider identity/account-link; inbound update intake and deduplication; mutually exclusive webhook/getUpdates mode; existing-bot/protected-secret evidence; command/message/Avito-link intent normalization; callback validation and destructive-action confirmation; deep-link validation; Mini App raw-init-data validation; private-chat-v1 admission; outbound Notification attempt mapping; Telegram listing/status display projection; provider outcome, reconciliation and false-success handling; and security/privacy/retention plus runtime/provider/schema/dependency gates.

## 8. Ownership boundaries

`account_id` is authoritative internally; Telegram IDs are external only. Identity owns account creation, linking, merging and authentication. Beacon Management owns Beacon validation, lifecycle and mutation. Notification Delivery owns generic outbox, attempt, lifecycle and acceptance. Scan owns scan facts and recovery. Egress owns transport routes. Entitlements owns limits and access. MAX and Web Cabinet remain separate modules. Telegram Adapter has no direct foreign-module mutation authority.

## 9. Existing bot and secret status

- bot exists: `@signalings_bot`
- numeric provider ID: `8664835407`
- token reference: `/etc/avito-mayak/secrets/telegram_bot_token`
- public metadata reference: `/etc/avito-mayak/telegram-bot.conf`
- bot creation: complete
- safe metadata observed for the protected token: present, root owner/group, mode `0600`, non-zero size
- raw token: `NOT_READ_NOT_PRINTED`

BotFather reconfiguration and token rotation/revocation/deletion remain owner-gated. Bot/token presence does not authorize provider calls or runtime.

## 10. Operational mode status

Production target direction is webhook. Development/proof may use `getUpdates` only under an exact future task. Modes are mutually exclusive and no live mode is selected. Webhook authenticity is mandatory if selected. Endpoint/domain/TLS/certificate/port remain unresolved and blocked; occupied shared-host ports are not assigned to Telegram Adapter.

## 11. Input trust and safety

Commands, messages, callbacks, deep links, update payloads and Mini App launch data are untrusted. Callback data is not executable authority. Destructive actions require server-side ownership checks and confirmation. Raw IDs and secrets are forbidden in callback/deep-link authority. `initDataUnsafe` is never trusted. Groups, channels and topics are unsupported in v1.

## 12. Outbound and display semantics

Only Notification attempt mapping is in scope. `ok=true` means provider accepted the request, not human read/click or final business success. Ambiguous provider effect is reconciliation-first with no blind retry. There is no default 20-message spam burst and no listing-reference loss at the adapter boundary. Optional phone, seller and details come only from approved upstream safe facts; there is no Avito parsing/enrichment. No-new and unavailable/recovery eligibility remains upstream-owned.

## 13. Security, privacy and retention

No raw token, webhook secret or private key; no raw provider payload in ordinary logs/fixtures; no private-message archive; no group-member lists; and no contact requests or phone numbers by default. Safe diagnostics are limited to minimized IDs/classes, reason codes, correlation/causation and redacted evidence references. External strings never become shell commands. `OD-013` remains `OPEN`; no retention, deletion, archive or compaction values are guessed.

## 14. Runtime, provider, schema and dependency gate matrix

All of the following remain blocked until their own exact gates and a later implementation task: PostgreSQL tables, SQLAlchemy models, Psycopg, Alembic, provider SDK/library, HTTP client, Telegram API calls, webhook endpoint, `getUpdates` loop, polling cursor, Mini App frontend, BotFather configuration, bot-token consumption, provider credentials, message templates, queues/workers/services, endpoint/domain/TLS/port, and Docker/CI/CD/deploy. Even a satisfied gate reference does not grant implementation authority.

## 15. Current infrastructure evidence

Safe redacted snapshot only: sufficient disk was available; isolated CPython path is `/opt/avito-mayak/.venv/bin/python` (Python 3.14.6); deploy-key path is `/root/.ssh/avito_mayak_github_deploy_ed25519` with safe metadata only (mode `0600`, root owner/group, non-zero metadata size); no key contents, token contents, environment dump or provider runtime claim is included.

## 16. Fresh verification evidence

Commands and exact results on the clean expected-base checkout:

| Check | Command/result |
|---|---|
| syntax/import | `/opt/avito-mayak/.venv/bin/python -m compileall -q src/mayak/modules/telegram_adapter` — PASS |
| Ruff | `/opt/avito-mayak/.venv/bin/ruff check` over source and all Telegram test files — PASS, all checks passed |
| Telegram unit | explicit tracked `tests/unit/*telegram*` files — `410 passed` |
| Telegram contract | explicit tracked `tests/contract/*telegram*` files — `36 passed` |
| Telegram architecture | explicit tracked `tests/architecture/*telegram*` files — `75 passed` |
| full repository suite | `/opt/avito-mayak/.venv/bin/python -m pytest -q` — `4308 passed` |
| `git diff --check` | PASS |
| forbidden artifact/import/call scans | PASS; no runtime/provider implementation or forbidden artifact introduced |

The broader `tests/unit -k telegram` selector reported 434 because it also selected four non-Telegram-file tests; the exact tracked Telegram-file run above is the required 410-count result.

## 17. Parallel-work notes

Web Cabinet commits advanced `main` during TG-14/TG-15 preparation. Accepted refreshes were byte-exact and overlap-free. No uncontrolled merge, rebase, reset, cherry-pick, amend, squash, stash, clean or force-push occurred. GitHub `main` remained the source of truth. TG-16 changes no foreign-module path.

## 18. Remaining gates and dependencies

Remaining dependencies include Identity, Beacon, Notification, Scan, Egress, Entitlements, MAX and Web, plus provider/runtime/schema/dependency/security/operations gates; exact webhook/getUpdates mode selection; Mini App security/UI/hosting/auth_date; callback/deep-link final formats; final command/template/UI catalogs; groups/channels/topics; and `OD-013`. No open decision is closed by implication.

## 19. Scope completion and handoff status

TG-00–TG-16 is complete only after this commit is independently accepted. The module is complete for governance, semantic, synthetic-test, static-boundary and evidence scope. It is not runtime-ready or deployed. No next module or roadmap step is selected. Future runtime work requires new owner, architecture, security and operations tasks.

TELEGRAM_ADAPTER_HANDOFF_STATUS=SEMANTIC_DOCUMENTATION_SCOPE_COMPLETE_PENDING_INDEPENDENT_ACCEPTANCE

## 20. Evidence controls

This handoff contains evidence only: no new architecture, product decision, owner decision, implementation authority, provider call, credential use, schema, runtime, deployment, template, UI, callback/deep-link format or retention value. Protected token and private key contents were not read, printed, copied, hashed, fingerprinted, base64-encoded or otherwise represented. No raw provider payload or personal-message content is present. The only permitted write path for TG-16 is this file.
