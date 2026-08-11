from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.runtime import rf26_h19_preflight as preflight


def test_child_process_receives_required_h19_names_without_value_output(
    tmp_path: Path, monkeypatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    password_file = state_dir / "rf11-password"
    password_file.write_text("synthetic-only\n")
    password_file.chmod(0o600)
    marker = state_dir / "h19.env"
    marker.write_text(
        "\n".join(
            (
                "MAYAK_RF10_POSTGRES_DSN=postgresql+psycopg://mayak_migration:synthetic-only@db:5432/rf26_h19_rf10_123",
                f"MAYAK_RF11_POSTGRES_PASSWORD_FILE={password_file}",
                "MAYAK_RF11_POSTGRES_USER=mayak_migration",
                "MAYAK_RF11_POSTGRES_HOST=db",
                "MAYAK_RF11_POSTGRES_PORT=5432",
                "MAYAK_RF11_POSTGRES_DB=rf26_h19_rf11_123",
                "RF26_H19_RF10_DB=rf26_h19_rf10_123",
                "RF26_H19_RF11_DB=rf26_h19_rf11_123",
            )
        )
        + "\n"
    )
    marker.chmod(0o600)
    monkeypatch.setattr(
        preflight,
        "_validated_state",
        lambda **_: ("rf26_h19_rf10_123", "rf26_h19_rf11_123"),
    )
    values = preflight._read_state(state_dir, "123")
    env_file = tmp_path / "github-env"
    preflight._append_env(
        values=values,
        path=env_file,
        state_dir=state_dir,
        junit=tmp_path / "junit",
        diagnostic=tmp_path / "diag",
    )
    child_env = dict(os.environ)
    for line in env_file.read_text().splitlines():
        key, value = line.split("=", 1)
        child_env[key] = value
    result = subprocess.run(
        [
            "python",
            "-c",
            "import os; print(','.join(sorted(k for k in os.environ if k.startswith('MAYAK_RF'))))",
        ],
        env=child_env, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == ",".join(sorted(preflight.REQUIRED))
    assert "synthetic-only" not in result.stdout
