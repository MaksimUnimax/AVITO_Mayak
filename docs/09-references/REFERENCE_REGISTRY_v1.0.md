# Маяк Авито — Reference Registry

**Версия:** 1.0
**Статус:** APPROVED documentation registry
**Дата:** 2026-07-07
**Основание:** Source of Truth Policy, Documentation Governance, Contract Change Policy v1.0, Data Model v1.0, Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.0, Reference Regression Policy v1.0, OPEN_DECISIONS.md.
**Не является:** provider API specification, legal opinion, permission to access Avito, parser design, runtime registry, credential store, archived copy of third-party content or разрешением выполнять provider requests.

---

## 1. Назначение

Registry хранит стабильные идентификаторы внешнего evidence, используемого документацией проекта.

Он нужен, чтобы каждое provider-dependent утверждение имело:

- authority class;
- exact source identity;
- retrieval date;
- covered scope;
- evidence lifecycle status;
- limitations;
- affected project documents;
- fixture and acceptance links;
- explicit unsupported or blocked claims.

URL без scope, status and limitations не является достаточным evidence.

## 2. Authority classes

| Authority class | Meaning | Допустимое использование |
|---|---|---|
| `OFFICIAL_PROVIDER_DOCUMENTATION` | Документ, опубликованный самим provider | Provider facts только в exact covered scope |
| `OFFICIAL_PROVIDER_REPOSITORY` | First-party repository, контролируемый provider | Exact repository behavior/specification at named revision |
| `OFFICIAL_PROVIDER_ANNOUNCEMENT` | First-party changelog, announcement or status statement | Exact announced change and effective scope |
| `FIRST_PARTY_OBSERVATION` | Safe evidence from separately approved provider task | Только наблюдавшееся поведение, без расширения scope |
| `PRIMARY_IMPLEMENTATION_REFERENCE` | Named technical reference required by project governance | Exact behavior of reference at named revision; не provider contract |
| `EVIDENCE_GAP` | Required source was not available or sufficient | Blocks dependent assertion; does not prove absence |

Authority class and lifecycle status are independent. A current primary implementation reference is not official provider documentation.

## 3. Lifecycle statuses

The canonical statuses are:

- `CURRENT`;
- `STALE`;
- `SUPERSEDED`;
- `WITHDRAWN`;
- `UNAVAILABLE`;
- `DISPUTED`.

A record is `CURRENT` only in its declared scope. Historical records are never silently rewritten; replacement evidence links to superseded records.

## 4. Mandatory record fields

Each record contains:

- `reference_id`;
- `provider`;
- `authority_class`;
- `source_type`;
- `url`;
- `retrieved_at`;
- `effective_at`, if stated by source;
- `scope`;
- `status`;
- `content_identity`;
- `claims_supported`;
- `claims_not_supported`;
- `limitations`;
- `affected_documents`;
- `fixture_links`;
- `acceptance_rows`;
- `reviewed_by`;
- `revalidation_triggers`.

## 5. Avito records

### AVITO-OFFICIAL-ADS-HELP-001

- **Provider:** Avito.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** first-party Avito Ads help page.
- **URL:** `https://ads-help.avito.com/external/api`.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Effective at:** not stated in the captured page.
- **Scope:** public Avito Ads API for advertising accounts: account/access administration, finance, advertisers/contracts, campaigns/groups/creatives, statistics, API point balance, method-specific request-frequency restrictions, API-key access and sandbox.
- **Status:** `CURRENT`.
- **Content identity:** page title `Публичный API Авито Рекламы`, exact URL and retrieval timestamp; no full-page copy stored.
- **Claims supported:**
  - Avito publishes a public API for the Avito Ads advertising product;
  - the page links first-party technical documentation and official SDKs;
  - Ads API access, credentials, quotas and sandbox are advertising-account concepts.
