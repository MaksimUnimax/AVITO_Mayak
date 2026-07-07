# Маяк Авито — Avito Reference Evidence

**Версия:** 1.0
**Статус:** APPROVED evidence snapshot
**Дата:** 2026-07-07
**Retrieved at:** `2026-07-07T09:00:29+02:00`
**Основание:** Reference Registry v1.0, Avito Reference Policy v1.0, Source of Truth Policy, Reference Regression Policy v1.0, OPEN_DECISIONS.md.
**Не является:** legal opinion, permission to use Avito, official consumer-search API specification, parser design, runtime test, provider-call report or production acceptance.

---

## 1. Method and safety boundary

Run 9 reviewed public pages and public repository revisions only.

Reviewed:

- official Avito Ads help;
- official `avito-tech` Ads SDK repository;
- linked Avito developer-documentation location;
- mandatory primary implementation reference `Duff89/parser_avito`.

Not performed:

- requests to Avito search, listing or API operations;
- real search-URL tests;
- endpoint probing;
- parser execution;
- use of authentication material or private provider data.

## 2. AVITO-OFFICIAL-ADS-HELP-001

- **URL:** `https://ads-help.avito.com/external/api`.
- **Authority:** official Avito documentation.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Status:** `CURRENT`.
- **Scope:** Avito Ads advertising-account API only.
- **Content identity:** page title `Публичный API Авито Рекламы`, exact URL and retrieval timestamp.

Supported in this scope:

- the Avito Ads product has a public API;
- the page describes advertising accounts/access, finance, advertisers/contracts, campaigns/groups/creatives and statistics;
- Ads API usage includes a point balance, method-specific frequency restrictions, administrator-created keys and a sandbox;
- official technical documentation and SDKs are linked.

Not supported:

- consumer classified-search monitoring;
- consumer search URL/filter semantics;
- listing-page or embedded-state stability;
- internal consumer website endpoint stability;
- supported Маяк categories, markets, listing fields or cadence;
- legal permission for consumer-search automation.

No Ads-specific quota or access rule is reused as a consumer-search rule.

## 3. AVITO-OFFICIAL-ADS-SDK-PY-001

- **URL:** `https://github.com/avito-tech/avito-ads-sdk-python3`.
- **Authority:** official first-party repository in `avito-tech`.
- **Revision:** `41a3c72cf4c18ed76e43925f6a7e5e6ae9238267`.
- **Revision date:** `2026-06-08`.
- **Status:** `CURRENT`.
- **Scope:** Avito Ads Python SDK 1.0.0.

The repository identifies itself as an Avito Ads API SDK and links the Ads help and developer portal. Its exact revision documents Ads resources and client behavior. It does not document consumer classified search and does not authorize importing Ads endpoints, authentication or retry semantics into a Маяк search adapter.

## 4. AVITO-OFFICIAL-ADS-TECHDOC-001

- **URL:** `https://developers.avito.ru/api-catalog/ads/documentation`.
- **Authority:** official developer location linked by the current Ads help and SDK.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Status:** `UNAVAILABLE`.
- **Scope:** source identity only.

Direct content was not retrievable during Run 9. Therefore no endpoint, field, authentication, limit, compatibility or error detail is derived from this page.

## 5. AVITO-PRIMARY-PARSER-001

- **URL:** `https://github.com/Duff89/parser_avito`.
- **Authority:** `PRIMARY_IMPLEMENTATION_REFERENCE`, not Avito.
- **Default branch:** `master`.
- **Revision:** `48441c352e36919abef13c436f41a3a62636da17`.
- **Revision date:** `2026-06-30`.
- **Reported version:** 3.2.16.
- **Status:** `CURRENT` only as exact implementation evidence.

Reviewed files:

- `README.md`;
- `parser_cls.py`;
- `utils/build_api_params.py`;
- `utils/normalize_parametr.py`;
- `db_service.py`;
- `parser/http/client.py`.

Behavior confirmed at that revision:

