# Маяк Авито — реестр модулей

**Версия:** 1.6
**Статус:** APPROVED registry derived from Architecture Baseline v1.1
**Правило:** это реестр границ. Playbook status does not authorize implementation; each published run still requires exact server synchronization and independent acceptance.

| № | ID каталога | Модуль | Владелец данных / граница | Playbook |
|---:|---|---|---|---|
| 01 | `01-platform-and-contracts` | Platform & Contracts | application skeleton, configuration conventions, common errors, idempotency conventions, migration/tooling conventions after approval; no foreign business state | v1.0 accepted |
| 02 | `02-identity-and-access` | Identity & Access | accounts, identities, authentication records, roles, sessions, auth/link challenges | v1.0 accepted |
| 03 | `03-entitlements-and-billing` | Entitlements & Billing | tariff definitions, subscriptions, entitlement grants, manual access, future payment records and later approved usage counters | v1.0 accepted |
| 04 | `04-beacon-management` | Beacon Management | Beacons, source URLs, extracted snapshots, user overrides, effective configuration, immutable revisions and lifecycle authority | v1.0 accepted |
| 05 | `05-avito-parser-adapter` | Avito Parser Adapter | evidence-bound source/page extraction, response classification, normalized search configuration and listing candidates; no Beacon/Scan/route/notification mutation | v1.0 accepted |
| 06 | `06-scan-orchestration-and-listing-state` | Scan Orchestration & Listing State | durable scan intent/run/claim state, immutable observations, per-Beacon listing state, baseline/difference decisions and committed scan-domain events | v1.0 published; Run 17 sync pending |
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
- Parser не отправляет Telegram/MAX напрямую and does not create notifications; it returns explicit normalized outcomes for Beacon/Scan consumers.
- История объявлений, scan state и notifications изолированы по `beacon_id`.
- Framework, ORM and provider types do not become public intermodule contracts.
- Platform & Contracts owns common conventions, not foreign business state.
- Identity & Access owns account identity, contact, role, session and auth/link challenge state; adapters and Web Cabinet do not create separate customer databases.
- Entitlements & Billing owns tariff, subscription, grant and payment authority; Beacon/Scan consume effective entitlement decisions and do not duplicate billing state.
- Beacon Management is the only owner of Beacon configuration/lifecycle state. Every ScanRun is pinned to one immutable configuration revision and never silently follows “latest”.
- Avito Parser Adapter owns extraction/normalization and explicit parser outcomes only. It does not own run, baseline, difference, listing history or notification decisions.
- Scan Orchestration & Listing State owns durable scan/run state, immutable observations, per-Beacon listing state, baseline/difference decisions and scan-domain event facts. It does not own routes, parser mappings, Beacon configuration or delivery attempts.
- Egress transport success is not parser success. Parser success is not a committed scan comparison. A committed scan comparison is not notification delivery.
- Only a complete comparison-eligible parser outcome may establish/advance baseline and differences. Partial, restricted, malformed, route-failed, stale or ambiguous outcomes cannot erase state or become no listings.
- First complete baseline contents produce no listing-change event. Later unseen listing identity or unseen identity+price pair may produce committed scan-domain events under the accepted v1.0 semantics.
- Same provider listing identity in different Beacons remains separate authoritative state.
- Missing from one result does not prove listing removal.
- Notification Delivery consumes committed scan-domain events and owns outbox/delivery state; Scan does not call Telegram/MAX directly.
- Internal Avito structures and endpoints observed in a primary reference remain unsupported as stable provider contracts.
- Payment provider response is external evidence, not entitlement authority, until verified and converted by an approved server-side transition.
- Модульные границы и владение данными меняются только через decision log and approved contract/architecture change packet.