- **Claims not supported:**
  - consumer classified-search monitoring;
  - public search URL/filter semantics;
  - listing-page HTML or embedded state;
  - `/web/1/js/items`;
  - permission to scrape or automate consumer search;
  - product monitoring frequency for Маяк;
  - supported consumer categories, markets or listing fields.
- **Limitations:** Ads product only; account eligibility and exact method limits are outside the captured consumer-search scope.
- **Affected documents:** `AVITO_REFERENCE_POLICY_v1.0.md`, `AVITO_REFERENCE_EVIDENCE_v1.0.md`, future Run 15/17/23 playbooks.
- **Fixture links:** `FX-REF-CURRENT-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-REF-001`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** source content/URL change, official deprecation, new Avito integration task, final documentation audit.

### AVITO-OFFICIAL-ADS-SDK-PY-001

- **Provider:** Avito.
- **Authority class:** `OFFICIAL_PROVIDER_REPOSITORY`.
- **Source type:** public repository in the first-party `avito-tech` GitHub organization.
- **URL:** `https://github.com/avito-tech/avito-ads-sdk-python3`.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Effective at:** repository commit date `2026-06-08`.
- **Scope:** Avito Ads Python SDK version 1.0.0 at commit `41a3c72cf4c18ed76e43925f6a7e5e6ae9238267`; advertising-account API client behavior and links to official Ads documentation.
- **Status:** `CURRENT`.
- **Content identity:** Git commit `41a3c72cf4c18ed76e43925f6a7e5e6ae9238267`.
- **Claims supported:**
  - Avito publishes first-party SDKs for the Avito Ads API;
  - this SDK is limited to advertising API resources and authentication described by its exact revision.
- **Claims not supported:**
  - consumer search/listing parser behavior;
  - internal website endpoint stability;
  - consumer search access permission;
  - supported Маяк filters, markets, categories or cadence.
- **Limitations:** repository is official but belongs to the Ads API product, not consumer classified search.
- **Affected documents:** `AVITO_REFERENCE_POLICY_v1.0.md`, `AVITO_REFERENCE_EVIDENCE_v1.0.md`.
- **Fixture links:** `FX-REF-CURRENT-001`, `FX-REF-UNSUPPORTED-001`.
- **Acceptance rows:** `AM-REF-001`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** default-branch or release change, repository archive, official scope change, implementation task relying on the SDK.

### AVITO-OFFICIAL-ADS-TECHDOC-001

- **Provider:** Avito.
- **Authority class:** `OFFICIAL_PROVIDER_DOCUMENTATION`.
- **Source type:** developer portal linked by official Ads help and SDK.
- **URL:** `https://developers.avito.ru/api-catalog/ads/documentation`.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Effective at:** unavailable.
- **Scope:** intended Avito Ads technical documentation identity only.
- **Status:** `UNAVAILABLE`.
- **Content identity:** exact URL linked by two current first-party sources; direct content was not retrievable in this evidence run.
- **Claims supported:** the linked technical-documentation location is identified by first-party Ads sources.
- **Claims not supported:** any endpoint, payload, authentication, limit, compatibility or error detail not captured from the page.
- **Limitations:** direct page content unavailable; it cannot be used as current detailed evidence.
- **Affected documents:** `AVITO_REFERENCE_EVIDENCE_v1.0.md`, future Ads-related work only.
- **Fixture links:** `FX-REF-MISSING-001`, `FX-REF-STALE-001`.
- **Acceptance rows:** `AM-REF-002`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** any task requiring an exact Ads endpoint or method contract; source becomes directly retrievable.

### AVITO-PRIMARY-PARSER-001

