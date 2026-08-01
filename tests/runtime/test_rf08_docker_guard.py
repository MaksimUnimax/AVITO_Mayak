from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.runtime.rf08_docker_authority import (
    GatewayAuthority,
    ObservationRequest,
    ObservationTemplate,
    gateway_token_active,
)


def _completed(stdout: bytes = b"", stderr: bytes = b"") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr=stderr)


def test_gateway_token_is_active_only_during_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[bool] = []

    def fake_run(*args: Any, **kwargs: Any) -> SimpleNamespace:
        seen.append(gateway_token_active())
        return _completed(stdout=b"{}\n")

    monkeypatch.setattr("scripts.runtime.rf08_docker_authority.subprocess.run", fake_run)
    gateway = GatewayAuthority()
    gateway.observe(ObservationRequest(template=ObservationTemplate.DAEMON_VERSION), stage="daemon")
    assert seen == [True]
    assert not gateway_token_active()


def test_gateway_rejects_relative_compose_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        from scripts.runtime.rf08_docker_authority import ComposeBinding

        ComposeBinding.from_path(
            "compose.yaml",
            project_name="avito-mayak-rf08-secret-delivery",
            profile="runtime-foundation",
        )
