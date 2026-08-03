"""Build the minimal reproducible transport-neutral RF16 agent artifact."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "mayak/modules/egress_routing/protocol.py",
    "mayak/modules/egress_routing/agent_entrypoint.py",
)
FORBIDDEN = ("password", "secret", "cookie", "private_key", "shell", "subprocess", "sqlalchemy")


def build(output: Path) -> tuple[Path, str, list[str]]:
    source_root = ROOT / "src"
    contents = {name: (source_root / name).read_bytes() for name in FILES}
    for name, data in contents.items():
        lowered = data.decode("utf-8").lower()
        if any(marker in lowered for marker in FORBIDDEN):
            raise RuntimeError(f"forbidden marker in agent source: {name}")
    manifest = {
        "source_release": "rf16-egress-routing-durable-runtime-20260803-01",
        "files": list(FILES),
    }
    payload = {
        **contents,
        "MANIFEST.json": json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload[name])
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return output, digest, list(payload)


def main() -> int:
    output, digest, names = build(ROOT / "dist/rf16/rf16-agent.zip")
    print(json.dumps({"artifact": str(output), "sha256": digest, "files": names}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
