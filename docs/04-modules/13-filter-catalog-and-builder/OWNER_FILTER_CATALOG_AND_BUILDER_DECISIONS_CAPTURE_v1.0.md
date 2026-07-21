# Маяк Авито — Filter Catalog & Builder Owner Decisions Capture v1.0

**Status:** OWNER-APPROVED decisions; repository capture pending independent acceptance
**Date:** 2026-07-21
**Module:** `13-filter-catalog-and-builder`
**Roadmap step:** `FC-01`
**Technical ID:** `FC-01-FILTER-CATALOG-OWNER-DECISIONS-CAPTURE-20260721-003`
**Governance reference:** `ADR-0029`
**Source-of-truth playbook:** `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md`
**Scope:** documentation/governance-only

## Purpose and boundary

This document captures the confirmed owner decisions for the first governance stage of Filter Catalog & Builder. It is a documentation/governance-only capture. It does not approve a complete manually authored Avito filter catalog, product code, semantic contracts, tests, fixtures, runtime, provider behavior, persistence or any implementation step.

Filter Catalog & Builder owns the evidence-bound catalog-definition and UI-neutral builder boundary. Beacon Management remains the authority for Beacon source URL, accepted snapshot, overrides, effective configuration, revisions, lifecycle and Beacon override-candidate acceptance. Parser, Web Cabinet and Entitlements & Billing retain their own boundaries.

## Owner decisions

1. The first scope does not approve a complete Avito filter catalog manually.
2. Editability is determined by the rule/evidence boundary, not by a visible UI label, parser success or a user request.
3. Geography/city, price range, category, search text, and simple single-value and multivalue parameters are priority candidates for future evidence verification only; they are not approved and are not universal.
4. A found but unsupported, uncertain or ambiguous filter is shown as `found-but-not-editable`; it must not be silently hidden, discarded or made editable.
5. Published catalog versions are immutable. Changed evidence creates a new version or supersession, and historical Beacon revisions are never rewritten.
6. Beacon Management owns source URL, accepted snapshot, overrides, effective configuration, revisions, lifecycle and acceptance of the Beacon override candidate.
7. Avito Parser Adapter supplies extraction/normalization evidence and warnings, but does not approve editability. Parser success and an internal endpoint are not catalog authority.
8. Web Cabinet may display only catalog-approved UI-neutral builder definitions. A web draft/client validation is not business authority and does not authorize direct Beacon writes.
9. Entitlements & Billing owns tariff, access, limits and allowed intervals. Filter Catalog does not duplicate or issue entitlement.

## Ownership consequences

Filter Catalog & Builder may define evidence-bound catalog semantics and safe UI-neutral builder definitions only after the relevant evidence and approval gates. It does not own Beacon state, parser extraction, provider behavior, Web Cabinet presentation, or entitlement decisions.

Beacon Management remains the sole owner of the Beacon source URL, accepted snapshot, overrides, effective configuration, revisions and lifecycle, and accepts any override candidate. Parser Adapter remains the evidence and warning supplier. Web Cabinet remains a presentation, safe-read, draft and command-envelope boundary. Entitlements & Billing remains the authority for tariff, access, limits and allowed intervals.

## Evidence and editability consequences

Evidence must establish the applicable scope and semantics before a filter becomes editable. A visible provider label, parser success, internal endpoint, or user request is insufficient. Stale, missing or contradictory evidence blocks editability. Unsupported, uncertain, ambiguous or lossy results remain explicit as `found-but-not-editable`.

Repeated or multivalue parameters must preserve all approved values and must not be silently collapsed. Client-side validation remains usability only; catalog and owning-module/server validation remain authoritative. Raw Avito/provider payload retention is prohibited by default.

No exact supported filter, Avito URL parameter, category taxonomy, option/value, range unit, dependency, official/stable Avito filter API or runtime/provider support is approved by this capture.

## Preserved open decisions

`OD-009` remains OPEN. The exact first-stage supported filter list remains open. Exact category taxonomy, exact URL mapping, exact option sets, range units/bounds/inclusivity, and the dependency graph remain open. Evidence approval thresholds and refresh cadence remain open. `OD-013` and relevant retention/privacy decisions remain open.

Persistence, database, migrations, API, frontend, runtime and provider behavior remain blocked. Raw Avito/provider payload retention remains prohibited by default. No numbered open decision is closed by assumption.

## Blocked gates

This capture does not authorize FC-02 or product implementation before independent acceptance and a fresh GitHub gate. It does not authorize exact catalog creation, parser implementation or probes, Avito live/provider calls, frontend/UI/routes/API handlers, database/ORM/schema/migrations/persistence, runtime/services/workers/schedulers, Docker, CI/CD, deploy, ports/listeners, credentials, secrets, or direct mutation of Beacon or any foreign authoritative state.

OD-013 and relevant retention/privacy decisions remain open; raw provider payload retention is forbidden by default. Stale, missing or contradictory evidence blocks editability, and repeated/multivalue parameters cannot be silently collapsed. Client-side validation remains usability only.

## Acceptance boundary

This document is complete only as a governance capture pending independent GitHub acceptance. It creates no exact filter list and no provider fact. It does not authorize FC-02 or any product implementation. Any next roadmap step requires its own exact task, fresh GitHub/parallel-main verification and the applicable evidence and acceptance gates.
