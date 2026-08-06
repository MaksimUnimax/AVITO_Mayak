"""Bounded, process-local provenance for the RF24 synthetic acceptance run."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

_MAX_RECORD_BYTES = 4096
_MAX_RECORDS = 128
_PATH_ENV = {
    "mayak-scheduler": "RF24_SCHEDULER_OBSERVATIONS",
    "mayak-worker": "RF24_WORKER_OBSERVATIONS",
}


def _enabled() -> bool:
    return os.environ.get("MAYAK_RUNTIME_PROFILE") == "synthetic_acceptance"


def emit_process_observation(record: dict[str, Any]) -> None:
    """Append a safe observation; production runtimes have no observation side effect."""
    if not _enabled():
        return
    process_kind = os.environ.get("MAYAK_PROCESS_KIND", "")
    env_name = _PATH_ENV.get(process_kind)
    run_id = os.environ.get("MAYAK_ENVIRONMENT_ID")
    if env_name is None or not run_id:
        raise RuntimeError("RF24 provenance requires an acceptance run and process kind")
    configured = os.environ.get(env_name)
    if not configured:
        raise RuntimeError(f"missing RF24 provenance path: {env_name}")
    path = Path(configured)
    if not path.is_absolute() or path.is_symlink() or path.name in {"", ".", ".."}:
        raise RuntimeError("RF24 provenance path must be an absolute non-symlink file")
    safe = {
        "technical_id": "RF24-RUNTIME-VERTICAL-SPINE-01-CORRECTIVE-02",
        "acceptance_run_id": run_id,
        "process_kind": process_kind,
        "process_pid": os.getpid(),
        "observed_at": datetime.now().astimezone().isoformat(),
        **record,
    }
    if safe.get("acceptance_run_id") != run_id or safe.get("process_kind") != process_kind:
        raise RuntimeError("RF24 provenance identity mismatch")
    encoded = (json.dumps(safe, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > _MAX_RECORD_BYTES:
        raise RuntimeError("RF24 provenance record is too large")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(path, flags, 0o600)
    try:
        if path.stat().st_size // max(len(encoded), 1) >= _MAX_RECORDS:
            raise RuntimeError("RF24 provenance record limit exceeded")
        os.write(fd, encoded)
    finally:
        os.close(fd)


__all__ = ["emit_process_observation"]