1. configured Avito URLs are used as input;
2. first-page HTML is read;
3. embedded `loaderData.data`, `searchCore`, `context` and `catalog` are consumed;
4. later pages are requested through `https://www.avito.ru/web/1/js/items` with derived parameters;
5. result models are normalized and locally filtered;
6. local history uses listing `id + price`;
7. request failures and restriction-like statuses have explicit handling;
8. current repeated-value normalization can replace an earlier value.

This is evidence about one third-party implementation at one commit. It is not evidence of an official Avito contract, endpoint stability, legal permission, production safety or approved Маяк behavior.

Future playbooks must explicitly reject or redesign reference characteristics that conflict with approved boundaries, including global local history, direct parser-to-notification coupling, local single-user configuration, loss of repeated filter values and unapproved collection/retry behavior.

## 6. Evidence comparison

| Assertion | Official evidence | Primary reference | Run 9 conclusion |
|---|---|---|---|
| Public Avito Ads API exists | Confirmed in Ads scope | Not required | Supported only for Ads |
| Official consumer-search API for Маяк exists | Not captured | Cannot prove | Blocked |
| Embedded consumer page structures are stable | Not captured | Used at exact commit | Implementation observation only |
| `/web/1/js/items` is a stable public contract | Not captured | Used at exact commit | Unsupported as contract |
| Search/filter semantics are stable | Not captured | Partially inferred by code | Blocked |
| Specific filters/categories/markets are supported | Not captured | Example behavior only | OD-009/OD-010 remain open |
| Monitoring cadence is allowed/sustainable | Not captured | Local setting only | OD-011 remains open |
| Restriction or malformed response means no listings | No support | Cannot define project semantics | Explicitly prohibited |
| Consumer-search automation is permitted | Not established | Cannot prove | Legal/compliance gate remains blocked |

## 7. Supported conclusions

Run 9 supports only:

- official first-party integration evidence exists for the distinct Avito Ads product;
- Ads evidence cannot be generalized to consumer classified search;
- the primary reference has the recorded implementation behavior at exact commit `48441c352e36919abef13c436f41a3a62636da17`;
- internal structures observed in that reference remain unsupported as stable contracts;
- evidence gaps block provider-dependent implementation;
- restriction, malformed/incomplete result, unavailable route and ambiguity remain explicit failure states, never a clean empty result.

## 8. Unsupported and blocked conclusions

Run 9 does not establish:

- official consumer-search API availability;
- stable listing identifier or field contract;
- stable category, geography or filter semantics;
- country-wide support;
- permitted request cadence;
- legal permission for automation;
- restriction-handling implementation;
- session/route/retry design;
- provider authentication for consumer search;
- production eligibility.

## 9. Open decisions preserved

- `OD-009` remains unresolved.
- `OD-010` remains unresolved.
- `OD-011` remains unresolved.
- `OD-013` continues to block raw provider-evidence retention.

OD-001–OD-014 are not modified.

## 10. Revalidation triggers

Review again when:

- an official source changes or becomes available/unavailable;
- `Duff89/parser_avito` relevant revision changes;
- a fixture contradicts the recorded behavior;
- Run 15, Run 17 or Run 23 is prepared;
- a new field, category, market, filter, route or cadence is proposed;
- legal/compliance scope is reviewed;
- final documentation audit runs.

## 11. Acceptance mapping

Fixtures:

- `FX-REF-CURRENT-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-STALE-001`;
- `FX-REF-CHANGED-BREAKING-001`;
- `FX-REF-UNSUPPORTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-AVITO-CAPTCHA-001`;
- `FX-ROUTE-FAILURE-001`.

Acceptance rows:

- `AM-DOC-001` through `AM-DOC-003`;
- `AM-EXT-001` through `AM-EXT-004`;
- `AM-AVITO-001`;
- `AM-EGRESS-001`;
- `AM-REF-001` through `AM-REF-004`;
- `AM-DATA-007`.

## 12. Final evidence verdict

**Verdict:** `APPROVED_DOCUMENTATION_BOUNDARY_ONLY`.

The snapshot is sufficient to accept reference governance and explicit blocked states. It is insufficient to authorize provider access, parser implementation, supported filters/markets/cadence, egress setup or production use.

## 13. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial dated Avito official/primary evidence snapshot with scope, status, limitations and blocked claims. |
