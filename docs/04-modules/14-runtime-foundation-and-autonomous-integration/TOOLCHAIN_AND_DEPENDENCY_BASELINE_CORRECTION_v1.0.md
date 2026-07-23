# Toolchain and Dependency Baseline Correction v1.0

## Metadata

- Version: `1.0`
- Status: `APPROVED_CORRECTIVE_CANDIDATE`
- Date: `2026-07-23`
- Technical ID: `RF-06-01-CORRECTIVE-01-UV-CANDIDATE-FRESHNESS-20260723`
- Exact source SHA: `85f520a179d6399337c94cb3a8a4e5bd46c1c664`
- Evidence timestamp UTC: `2026-07-23T13:57:27Z`
- Scope: RF-06-01 candidate freshness correction only; no bootstrap or dependency mutation.

## Independent rejection basis

The original RF-06-01 publication selected uv `0.11.8` although the authoritative official uv release surface already exposed stable `0.11.31`. The original value therefore fails the requirement to select the current latest stable release and is rejected as stale. RF-06-01 remains pending independent acceptance.

## Original incorrect object

- Original incorrect object: uv exact candidate `0.11.8`.
- Original publication: `85f520a179d6399337c94cb3a8a4e5bd46c1c664`.
- Original release date: `2026-04-27`.
- Required behavior: select the current latest stable uv release at execution time, then verify the exact Linux x86_64 GNU artifact and public integrity evidence.

## Five-transition root-cause trace

### Transition-01-Input

Input: the original requirement was to select the current latest stable uv release at execution time.

### Transition-02-Metadata-Retrieval

The corrective execution queried `GET https://api.github.com/repos/astral-sh/uv/releases/latest` at `2026-07-23T13:55:01Z` UTC; HTTP `200`. It returned tag/name `0.11.31`, release ID `357733488`, created `2026-07-22T00:46:37Z`, published `2026-07-22T01:49:40Z`, `draft=false`, `prerelease=false`, target commit `b7fdec626cdafcfb0d0db54d39d3d5f114aefb5c`. A pagination-aware `GET https://api.github.com/repos/astral-sh/uv/releases?per_page=100&page=1` also returned HTTP `200` and a `rel="next"` link; its newest stable sequence began `0.11.31, 0.11.30, 0.11.29, ...` and included `0.11.8`.

### Transition-03-Candidate-Filtering

The deterministic filter is: retain only releases with `draft == false` and `prerelease == false`; require an exact asset named `uv-x86_64-unknown-linux-gnu.tar.gz` plus a checksum asset; exclude all non-Linux, non-x86_64, non-GNU, draft and prerelease entries. The corrective latest release passes these filters. The original artifact does not preserve the input response or filtering implementation.

### Transition-04-Selection-Mechanism

The original baseline records only the selected value `0.11.8` and its release evidence; it does not preserve an exact selection function, command, complete API response, pagination handling or sorting rule. Therefore the mechanism that transformed the filtered metadata into `0.11.8` cannot be proven from repository evidence.

### Transition-05-Incorrect-Output

Output: uv `0.11.8`, published `2026-04-27`, with its historical release/checksum evidence. At the same corrective execution timestamp, the authoritative latest stable was `0.11.31`, published `2026-07-22`; the official stable list contains `0.11.9` through `0.11.31` after `0.11.8` (23 superseding stable patch releases).

## Root-cause verdict

`ROOT_CAUSE_NOT_FULLY_PROVEN`: stale candidate selection is proven, but the exact original selection mechanism is not preserved. No narrower mechanism is asserted.

## Official release endpoint evidence

- Latest endpoint: <https://api.github.com/repos/astral-sh/uv/releases/latest>.
- Release list: <https://api.github.com/repos/astral-sh/uv/releases?per_page=100&page=1>; pagination exposed a next page, and page 1 contained the complete newest range through the historical value.
- Release surface: <https://github.com/astral-sh/uv/releases>.
- Exact tag: <https://github.com/astral-sh/uv/releases/tag/0.11.31>.
- Corrective evidence was obtained by HTTPS GET from official GitHub/astral resources only.

## Latest stable uv release

The corrected candidate is uv `0.11.31`. API metadata says tag/name `0.11.31`, release ID `357733488`, created `2026-07-22T00:46:37Z`, published `2026-07-22T01:49:40Z`, `draft=false`, `prerelease=false`, target commit `b7fdec626cdafcfb0d0db54d39d3d5f114aefb5c`. The release JSON has `immutable=true`.

## Release freshness comparison

| value | official release date | result |
|---|---|---|
| historical uv `0.11.8` | `2026-04-27` | `REJECTED_STALE_CANDIDATE` |
| corrected uv `0.11.31` | `2026-07-22` API published timestamp | latest stable at evidence time |