- **Provider:** external technical reference concerning Avito.
- **Authority class:** `PRIMARY_IMPLEMENTATION_REFERENCE`.
- **Source type:** public third-party implementation required by `SOURCE_OF_TRUTH_POLICY.md`.
- **URL:** `https://github.com/Duff89/parser_avito`.
- **Retrieved at:** `2026-07-07T09:00:29+02:00`.
- **Effective at:** commit date `2026-06-30`.
- **Scope:** repository default branch `master`, version 3.2.16, commit `48441c352e36919abef13c436f41a3a62636da17`; exact implementation behavior in `README.md`, `parser_cls.py`, `utils/build_api_params.py`, `utils/normalize_parametr.py`, `db_service.py` and `parser/http/client.py`.
- **Status:** `CURRENT`.
- **Content identity:** Git commit `48441c352e36919abef13c436f41a3a62636da17`.
- **Claims supported:**
  - the reference accepts configured Avito URLs and fetches first-page HTML;
  - it extracts `loaderData.data`, including `searchCore`, `context` and `catalog`;
  - it requests later pages from `https://www.avito.ru/web/1/js/items` using derived parameters;
  - it normalizes listing models, filters results and tracks an `id + price` pair in local SQLite;
  - it contains retry, cookie, proxy and 401/403/429 handling behavior at the named revision;
  - repeated values in its current `normalize_params` dictionary path overwrite earlier values;
  - its phone-parsing branch is effectively disabled at the named revision.
- **Claims not supported:**
  - official Avito API or website contract;
  - stability, permission or availability of internal page structures/endpoints;
  - legal compliance;
  - production safety, SaaS suitability or multi-tenant isolation;
  - approved Маяк product behavior.
- **Limitations:** third-party `as is` implementation; internal structures may change; direct notifications, global SQLite history, local configuration and retry behavior are not automatically suitable for Маяк.
- **Affected documents:** target model v0.1 and architecture map v0.1 as DRAFT context; Data Model v1.0; future Run 15 Avito Parser Adapter, Run 17 Egress Routing and Run 23 Filter Catalog & Builder playbooks.
- **Fixture links:** `FX-REF-CURRENT-001`, `FX-REF-CHANGED-BREAKING-001`, `FX-REF-UNSUPPORTED-001`, `FX-EXT-MALFORMED-001`, `FX-AVITO-CAPTCHA-001`.
- **Acceptance rows:** `AM-EXT-003`, `AM-AVITO-001`, `AM-REF-001`, `AM-REF-003`, `AM-REF-004`.
- **Reviewed by:** ChatGPT.
- **Revalidation triggers:** reference commit/default branch changes, Avito page/endpoint mismatch, Run 15/17/23 task preparation, relevant fixture failure.

## 6. Evidence gaps recorded by Run 9

The following required claims have no current sufficient official evidence in this registry:

- official consumer-search API or contract for Маяк monitoring;
- stability of consumer search URL/filter semantics;
- stability of `loaderData`, `searchCore`, `context`, `catalog` or `/web/1/js/items`;
- permitted automation/scraping scope and legal basis;
- supported editable filter catalog;
- country-wide/market support;
- sustainable or allowed monitoring frequency;
- CAPTCHA, cookie, proxy, route or retry policy;
- stable consumer listing field and identifier contract.

These gaps are not proof that a capability does or does not exist. They are `EVIDENCE_GAP` conditions that block dependent acceptance until current official evidence or a separately approved safe proof task is accepted.

## 7. Registry change control

A registry change requires:

1. exact old/new source identity;
2. lifecycle status transition;
3. scope and limitation comparison;
4. affected documents, fixtures and acceptance rows;
5. security/privacy/copyright review;
6. compatibility classification;
7. open decisions touched but not closed;
8. independent GitHub acceptance.

Provider change does not automatically authorize product or implementation change.

## 8. Explicit prohibitions

This registry does not authorize:

- provider requests;
- scraping or parser implementation;
- credentials, cookies, sessions or proxy use;
- executable fixtures or tests;
- endpoint probing;
- route/agent creation;
- runtime configuration;
- product-code;
- migrations, database, CI/CD, Docker, deploy or production infrastructure.

## 9. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial cross-provider registry populated with Run 9 Avito official/primary records and explicit evidence gaps. |
