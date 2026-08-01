from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runtime.rf08_verify_structural_gateway import SCHEMA_VERSION, verify_source


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "source",
    [
        "from scripts.runtime.rf08_docker_authority import _ReadOnlyDockerQuery\n",
        "from scripts.runtime.rf08_docker_authority import classify_docker_command_class\n",
        "class RenamedRawPlan:\n    argv: tuple[str, ...]\n",
        "class _RawBase:\n    pass\nclass Public(_RawBase):\n    pass\n",
        "def run(command: list[str]):\n    return command\n",
        "def run(*, extra_args: list[str]):\n    return extra_args\n",
        "import subprocess\nsubprocess.run(('docker','ps','-aq'))\n",
        (
            "import subprocess\nsubprocess.run(('docker','ps','-aq'))\n"
            "subprocess.run(('docker','network','ls','-q'))\n"
        ),
        "import subprocess\nreturn subprocess.CompletedProcess(('docker',), 0)\n",
        "class Store:\n    command_tokens: tuple[str, ...]\n",
    ],
)
def test_structural_verifier_rejects_malicious_shapes(tmp_path: Path, source: str) -> None:
    _write(tmp_path, "bad.py", source)
    payload = verify_source(tmp_path)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["finding_count"] > 0


def test_structural_verifier_accepts_minimal_semantic_source(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "good.py",
        "from dataclasses import dataclass\n\n"
        "@dataclass(frozen=True)\n"
        "class Action:\n"
        "    value: str\n\n"
        "def build(action: Action) -> str:\n"
        "    return action.value\n",
    )
    payload = verify_source(tmp_path)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["finding_count"] == 0
