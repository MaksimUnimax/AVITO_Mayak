from __future__ import annotations

# Fixture source strings intentionally remain readable as one semantic unit.
# ruff: noqa: E501
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


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess\nclass Quiet:\n    def harmless(self): return 7\nclass Relay:\n    def execute(self, value): subprocess.run(value)\nclass Bridge:\n    def pass_value(self): return Relay().execute(Quiet().harmless())\nBridge().pass_value()\n",
        "import subprocess\nclass Alpha:\n    def alpha(self): return 7\nclass Beta:\n    def _execute(self, value): subprocess.run(value)\nclass Gamma:\n    def alpha(self): return Beta()._execute(Alpha().alpha())\nGamma().alpha()\n",
        "import subprocess\nclass First:\n    def _quiet(self): return 7\nclass Second:\n    def execute(self, value): subprocess.run(value)\nclass Third:\n    def _relay(self): return Second().execute(First()._quiet())\nThird()._relay()\n",
    ],
)
def test_reviewer_self_authorization_topology_is_rejected(tmp_path: Path, source: str) -> None:
    payload = _verify(tmp_path, source)
    assert payload["finding_count"] > 0
    assert payload["authorized_docker_transport_count"] == 0


def test_same_spelling_in_distinct_modules_cannot_share_authority(tmp_path: Path) -> None:
    runtime = tmp_path / "scripts" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "a.py").write_text(
        "def build(action: object):\n"
        "    if isinstance(action, object): return ('docker', 'ps')\n"
        "    raise ValueError()\n",
        encoding="utf-8",
    )
    (runtime / "b.py").write_text(
        "import subprocess\n"
        "def build(value): return value\n"
        "subprocess.run(build(('docker', 'ps')))\n",
        encoding="utf-8",
    )
    assert verify_source(tmp_path)["finding_count"] > 0


def test_same_spelling_in_distinct_classes_is_not_authority(tmp_path: Path) -> None:
    payload = _verify(
        tmp_path,
        "import subprocess\n"
        "class Safe:\n"
        "    def execute(self, action: object):\n"
        "        if isinstance(action, object): return ('docker', 'ps')\n"
        "        raise ValueError()\n"
        "class Unsafe:\n"
        "    def execute(self, value): subprocess.run(value)\n"
        "Unsafe().execute(('docker', 'ps'))\n",
    )
    assert payload["finding_count"] > 0


def test_five_safe_callers_plus_external_unsafe_caller_fail_closed(tmp_path: Path) -> None:
    runtime = tmp_path / "scripts" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "wrapper.py").write_text(
        "import subprocess\n"
        "def relay(value): subprocess.run(value)\n"
        "relay(('echo', '1'))\nrelay(('echo', '2'))\nrelay(('echo', '3'))\n"
        "relay(('echo', '4'))\nrelay(('echo', '5'))\n",
        encoding="utf-8",
    )
    (runtime / "external.py").write_text(
        "from scripts.runtime.wrapper import relay\nrelay(('docker', 'ps'))\n",
        encoding="utf-8",
    )
    assert verify_source(tmp_path)["finding_count"] > 0


def test_textual_docker_word_does_not_prove_else_branch(tmp_path: Path) -> None:
    payload = _verify(
        tmp_path,
        "import subprocess\n"
        "value = command\n"
        "if 'docker' in label:\n"
        "    pass\n"
        "else:\n"
        "    subprocess.run(value)\n",
    )
    assert payload["finding_count"] > 0


@pytest.mark.parametrize("field", ["banana", "state", "parcel", "neutral"])
def test_stored_authority_is_field_spelling_independent(tmp_path: Path, field: str) -> None:
    payload = _verify(
        tmp_path,
        "import subprocess\n"
        "class Carrier:\n"
        f"    {field}: tuple[str, ...]\n"
        f"item = Carrier(('docker', 'ps'))\nsubprocess.run(item.{field})\n",
    )
    assert payload["finding_count"] > 0
