# Dependency Artifact Count Semantics Correction

## Metadata

- Version: `1.0`
- Status: `PUBLISHED_PENDING_ACCEPTANCE`
- Date: `2026-07-23`
- Technical ID: `RF-06-03-CORRECTIVE-06-ARTIFACT-COUNT-SEMANTICS-AND-EVIDENCE-CORRECTION-20260723`
- RF step: `RF-06-03-CORRECTIVE-06`
- Exact source SHA: `c0104df4fb356862beffc04abe8b0170498eaf3c`
- UTC evidence timestamp: `2026-07-23T16:53:19Z`

## Trigger

`RF-06-04-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260723` stopped at `STOP_LOCK_EVIDENCE_MISMATCH`.

## First proven defect

`WHEEL_COUNT_WAS_LABELED_AS_TOTAL_ARTIFACT_COUNT`.

## Immutable accepted state

- `pyproject.toml` SHA-256: `c9c905db608ce2ccece5acfcdbff066a241f3c55a03d716d1e08864055b7ffdb`.
- `uv.lock` SHA-256: `9c9a87fb0c455d36162c3dbcfbdddc8c3f7d3e528157fb0f228678695263c020`.
- Toolchain manifest SHA-256: `a5c2fa436d3721f1fbb0a05c9c335486455e5292835b5ac87dc6720cfb0091a2`.
- Installed package count: `47`.
- Environment: `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1`.

## Counting method

The current `uv.lock` was parsed with Python `tomllib`. Every sdist object/list entry and every wheel entry was counted individually. Each artifact URL was required to be present and each hash was required to use the `sha256:` prefix. URL uniqueness and duplicate URL/hash pairs were counted independently.

## Package and artifact records

- Package records: `50`.
- Registry records: `49`.
- Local editable root: `1`.
- Sdist artifact entries: `48`.
- Wheel artifact entries: `246`.
- Total artifact entries: `294`.
- Hash coverage: `294/294` (`0` unhashed).
- Unique artifact URLs: `294`.
- Duplicate artifact entries: `0`.
- Duplicate URLs with different hashes: `0`.

## Wheel-only semantics

The lock may record sdists. The accepted sync selected wheels only; no source build occurred, and no recorded sdist was installed or built.

## Historical-report reconciliation

`294` was factually correct when used as the total artifact count. `246` is factually correct only as the wheel artifact count. Earlier wording labeling `246` as the total is superseded by this correction.

## Environment manifest audit

The manifest is **State B**: `registry_policy.artifacts: 246` and `registry_policy.hashed_artifacts: 246/246` are explicit wheel-only registry-policy fields, with no generic total-artifact field. Old SHA-256 is `0be844c148676dbcdc70fb5c16fb0913ab1869f6d30955d38c0301c70ec70fc6`; new SHA-256 is the same. Correction required: `no`. Exact field correction: `none`; the manifest was not changed.

## Repository changes

The original RF-06-03 artifact now contains an explicit correction notice and corrected count wording. This correction artifact and the governance/index surfaces record the same authoritative `48/246/294` breakdown.

## Explicit non-impact

No `pyproject.toml` or `uv.lock` changes; no package or environment-content changes; no source or test changes; no runtime or infrastructure mutation; no credentials or secrets access.

## Limitations

RF-06 closure is not published. RF-07 remains blocked.

## Verdict

- `RF06_ARTIFACT_COUNT_SEMANTICS_CORRECTED`
- `LOCK_BYTES_UNCHANGED`
- `DEPENDENCY_ENVIRONMENT_UNCHANGED`
- `RF06_CLOSURE_REMAINS_BLOCKED`
- `NOT_PRODUCTION_READY`

## Next gate

Independent ChatGPT acceptance is required; only then may RF-06-04 be reissued.
