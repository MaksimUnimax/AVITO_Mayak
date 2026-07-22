# Filter Catalog & Builder — Full Evidence and Handoff v1.0

## 1. Metadata

| Field | Value |
|---|---|
| Status | FINAL EVIDENCE/HANDOFF FOR ACCEPTED SEMANTIC SCOPE |
| Date | 2026-07-22 |
| Module | `13-filter-catalog-and-builder` |
| Roadmap step | `FC-09` |
| Technical ID | `FC-09-FILTER-CATALOG-AND-BUILDER-MODULE-EVIDENCE-HANDOFF-20260722-036` |
| Accepted semantic/test evidence base | `7d31c0e3d2a351df934f3797e02b3bc909d6ed34` |
| Source-of-truth playbook | `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` |
| Owner decision capture | `docs/04-modules/13-filter-catalog-and-builder/OWNER_FILTER_CATALOG_AND_BUILDER_DECISIONS_CAPTURE_v1.0.md` |
| Governance reference | `docs/00-governance/DECISION_LOG_APPEND_ONLY.md:1211–1239`, ADR-0029 |
| Open-decision register | `docs/00-governance/OPEN_DECISIONS.md` |
| Scope classification | governance; provider-neutral semantic contracts; deterministic semantic functions; safe read projections; synthetic deterministic tests; architecture/contract/unit evidence; documentation handoff |

## 2. Executive summary

FC-00 through FC-08 are accepted on the evidence base recorded below. FC-09 is the final evidence/handoff step for this module. Module 13 is complete only in governance, provider-neutral semantic contracts/functions, safe projections and synthetic deterministic-test evidence.

This handoff is not runtime implementation, provider integration, Avito support implementation, persistence, UI, API, exact supported-filter catalog or deployment evidence. It does not approve an exact Avito filter catalog and does not authorize implementation.

## 3. Source-of-truth hierarchy

The applicable hierarchy is public GitHub `main`, approved governance, linked module playbooks and accepted handoffs, then the Module 13 playbook and its accepted semantic/test evidence. Parser observation, a visible UI label, an internal Avito endpoint and a hand-written list are not catalog authority.

## 4. Accepted FC-00—FC-08 SHA chain

FC-00 was read-only verification with no commit. Each committed SHA below was inspected with `git show`, `git diff-tree` and `git merge-base --is-ancestor`; every SHA is an ancestor of the accepted base.

| Step | Accepted SHA | Exact subject | Changed paths | Scope result |
|---|---|---|---|---|
| FC-00 | no commit | read-only verification | none | governance/base verification only |
| FC-01 | `22ce21e7bffa8b378fc362255925897016ef996a` | `fc-01: capture filter catalog owner decisions` | `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`; `docs/04-modules/13-filter-catalog-and-builder/OWNER_FILTER_CATALOG_AND_BUILDER_DECISIONS_CAPTURE_v1.0.md` | owner decisions and governance capture |
| FC-02 | `0748d28089ca7bae6cfcee205cb0665c37e3976b` | `fc-02: fix catalog read model version checks` | `src/mayak/modules/filter_catalog/contracts.py` | provider-neutral catalog contracts and version checks |
| FC-03 | `6c89efa08ea399bf88249ee15dd430e166226c35` | `fc-03: add evidence approval boundary semantics` | `src/mayak/modules/filter_catalog/__init__.py`; `src/mayak/modules/filter_catalog/evidence_approval.py` | evidence approval boundary |
| FC-04 | `6ab0451980209dd78603e680e2256b5c6fb4be17` | `fc-04: add builder field and draft validation semantics` | `src/mayak/modules/filter_catalog/__init__.py`; `src/mayak/modules/filter_catalog/builder_validation.py` | builder field and server-side draft validation semantics |
| FC-05 | `b361ac92c132d73d91804a6e2d7f1c8751657d10` | `fc-05: correct dependency graph linkage blocker` | `src/mayak/modules/filter_catalog/value_dependency_semantics.py` | multivalue, range and explicit dependency semantics |
| FC-06 | `9e6f1fe38b637fee22ee49b16124ce885dc58150` | `fc-06: add beacon override candidate mapping semantics` | `src/mayak/modules/filter_catalog/__init__.py`; `src/mayak/modules/filter_catalog/beacon_override_candidate.py` | candidate preparation; Beacon acceptance remains external |
| FC-07 | `948c1efbe8ccc43eff02d4c40741d47dfd52595e` | `fc-07: add safe catalog read models` | `src/mayak/modules/filter_catalog/__init__.py`; `src/mayak/modules/filter_catalog/safe_read_models.py` | safe Web/Admin projections |
| FC-08 | `7d31c0e3d2a351df934f3797e02b3bc909d6ed34` | `fc-08: remove generic dispatch and enforce exact ast counts` | `tests/architecture/test_filter_catalog_semantic_boundaries.py`; `tests/unit/test_filter_catalog_semantic_contracts.py` | final deterministic synthetic evidence and static guards |

