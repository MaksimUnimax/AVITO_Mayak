# Маяк Авито — Avito Reference Policy

**Версия:** 1.0
**Статус:** APPROVED documentation policy
**Дата:** 2026-07-07
**Основание:** Reference Registry v1.0, Source of Truth Policy, Security and Privacy Model v1.0, Contract Change Policy v1.0, Data Model v1.0, Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.0, Reference Regression Policy v1.0, Windows Egress Agent Runbook v1.0, OPEN_DECISIONS.md.
**Не является:** legal opinion, Avito permission, API contract, parser specification, rate-limit policy, egress design, executable test, runtime configuration or permission to access provider systems.

---

## 1. Назначение

Policy defines how project documentation may make Avito-dependent assertions.

Its goals are:

- prevent memory, examples or third-party code from becoming provider facts;
- distinguish official Avito evidence from implementation reference behavior;
- block unsupported filters, markets, cadence and internal endpoint assumptions;
- preserve explicit external failure and ambiguity;
- connect evidence to fixtures, acceptance and future module playbooks;
- require safe revalidation before provider-dependent implementation.

## 2. Scope

This policy applies to future documentation or tasks concerning:

- Avito source URLs and search configuration;
- category, geography and filter semantics;
- listing identity and fields;
- first-page and pagination extraction;
- access restriction, CAPTCHA and malformed/incomplete results;
- cookies, sessions, proxies, routes and retries;
- provider rate/access limits;
- reference-driven fixtures;
- Avito Parser Adapter, Egress Routing, Beacon Management, Scan Orchestration and Filter Catalog & Builder.

This policy does not define any of those behaviors where evidence is missing.

## 3. Source hierarchy

For Avito-dependent claims use this order:

1. current official Avito documentation covering the exact product and behavior;
2. current official Avito repository, SDK, changelog or announcement in exact scope;
3. first-party behavior captured by a separately approved safe `proof_only` task;
4. `Duff89/parser_avito` as the mandatory primary implementation reference at an exact commit;
5. secondary/community material only to identify a question, never to approve behavior.

A source from Avito Ads does not become evidence for consumer classified search merely because both are Avito products.

## 4. Authority boundary

### 4.1. Official evidence

Official evidence may support only the claim within its exact:

- product;
- account type;
- market;
- method/page/field;
- effective period;
- authentication and permission scope;
- limitations.

Official documentation change is evidence to review, not automatic authorization to change product behavior.

### 4.2. Primary implementation reference

`Duff89/parser_avito` may prove only:

```text
At exact commit X, this reference implementation performs behavior Y.
```

It cannot prove:

- an official contract;
- endpoint or page-structure stability;
- provider permission;
- legal compliance;
- safe request frequency;
- production readiness;
- SaaS or multi-tenant suitability;
- approved Маяк semantics.

Any deliberate project deviation from the reference must be explicit in the future module playbook.

## 5. Evidence record requirements

An Avito-dependent assertion is acceptable only when its `reference_id` resolves in `REFERENCE_REGISTRY_v1.0.md` and the record contains:

- exact URL or repository/commit;
- retrieval timestamp;
- authority class;
- covered scope;
- lifecycle status;
- content identity/fingerprint;
- supported and unsupported claims;
- limitations;
- affected documents;
- fixtures and Acceptance Matrix rows;
- revalidation triggers.

A URL, screenshot, code fragment, status code or memory-only statement is insufficient by itself.

## 6. Currentness and revalidation

Run 9 selects no fixed calendar review interval.

Revalidation is mandatory:

- immediately before Run 15, Run 17 or Run 23 provider-dependent implementation planning;
- before any task using a new Avito field, filter, endpoint, category, market or account scope;
- when an official page, SDK or reference commit changes;
- when a fixture no longer matches evidence;
- when access, CAPTCHA, error, rate or retry behavior changes materially;
- when an official source disappears or becomes contradictory;
- during final documentation audit.

A known relevant change invalidates `CURRENT` for the affected scope immediately.

## 7. Unavailable, stale, superseded and disputed evidence

- `UNAVAILABLE`: do not infer content; dependent behavior remains blocked.
- `STALE`: refresh before dependent acceptance.
- `SUPERSEDED`: preserve old identity and link replacement.
- `WITHDRAWN`: no new reliance.
- `DISPUTED`: expose conflict and block the disputed behavior.

Missing official evidence is not filled from the implementation reference or analogy.

## 8. Consumer-search evidence gate

