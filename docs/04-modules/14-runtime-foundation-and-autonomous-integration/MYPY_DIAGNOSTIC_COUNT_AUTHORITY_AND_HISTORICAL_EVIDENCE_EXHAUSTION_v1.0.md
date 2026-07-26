# Mypy diagnostic count authority and historical evidence exhaustion

## Metadata

- Version: 1.0
- Status: PUBLISHED_PENDING_ACCEPTANCE
- Date: 2026-07-26
- Technical ID: RF-06-04-CORRECTIVE-07-AUTHORITATIVE-MYPY-COUNT-SUPERSESSION-20260726
- RF step: RF-06-04-CORRECTIVE-07
- Exact source SHA: `372ecc630106e9b813bddf1edd384ce36f48db6d`
- Production verdict: NOT_PRODUCTION_READY

## Trigger

Historical closure count: 248. Reproducible current count: 249. The historical cause remained unproven after full report materialization and bounded evidence exhaustion.

## Evidence chain

Technical IDs: RF-06-04-CORRECTIVE-01-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260723; RF-06-04-CORRECTIVE-02-MYPY-DIAGNOSTIC-COUNT-RECONCILIATION-20260723; RF-06-04-CORRECTIVE-03-MYPY-RECONCILIATION-EVIDENCE-MATERIALIZATION-20260724; RF-06-04-CORRECTIVE-04-MYPY-RECONCILIATION-EVIDENCE-MATERIALIZATION-20260724; RF-06-04-CORRECTIVE-05-MYPY-RECONCILIATION-REPORT-DELIVERY-COMPLETENESS-20260724; RF-06-04-CORRECTIVE-06-HISTORICAL-248-EVIDENCE-SURFACE-RECONCILIATION-20260726.

Reconciliation report: `/var/backups/avito-mayak/RF-06-04-CORRECTIVE-02-MYPY-DIAGNOSTIC-COUNT-RECONCILIATION-20260723-20260723T172307Z/REPORT.txt`; size 8823 bytes; SHA-256 `f633568bae2a106724171325995040e003f30177e6bbe54ae0af00a7754f4712`.

Bounded historical evidence primary directory: `/var/backups/avito-mayak/RF-06-04-CORRECTIVE-01-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260723-20260723T171206Z`.

Historical aggregate identity: `11d597423b5712c08ac91406d7b97a4f5a45211a03c6b2dcaad52db96603f565`.

## Proven current result

- mypy version: 1.20.2.
- Python: 3.14.6 standard-GIL.
- Canonical command: `mypy --show-error-codes src tests`.
- Repeated canonical counts: 249/249/249.
- No-incremental count: 249.
- Current normalized SHA-256: `4f6ac7fa39b343f16b207ff5bed187a7447f87515115dee250a25ebf06126e11`.
- Parser and mypy summary agree; implementation and current diagnostic sets are identical; no differential source/test/config regression exists.

## Bounded evidence exhaustion

RAW_HISTORICAL_OUTPUT_NOT_RETAINED; literal historical argv absent; exact historical cwd absent; invocation mypy executable/version absent; environment flags absent; cache policy absent; parser method absent; parser count absent; no first proven divergence; delta -1 not explained; bounded evidence exhausted.

## Non-speculation boundary

Historical 248 root cause is not proven. Historical 248 must not be labeled as a cache, command, parser, truncation, environment or transcription defect without new direct evidence. No source or test change is justified by historical 248, and no mypy debt remediation is authorized by this correction.

## Authority decision

Historical 248 remains preserved as `UNREPRODUCIBLE_HISTORICAL_RESULT`; it is not deleted or rewritten. It is superseded only as the expected count for future RF-06 closure. The authoritative closure expectation is 249, based on reproducible canonical current evidence and bounded historical evidence exhaustion, not on an invented historical root cause.

AUTHORITATIVE_CURRENT_MYPY_COUNT: 249

HISTORICAL_248_CAUSE: NOT_PROVEN

HISTORICAL_248_CLOSURE_EXPECTATION_STATUS: SUPERSEDED

## Exact future RF-06-04 mypy contract

Source/test/config identity remains unchanged from the current base except documentation-only descendants. The task must resolve and record absolute Python and mypy executables; mypy must belong to promoted environment `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1`. Record Python and mypy versions. CWD is the disposable worktree root. Target order is `src tests`; exact command is `mypy --show-error-codes src tests`.

Environment: `PYTHONPATH=<worktree>/src`; `PYTHONNOUSERSITE=1`; `PYTHONDONTWRITEBYTECODE=1`; `LC_ALL=C.UTF-8`; `MYPY_FORCE_COLOR=0`. Each run receives a fresh absent cache directory. Run two canonical fresh-cache executions and one explicit `--no-incremental` execution. Parser consumes stdout and stderr; error/note records are classified separately; summary line is excluded from diagnostic records; mypy summary count is compared independently. Expected count for all three runs is 249. Expected normalized SHA-256 is `4f6ac7fa39b343f16b207ff5bed187a7447f87515115dee250a25ebf06126e11`. If source/tests/mypy config identity changes, the normalized SHA expectation must not be silently reused. Any count, summary, parser or normalized-set mismatch stops publication before commit.

## Artifact-count acceptance transition

Correction commit `372ecc630106e9b813bddf1edd384ce36f48db6d`, subject `docs(rf06): correct dependency artifact count semantics`, is independently accepted. Authoritative breakdown: 48 sdists / 246 wheels / 294 total; SHA-256 coverage 294/294; lock/environment bytes unchanged.

## Current gates

RF-06-03-C06 artifact-count correction: INDEPENDENTLY_ACCEPTED. Current supersession correction: PUBLISHED_PENDING_ACCEPTANCE. RF-06-04 closure: BLOCKED_PENDING_SUPERSESSION_CORRECTION_ACCEPTANCE. RF-07: BLOCKED_PENDING_RF06_CLOSURE. Runtime: STOPPED. Eligibility: RUNTIME_ELIGIBLE. Production verdict: NOT_PRODUCTION_READY.

## Explicit non-impact

No source, test, pyproject, lock, package, environment, toolchain or runtime changes; no Docker/database/listener changes; no secrets access; no foreign-resource impact.

## Limitations

Historical 248 exact cause remains permanently unknown unless new direct historical evidence appears. This does not permit rewriting history or asserting a false cause.

## Verdict

HISTORICAL_248_CAUSE_NOT_PROVEN

BOUNDED_HISTORICAL_EVIDENCE_EXHAUSTED

AUTHORITATIVE_CURRENT_MYPY_COUNT_249

HISTORICAL_248_SUPERSEDED_FOR_CLOSURE_EXPECTATION

RF06_ARTIFACT_COUNT_CORRECTION_ACCEPTED

RF06_04_CLOSURE_REMAINS_BLOCKED

RF07_REMAINS_BLOCKED

RUNTIME_ELIGIBLE

NOT_PRODUCTION_READY

## Next gate

After independent ChatGPT acceptance of this correction, a new RF-06-04 documentation-only closure task may be issued. This artifact does not close RF-06.
