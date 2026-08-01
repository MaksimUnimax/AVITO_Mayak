from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.runtime.rf08_verify_structural_gateway import SCHEMA_VERSION, verify_source


def _verify(tmp_path: Path, source: str) -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "fixture.py").write_text(source, encoding="utf-8")
    return verify_source(tmp_path)


BAD = [
    # Local spelling is intentionally innocuous and must not affect verdict.
    "import subprocess\ncmd = ('docker', 'ps', '-q')\nsubprocess.run(cmd)\n",
    "import subprocess\nparcel = ('docker', 'ps', '-q')\nsubprocess.run(parcel)\n",
    "from subprocess import run as launch\nlaunch(('docker', 'ps', '-q'))\n",
    "import subprocess as engine\nengine.run(('docker', 'ps', '-q'))\n",
    (
        "import subprocess\nfrom subprocess import run as launch\n"
        "proxy = launch\nproxy(('docker', 'ps', '-q'))\n"
    ),
    (
        "import subprocess\n\ndef relay(value: tuple[str, ...]):\n"
        "    return value\nrelay(('docker', 'ps', '-q'))\n"
        "subprocess.run(relay(('docker', 'ps', '-q')))\n"
    ),
    (
        "import subprocess\nfrom dataclasses import dataclass\n"
        "@dataclass(frozen=True)\nclass Envelope:\n"
        "    payload: tuple[str, ...]\n"
        "item = Envelope(('docker', 'ps', '-q'))\nsubprocess.run(item.payload)\n"
    ),
    (
        "import subprocess\nclass Carrier:\n    @property\n"
        "    def payload(self):\n        return ('docker', 'ps', '-q')\n"
        "subprocess.run(Carrier().payload)\n"
    ),
    (
        "import subprocess\nclass Base: raw: tuple[str, ...]\n"
        "class Derived(Base): pass\nsubprocess.run(Derived().raw)\n"
    ),
    "import subprocess\nbase = ('docker',)\ncmd = base + ('inspect',)\nsubprocess.run(cmd)\n",
    "import subprocess\n\ndef make():\n    return ('docker', 'ps')\nsubprocess.run(make())\n",
    (
        "import subprocess\nsubprocess.run(('docker', 'inspect', '--format', '{}'))\n"
        "subprocess.run(('docker', 'ps'))\n"
    ),
    "import subprocess\nsubprocess.run(('docker', 'inspect'))\n",
    (
        "import subprocess\nclass Query:\n"
        "    def __init__(self, value: str): self.value = value\n"
        "def inspect(value: str): return Query(value)\n"
        "subprocess.run(inspect('docker ps'))\n"
    ),
    (
        "import subprocess\nsubprocess.run(('docker', 'ps'), capture_output=True)\n"
        "return subprocess.CompletedProcess(('docker',), 0)\n"
    ),
    "import subprocess\nsubprocess.run(('docker', 'ps'), shell=True)\n",
    "from scripts.runtime.rf08_docker_authority import gateway_token as renamed\n",
    "from scripts.runtime.rf08_docker_authority import _parse_docker_command as helper\n",
]


@pytest.mark.parametrize("source", BAD)
def test_semantic_bypasses_are_rejected(tmp_path: Path, source: str) -> None:
    payload = _verify(tmp_path, source)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["finding_count"] > 0


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            "import subprocess as x\nvalue = ('docker', 'ps')\nx.run(value)\n",
            "import subprocess as y\nrenamed = ('docker', 'ps')\ny.run(renamed)\n",
        ),
        (
            "from subprocess import run as x\nx(('docker', 'ps'))\n",
            "from subprocess import run as y\ny(('docker', 'ps'))\n",
        ),
    ],
)
def test_renaming_does_not_change_verdict(tmp_path: Path, left: str, right: str) -> None:
    assert _verify(tmp_path / "left", left)["finding_count"] > 0
    assert _verify(tmp_path / "right", right)["finding_count"] > 0


def test_closed_semantic_actions_and_bounded_observations_are_accepted(tmp_path: Path) -> None:
    payload = _verify(
        tmp_path,
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\nclass Action:\n    operation: str\n"
        "def build(action: Action) -> str:\n    return action.operation\n",
    )
    assert payload["finding_count"] == 0


def test_no_transport_is_not_an_acceptance_verdict(tmp_path: Path) -> None:
    payload = _verify(tmp_path, "import subprocess\nsubprocess.run(command)\n")
    assert payload["finding_count"] > 0
    assert any(item["kind"] == "zero-docker-transports" for item in payload["findings"])


def test_production_surface_has_exactly_one_transport() -> None:
    root = Path(__file__).resolve().parents[2]
    payload = verify_source(root)
    assert payload["finding_count"] == 0
    assert payload["docker_transport_count"] == 1
