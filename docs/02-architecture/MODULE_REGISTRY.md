# Маяк Авито — реестр модулей

**Версия:** 1.0  
**Статус:** APPROVED registry derived from architecture map v0.1  
**Правило:** это реестр границ. Полные автономные playbook-документы ещё не приняты и не должны предполагаться существующими.

| № | ID каталога | Модуль | Владелец данных / граница |
|---:|---|---|---|
| 01 | `01-platform-and-contracts` | Platform & Contracts | application skeleton, configuration conventions, common errors, idempotency conventions, migrations/tools only after approval |
| 02 | `02-identity-and-access` | Identity & Access | accounts, identities, credentials, roles, sessions, auth/link challenges |
| 03 | `03-entitlements-and-billing` | Entitlements & Billing | tariffs, entitlements, subscriptions, future payment records |
| 04 | `04-beacon-management` | Beacon Management | beacons, source URLs, extracted snapshots, overrides, configuration revisions |
| 05 | `05-avito-parser-adapter` | Avito Parser Adapter | extraction/normalization of Avito search data; no direct notification delivery |
| 06 | `06-scan-orchestration-and-listing-state` | Scan Orchestration & Listing State | runs, observations, baseline/diff, listing state |
| 07 | `07-egress-routing` | Egress Routing | routes, agents, leases, heartbeat |
| 08 | `08-notification-delivery` | Notification Delivery | notification events, outbox, delivery attempts, delivery logs |
| 09 | `09-telegram-adapter` | Telegram Adapter | Telegram provider ingress/egress mapping and UI adaptation; no business-table ownership |
| 10 | `10-max-adapter` | MAX Adapter | MAX provider ingress/egress mapping and UI adaptation; no business-table ownership |
| 11 | `11-admin-and-support` | Admin & Support | admin/support views and work items through public services; no bypass of module ownership |
| 12 | `12-web-cabinet` | Web Cabinet | web UI/session presentation state; no second user database |
| 13 | `13-filter-catalog-and-builder` | Filter Catalog & Builder | verified filter definitions/options and builder UI over the same Beacon configuration model |

## Неподвижные межмодульные правила

- Внешний интерфейс не пишет напрямую в таблицу чужого модуля.
- Telegram/MAX/Web/Admin используют публичные команды/сервисы соответствующих модулей.
- Parser не отправляет Telegram/MAX напрямую; он создаёт нормализованный результат/событие для Scan/Notification contracts.
- История объявлений и уведомления изолированы по `beacon_id`.
- Модульные границы и владение данными меняются только через decision log и обновление контракта.
