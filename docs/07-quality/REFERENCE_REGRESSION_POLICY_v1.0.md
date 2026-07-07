# Маяк Авито — Reference Regression Policy

**Версия:** 1.0
**Статус:** APPROVED documentation policy
**Дата:** 2026-07-07
**Основание:** Test Strategy v1.0, Fixture Registry v1.0, Acceptance Matrix v1.0, Contract Change Policy v1.0, Migration and Compatibility Policy v1.0, Security and Privacy Model v1.0, OPEN_DECISIONS.md.
**Не является:** Avito/Telegram/MAX evidence registry, provider API specification, scraper/parser design, automated monitoring job, CI configuration или разрешением обращаться к providers.

---

## 1. Назначение

Policy определяет, как внешнее official/primary evidence связывается с contracts, fixtures and acceptance, как обнаруживается reference regression и когда provider-dependent behavior блокируется.

Run 9 и Run 10 создадут provider-specific reference documents. Этот документ задаёт их обязательный quality lifecycle, но не заполняет provider facts по памяти.

## 2. Reference evidence record

Каждая reference запись обязана содержать:

| Поле | Требование |
|---|---|
| `reference_id` | Стабильный внутренний идентификатор evidence record |
| `provider` | Avito, Telegram, MAX or separately approved source |
| `source_type` | Official documentation, official announcement, first-party response or other justified primary source |
| `url` | Exact public source URL |
| `retrieved_at` | Дата/время получения в approved time representation |
| `effective_at` | Дата действия, если источник её указывает |
| `scope` | Exact page/API/payload/field/behavior covered |
| `status` | CURRENT, STALE, SUPERSEDED, WITHDRAWN, UNAVAILABLE or DISPUTED |
| `limitations` | Markets, account types, rollout, ambiguity, missing details |
| `content_fingerprint` | Safe hash or equivalent identity when captured lawfully |
| `affected_documents` | Contracts, playbooks, fixtures, mappings, operations docs |
| `fixture_links` | Applicable `FX-REF-*` and provider-specific fixtures |
| `reviewed_by` | Acceptance authority, normally ChatGPT for documentation cycle |

A URL alone is not sufficient evidence.

## 3. Source priority

Preferred order:

1. official provider documentation;
2. official changelog/announcement/status statement;
3. first-party behavior observed in a separately approved safe evidence task;
4. other primary source with explicit limitations.

Secondary articles, community posts, memory, old screenshots and undocumented payloads may identify a question but do not approve product behavior.

Conflicting sources produce `DISPUTED` or blocked state until reconciled. Newer publication date does not automatically override a source with a later effective date or narrower authoritative scope.

## 4. Reference lifecycle

### 4.1. CURRENT

Evidence is current only when:

- source remains accessible or preserved lawfully;
- covered behavior has no known contradictory official update;
- scope and limitations match the assertion;
- retrieval/effective dates are recorded;
- affected fixtures/documents have been reviewed.

### 4.2. STALE

Evidence becomes stale when:

- review window defined by future provider policy expires;
- provider announces or demonstrates relevant change;
- source disappears and no accepted preserved evidence exists;
- scope no longer matches target market/account/channel;
- implementation or fixture expects fields outside recorded scope.

Exact calendar review windows are not selected here. Provider policies in Run 9/10 must define them from evidence and risk.

### 4.3. SUPERSEDED or WITHDRAWN

- `SUPERSEDED` links old and replacement evidence and preserves history.
- `WITHDRAWN` marks provider removal or invalidation.
- Historical records are not silently rewritten.
- A superseded source may remain relevant for compatibility fixtures but not for current behavior without explicit version scope.

### 4.4. UNAVAILABLE or DISPUTED

Provider-dependent acceptance is blocked when necessary evidence is unavailable or materially disputed. The system must expose unsupported/unknown behavior rather than fabricate compatibility.

## 5. Regression triggers

Reference regression review is mandatory when:

- official content fingerprint changes;
- provider changes field meaning, validation, authentication or verification;
- endpoint/page/payload disappears or is renamed;
- supported market/category/account scope changes;
- rate/restriction/CAPTCHA/access behavior changes materially;
- error or retry semantics change;
- rollout/deprecation deadline appears;
- existing fixture no longer matches evidence;
- provider behavior contradicts current approved mapping;
- a module proposes using a new external field or action.

A provider change does not automatically authorize implementation change.

## 6. Change classification

### 6.1. Clarification

No observable contract, mapping, security, privacy, idempotency or error meaning changes. Existing fixtures remain valid.

### 6.2. Compatible extension

New optional behavior may be added only when:

- old behavior remains supported;
- absence has safe documented meaning;
- verification and authorization are unchanged or strengthened;
- existing consumers remain valid;
- fixture and acceptance updates are prepared before implementation.

Use `FX-REF-CHANGED-COMPATIBLE-001`.

### 6.3. Breaking reference change

Breaking examples:

- removed/renamed required field;
- changed field semantics;
- changed authenticity/verification procedure;
- changed identifier stability;
- new mandatory permission/account condition;
- changed retry/error meaning;
- changed privacy exposure;
- provider action no longer available;
- source structure makes prior parser mapping unreliable.

Use `FX-REF-CHANGED-BREAKING-001`. Contract Change Policy and Migration/Compatibility Policy apply before implementation.

## 7. Mandatory regression packet

A reference update packet must contain:

1. provider and `reference_id`;
2. old and new source identity;
3. retrieval/effective dates;
4. exact changed scope;
5. literal or safely summarized evidence with copyright/privacy limits;
6. change classification;
7. affected contracts, data mappings, modules and operations;
8. security/privacy impact;
9. error, retry and idempotency impact;
10. fixture additions/updates/supersessions;
11. Acceptance Matrix rows;
12. compatibility and unsupported behavior;
13. open decisions touched but not closed;
14. allowed and forbidden implementation actions;
15. rollback/fallback or explicit blocked state;
16. independent acceptance authority.

Missing items keep the change blocked.

## 8. Fixture requirements

Provider-specific fixture must:

- reference one or more evidence records;
- state provider, scope and fixture version;
- use synthetic/redacted payloads unless separately approved evidence handling allows otherwise;
- cover valid, rejected, unavailable, malformed, ambiguous and unsupported states when applicable;
- cover authenticity/verification failure;
- preserve error/idempotency semantics;
- avoid real credentials and unnecessary personal data;
- record limitations and market/account scope;
- fail closed when evidence is missing or stale.

Golden snapshot alone is insufficient if semantic assertions and provenance are absent.

## 9. Provider-specific minimum gates

### 9.1. Avito

Future Avito policy/evidence must cover only verified scope for:

- source URL and search/filter semantics;
- listing identity and fields used by approved product scope;
- market/category limitations;
- blocked/CAPTCHA/malformed/incomplete outcomes;
- rate or access restrictions when officially evidenced;
- change detection limitations;
- prohibition on treating failure as no listings.

OD-009–OD-011 remain open until separately decided.

### 9.2. Telegram

Future Telegram policy must cover:

- official bot/webhook/Mini App authenticity rules used by approved scope;
- provider identifiers and replay/duplicate semantics;
- delivery outcomes and ambiguity;
- privacy/data minimization;
- supported interaction surfaces.

No Telegram payload becomes trusted by display name or unverified client assertion.

### 9.3. MAX

Future MAX policy must use official/primary sources and record any documentation availability limits. Unsupported or undocumented verification/delivery behavior remains blocked.

Absence of evidence must not be filled by analogy with Telegram.

## 10. Staleness and review

Provider policies in Run 9/10 must define risk-based review triggers. Until then:

- known official change immediately invalidates `CURRENT` status for affected scope;
- new implementation cannot rely on evidence known to be stale;
- inaccessible source requires preserved accepted evidence or refresh;
- time-sensitive assertion is rechecked immediately before an implementation task;
- final documentation audit verifies status and links, but does not infer provider facts.

## 11. Failure behavior

When reference regression is detected:

1. stop affected acceptance;
2. mark evidence `STALE`, `SUPERSEDED`, `WITHDRAWN`, `UNAVAILABLE` or `DISPUTED` as proven;
3. do not rewrite historical evidence silently;
4. identify first affected contract/mapping/fixture;
5. expose unsupported/blocked/ambiguous state;
6. create one scoped documentation change packet;
7. update affected fixtures and matrix rows;
8. independently verify GitHub result;
9. only then allow separate implementation planning.

Provider failure or uncertainty never becomes clean empty result.

## 12. Security, privacy and copyright boundary

Reference evidence handling must not:

- store credentials, cookies, tokens or private keys;
- capture private customer content without separate approval;
- publish unnecessary personal data;
- copy large copyrighted pages when URL, metadata and limited evidence are sufficient;
- expose foreign-host internals;
- execute external strings as shell commands;
- use production provider interaction without exact approved task.

## 13. Explicit non-decisions

Policy does not choose:

- automated crawler or monitoring tool;
- reference storage format;
- screenshot/archive service;
- review interval values;
- provider SDK/library;
- parser implementation;
- API endpoints or payload schemas;
- rate limits;
- external credentials;
- release/deployment behavior;
- provider-specific product scope blocked by open decisions.

## 14. Acceptance criteria

Reference regression policy is accepted when:

- evidence schema and source priority are explicit;
- current/stale/superseded/unavailable/disputed states are defined;
- regression triggers and change classes are defined;
- fixture and Acceptance Matrix integration is mandatory;
- Avito, Telegram and MAX future policy gates are distinguished;
- no provider facts are invented;
- no external call, executable test, parser or runtime artifact is created.

## 15. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первая policy для official/primary evidence lifecycle, staleness, provider change classification and fixture regression без provider implementation. |
