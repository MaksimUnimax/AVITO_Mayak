# Existing Server Environment Record v1.0

## Metadata

- Version: `1.0`; status: `APPROVED_CANDIDATE`; date: 2026-07-23.
- Module 14; RF step: RF-05-05 — repository evidence and closure.
- Source repository SHA: `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
- Evidence timestamp UTC: `2026-07-23T13:26:13Z`.
- Technical ID: `RF-05-05-EXISTING-SERVER-ENVIRONMENT-RECORD-CLOSURE-20260723`.

## Purpose and scope

Sanitized, read-only evidence of existing project-owned acceptance allocations. This records boundaries and eligibility only; it does not claim that runtime, Docker resources, database, API, worker or scheduler exists.

## Evidence provenance

- Live read-only server inspection.
- Current GitHub `main` fetched at exact base `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
- Exact source path: `/etc/avito-mayak-01/environment.json`.
- No secrets, secret-directory contents, hostname, public IP or auth data copied.

## Host capacity

- Ubuntu 24.04.3 LTS; kernel `6.8.0-124-generic`; `x86_64`; 4 logical CPUs.
- Memory: 7.65 GiB total; 6.02 GiB available at inspection.
- Project roots are on the local root filesystem, read/write, 63% used; no separate mount boundary was asserted.

## Installed toolchain

- Python in PATH: CPython `3.12.3`; CPython 3.14 absent; `uv` absent.
- Git `2.43.0`; OpenSSL `3.0.13`; curl `8.5.0`.
- CPython 3.14 and exact pinned uv are RF-06 prerequisite/gap, not an RF-05 defect.

## Docker/Compose capability

- Docker Engine `29.2.1`, API `1.53`; daemon available.
- Docker Compose plugin `5.0.2`.
- No containers, networks or volumes were created or started.

## Project service identity

- User `avito-mayak`: UID `997`, primary GID `987`, shell `/usr/sbin/nologin`.
- Group `avito-mayak`: GID `987`.
- Supplementary groups: `avito-mayak`; no membership in `sudo`, `wheel` or `docker`.
- No running process owned by the service user; no `authorized_keys` file present for its identity.

## Project-owned filesystem boundaries

| Path | Metadata | Service-user access |
|---|---|---|
| `/opt/avito-mayak-runtime` | directory, `root:avito-mayak`, mode `750`, not symlink | not writable |
| `/etc/avito-mayak` | directory, `root:root`, mode `755`, not symlink | not writable |
| `/etc/avito-mayak-01` | directory, `root:avito-mayak`, mode `750`, not symlink | not writable |
| `/etc/avito-mayak-01/secrets` | directory, `root:avito-mayak`, mode `750`, not symlink; 0 direct entries | not writable; contents not read |
| `/var/lib/avito-mayak` | directory, `avito-mayak:avito-mayak`, mode `750`, not symlink | writable |
| `/var/backups/avito-mayak` | directory, `avito-mayak:avito-mayak`, mode `750`, not symlink | writable |

No probe files were created.

## Environment allocation

- Environment ID: `avito-mayak-acceptance-local-01`; profile: `synthetic_acceptance`; class: `SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`.
- Compose project: `avito-mayak-acceptance`; logical network key: `mayak-internal`; PostgreSQL logical volume key: `postgres-data`.
- Runtime root `/opt/avito-mayak-runtime`; configuration root `/etc/avito-mayak-01`; secrets root `/etc/avito-mayak-01/secrets`; data root `/var/lib/avito-mayak`; backup root `/var/backups/avito-mayak`.
- API bind `127.0.0.1`; allocated API port `18085`; observed free and unbound. PostgreSQL host port: `NONE`.
- Providers disabled by default; public ingress none; `PROVIDER_DISABLED_CONTINUE`.
- Allocation states are logical/unbound only; no Docker network, volume, database or service was present.
- Retention metadata: application logs 7 days, backups 7 days, synthetic database 14 days.

## Network and port allocation

Port `18085` was free. Ports `18080`–`18084` were occupied by unrelated listeners and were not touched. No project-owned listener, public ingress or project-owned PostgreSQL host-published port was observed.

## Provider readiness

Optional providers are disabled by default. `PROVIDER_DISABLED_CONTINUE` applies; no provider was contacted.

## Security and isolation evidence

The environment record is a regular `root:avito-mayak` file mode `640`; it is readable but not writable by `avito-mayak`. JSON is valid, has 60 top-level keys, has no duplicate keys, and has no detected token, password, private-key or `.env` payload. Secret-like values were redacted and secrets-directory contents were not read.

## Foreign-resource impact

`NONE`. Foreign listeners were classified only as occupied/unrelated; no foreign resource was changed, stopped or reused.

## Credentials exposure

`NONE`. No credentials, tokens, private keys, auth files, hostname, public IP or provider data are included.

## Runtime eligibility

`RUNTIME_ELIGIBLE` — allocation and isolation checks satisfy the RF-05 repository-evidence boundary. Runtime implementation and startup remain absent.

## Production verdict

`NOT_PRODUCTION_READY`.

## Known gaps deferred to RF-06+

CPython 3.14; exact pinned uv; expanded runtime dependencies; CI; containers; PostgreSQL; migrations; API/worker/scheduler; runtime deployment.

## Exact safe SHA-256 evidence

- Repository source SHA: `b6e4ad20bedc229b967fccd1dfcd41c7ea5fda58`.
- Environment record SHA-256: `d7b0e7369ad705ea6fbd2ca9f474a1498d217b2585c635b618c70675e4558566`.
- No secret artifact hashes are published.

## Explicit prohibitions preserved

No service start, container or volume creation, PostgreSQL provisioning, migrations, public ingress, provider calls, system configuration mutation, secret mutation or foreign-resource mutation was performed.

## Next gate

Independent ChatGPT acceptance of the RF-05 closure is required. RF-06 remains blocked until that acceptance.
