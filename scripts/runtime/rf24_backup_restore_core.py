"""Pure, fail-closed checks for the RF24 PostgreSQL recovery rehearsal.

The module deliberately contains no database authority.  It validates the
safe projection emitted by the acceptance runner and is therefore also useful
to offline tests and independent artifact verification.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

TECHNICAL_ID = "RF24-BACKUP-RESTORE-SCENARIO-01"
REQUIRED_CONTROLS = (
    "tampered_digest",
    "corrupt_copy",
    "wrong_source_revision",
    "nonempty_newer_target",
    "duplicate_restore",
)
SECRET = re.compile(
    r"(postgres(?:ql)?://[^\s:@/]+:[^\s@/]+@|password\s*[=:]\s*[^<\s,}]+|"
    r"bearer\s+[A-Za-z0-9._-]+|BEGIN [A-Z ]+PRIVATE KEY|set-cookie|authorization)",
    re.I,
)
RAW_SUFFIXES = {".dump", ".backup", ".tar", ".tar.gz", ".sql.gz", ".pgdump"}


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_evidence(
    evidence: dict[str, Any], *, source_sha: str, run_id: str | None = None
) -> dict[str, Any]:
    require(evidence.get("technical_id") == TECHNICAL_ID, "technical identity mismatch")
    require(evidence.get("schema_version") == 1, "unsupported evidence schema")
    require(
        re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("source_sha", "")))
        and evidence["source_sha"] == source_sha,
        "source SHA mismatch",
    )
    if run_id is not None:
        require(evidence.get("hosted_run_id") == run_id, "hosted run identity mismatch")
    require(evidence.get("backup", {}).get("sha256"), "backup digest missing")
    require(int(evidence.get("backup", {}).get("size", 0)) > 0, "backup size missing")
    require(evidence.get("backup", {}).get("verified") is True, "backup not verified")
    require(evidence.get("restore", {}).get("result") == "PASS", "restore failed")
    require(
        evidence.get("source_fingerprint_before") == evidence.get("source_fingerprint_after"),
        "source mutated",
    )
    require(
        evidence.get("target_semantic_equivalence") is True, "target is not semantically equivalent"
    )
    controls = evidence.get("negative_controls", {})
    for name in REQUIRED_CONTROLS:
        require(controls.get(name) == "BLOCKED", f"negative control not blocked: {name}")
    security = evidence.get("security", {})
    for name, expected in {
        "provider_live_calls": 0,
        "raw_provider_payload": False,
        "production_personal_data": False,
        "public_ingress": False,
        "postgres_host_published": False,
        "foreign_resource_impact": "none",
        "credentials_exposure": False,
        "raw_backup_uploaded": False,
        "raw_backup_cleanup": True,
        "direct_foreign_module_dml": False,
        "owner_bypass": False,
    }.items():
        require(security.get(name) == expected, f"security invariant failed: {name}")
    require(evidence.get("clean_target_prerequisite") is True, "clean target prerequisite missing")
    return {
        "schema_version": 1,
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "verdict": "PASS",
    }


def scan_paths(paths: list[Path]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            findings.append({"path": path.name, "reason": "missing-or-empty"})
            continue
        if path.suffix.lower() in RAW_SUFFIXES or path.name.endswith(".sql.gz"):
            findings.append({"path": path.name, "reason": "raw-backup-file"})
        data = path.read_bytes()
        text = data.decode("utf-8", "replace")
        if SECRET.search(text):
            findings.append({"path": path.name, "reason": "credential-or-secret-material"})
        if "raw_provider_payload" in text and '"raw_provider_payload": false' not in text:
            findings.append({"path": path.name, "reason": "raw-provider-payload-marker"})
        if (
            re.search(r"production[_ -]?personal|real[_ -]?person|@avito\.ru", text, re.I)
            and '"production_personal_data": false' not in text
        ):
            findings.append({"path": path.name, "reason": "production-personal-data-marker"})
    return {
        "schema_version": 1,
        "scanner": "rf24-backup-restore",
        "finding_count": len(findings),
        "findings": findings,
        "sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()
        },
    }


def build_manifest(
    paths: list[Path], *, source_sha: str, run_id: str, scanner: dict[str, Any]
) -> dict[str, Any]:
    require(scanner.get("finding_count") == 0, "artifact scanner is not clean")
    return {
        "schema_version": 1,
        "artifact_name": "rf24-backup-restore",
        "technical_id": TECHNICAL_ID,
        "source_sha": source_sha,
        "hosted_run_id": run_id,
        "raw_backup_excluded": True,
        "finding_count": 0,
        "files": [
            {
                "filename": p.name,
                "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in paths
        ],
    }
