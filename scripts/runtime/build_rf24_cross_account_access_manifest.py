"""Build a deterministic hash-bound RF24 artifact manifest."""
# ruff: noqa
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("artifacts", type=Path); p.add_argument("--source-sha", required=True); p.add_argument("--run-id", required=True); p.add_argument("--output", type=Path, required=True); a=p.parse_args()
    files=[]
    for item in sorted(a.artifacts.glob("rf24-cross-account-access*")):
        if item == a.output or not item.is_file(): continue
        files.append({"name":item.name,"sha256":hashlib.sha256(item.read_bytes()).hexdigest()})
    a.output.write_text(json.dumps({"technical_id":"RF24-CROSS-ACCOUNT-ACCESS-SCENARIO-01","source_sha":a.source_sha,"hosted_run_id":a.run_id,"files":files}, indent=2, sort_keys=True), encoding="utf-8"); return 0
if __name__ == "__main__": raise SystemExit(main())
