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

from scripts.runtime.rf08_docker_authority import MutationAuthority

EXPECTED_BASE_SHA: Final = "b43be0f0f007267126a8eac79248af7d79f344bb"
COPY_PLAN: Final[tuple[tuple[str, str], ...]] = (
    ("pyproject.toml", "pyproject.toml"),
    ("uv.lock", "uv.lock"),
    ("README.md", "README.md"),
    ("src", "src"),
    ("alembic.ini", "alembic.ini"),
    ("alembic", "alembic"),
)
SCHEMA_VERSION: Final = "rf08-docker-native-context-v1"


def _safe_relative(path: str) -> str:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or "" in p.parts:
        raise ValueError("unsafe context path")
    return p.as_posix()


def materialize_clean_context(repo: Path, destination: Path, run_id: str) -> dict[str, str]:
    """Export only the expected-base Git tree and return safe identities."""
    destination = destination.resolve()
    if destination == Path("/") or destination in destination.parents:
        raise ValueError("invalid context destination")
    source = destination / run_id / "source"
    if source.exists():
        raise ValueError("context already exists")
    source.parent.mkdir(mode=0o700, parents=True)
    source.parent.chmod(0o700)
    archive = source.parent / "source.tar"
    env = {"PATH": os.environ.get("PATH", "")}
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", f"{EXPECTED_BASE_SHA}^{{tree}}"],
        text=True,
        env=env,
    ).strip()
    with archive.open("wb") as stream:
        subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", EXPECTED_BASE_SHA],
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
    return {"source_sha": EXPECTED_BASE_SHA, "tree_identity": tree, "archive_sha256": archive_hash}


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
    context: Path, runtime_root: Path, run_id: str, *, gateway: MutationAuthority
) -> tuple[tuple[dict[str, str], ...], dict[str, str]]:
    """Materialize COPY output using BuildKit local output and hash files."""
    run_root = runtime_root / run_id
    output = run_root / "docker-native-output"
    inspector = _inspector_file(run_root)
    output.mkdir(mode=0o700, parents=True)
    capability = gateway.issue_buildx_manifest(
        stage="docker-native-manifest",
        context=str(context),
        dockerfile=str(inspector),
        output=str(output),
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
    context: Path, manifest: tuple[dict[str, str], ...] | list[dict[str, str]], tree_identity: str
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "expected_base_tree_identity": tree_identity,
        "dockerfile_sha256": hashlib.sha256((context / "Dockerfile").read_bytes()).hexdigest(),
        "dockerignore_sha256": hashlib.sha256((context / ".dockerignore").read_bytes()).hexdigest(),
        "normalized_copy_plan": [{"source": a, "destination": b} for a, b in COPY_PLAN],
        "effective_file_manifest": list(manifest),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