## 5. Rejected/corrected FC-08 history

The following seven intermediate FC-08 commits are historical evidence only, not separate accepted roadmap steps. The only accepted FC-08 evidence base is `7d31c0e3d2a351df934f3797e02b3bc909d6ed34`.

| Full SHA | Subject | Historical classification |
|---|---|---|
| `8a6734f36c1de10f0c97e7952576d5499a8abb31` | `fc-08: add synthetic filter catalog contract tests` | corrected synthetic contract/fixture evidence |
| `bdf12b1e6e01e39af21f4aa93211759673194fdf` | `fc-08: correct explicit filter catalog vector tests` | corrected vector order/corpus evidence |
| `43653f6342ac9f0507a29e02deb72f1d781c80cc` | `fc-08: enforce public projection and deterministic results` | corrected public projection and semantic result binding |
| `bb19c124d7f2d0968c06b5a98c4af5ad0790f91c` | `fc-08: restore exact synthetic test contract` | corrected deterministic fixture/schema checks |
| `623870e173ba3ce3fcabf25e8e4b2ba2414e62d6` | `fc-08: assert normalized vector outcomes` | corrected semantic result binding |
| `4eeaa81e9b92c7398433b47e1895c7fdf1106c02` | `fc-08: harden static evidence guards` | corrected static evidence guards |
| `d19034c47f4a483635f3510b28d835da91d24859` | `fc-08: complete fixture and ast proofs` | corrected deterministic fixture/schema and vector-order/corpus/AST proofs |

The final accepted commit removes generic dispatch and enforces exact AST counts. These categories follow the observed commit subjects and final commit metadata; no additional cause is asserted.

## 6. Accepted artifact inventory

Git blobs and SHA-256 values below were computed from the exact accepted base. Owning steps are the accepted chain steps that introduced or finalized the artifact.

