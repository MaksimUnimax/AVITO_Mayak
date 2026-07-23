# Toolchain and Dependency Baseline v1.0

## Metadata

- Version: `1.0`
- Status: `APPROVED_CANDIDATE`
- Date: `2026-07-23`
- Technical ID: `RF-06-01-TOOLCHAIN-AND-DEPENDENCY-BASELINE-AUDIT-20260723`
- Module: `14-runtime-foundation-and-autonomous-integration`
- RF step: `RF-06-01`
- Exact source SHA: `8d502c9baaad5008f79ebc916f9efc3f3378d985`
- Evidence timestamp UTC: `2026-07-23T13:41:08Z`

## Correction notice

- Original publication SHA: `85f520a179d6399337c94cb3a8a4e5bd46c1c664`.
- Original candidate: `uv 0.11.8`.
- Verdict: `REJECTED_STALE_CANDIDATE`.
- Corrective Technical ID: `RF-06-01-CORRECTIVE-01-UV-CANDIDATE-FRESHNESS-20260723`.
- Corrective evidence: [`TOOLCHAIN_AND_DEPENDENCY_BASELINE_CORRECTION_v1.0.md`](TOOLCHAIN_AND_DEPENDENCY_BASELINE_CORRECTION_v1.0.md).
- The authoritative uv candidate is taken from the corrective artifact, not from the historical value below.
- RF-06-01 remains pending independent acceptance; installation of CPython, uv or packages is not permitted.

## Purpose and non-goals

This document is a read-only baseline of the current Python host toolchain, committed project metadata, lock surface, Module 14 dependency gap, and official candidates for a later deterministic RF-06 bootstrap.

This task did not install CPython, uv, packages or a virtual environment; did not run `uv sync`; did not modify `pyproject.toml` or `uv.lock`; did not create runtime resources; and did not start the runtime. RF-07 and all later runtime tasks remain outside this iteration.

## RF-05 prerequisite acceptance

RF-05 is independently accepted at `8d502c9baaad5008f79ebc916f9efc3f3378d985`. The accepted environment allocation is `RUNTIME_ELIGIBLE`; runtime implementation/startup is absent and the production verdict remains `NOT_PRODUCTION_READY`. RF-06-01 is published for independent acceptance. RF-07 remains blocked.

## Evidence provenance

- Fresh `git fetch origin main` and exact-base worktree inspection.
- Repository evidence read from the accepted Module 14 RF-05 artifacts and governance surfaces.
- Host checks were read-only and did not inspect secrets, auth files, private keys, hostname, public IP or secret values.
- Official upstream release metadata was read only from Python.org and the official astral-sh/uv GitHub release.

## Current host toolchain

The PATH exposes one Python implementation through three names, all resolving to the same executable:

| PATH name | executable | implementation/version | architecture | SOABI | GIL classification |
|---|---|---|---|---|---|
| `python` | `/usr/bin/python` -> `/usr/bin/python3.12` | CPython 3.12.3 | x86_64, 64-bit | `cpython-312-x86_64-linux-gnu` | standard GIL build; `Py_GIL_DISABLED=None`; `sys.abiflags=''` |
| `python3` | `/usr/bin/python3` -> `/usr/bin/python3.12` | CPython 3.12.3 | x86_64, 64-bit | `cpython-312-x86_64-linux-gnu` | standard GIL build; `Py_GIL_DISABLED=None`; `sys.abiflags=''` |
| `python3.12` | `/usr/bin/python3.12` | CPython 3.12.3 | x86_64, 64-bit | `cpython-312-x86_64-linux-gnu` | standard GIL build; `Py_GIL_DISABLED=None`; `sys.abiflags=''` |

Capability evidence for the available CPython: `venv` module available; bundled pip module `26.0.1` available as `python -m pip`, but no `pip` or `pip3` executable is in PATH; SSL is OpenSSL `3.0.13`; SQLite is `3.45.1` and is only a technical capability, not an authoritative runtime store; platform tag is `linux-x86_64`. CPython 3.14 is absent. The externally-managed marker `/usr/lib/python3.12/EXTERNALLY-MANAGED` is present.

