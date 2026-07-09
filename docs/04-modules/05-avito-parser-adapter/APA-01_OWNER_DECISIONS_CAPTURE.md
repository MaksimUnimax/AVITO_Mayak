# Маяк Авито — APA-01 Owner Decisions Capture

**Модуль:** `05-avito-parser-adapter`  
**Roadmap step:** APA-01 — Governance capture of owner Parser decisions  
**Статус:** APPROVED governance capture, semantic planning only  
**Дата:** 2026-07-09  
**Primary governance record:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0017`

## 1. Назначение

Этот документ фиксирует модульный handoff для owner decisions, captured by `ADR-0017`, so later Avito Parser Adapter tasks can use the decisions without re-reading chat history.

This document does not authorize product-code, live Avito calls, endpoint probing, provider runtime, database schema, migrations, UI, deployment or infrastructure.

## 2. Captured owner decisions

1. Parser Adapter is a Mayak module, not a copy of the reference parser.
2. The reference parser is technical evidence / observation only.
3. Live Avito calls and endpoint probing are forbidden at the current stage.
4. Current allowed scope is semantic contracts, synthetic fixtures, fake response classifications, safe parser outcome models, reference-profile placeholders, negative safety outcomes and no-live-traffic evidence.
5. Internal endpoint `/web/1/js/items` is observation only and not a stable contract.
6. Listing-card field families desired by the owner include title, normalized price, source/listing URL, preview/image reference, geography, category, publication/order signal if proven, full description if proven, seller if proven, seller rating if proven and phone/contact availability if proven.
7. Free users must not be intentionally deprived of convenient listing-card fields. Monetization is primarily active Beacon count, monitoring interval and geography.
8. Phone/seller/rating/description are evidence-gated optional candidates, not mandatory global fields.
9. Phone value extraction requires a separate approved phone-enrichment gate.
10. Parser Adapter must distinguish search-result fields, listing-detail fields and contact/phone fields.
11. Category-specific characteristics are Filter Catalog / evidence-bound concerns, not Parser guesses.
12. Parser may later return observed ordering, sort context and timestamp candidates if proven.
13. Parser does not decide baseline, newness, price-change events, anchor windows, lost-anchor recovery or notifications.
14. Future Scan handoff includes newest-first top-window logic, baseline on first successful scan, future admin-configurable anchor window size and safe lost-anchor recovery semantics.
15. Raw provider payloads are not retained by default.
16. Clean empty result requires future compatibility profile proof.
17. Live pagination remains blocked; only semantic page/batch/partial placeholders are allowed before an evidence/access gate.
18. Parser does not own cookies, sessions, proxy/VPN/CAPTCHA tooling or Egress route decisions.

## 3. Current allowed next use

After this capture is accepted, APA-02 may define semantic Parser request/outcome contracts and synthetic fixture identifiers only after a separate exact task.

## 4. Still blocked

- live Avito calls;
- endpoint probing;
- source URL live validation;
- HTML/JSON runtime parser implementation;
- HTTPX live client;
- cookies/sessions/proxy/CAPTCHA tooling;
- browser automation;
- real Avito fixtures;
- raw provider payload retention;
- listing detail enrichment runtime;
- phone extraction runtime;
- database schema;
- migrations;
- repositories;
- persistence;
- Scan runtime;
- Egress runtime;
- Notification runtime;
- Filter Catalog implementation;
- Admin/Web/Telegram/MAX UI;
- Docker;
- CI/CD;
- deploy;
- runtime services;
- ports/listeners;
- credentials;
- secrets;
- tokens.

## 5. Handoff to later roadmap steps

- APA-02: may use this capture for semantic request/outcome contracts.
- APA-08: may model desired listing-card field families only as evidence-gated optional candidates.
- APA-09: may model ordering/newest-sort evidence and Scan handoff, without implementing Scan behavior.
- APA-10: remains blocked for live pagination.
- APA-11: raw retention and personal-data storage remain blocked by OD-013 / evidence policy gates.
- APA-12: must include this capture in final module evidence/handoff if applicable.
