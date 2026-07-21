# Маяк Авито — Web Cabinet Owner Decisions Capture v1.0

**Status:** OWNER-APPROVED decisions; repository capture pending independent acceptance
**Date:** 2026-07-21
**Module:** 12-web-cabinet
**Roadmap step:** WC-01
**Technical ID:** WC-01-WEB-CABINET-OWNER-DECISIONS-CAPTURE-20260721-001
**Governance reference:** ADR-0028
**Source-of-truth playbook:** `docs/04-modules/12-web-cabinet/MODULE_PLAYBOOK.md`
**Scope:** documentation/governance-only.

## Purpose and boundary

This document captures owner direction for subsequent exact semantic tasks. It is not product code, an executable contract, a wire schema, frontend, route, API, auth/session, analytics implementation, database, provider runtime, infrastructure, or permission to implement any of those things. It does not replace GitHub `main`, close numbered open decisions, or change ownership of another module.

## Owner decisions

### 1. Beacon History / Archive входит в Web Cabinet v1

Web Cabinet показывает active Beacons и History/Archive. History может включать frozen, user-deleted и archived Beacons в рамках accepted Beacon Management policy. Restore выполняется без повторной вставки source URL, только если current entitlement, policy и validation разрешают. Permanent delete делает восстановление невозможным. History/archive Beacons не входят в active Beacon limit. Archive, restore, ordinary delete и permanent delete принадлежат Beacon Management. Web Cabinet только читает safe projections и отправляет public commands. Запрещена отдельная web-owned history database и direct Beacon lifecycle write.

### 2. Редактирование Beacon использует current-config policy модуля 04

Web form/draft state не является authoritative. Save выполняется через Beacon Management public command. Save patch-based: owning module читает current authoritative state и применяет только переданные поля. Client-side validation — только usability. Server-side Beacon validation — authority. Stale full-form overwrite запрещён. После accepted save Web Cabinet показывает authoritative reloaded current state. Нельзя создавать unlimited user-facing old-revision clutter.

### 3. Web authorization/login не изобретается внутри модуля 12

Internal account_id — authoritative account identity. Telegram, MAX и Web Cabinet — interfaces одного internal account. Web Cabinet не создаёт вторую customer database. Telegram linking идёт через Telegram Adapter и Identity & Access. MAX linking идёт через MAX Adapter и Identity & Access. Web login/session/recovery принадлежат Identity & Access и future exact gates. Phone/password/recovery/account merge не определяются модулем 12. Provider username, display name, avatar, phone или chat state не являются account authority.

### 4. Tariff/access/limits отображаются только через Entitlements & Billing

Web Cabinet показывает current tariff, access и approved limits через safe projections. Available tariff definitions показываются только когда их предоставляет Entitlements & Billing. Upgrade/payment placeholder допустим только через approved billing projection. Web Cabinet не изобретает tariff names, prices, periods, currencies или limits. Payment provider, recurring/manual payment, refunds и provider runtime остаются gated. Web Cabinet не grants entitlement и не mutates billing state.

### 5. История сообщений/результатов берётся из Notification Delivery

Web Cabinet использует accepted minimal delivery/message history. Результат связывается с Beacon и committed scan/source event. Показывается полный count найденных listings. Сохраняются все approved safe listing-card references одного grouped result. Показываются safe channel attempt/status summary и safe reason/error classification. Notification Delivery не должен обрезать safe references до preview limit. Web Cabinet не создаёт новый full message/chat archive или unbounded listing archive. Raw Avito/provider payloads, cookies, tokens и secrets запрещены.

### 6. User-facing statuses происходят из Scan и Notification semantics

Разрешённые смысловые семейства:

- новых объявлений нет;
- Avito/route/parser сейчас недоступен или мешает проверке, и это не clean no-new;
- проверка восстановлена и сформирован один recovery result;
- lost anchors: состояние восстановлено, показываются latest fresh listings, но не confirmed-new;
- access expired/restricted и требуется approved Free/user-choice flow;
- channel not linked, not verified или disabled;
- notification failed, unknown или reconciliation required;
- read model stale / данные могут быть устаревшими.

Запрещены stack traces, raw provider payload, secret values, false no-new при CAPTCHA/external failure, false confirmed-new при lost anchors и ambiguous owning-module outcome как completed success.

### 7. Все interfaces связываются через один account

Web Cabinet показывает linked Telegram/MAX status через verified adapter projections. Start/connect/link intent из Web допускается только через accepted adapter + Identity boundary. Telegram/MAX могут вести пользователя к Web/Mini App только после соответствующих gates. Enable/disable channel выполняется через approved generic preference/owning-module boundary. All enabled and verified channels получают planned Notification work по current Notification policy, пока пользователь не отключил channel. Telegram остаётся first practical channel. MAX остаётся future/secondary channel до своих gates. Web Cabinet не является Telegram/MAX push-provider runtime.

### 8. Admin analytics входит в future Module 12 v1 semantic scope

**Compatibility clarification:** текущий Web Cabinet playbook блокирует analytics через OD-014 и OD-013. Owner direction теперь требует, чтобы future admin-only analytics semantic boundary входил в roadmap модуля 12, но это не разрешает implementation.

Первый semantic scope:

- admin-only analytics read model;
- visitor count;
- registered/linked user count;
- active/using user count;
- Free tariff count;
- counts grouped by each approved paid tariff;
- sortable tabular projection;
- future filters by approved period, tariff and account/use status;
- aggregated counts by default;
- minimal personal data.

Остаются запрещены до отдельных gates: tracker implementation, marketing/ad pixels, external analytics provider, consent implementation, event collection runtime, exact screen map, exact period definitions, retention, user-level analytics export и unnecessary personal data. OD-014 и OD-013 не закрываются.

### 9. Customer-facing support handoff отделён от internal support state

Web Cabinet может показывать support entry, customer-visible status и public answer через Admin & Support safe views. Internal notes, private audit, operator-only fields, raw logs, secrets и hidden evidence клиенту не показываются. Web Cabinet не mutates support cases и не создаёт operator actions.

### 10. Web Cabinet остаётся presentation and command boundary

Только safe reads, composition, explanations, non-authoritative drafts и command envelopes. Никаких direct writes в authoritative state других модулей. Green button, browser route, local state или client validation не доказывают business success. Owning-module explicit outcome остаётся authority. Freshness, provenance, redaction, ownership, authorization, idempotency, correlation/causation и ambiguity должны сохраняться. Filter definitions и visual builder behavior не изобретаются модулем 12.

## Preserved open decisions

Открытыми явно сохраняются: `OD-006`; `OD-007`; `OD-008`; `OD-009`; `OD-013`; `OD-014`; exact web screen map; frontend framework/component library; route/API surface; session storage; login/recovery flow; analytics event catalog; consent; analytics retention; exact visitor/active-user definitions; exact period filters; customer support visibility details; notification preference storage; channel-link UX; exact tariff values, кроме уже отдельно approved Entitlements facts; payment/runtime/provider decisions.

`docs/00-governance/OPEN_DECISIONS.md` этим task не редактируется.

## Blocked gates

Следующие действия явно запрещены этим capture: product code; semantic Python contracts; tests и fixtures; frontend, pages, routes, API handlers и UI components; auth/session/recovery/account merge; analytics/tracking implementation; payment UI/provider calls; database, ORM, migrations и persistence; queue, worker, scheduler, service и runtime; Telegram/MAX/Avito/payment calls; Docker, CI/CD и deploy; ports, listeners, certificates, credentials и secrets; raw provider payload retention; direct mutation of foreign module state.