The current accessible first-party evidence in Run 9 covers Avito Ads, not consumer classified-search monitoring.

Therefore the following remain blocked:

- declaring an official public consumer-search API;
- treating internal website endpoints as public API;
- claiming stable search/filter URL semantics;
- selecting supported editable filters;
- selecting country-wide/market support;
- selecting monitoring frequency or request rate;
- choosing cookies, proxy, CAPTCHA, retry or route behavior;
- claiming permission to scrape or automate;
- treating any internal field as a stable provider contract.

A future legal/compliance decision must use current official terms or other authoritative evidence; this policy is not legal advice.

## 9. Safe evidence capture

Allowed documentation capture:

- exact URL and retrieval timestamp;
- page/repository title;
- narrow paraphrase of relevant facts;
- exact commit SHA or lawful content fingerprint;
- public non-secret metadata;
- explicit scope and limitations.

Prohibited:

- large copied provider pages;
- credentials, tokens, cookies, session material or private keys;
- private customer/provider content;
- unnecessary personal data;
- raw browser profiles;
- endpoint probing or traffic generation without approved task;
- secrets in Git, prompts, logs or reports.

## 10. Failure and ambiguity

Provider/route/parser outcomes must distinguish:

- no request sent;
- explicit usable success;
- explicit rejection;
- unavailable dependency;
- malformed/incomplete response;
- access restriction or CAPTCHA;
- ambiguous outcome;
- unsupported/evidence-stale behavior.

None of these failure states may become a clean empty listing result.

Retry is not authorized by this policy. Retry counts, delays, backoff, rate limits and reconciliation mechanisms require separate approved evidence and module contracts.

## 11. Required future fixture and acceptance coverage

Applicable fixtures include:

- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-CHANGED-COMPATIBLE-001`;
- `FX-REF-CHANGED-BREAKING-001`;
- `FX-REF-UNSUPPORTED-001`;
- `FX-EXT-SUCCESS-001`;
- `FX-EXT-REJECTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-AVITO-CAPTCHA-001`;
- `FX-ROUTE-FAILURE-001`.

Applicable Acceptance Matrix rows include:

- `AM-EXT-001` through `AM-EXT-004`;
- `AM-AVITO-001`;
- `AM-EGRESS-001`;
- `AM-REF-001` through `AM-REF-004`;
- `AM-DATA-007`;
- `AM-SEC-001` through `AM-SEC-003`, where applicable.

Executable fixture files are not created by Run 9.

## 12. Open decisions

This policy leaves unresolved:

- `OD-009` — initial supported editable Avito filters;
- `OD-010` — country-wide/market support;
- `OD-011` — sustainable and allowed monitoring frequency.

It also does not decide:

- stable listing identifier or field set;
- parser extraction strategy;
- route technology or switching;
- cookie/session policy;
- CAPTCHA handling;
- request headers;
- retry/backoff;
- provider credentials;
- data/evidence retention;
- legal basis or terms interpretation.

## 13. Reference change packet

Before changing an Avito-dependent contract or mapping, the packet must include:

1. old/new `reference_id` and source identity;
2. retrieval/effective dates;
3. exact changed scope;
4. lifecycle status transition;
5. compatibility classification;
6. affected contracts, data and modules;
7. error/retry/idempotency impact;
8. security/privacy/legal-review impact;
9. fixtures and matrix rows;
10. unsupported behavior;
11. open decisions touched but not closed;
12. fallback/blocked state;
13. allowed and forbidden implementation actions;
14. independent acceptance authority.

Provider change never silently changes approved project semantics.

## 14. Explicit prohibitions

Run 9 and this policy do not authorize:

- Avito requests or real search URL tests;
- parser or scraper implementation;
- use of internal endpoints;
- cookies, sessions, proxy or VPN setup;
- route/agent creation;
- credential creation or reading;
- executable tests;
- product-code;
- migrations, databases, Dockerfiles, CI/CD;
- services, containers, ports, deploy or production infrastructure.

## 15. Acceptance criteria

Policy is accepted when:

- official and primary-reference authority is separated;
- Ads API scope is not generalized to consumer search;
- unavailable evidence blocks dependent claims;
- failure never becomes empty success;
- evidence capture is minimized and secret-free;
- fixtures and matrix rows are linked;
- OD-009–OD-011 remain open;
- no provider request or implementation artifact is created.

## 16. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Initial Avito evidence authority, lifecycle, capture, failure and implementation-gate policy. |