| Classification | Path | Git blob | SHA-256 | Owning step |
|---|---|---|---|---|
| governance/documentation | `docs/04-modules/13-filter-catalog-and-builder/MODULE_PLAYBOOK.md` | `074540dc987d0e499ca3b27e8b3cd7aaf29fcb54` | `129ba622cf5359e7f15d789b0024b2346cc8ce9a9aabab88379cc551bf0325e9` | pre-FC-01 approved playbook |
| governance/documentation | `docs/04-modules/13-filter-catalog-and-builder/OWNER_FILTER_CATALOG_AND_BUILDER_DECISIONS_CAPTURE_v1.0.md` | `555cc4cac5656ef2c73d1cf0c458451cc8803e08` | `a91577131f3b12b930f137b8f258c3ae3fbd616b192b37f08b0b6c4a95e3a6f6` | FC-01 |
| governance/documentation | `docs/00-governance/DECISION_LOG_APPEND_ONLY.md` | `4a174b807d9256c9525fe5b728f05216e9968ba0` | `7527b8cad88c0ac379bcc5b0709bde33ec4cc0254c28e09b9661f8825d2ed08d` | FC-01 |
| governance/documentation | `docs/00-governance/OPEN_DECISIONS.md` | `df2d024ec54f84b53eca519681f82b062b9e4d7c` | `c76036e125a07f5a50b5bb4c8c7d5a843555be2dc0985e3be20aea369d3e3774` | governance baseline |
| production semantic contract/function | `src/mayak/modules/filter_catalog/__init__.py` | `f880efde1ae75cb7357de15328e6685d8244d80d` | `168cc2fba704952fbff1cac50214f782baf4cf84384f2335bdb6e81ec21ca545` | FC-03—FC-07 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/contracts.py` | `30055bec462fd772d06f1dc12de1ea8fcba3da77` | `d1033f905adb2dd219c0a80865e1fab1c37b6df6862fec50de6750445c5cfd1d` | FC-02 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/evidence_approval.py` | `9491ee2a90aa4f6cd580c4a9bf511942c92f2f0a` | `8ab26de5a363844dbc9f96ba9d67aa06655330b7d6d615e15944f3253bcd0684` | FC-03 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/builder_validation.py` | `084ba9d7083b6ca6fab8b03c7be34e4d3f50c3fb` | `fa8f49f48a497d512b6e97823651426c992da82406a5d68ec2af4afdc9dcd252` | FC-04 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/value_dependency_semantics.py` | `9cb0f1648a359ae86c5e699250111bbe62825d27` | `d98ed49cf765172758d1740957e61b68e091b93f8dfe0a2cbf6aafd6918276f0` | FC-05 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/beacon_override_candidate.py` | `1a441afd4352fd56c295b6a656262c00f226b2c1` | `4457a6d115ec17e880432c863887002e1ae7b3cec0af053735aa56546641e006` | FC-06 |
| production semantic contract/function | `src/mayak/modules/filter_catalog/safe_read_models.py` | `239d79ab54e03838da2967d24b2ca3ee60da65fe` | `016580d2149f6752c2eac253d3bd62bf88e8205481fe607a6a8faede32179dc0` | FC-07 |
| architecture test | `tests/architecture/test_filter_catalog_semantic_boundaries.py` | `229bbb1603226f4f689539a951cd08dc72f613d0` | `0a3609125d520db25f7b49ac20bd92ec301b59afc13da29ea50eeb16864d527d` | FC-08 |
| contract test | `tests/contract/test_filter_catalog_semantic_contract_exports.py` | `9386f1a6e153f9fd9e9e1a7ff1b394ae46c8f60a` | `d08d808d3668b7f6c55d40bf5f1888d32a0e3c5692fffc82ee661053d7116979` | FC-08 |
| synthetic fixture | `tests/fixtures/filter_catalog_semantic_vectors.json` | `e568df8934cc6b1c881ba831c8a4618696381719` | `12f417871d955f30b1e2300e7d639d1aed3f059438974ee9a687204e25d12785` | FC-08 |
| unit test | `tests/unit/test_filter_catalog_semantic_contracts.py` | `d682a5735c2b5ace5236c7d127e789510e0d668a` | `5c27692f93b2c5ae3330d331ad827c86f288f2c65c6735bd4b57e0ff79c22c68` | FC-08 |

### Cumulative Module 13 path evidence

`git diff --name-status ef91ae8aeaaccbee20a02ee78e63677f2d5d5fb4 7d31c0e3d2a351df934f3797e02b3bc909d6ed34` showed 22 paths in total, including unrelated Module 12 Web Cabinet paths. The exact Module 13 inventory is the following 13 paths; no unrelated path is classified as a Module 13 artifact:

| Classification | Path |
|---|---|
| governance/documentation | `docs/00-governance/DECISION_LOG_APPEND_ONLY.md` |
| governance/documentation | `docs/04-modules/13-filter-catalog-and-builder/OWNER_FILTER_CATALOG_AND_BUILDER_DECISIONS_CAPTURE_v1.0.md` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/__init__.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/beacon_override_candidate.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/builder_validation.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/contracts.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/evidence_approval.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/safe_read_models.py` |
| production semantic contract/function | `src/mayak/modules/filter_catalog/value_dependency_semantics.py` |
| architecture test | `tests/architecture/test_filter_catalog_semantic_boundaries.py` |
| contract test | `tests/contract/test_filter_catalog_semantic_contract_exports.py` |
| synthetic fixture | `tests/fixtures/filter_catalog_semantic_vectors.json` |
| unit test | `tests/unit/test_filter_catalog_semantic_contracts.py` |

The cumulative diff stat was 16,730 insertions across 22 paths; Module 12 paths are excluded from the Module 13 count of 13.

## 7. Semantic contract/function evidence

The package exports immutable, extra-forbidden Pydantic semantic models and pure deterministic functions. The evidence covers catalog versioning; filter definitions, options, ranges, dependencies, capability profiles and evidence references; evidence approval; builder field projection and server-side draft validation; preservation of multivalue and range/dependency semantics; Beacon override-candidate preparation; and Web/Admin safe read projections.

The contracts include `FilterCatalogVersion`, `FilterDefinition`, `FilterOptionDefinition`, `FilterRangeDefinition`, `FilterDependencyRule`, `FilterCapabilityProfile` and `FilterEvidenceReference`, with explicit state, scope, provenance and supersession references. `FilterRangeDefinition` requires unit and bound/inclusivity semantics. `FilterDependencyRule` requires an explicit graph edge, condition and outcome. No exact Avito values are selected by these synthetic semantics.

The deterministic functions are `evaluate_filter_evidence_approval`, `project_builder_field_definition`, `validate_builder_draft`, `evaluate_multivalue_preservation`, `validate_range_value`, `evaluate_filter_semantic_exposure`, `prepare_beacon_override_candidate`, and `project_catalog_safe_filter_read`. They return semantic outcomes and safe references; they do not persist state, execute runtime, call providers, mutate Beacon or grant entitlements.

## 8. Owner decisions preserved

