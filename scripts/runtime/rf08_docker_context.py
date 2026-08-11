# ruff: noqa: E501
"""Docker-native build-context evidence for RF-08.

The helper deliberately asks BuildKit to perform COPY resolution.  It is not
an implementation of Docker's ignore-file grammar.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Final

from scripts.ci.verify_security_supply_chain import detect_findings
from scripts.runtime.rf08_docker_authority import (
    GatewayAuthority,
    ImageAction,
    ImageOperation,
    PathCapability,
    PathCapabilityKind,
)

COPY_PLAN: Final[tuple[tuple[str, str], ...]] = (
    ("pyproject.toml", "pyproject.toml"),
    ("uv.lock", "uv.lock"),
    ("README.md", "README.md"),
    ("src", "src"),
    ("scripts/runtime/run_rf12_postgres_acceptance.py", "scripts/runtime/run_rf12_postgres_acceptance.py"),
    ("scripts/runtime/verify_rf12_acceptance.py", "scripts/runtime/verify_rf12_acceptance.py"),
    ("scripts/runtime/rf26_operability.py", "scripts/runtime/rf26_operability.py"),
    ("alembic.ini", "alembic.ini"),
    ("alembic", "alembic"),
)
SCHEMA_VERSION: Final = "rf08-docker-native-context-v2"


def _reject_classified_input(path: Path, data: bytes) -> None:
    if path.name in {".env", "id_rsa", "id_ed25519"} or path.suffix.lower() in {".pem", ".key"}:
        raise ValueError("classified secret build input")
    if detect_findings(path.as_posix(), data):
        raise ValueError("classified secret build input")


def dockerfile_copy_contract(dockerfile: Path) -> tuple[tuple[str, str], ...]:
    """Read the bounded, single-source COPY syntax used by this Dockerfile."""
    rows: list[tuple[str, str]] = []
    for raw in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("COPY "):
            parts = line.split()[1:]
            if len(parts) < 2:
                raise ValueError("unsupported Docker COPY syntax")
            sources, destination = parts[:-1], parts[-1]
            if any(source.startswith("--") for source in sources) or any(
                ch in "".join(parts) for ch in "{}$"
            ):
                raise ValueError("unsupported Docker COPY syntax")
            if destination.startswith("/"):
                raise ValueError("absolute Docker COPY path")
            for source in sources:
                if source.startswith("/"):
                    raise ValueError("absolute Docker COPY path")
                target = (
                    source
                    if destination in {".", "./"}
                    else destination.removeprefix("./").rstrip("/")
                )
                rows.append((source, target))
    return tuple(rows)


def validate_copy_contract(dockerfile: Path) -> tuple[tuple[str, str], ...]:
    actual = dockerfile_copy_contract(dockerfile)
    if actual != COPY_PLAN:
        raise ValueError("Dockerfile COPY contract diverges from authoritative COPY_PLAN")
    if len({source for source, _ in actual}) != len(actual):
        raise ValueError("duplicate Docker COPY source")
    return actual


def validate_copy_root(
    root: Path,
    expected_files: set[str],
    *,
    tracked_files: set[str] | None = None,
) -> tuple[str, ...]:
    """Fail closed on missing, extra, unsafe, or classified build inputs."""
    root = root.resolve()
    observed: set[str] = set()
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            if path.is_symlink() or not path.is_dir():
                raise ValueError("unsafe build input")
            continue
        if path.is_file():
            observed.add(rel)
            data = path.read_bytes()
            _reject_classified_input(path, data)
    if tracked_files is not None and observed - tracked_files:
        raise ValueError("unexpected untracked build input")
    if observed != expected_files:
        raise ValueError("build input completeness mismatch")
    return tuple(sorted(observed))


def _safe_relative(path: str) -> str:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or "" in p.parts:
        raise ValueError("unsafe context path")
    return p.as_posix()


def _git_command(repo: Path, *arguments: str) -> list[str]:
    """Build a Git command with exact, command-local repository trust."""
    resolved_repo = repo.resolve()
    return [
        "git",
        "-c",
        f"safe.directory={resolved_repo}",
        "-C",
        str(resolved_repo),
        *arguments,
    ]


def materialize_clean_context(repo: Path, destination: Path, run_id: str) -> dict[str, str]:
    """Export the exact clean candidate Git tree and return safe identities."""
    repo = repo.resolve()
    destination = destination.resolve()
    if destination == Path("/") or destination in destination.parents:
        raise ValueError("invalid context destination")
    source = destination / run_id / "source"
    if source.exists():
        raise ValueError("context already exists")
    source.parent.mkdir(mode=0o700, parents=True)
    source.parent.chmod(0o700)
    validate_copy_contract(repo / "Dockerfile")
    archive = source.parent / "source.tar"
    env = {
        "PATH": os.environ.get("PATH", ""),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    source_sha = subprocess.check_output(
        _git_command(repo, "rev-parse", "HEAD"),
        text=True,
        env=env,
    ).strip()
    tree = subprocess.check_output(
        _git_command(repo, "rev-parse", "HEAD^{tree}"),
        text=True,
        env=env,
    ).strip()
    with archive.open("wb") as stream:
        subprocess.run(
            _git_command(repo, "archive", "--format=tar", "HEAD"),
            stdout=stream,
            stderr=subprocess.DEVNULL,
            check=True,
            env=env,
        )
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    source.mkdir(mode=0o700)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            relative = _safe_relative(member.name)
            target = source / relative
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise ValueError("unsafe archive entry")
            if member.isdir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    raise ValueError("missing archive member")
                with src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                target.chmod(member.mode & 0o777)
            else:
                raise ValueError("unsupported archive entry")
    archive.unlink()
    # The finalization worktree may contain the not-yet-committed RF-08
    # correction. Overlay only the exact Docker COPY inputs; authority and
    # evidence scripts can never enter the application image context.
    overlay = ("Dockerfile", ".dockerignore", *tuple(item[0] for item in COPY_PLAN))
    for relative in overlay:
        source_path = repo / relative
        target_path = source / relative
        if source_path.is_symlink():
            raise ValueError("build input contains symlink")
        if source_path.is_dir():
            shutil.copytree(source_path, target_path, symlinks=False, dirs_exist_ok=True)
        elif source_path.is_file():
            target_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
        else:
            raise ValueError("missing build input")
    # The archive is the source authority; this second check proves that the
    # materialized context contains exactly the tracked regular files consumed
    # by directory COPY roots and no untracked additions.
    for root_name in ("src", "alembic"):
        tracked = {
            name.removeprefix(f"{root_name}/")
            for name in subprocess.check_output(
                _git_command(repo, "ls-files", "--", root_name), text=True, env=env
            ).splitlines()
            if name.startswith(f"{root_name}/")
        }
        validate_copy_root(source / root_name, tracked, tracked_files=tracked)
    for relative, _destination in COPY_PLAN:
        if relative in {"src", "alembic"}:
            continue
        path = source / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError("individual Docker COPY input is not a regular file")
        _reject_classified_input(path, path.read_bytes())
    return {
        "candidate_source_sha": source_sha,
        "candidate_tree_identity": tree,
        "archive_sha256": archive_hash,
    }


def _inspector_file(root: Path) -> Path:
    path = root / "rf08-docker-native-inspector.Dockerfile"
    path.write_text(
        "FROM scratch\n"
        "COPY pyproject.toml uv.lock README.md /effective/\n"
        "COPY src /effective/src\n"
        "COPY alembic.ini /effective/alembic.ini\n"
        "COPY alembic /effective/alembic\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


def docker_native_manifest(
    context: Path, runtime_root: Path, run_id: str, *, gateway: GatewayAuthority
) -> tuple[tuple[dict[str, str], ...], dict[str, str]]:
    """Materialize COPY output using BuildKit local output and hash files."""
    run_root = runtime_root / run_id
    output = run_root / "docker-native-output"
    inspector = _inspector_file(run_root)
    output.mkdir(mode=0o700, parents=True)
    capability = gateway.issue(
        ImageAction(
            operation=ImageOperation.BUILDX_MANIFEST,
            context=PathCapability.from_path(
                context, kind=PathCapabilityKind.DIRECTORY, require_exists=True
            ),
            dockerfile=PathCapability.from_path(
                inspector, kind=PathCapabilityKind.FILE, require_exists=True
            ),
            output=PathCapability.from_path(
                output, kind=PathCapabilityKind.DIRECTORY, require_exists=False
            ),
        ),
        stage="docker-native-manifest",
    )
    gateway.execute(
        capability,
        stage="docker-native-manifest",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=180,
    )
    rows: list[dict[str, str]] = []
    effective = output / "effective"
    if not effective.is_dir():
        raise ValueError("Docker inspector did not export effective root")
    for path in sorted(effective.rglob("*")):
        if path.is_symlink() or not path.is_file():
            if path.is_symlink():
                raise ValueError("Docker output contains symlink")
            continue
        relative = _safe_relative(path.relative_to(effective).as_posix())
        rows.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = tuple(sorted(rows, key=lambda item: item["path"]))
    if tuple(x["path"] for x in manifest) != tuple(sorted({x["path"] for x in manifest})):
        raise ValueError("manifest is not sorted and unique")
    export_identity = {
        "inspector_sha256": hashlib.sha256(inspector.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(canonical_manifest(manifest)).hexdigest(),
    }
    return manifest, export_identity


def canonical_manifest(manifest: tuple[dict[str, str], ...] | list[dict[str, str]]) -> bytes:
    return json.dumps(
        list(manifest), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode()


def build_input_digest(
    context: Path,
    manifest: tuple[dict[str, str], ...] | list[dict[str, str]],
    candidate_tree_identity: str,
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "candidate_tree_identity": candidate_tree_identity,
        "dockerfile_sha256": hashlib.sha256((context / "Dockerfile").read_bytes()).hexdigest(),
        "dockerignore_sha256": hashlib.sha256((context / ".dockerignore").read_bytes()).hexdigest(),
        "normalized_copy_plan": [{"source": a, "destination": b} for a, b in COPY_PLAN],
        "effective_file_manifest": list(manifest),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
