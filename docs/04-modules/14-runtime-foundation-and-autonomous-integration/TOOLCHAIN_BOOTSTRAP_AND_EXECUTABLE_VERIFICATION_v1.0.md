# RF-06-02 — pinned toolchain bootstrap and executable verification

## Metadata

- Version: `1.0`
- Status: `APPROVED_CANDIDATE`
- Date: `2026-07-23`
- Technical ID: `RF-06-02-PINNED-TOOLCHAIN-BOOTSTRAP-AND-EXECUTABLE-VERIFICATION-20260723`
- Retry: `RETRY-01`
- Gate: `RF-06-02`
- Evidence timestamp: `2026-07-23T14:38:40Z` backup gate; executable and lock verification completed on the same UTC task run.
- Exact source SHA: `f77a1d85d7c8b8fd1f2e60694729d1b7c3a1598c`

## Prerequisite acceptance

RF-06-01 corrective chain is independently accepted at the exact source SHA. RF-06-02-CORRECTIVE-03 build prerequisites were provisioned previously and reverified read-only for this task. No APT mutation was performed here.

The live Ubuntu 24.04 noble amd64 probes passed for the compiler/toolchain and OpenSSL, zlib, bz2, lzma, libffi, sqlite3, readline, ncursesw and uuid. The accepted prerequisite manifest is available at `/var/backups/avito-mayak/RF-06-02-CORRECTIVE-03-ISOLATED-BUILD-PREREQUISITE-PROVISIONING-20260723-20260723T142933Z/build-prerequisite-manifest.json` with SHA-256 `d307d72c76fed3634052f3f3687d2a9dba311fe401298d9ceae9285dc9160b27`.

## Purpose and non-goals

This gate installs only the accepted CPython and uv pins in the project-owned boundary and proves executable, ABI, module, venv and offline lock behavior. It does not install project dependencies, run `uv sync`, create a persistent project virtualenv, start the runtime, create Docker or database resources, open a listener, change configuration, or claim production readiness.

## Source and dedicated worktree model

The administrative source checkout `/opt/avito-mayak` retained its historical HEAD and known untracked `__pycache__` files. It was not cleaned, reset or modified. A clean dedicated worktree `/opt/avito-mayak-worktrees/rf06-toolchain-bootstrap-r1-f77a1d8` on branch `rf06-toolchain-bootstrap-r1-f77a1d8` was created directly from the exact expected SHA. `origin/main` and the dedicated worktree were equal to that SHA at preflight and before publication.

## Pre-existing toolchain state and backup

The toolchain root was absent before this task. The rollback backup is `/var/backups/avito-mayak/RF-06-02-PINNED-TOOLCHAIN-BOOTSTRAP-AND-EXECUTABLE-VERIFICATION-20260723-RETRY-01-20260723T143840Z`, with aggregate SHA-256 `c8a7a93ad5c5595e457d8efb94428d7848780d93e807f0588dc12f2e0572e5f5`. It contains no secrets, auth data, `.git` data or executable archives.

## Exact accepted pins and official sources

| Component | Pin | Official source | SHA-256 |
|---|---|---|---|
| CPython | 3.14.6 standard-GIL | <https://www.python.org/ftp/python/3.14.6/Python-3.14.6.tgz> | `74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222` |
| uv | 0.11.31 | <https://github.com/astral-sh/uv/releases/download/0.11.31/uv-x86_64-unknown-linux-gnu.tar.gz> | `8cc1cd82d434ec565376f98bd938d4b715b5791a80ff2d3aa78821cf85091b4b` |

The uv release API reported ID `357733488`, `draft=false`, `prerelease=false`, `immutable=true`, target commit `b7fdec626cdafcfb0d0db54d39d3d5f114aefb5c`; its official checksum file and API asset digest matched. Two official GitHub Sigstore attestation records were present. The CPython archive SHA matched the accepted pin and its official `.sigstore` bundle was structurally valid with certificate, message signature and one transparency-log entry. No Sigstore verifier was installed, so cryptographic verification is deferred to RF-25: `OFFICIAL_SHA256_VERIFIED_SIGSTORE_BUNDLE_PRESENT_CRYPTO_VERIFICATION_DEFERRED_RF25`.

## CPython configure, build and standard-GIL proof

The build used at most two jobs under the exact staging root. Configure was:

```text
./configure --prefix=/opt/avito-mayak-runtime/toolchain/.staging/RF-06-02-PINNED-TOOLCHAIN-BOOTSTRAP-AND-EXECUTABLE-VERIFICATION-20260723/cpython/3.14.6 --with-ensurepip=install --without-lto
```