No `uv`, `pipx`, `python3.13` or `python3.14` executable is in PATH. Relevant safe environment metadata exposed only `PATH`, `LANG`, `LC_ALL` and `LC_CTYPE`; no secret values were recorded. Git is `2.43.0`, OpenSSL is `3.0.13`, and curl is `8.5.0`. The project filesystem is on an ext4 root mount with `rw,relatime,quota,usrquota,grpquota`; the recorded project-owned runtime boundaries are available for a future task, but this task performed no writes there.

## Current pyproject.toml inventory

- Build system: `setuptools>=75`, `wheel`; backend `setuptools.build_meta`.
- Project: `mayak` version `0.0.0`; `requires-python = ">=3.14,<3.15"`.
- Direct runtime declarations: `pydantic>=2.11,<3`; `pydantic-settings>=2.7,<3`.
- Optional dependencies: none.
- Dependency group: `dev` declares `coverage>=7.6,<8`, `import-linter>=2.9,<3`, `mypy>=1.14,<2`, `pytest>=8.3,<9`, `pytest-asyncio>=0.25,<1`, and `ruff>=0.9,<1`.
- Package discovery: setuptools package-dir `src`, find packages under `src`, package data includes `mayak/py.typed`.
- Pytest: `tests` test path and `src` python path.
- Ruff: target `py314`, line length 100, rules `E`, `F`, `I`.
- Mypy: Python 3.14, `src` path, `src` and `tests` files, strictness settings as committed.
- Import-linter: three forbidden-module contracts covering platform/contracts isolation, module isolation, and external/persistence freedom of public contracts.
- Coverage settings: no `[tool.coverage]` table is declared.
- Scripts/entry points: none declared.
- Markers/platform constraints: no pytest markers or dependency platform constraints are declared in `pyproject.toml`; the Python version references are `>=3.14,<3.15`, Ruff `py314`, and mypy `3.14`.
- All declarations are ranged pins, not exact pins. Exact resolution is in the lock.

## Current uv.lock inventory

The lock has format `version = 1`, `revision = 3`, and `requires-python = "==3.14.*"`. It contains 27 package records, one resolution, one editable local package record (`mayak`), and registry sources only at `https://pypi.org/simple`. The lock root reproduces the two runtime requirements and the six `dev` requirements from `pyproject.toml`. All registry package records have sdist and wheel artifact records with SHA-256 hashes; the editable local record has no artifact because it is the project itself.

Exact locked package versions are: `pydantic 2.13.4`, `pydantic-settings 2.14.2`, `coverage 7.15.0`, `import-linter 2.13`, `mypy 1.20.2`, `pytest 8.4.2`, `pytest-asyncio 0.26.0`, `ruff 0.15.20`, plus 18 transitive packages (`annotated-types 0.7.0`, `click 8.4.2`, `colorama 0.4.6`, `grimp 3.15`, `iniconfig 2.3.0`, `librt 0.12.0`, `markdown-it-py 4.2.0`, `mdurl 0.1.2`, `mypy-extensions 1.1.0`, `packaging 26.2`, `pathspec 1.1.1`, `pluggy 1.6.0`, `pydantic-core 2.46.4`, `pygments 2.20.0`, `python-dotenv 1.2.2`, `rich 15.0.0`, `typing-extensions 4.16.0`, and `typing-inspection 0.4.2`).

No yanked package marker, URL/git/path dependency, custom index, or multiple resolution environment was found. The lock is structurally compatible with CPython 3.14 standard-GIL Linux x86_64: it declares exactly 3.14, and its artifact set includes `cp314-cp314` Linux x86_64 wheels where packages publish platform wheels; executable verification with the selected interpreter and uv is still required. Structural parsing was performed with CPython 3.12 `tomllib`; uv executable verification was not possible because uv is absent.

## SHA-256 evidence

| file | SHA-256 before | SHA-256 after |
|---|---|---|
| `pyproject.toml` | `d443407018e618613f606aedfd532048cbf47ab29c1f0f5263bc639e5f55ece9` | `d443407018e618613f606aedfd532048cbf47ab29c1f0f5263bc639e5f55ece9` |
| `uv.lock` | `24e0612d06957ef1452f317878f6c6dc354dafc202ff1607ee3f23e348271577` | `24e0612d06957ef1452f317878f6c6dc354dafc202ff1607ee3f23e348271577` |

## Python requirement consistency