- No manually invented full Avito catalog.
- Editability is evidence/rule-based.
- Priority filter families are candidates only.
- Unknown or ambiguous remains `found-but-not-editable`.
- Catalog versions are immutable; changed evidence creates a new version/supersession.
- Beacon owns configuration and acceptance.
- Parser provides evidence only.
- Web renders approved definitions only.
- Entitlements owns tariff, access, limits and allowed intervals.
- Multivalue values are not collapsed.
- A range requires unit, bounds and inclusivity.
- Category, geography and provider scope are explicit.
- Dependencies require an explicit graph.

## 9. OD-009 and open gates

The exact active Markdown-table row is `| OD-009 | OPEN | Not changed by ADR-0009. |`. OD-009 remains OPEN. Exact first-stage editable filters are not approved. There is no approved category taxonomy, provider URL mapping, option catalog, invented range unit or invented dependency graph.

## 10. FC-08 deterministic test evidence

The repository-derived exact evidence counts are: canonical references 36; vectors 56; `CATALOG` 8; `EVIDENCE` 8; `BUILDER` 8; `VALUE` 8; `BEACON` 8; `SAFE_READ` 12; `STATIC` 4; architecture tests 8; contract tests 10; unit tests 64; targeted tests 82; exact explicit handlers 56; exact explicit vector tests 56; generic dispatch registries 0; dynamic reflection 0; SAFE_READ public projection handlers 12; current synthetic fixture violations none.

## 11. Fresh final verification

All Python/pytest commands were run with `PYTHONDONTWRITEBYTECODE=1` in the clean checkout at the accepted base.

| Verification | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/architecture/test_filter_catalog_semantic_boundaries.py --collect-only -q` | 8 tests collected |
| `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/contract/test_filter_catalog_semantic_contract_exports.py --collect-only -q` | 10 tests collected |
| `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit/test_filter_catalog_semantic_contracts.py --collect-only -q` | 64 tests collected |
| targeted three-file run | 82 passed in 1.24s |
| `PYTHONDONTWRITEBYTECODE=1 python -m pytest --collect-only -q` | 4511 tests collected |
| `PYTHONDONTWRITEBYTECODE=1 python -m pytest` | 4511 passed in 36.13s |
| `git diff --check` | clean |
| protected production blobs | all match expected protected blobs |
| OD-009 exact active status | OPEN |
| forbidden artifact scan | no forbidden imports, runtime calls or artifacts detected |

## 12. Compatibility boundaries

### Module 03 Entitlements & Billing

Entitlements owns tariff, access, limits and allowed intervals. Module 13 does not grant or duplicate entitlement state. The Module 03 handoff remains semantic-scope evidence with runtime, payment and persistence gates outside its completion.

### Module 04 Beacon Management

Beacon owns source URL, accepted snapshot, override acceptance, actual/effective configuration, revisions and lifecycle. A builder draft or candidate is not Beacon state. Module 13 prepares a candidate and requires Beacon acceptance; it does not mutate Beacon or rewrite history.

### Module 05 Avito Parser Adapter

Parser supplies extraction/normalization evidence and warnings only. Parser success and internal endpoints do not approve editability. Raw provider payload is not retained by default. Provider/runtime parser work remains separately gated.

### Module 12 Web Cabinet

Web may render approved UI-neutral definitions and submit owning-module commands only. Web draft/client validation is not authority. There is no direct Beacon/catalog table write and no frontend, API or runtime implementation in this evidence scope.

## 13. Forbidden-artifact absence

The cumulative Module 13 diff and current package were scanned for and contain no Module 13 additions consisting of API routes/handlers; frontend pages/components; DB tables, ORM or migrations; persistence; provider SDKs; live Avito/network calls; Docker/CI/CD/deploy; services, workers, schedulers; ports/listeners; credentials/secrets; real provider payload fixtures; exact supported-filter catalog; direct Beacon mutation; or historical Beacon rewrite. Documentation mentions of these boundaries are not implementations. Static checks found no forbidden imports such as `httpx`, `requests`, provider SDKs, FastAPI routes, SQLAlchemy/ORM, migrations, sockets or network execution, and no direct imports/mutations of foreign authoritative state.

## 14. Blocked future gates

Separate future gates are required for exact supported filter list and category coverage; official/accepted provider evidence; parser integration; runtime service; persistence/schema/migrations; API; frontend visual builder; Beacon runtime integration; entitlement runtime integration; live Avito calls/probes; deployment/infrastructure; and credentials/secrets.

## 15. Completion and handoff statement

Module 13 is complete only for governance, semantic contracts/functions and synthetic deterministic tests. Future implementation must use the accepted Module 13 public contracts, owning-module boundaries, fresh exact owner/evidence gates and a separate atomic task. FC-09 does not authorize implementation, provider integration, exact catalog selection or any future roadmap step.
