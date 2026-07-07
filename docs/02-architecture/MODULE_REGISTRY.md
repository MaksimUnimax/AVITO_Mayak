# Маяк Авито — реестр модулей

**Версия:** 1.4
**Статус:** APPROVED registry derived from Architecture Baseline v1.1
**Правило:** это реестр границ. Playbook status does not authorize implementation; each published run still requires exact server synchronization and independent acceptance.

| № | ID каталога | Модуль | Владелец данных / граница | Playbook |
|---:|---|---|---|---|
| 01 | `01-platform-and-contracts` | Platform & Contracts | application skeleton, configuration conventions, common errors, idempotency conventions, migration/tooling conventions after approval; no foreign business state | v1.0 accepted |
| 02 | `02-identity-and-access` | Identity & Access | accounts, identities, authentication records, roles, sessions, auth/link challenges | v1.0 accepted |
| 03 | `03-entitlements-and-billing` | Entitlements & Billing | tariff definitions, subscriptions, entitlement grants, manual access, future payment records and later approved usage counters | v1.0 accepted |
| 04 | `04-beacon-management` | Beacon Management | Beacons, source URLs, extracted snapshots, user overrides, effective configuration, immutable revisions and lifecycle authority | v1.0 published; Run 15 sync pending |
| 05 | `05-avito-parser-adapter` | Avito Parser Adapter | extraction/normalization of Avito search data; no direct Beacon mutation or notification delivery | RESERVED — Run 16 |
| 06 | `06-scan-orchestration-and-listing-state` | Scan Orchestration & Listing State | runs, observations, baseline/diff, listing state | RESERVED — Run 17 |
| 07 | `07-egress-routing` | Egress Routing | routes, agents, leases, heartbeat | RESERVED — Run 18 |
| 08 | `08-notification-delivery` | Notification Delivery | notification events, outbox, delivery attempts, delivery logs | RESERVED — Run 19 |
| 09 | `09-telegram-adapter` | Telegram Adapter | Telegram provider ingress/egress mapping and UI adaptation; no business-table ownership | RESERVED — Run 20 |
| 10 | `10-max-adapter` | MAX Adapter | MAX provider ingress/egress mapping and UI adaptation; no business-table ownership | RESERVED — Run 21 |
| 11 | `11-admin-and-support` | Admin & Support | admin/support views and work items through public services; no bypass of module ownership | RESERVED — Run 22 |
| 12 | `12-web-cabinet` | Web Cabinet | web UI/session presentation state; no second user database | RESERVED — Run 23 |
| 13 | `13-filter-catalog-and-builder` | Filter Catalog & Builder | verified filter definitions/options and builder UI over the same Beacon configuration model | RESERVED — Run 24 |

## Неподвижные межмодульные правила

- Внешний интерфейс не пишет напрямую в таблицу чужого модуля.
- Telegram/MAX/Web/Admin используют публичные команды/сервисы соответствующих модулей.
- Parser не отправляет Telegram/MAX напрямую; он создаёт нормализованный результат/событие для Scan/Notification contracts.
- История объявлений и уведомления изолированы по `beacon_id`.
- Framework, ORM and provider types do not become public intermodule contracts.
- Platform & Contracts owns common conventions, not foreign business state.
- Identity & Access owns account identity, contact, role, session and auth/link challenge state; adapters and Web Cabinet do not create separate customer databases.
- Entitlements & Billing owns tariff, subscription, grant and payment authority; Beacon Management consumes effective entitlement decisions and does not duplicate billing state.
- Beacon Management is the only owner of Beacon configuration/lifecycle state; Parser returns normalized outcomes, Scan consumes immutable revision references, and adapters/UI use public commands.
- Source URL is preserved separately from extracted snapshot and overrides; effective configuration change creates a new immutable revision.
- Payment provider response is external evidence, not entitlement authority, until verified and converted by an approved server-side transition.
- Модульные границы и владение данными меняются только через decision log and approved contract/architecture change packet.
