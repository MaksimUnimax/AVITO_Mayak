# RF26 operability acceptance record

Technical ID: `RF26-OBSERVABILITY-BACKUP-RECOVERY-01`

This record closes the Module 14 acceptance package for structured runtime
observability and project-owned backup/recovery operations. It is an
acceptance objective, not a production SLA and does not authorize production
restore or RF27 deployment.

The runtime emits newline-delimited JSON when `MAYAK_LOG_FORMAT=json`. Each
record has UTC timestamp, environment/source/process identity, producer,
operation, outcome and stable reason code. Correlation, causation, run, work
and attempt identifiers are included only when known. Formatting and optional
telemetry failures are best effort and cannot change a committed outcome.

`/health/live` is process-only. `/health/ready` fails closed for unavailable,
structurally invalid or non-current migration state. `/version` and
`/health/diagnostics` expose only bounded identity/readiness metadata; neither
returns secrets, credentials, private data or provider payloads. The request
boundary accepts only bounded safe `X-Correlation-ID` values and returns the
selected value in the same header.

RF24 remains the semantic restore authority. RF26 adds the operational wrapper
in `scripts/runtime/rf26_operability.py`: canonical project-owned backup root,
atomic temporary creation, mode `0600` artifacts, digest/readability metadata,
and fail-closed seven-day cleanup. Unknown, malformed, newer, symlinked,
foreign-looking and active sets are retained.

Acceptance evidence must contain metadata and sanitized summaries only. Raw
logical dumps, secrets, credentials, cookies, provider payloads and complete
unbounded logs are excluded. The acceptance mapping is a maximum planned
backup interval of 24 hours and a measured isolated restore/rebuild duration
below two hours; these are RPO/RTO acceptance objectives, not production SLAs.