The project requirement `>=3.14,<3.15` and lock requirement `==3.14.*` are consistent. The host requirement is not satisfied because only CPython 3.12.3 is available. This is a proven toolchain gap, not a dependency inconsistency; neither file is changed in RF-06-01.

## Dependency gap matrix

`PRESENT_AND_LOCKED` means direct or declared development dependency and exact lock record are both present. `MISSING` means absent from both the project declaration and lock, unless noted otherwise. Compatibility status is based on official package artifacts present in the lock and source metadata only; executable verification is a later gate.

| component | required capability | declaration / lock | relation and exact version | Python 3.14 / standard-GIL Linux x86_64 evidence | status | future RF-06 action |
|---|---|---|---|---|---|---|
| FastAPI | ASGI API framework | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Uvicorn | ASGI server | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Pydantic v2 | typed models/validation | direct / locked | direct; `2.13.4` | lock has cp314-compatible project dependency graph; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| pydantic-settings | typed settings boundary | direct / locked | direct; `2.14.2` | lock has cp314-compatible project dependency graph; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| HTTPX | HTTP client boundary | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| SQLAlchemy 2.x | ORM/persistence boundary | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Psycopg 3.x | PostgreSQL driver | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Alembic | migration engine | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Jinja2 | server-rendered Web/Admin templates | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| OpenTelemetry API/SDK | telemetry API/SDK boundary | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| pytest | test runner | dev direct / locked | dev direct; `8.4.2` | lock contains cp314 pure-Python artifact; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| pytest-asyncio | async test integration | dev direct / locked | dev direct; `0.26.0` | lock contains cp314-compatible pure-Python artifact; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| RESpx | HTTP mocking | absent / absent | none | unproven | MISSING | later dependency decision and lock update |
| Ruff | lint/format tool | dev direct / locked | dev direct; `0.15.20` | lock publishes cp314 Linux x86_64 wheel; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| mypy | static typing | dev direct / locked | dev direct; `1.20.2` | lock publishes cp314-compatible artifact; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| import-linter | architecture import contracts | dev direct / locked | dev direct; `2.13` | lock publishes cp314-compatible artifact; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |
| coverage.py | coverage measurement | dev direct / locked | dev direct; `7.15.0` | lock publishes cp314 Linux x86_64 wheel; executable proof pending | PRESENT_AND_LOCKED | verify in clean-room bootstrap |

No listed component is merely transitive-only in the current lock for the target scope. The current lock is a baseline for the existing skeleton, not proof of the complete Module 14 runtime surface. Dependency installation and resolution are not started here and are not RF-07 CI work.

## Explicit out-of-scope dependencies/toolchains

Redis, Celery, RabbitMQ, Kafka and external brokers are `OUT_OF_SCOPE` under accepted Module 14 decisions. Node/npm, SPA frameworks and a separate frontend build toolchain are `OUT_OF_SCOPE`; the accepted Web Cabinet uses server-rendered FastAPI/Jinja2/local CSS/minimal vanilla JavaScript. No package is added merely because it is popular.

## CPython 3.14 exact candidate

Candidate: CPython `3.14.6`, stable standard-GIL Linux x86_64 build, release date `2026-06-10`. The candidate is the latest stable 3.14 maintenance release in the official Python release listing at evidence time. The future build must use the normal CPython build (no `--disable-gil`), yielding expected ABI `cpython-314-x86_64-linux-gnu` and empty `sys.abiflags`; this is a candidate rationale, not an installed-runtime claim. Free-threaded-only, debug, alpha, beta and release-candidate artifacts are excluded.

Python.org does not publish a Linux x86_64 installer for this release; the official source candidate is the gzipped source tarball. Future RF-06 execution must obtain the exact source artifact, verify SHA-256 and Sigstore evidence, build inside `/opt/avito-mayak-runtime/toolchain`, and prove standard-GIL metadata before use. No source or executable artifact was downloaded in RF-06-01.

## uv exact candidate (historical publication retained)

Historical candidate: ~~uv `0.11.8`~~ — superseded and rejected as stale by the corrective chain. Its historical release date was `2026-04-27`; it must not be installed. Corrected authoritative candidate: uv `0.11.31`, as proven by the corrective artifact. Official Linux x86_64 artifact family remains `uv-x86_64-unknown-linux-gnu.tar.gz`; the artifact is a standalone GNU/Linux x86_64 binary archive and does not replace CPython.

