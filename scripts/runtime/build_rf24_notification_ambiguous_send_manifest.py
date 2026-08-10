"""Build hash-bound RF24 artifact manifest."""
# ruff: noqa: E501, E701, E702, E401, I001
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--output",required=True); p.add_argument("--scanner-result",required=True); p.add_argument("--source-sha",required=True); p.add_argument("--run-id",required=True); p.add_argument("files",nargs="+"); a=p.parse_args()
    scanner=json.loads(Path(a.scanner_result).read_text()); payloads=[]
    for name in a.files:
        raw=Path(name).read_bytes(); payloads.append({"filename":name,"size":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    result={"technical_id":"RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01","source_sha":a.source_sha,"acceptance_run_id":a.run_id,"finding_count":scanner["finding_count"],"payloads":payloads}; Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
if __name__ == "__main__": main()
