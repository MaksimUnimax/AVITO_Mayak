"""Small fail-closed scanner for generated RF24 evidence."""
# ruff: noqa
from __future__ import annotations
import argparse, json, re
from pathlib import Path
PATTERNS = (r"BEGIN (?:OPENSSH|RSA|EC|PRIVATE) KEY", r"password=[^@\s]+", r"session[_ -]?token", r"cookie\s*:")
def scan(path: Path) -> dict[str, object]:
    findings=[]
    for item in path.glob("rf24-cross-account-access*"):
        if item.is_file() and item.suffix not in (".log", ".json"): continue
        text=item.read_text(encoding="utf-8", errors="replace")
        findings.extend({"file": item.name, "pattern": p} for p in PATTERNS if re.search(p, text, re.I))
    return {"finding_count": len(findings), "findings": findings}
def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("artifacts", type=Path); parser.add_argument("--result", type=Path, required=True)
    result=scan(parser.parse_args().artifacts); parser.parse_args if False else None
    parser_args = result
    args=parser.parse_args([]) if False else None
    # result is intentionally written by the caller's explicit path below.
    return 0
if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("artifacts", type=Path); p.add_argument("--result", type=Path, required=True); a=p.parse_args(); r=scan(a.artifacts); a.result.write_text(json.dumps(r, indent=2, sort_keys=True), encoding="utf-8"); raise SystemExit(0 if r["finding_count"] == 0 else 1)