## Official source/checksum evidence

- CPython release: <https://www.python.org/downloads/release/python-3146/>. The official page identifies 3.14.6 as the sixth maintenance release, stable, dated 2026-06-10, and publishes source artifact SHA-256 and Sigstore links. Gzipped source SHA-256: `74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222`.
- uv historical release: <https://github.com/astral-sh/uv/releases/tag/0.11.8>. It remains historical evidence only and is rejected as stale.
- uv authoritative corrective release: <https://github.com/astral-sh/uv/releases/tag/0.11.31>; exact release/API, asset digest, checksum and attestation evidence are in the corrective artifact.

## Proposed project-owned installation boundaries

- Toolchain root: `/opt/avito-mayak-runtime/toolchain`.
- Exact CPython prefix: `/opt/avito-mayak-runtime/toolchain/cpython/3.14.6`.
- Exact uv prefix for a later separately authorized task: `/opt/avito-mayak-runtime/toolchain/uv/0.11.31`.
- Project cache/data: project-owned paths under `/var/lib/avito-mayak` or a separately approved project-owned cache path; never a foreign home/cache.
- Source and lock verification: dedicated repository worktree only; no source or lock writes.
- Project virtual environment: a later task may create an exact project-owned environment under `/opt/avito-mayak-runtime`, separate from the tool binaries. No environment is created here.

## Proposed deterministic bootstrap sequence

1. Re-fetch `origin/main` and require the exact accepted base and a clean dedicated worktree.
2. Obtain only the pinned CPython 3.14.6 source and corrected uv 0.11.31 x86_64 GNU/Linux artifact from the official sources; verify SHA-256 and the published Sigstore/attestation mechanism before execution.
3. Build/install CPython under the project-owned prefix with standard GIL, without changing `/usr/bin/python3`, system Python, global shell profiles or foreign caches.
4. Install uv at the exact pinned project-owned path, verify its version and checksum provenance, and bind it to the exact CPython executable.
5. Prove `sys.implementation`, `SOABI`, empty `sys.abiflags`, standard-GIL classification, SSL, platform tags and project-owned write boundary.
6. In a clean-room, project-owned virtual environment, run only the later task's explicitly authorized locked verification; do not resolve or alter dependencies until that task authorizes it.
7. Verify `uv.lock` without rewriting it, then run the authorized package/static checks and record results. Do not begin RF-07 CI or runtime assembly.

## Rollback design

Before any future installation, snapshot only the project-owned toolchain directory and task-owned metadata with mode `0700/0600`, record exact hashes and the base SHA, and prove restoration. Rollback removes only the new CPython/uv prefixes and project-owned virtual environment/cache created by that task; it does not touch `/usr/bin/python3`, repository files, foreign resources, system configuration or secrets. RF-06-01 itself has a repository backup under `/tmp` and has made no host installation changes.

## Security/supply-chain considerations

No curl-to-shell, unpinned installer, package install, executable download or executable execution was used. Future bootstrap must use exact URLs, pinned versions, SHA-256 verification and Python Sigstore / uv GitHub attestation evidence; no custom index, URL/git/path dependency or secret-bearing environment value is allowed. The externally-managed marker prohibits treating system pip as an installation boundary. Artifact execution must occur only after verification and only within the project-owned boundary.

## Evidence still requiring executable verification

The following remain later executable gates: CPython 3.14.6 standard-GIL build proof; corrected uv 0.11.31 version and artifact proof; clean-room `uv` lock verification; package installation and import checks for all later-added runtime dependencies; wheel selection on this host; static/architecture/test/coverage checks; and project-owned write/rollback proof. RF-06-01 does not claim any of these.

## Current verdict

- `RF06_BASELINE_DEFINED`
- toolchain not installed;
- dependencies not changed;
- runtime not deployed;
- `RUNTIME_ELIGIBLE` applies to the accepted environment allocation;
- `NOT_PRODUCTION_READY`;
- `PRODUCTION_READY` is not claimed.

## Next gate

Independent ChatGPT acceptance is required. Only after acceptance may RF-06-02 proceed. RF-07 remains blocked, and the Module 14 final status can become `READY_FOR_OPERATOR_ACCEPTANCE` only after RF-30.