The stable range in the paginated official list explicitly shows `0.11.9` through `0.11.31` after `0.11.8`: 23 superseding stable patch releases.

## Exact Linux x86_64 GNU asset

- Asset: `uv-x86_64-unknown-linux-gnu.tar.gz`.
- Official release asset URL: <https://github.com/astral-sh/uv/releases/download/0.11.31/uv-x86_64-unknown-linux-gnu.tar.gz>.
- Official checksum asset URL: <https://github.com/astral-sh/uv/releases/download/0.11.31/uv-x86_64-unknown-linux-gnu.tar.gz.sha256>.
- GitHub API asset size: `26181465` bytes.
- `dist-manifest.json` names the target `x86_64-unknown-linux-gnu`, the archive and its checksum, and records executable entries `uv` and `uvx`; the archive was not downloaded or unpacked.

## Public checksum evidence

- Per-asset SHA-256: `8cc1cd82d434ec565376f98bd938d4b715b5791a80ff2d3aa78821cf85091b4b`.
- Aggregate `sha256.sum` contains the exact filename and the same 64-hex digest.
- Per-asset `.sha256` contains the exact filename and the same 64-hex digest.
- GitHub API asset digest: `sha256:8cc1cd82d434ec565376f98bd938d4b715b5791a80ff2d3aa78821cf85091b4b`.
- No executable archive was downloaded; only small text/JSON metadata was fetched.

## Attestation and verification mechanism

GitHub’s official repository attestation endpoint for the digest, `GET https://api.github.com/repos/astral-sh/uv/attestations/sha256:8cc1cd82d434ec565376f98bd938d4b715b5791a80ff2d3aa78821cf85091b4b`, returned HTTP `200` with two public attestation records. The release target commit API reports `verification.verified=true`, reason `valid`, with verification timestamp `2026-07-22T00:46:38Z`. No signed bundle URL or token is reproduced here. Release JSON reports `immutable=true`; these are the recorded immutability and verification mechanisms.

## CPython candidate revalidation

The official Python.org source listing at <https://www.python.org/downloads/source/> identifies Python `3.14.6` as the latest Python 3 release and the latest stable `3.14.x` at evidence time. The exact release page is <https://www.python.org/downloads/release/python-3146/> and identifies the stable release date as `2026-06-10`; no newer stable 3.14.x entry is listed. The official source names are `Python-3.14.6.tgz` and `Python-3.14.6.tar.xz`.

- Confirmed candidate: CPython `3.14.6`.
- Selected source checksum (`Python-3.14.6.tgz`): `74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222`.
- XZ source checksum (`Python-3.14.6.tar.xz`): `143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63`.
- Python.org provides `.sigstore` metadata and SPDX `.spdx.json` SBOM links for both source tarballs; the selected gzip Sigstore and SPDX metadata were fetched as text/JSON evidence only.
- The normal source build remains compatible with a standard-GIL strategy; no `--disable-gil` build is selected.
- No CPython source archive was downloaded, extracted or executed.

## Corrected authoritative candidate matrix

| component | historical candidate | corrected authoritative candidate | status |
|---|---|---|---|
| uv | `0.11.8` (`2026-04-27`) | `0.11.31` (`2026-07-22` API published) | corrected, pending independent acceptance |
| CPython | `3.14.6` (`2026-06-10`) | `3.14.6` (`2026-06-10`) | confirmed fresh, pending later bootstrap gate |

## Installation remains prohibited

This correction performs no installation, no bootstrap, no `uv sync`, no package installation, no virtualenv creation, no dependency mutation and no runtime deployment. RF-06-02 and RF-07 remain blocked.

## Repository/source hashes unchanged

- `pyproject.toml`: `d443407018e618613f606aedfd532048cbf47ab29c1f0f5263bc639e5f55ece9`.
- `uv.lock`: `24e0612d06957ef1452f317878f6c6dc354dafc202ff1607ee3f23e348271577`.

## Security evidence

Only official HTTPS metadata endpoints were used. No executable artifacts were downloaded or run. No secrets, auth files, cookies, deploy-key contents, private keys, tokens or credentials were read or included. No server, container, network, volume, listener, system configuration, PATH or profile mutation occurred.

## Foreign-resource impact

`NONE`.

## Credentials exposure

`NONE`.

## Corrective verdict

`RF06_BASELINE_CORRECTED_PENDING_INDEPENDENT_ACCEPTANCE`.

## Next gate

Independent ChatGPT verification is required. RF-06-02 remains blocked; RF-06 is not complete; the module is not `PRODUCTION_READY` and the final module status remains possible only after RF-30.