PGO and LTO were not enabled for reproducibility and host-capacity reasons. Build and install both exited zero. Configure discovered `_ssl`, `_hashlib`, zlib, `_bz2`, `_lzma`, `_sqlite3`, `_ctypes`, readline, `_curses`, `_uuid`, multiprocessing support and all other required modules.

The promoted prefix is `/opt/avito-mayak-runtime/toolchain/cpython/3.14.6`. The executable is CPython `3.14.6`, x86_64, 64-bit, with `SOABI=cpython-314-x86_64-linux-gnu`, empty `sys.abiflags`, `Py_GIL_DISABLED=0` and `sys._is_gil_enabled()=true`. It is therefore standard-GIL, not free-threaded. SSL reports OpenSSL 3.0.13 and sqlite reports 3.45.1.

Required imports passed for ssl, hashlib, zlib, bz2, lzma, sqlite3, ctypes, readline, uuid, multiprocessing, asyncio, venv, ensurepip, json, tomllib and zoneinfo. `ensurepip` reports pip 26.1.2; the temporary venv contained only pip and was removed. No project package was installed.

## uv verification

The promoted uv prefix is `/opt/avito-mayak-runtime/toolchain/uv/0.11.31`. Extracted payload contained only the expected `uv` and `uvx` executables. Both report `0.11.31 (x86_64-unknown-linux-gnu)`, pass loader and help checks, and run as service identity `avito-mayak`. `UV_PYTHON_DOWNLOADS=never`, `UV_NO_MANAGED_PYTHON=1`, exact `UV_PYTHON`, and a unique temporary `UV_CACHE_DIR` were used. A temporary `uv venv --python` environment selected CPython 3.14.6 and was removed; no package or managed-Python download occurred.

## Installed paths, links and permissions

The only persistent toolchain objects are the accepted version directories, relative links and manifest:

- `/opt/avito-mayak-runtime/toolchain/cpython/3.14.6`
- `/opt/avito-mayak-runtime/toolchain/uv/0.11.31`
- `/opt/avito-mayak-runtime/toolchain/toolchain-manifest.json`
- `cpython/current -> 3.14.6`
- `uv/current -> 0.11.31`
- `bin/python3.14 -> ../cpython/current/bin/python3.14`
- `bin/python -> python3.14`
- `bin/uv -> ../uv/current/uv`
- `bin/uvx -> ../uv/current/uvx`

Directories are `0750`, executables are root-owned and group-readable/executable without world write, and the service identity can execute the stable links. The manifest is a regular `0640 root:avito-mayak` file; the service identity can read it but cannot write it. Manifest SHA-256 is `a5c2fa436d3721f1fbb0a05c9c335486455e5292835b5ac87dc6720cfb0091a2`.

## Offline lock check

In the dedicated worktree, exact command `uv lock --check --offline` exited `0` with managed-Python downloads disabled and a unique empty temporary cache. It resolved 27 packages without downloads, did not sync, and did not change either input. `pyproject.toml` remained `d443407018e618613f606aedfd532048cbf47ab29c1f0f5263bc639e5f55ece9`; `uv.lock` remained `24e0612d06957ef1452f317878f6c6dc354dafc202ff1607ee3f23e348271577` before and after.

## Explicit non-impact and rollback

No project dependencies were installed; no runtime was started; no Docker resource, listener, environment/configuration mutation, provider call, credential read, or foreign-resource impact occurred. No APT mutation or system Python mutation occurred. Rollback before push removes only this task's toolchain version directories, links, manifest, staging, temporary downloads/build residue and repository changes; it does not remove provisioned prerequisites or alter the source checkout.

## Limitations and verdict

The CPython Sigstore bundle was not cryptographically verified because no verifier was already installed; RF-25 owns that verification. The standard public Python checksum sidecar URLs were unavailable during the check, so the accepted archive SHA and official Sigstore bundle are the recorded integrity evidence. No infrastructure identity, credential or authentication value is recorded.

- `PINNED_TOOLCHAIN_INSTALLED`
- `EXECUTABLE_VERIFICATION_PASSED`
- `LOCK_CHECK_PASSED`
- `RUNTIME_ELIGIBLE`
- `NOT_PRODUCTION_READY`

Next gate is independent ChatGPT acceptance. RF-06-03 and RF-07 remain blocked. RF-06 is not complete.
