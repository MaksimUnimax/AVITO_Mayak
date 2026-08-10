"""Bounded safety scanner for RF24 ambiguous-send artifacts."""
# ruff: noqa: E501, E701, E702, E401, I001
from __future__ import annotations
import argparse, json, re
from pathlib import Path
PATTERNS=(re.compile(r"(?i)(authorization\s*[\"']?\s*[:=]|bearer\s+[A-Za-z0-9._-]+|password\s*[\"']?\s*[:=]|session[_ -]?cookie|private[_ -]?key)"), re.compile(r"(?i)(raw_provider|provider_payload|request_body|response_body)"))
def scan(paths: list[str]) -> dict[str, object]:
    findings=[]
    for name in paths:
        data=Path(name).read_text(encoding="utf-8")
        for pattern in PATTERNS:
            if pattern.search(data): findings.append({"filename":name,"finding":"unsafe-pattern"})
    return {"finding_count":len(findings),"findings":findings}
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--result",required=True); p.add_argument("files",nargs="+"); a=p.parse_args(); result=scan(a.files); Path(a.result).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n"); print(f"RF24_AMBIGUOUS_SCANNER_FINDINGS={result['finding_count']}"); raise SystemExit(1 if result["finding_count"] else 0)
if __name__ == "__main__": main()
