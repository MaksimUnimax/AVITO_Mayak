# Маяк Авито — реестр модулей

**Версия:** 1.11
**Статус:** APPROVED registry derived from Architecture Baseline v1.1
**Правило:** это реестр границ. Playbook status does not authorize implementation; each published run still requires exact server synchronization and independent acceptance.

| № | ID каталога | Модуль | Владелец данных / граница | Playbook |
|---:|---|---|---|---|
| 01 | `01-platform-and-contracts` | Platform & Contracts | application skeleton, configuration conventions, common errors, idempotency conventions, migration/tooling conventions after approval; no foreign business state | v1.0 accepted |
| 02 | `02-identity-and-access` | Identity & Access | accounts, identities, authentication records, roles, sessions, auth/link challenges | v1.0 accepted |
| 03 | `03-entitlements-and-billing` | Entitlements & Billing | tariff definitions, subscriptions, entitlement grants, manual access, future payment records and later approved usage counters | v1.0 accepted |
| 04 | `04-beacon-management` | Beacon Management | Beacons, source URLs, extracted snapshots, user overrides, effective configuration, immutable revisions and lifecycle authority | v1.0 accepted |
| 05 | `05-avito-parser-adapter` | Avito Parser Adapter | evidence-bound source/page extraction, response classification, normalized search configuration and listing candidates; no Beacon/Scan/route/notification mutation | v1.0 accepted |
| 06 | `06-scan-orchestration-and-listing-state` | Scan Orchestration & Listing State | durable scan intent/run/claim state, immutable observations, per-Beacon listing state, baseline/difference decisions and committed scan-domain events | v1.0 accepted |
| 07 | `07-egress-routing` | Egress Routing | logical agent/route registration, capability/readiness/health/quarantine, bounded route leases, route-selection decisions, transport assignment/outcome and reconciliation evidence | v1.0 accepted |
| 08 | `08-notification-delivery` | Notification Delivery | notification event intake, durable outbox, deduplication, delivery attempts, delivery logs and delivery reconciliation state | v1.0 accepted |
| 09 | `09-telegram-adapter` | Telegram Adapter | Telegram provider identity/update mapping, ingress/egress normalization, Mini App validation boundary and UI adaptation; no business-table ownership | v1.0 accepted |
| 10 | `10-max-adapter` | MAX Adapter | MAX eligibility evidence, provider identity/update mapping, Webhook/Long Polling boundaries, Mini App/contact validation and UI adaptation; no business-table ownership | v1.0 accepted |
| 11 | `11-admin-and-support` | Admin & Support | support cases, safe support reads, protected support command envelopes, audit references and escalation coordination through public services | v1.0 published; Run 22 sync pending |
| 12 | `12-web-cabinet` | Web Cabinet | web UI/session presentation state; no second user database | RESERVED — Run 23 |
| 13 | `13-filter-catalog-and-builder` | Filter Catalog & Builder | verified filter definitions/options and builder UI over the same Beacon configuration model | RESERVED — Run 24 |

## Неподвижные межмодульные правила

- Внешний интерфейс не пишет напрямую в таблицу чужого модуля.
- Telegram/MAX/Web/Admin используют публичные команды/сервисы соответствующих модулей.
- Parser не отправляет Telegram/MAX напрямую and does not create notifications; it returns explicit normalized outcomes for Beacon/Scan consumers.
- История объявлений, scan state и notifications изолированы по `beacon_id`.
- Framework, ORM and provider types do not become public intermodule contracts.
- Platform & Contracts owns common conventions, not foreign business state.
- Identity & Access owns account identity, contact, role, session and auth/link challenge state; adapters, Admin/Support and Web Cabinet do not create separate customer/operator databases.
- Entitlements & Billing owns tariff, subscription, grant and payment authority; Beacon/Scan/Notification/Admin consume effective entitlement decisions and do not duplicate billing state.
- Beacon Management is the only owner of Beacon configuration/lifecycle state. Every ScanRun is pinned to one immutable configuration revision and never silently follows “latest”.
- Avito Parser Adapter owns extraction/normalization and explicit parser outcomes only. It does not own route selection/execution, run, baseline, difference, listing history or notification decisions.
- Scan Orchestration & Listing State owns durable scan/run state, immutable observations, per-Beacon listing state, baseline/difference decisions and scan-domain event facts. It does not own routes, Parser mappings, Beacon configuration or delivery attempts.
- Egress Routing owns logical agent/route registration, capability/readiness/health/quarantine, bounded route leases, server-side selection decisions, dispatch/send outcomes and transport reconciliation. It does not own Beacon, account, entitlement, scan/listing, Parser mapping or notification state.
- Notification Delivery consumes committed scan-domain events and owns notification intake, outbox, deduplication, delivery attempts, delivery logs and delivery reconciliation. It does not create Scan facts, choose Egress routes or implement Telegram/MAX provider behavior.
- Telegram Adapter owns Telegram provider identity/update mapping, authenticity/replay handling, command/callback/deep-link normalization, Mini App validation result references and provider outcome mapping. It does not own account identity, generic notification outbox, Beacon state, Scan state, Egress route state or MAX provider behavior.
- MAX Adapter owns MAX provider identity/update mapping, eligibility/moderation evidence references, Webhook/Long Polling boundaries, contact/Mini App validation references and provider outcome mapping. It does not own account identity, generic notification outbox, Beacon state, Scan state, Egress route state, Telegram provider state or legal eligibility decisions.
- Admin & Support owns support cases, support read projections, protected support action requests, audit references and escalation coordination. It does not own or bypass authoritative state of Identity, Entitlements, Beacon, Scan, Egress, Notification, Telegram, MAX, Web Cabinet or Filter Catalog.
- `route_id`, `agent_id` and `lease_id` are semantic identifiers, not host/IP/port/process aliases.
- Windows Egress Agent is a replaceable execution dependency and does not store primary project database or authoritative business state.
- `ScanWorkClaim` and `RouteLease` are distinct. A route lease does not transfer Scan work ownership or business-state mutation authority.
- Agent heartbeat or connection does not prove readiness, route usability, request success, Parser success or business success.
- Route selection/fallback is server-side. Agent and Parser do not select fallback independently.
- Egress transport success is not Parser success. Parser success is not a committed scan comparison. A committed scan comparison is not notification delivery.
- Telegram/MAX provider acceptance is not human read, click or final business success until Notification accepts the provider outcome under its own state.
- Admin/support case closure is not domain success unless the owning module’s accepted outcome proves it.
- `SENT_SUCCESS_RESPONSE` remains a transport fact until Parser validates content.
- Unknown dispatch/send/provider/support action state is reconcile-first and is never retried blindly.
- Route/agent unavailable, expired/revoked lease, restriction/CAPTCHA, timeout, malformed response, transport failure or ambiguity cannot become clean Parser success or no listings.
- Public unauthenticated inbound exposure is prohibited by default; exact transport/topology/port/tunnel/VPN/proxy technology remains unselected.
- Foreign host containers, networks, ports, databases, queues, volumes, Nginx, services, certificates and secrets do not become project resources by visibility.
- Notification failure or ambiguity never rolls back committed Scan observations/listing state/domain events.
- Internal Avito structures and endpoints observed in a primary reference remain unsupported as stable provider contracts.
- Payment provider response is external evidence, not entitlement authority, until verified and converted by an approved server-side transition.
- Модульные границы и владение данными меняются только через decision log and approved contract/architecture change packet.
