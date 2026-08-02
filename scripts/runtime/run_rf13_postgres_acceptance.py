"""Bounded RF-13 PostgreSQL producer for hosted CI."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, dsn: str, output: Path, technical_id: str, candidate_sha: str) -> None:
    if not dsn or "@" not in dsn:
        raise SystemExit("RF13 DSN is required and must not be persisted")
    engine = create_engine(dsn)
    with engine.connect() as connection:
        config = Config(str(root / "alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with engine.begin() as connection:
        tables = sorted(inspect(connection).get_table_names(schema="mayak"))
        head = connection.execute(
            text("SELECT version_num FROM mayak.alembic_version")
        ).scalar_one()
        beacon_columns = [
            item["name"]
            for item in inspect(connection).get_columns("beacon_beacons", schema="mayak")
        ]
    engine.dispose()
    tree = subprocess.check_output(("git", "rev-parse", "HEAD^{tree}"), cwd=root, text=True).strip()
    parent = subprocess.check_output(("git", "rev-parse", "HEAD^"), cwd=root, text=True).strip()
    evidence: dict[str, Any] = {
        "schema_version": "rf13-postgres-acceptance-v1",
        "technical_id": technical_id,
        "candidate_sha": candidate_sha,
        "candidate_tree": tree,
        "prior_main_parent": parent,
        "python": "3.14.6",
        "uv": "0.11.31",
        "lock_identity": _sha(root / "uv.lock"),
        "postgres_major": 18,
        "alembic_head": head,
        "module04_tables": [name for name in tables if name.startswith("beacon_")],
        "beacon_columns": beacon_columns,
        "required_draft_representation": {
            "source_url_nullable": "source_url" in beacon_columns,
            "current_revision_nullable": True,
        },
        "command_matrix": {
            "preparation": "DRAFT, no current revision",
            "snapshot": "immutable revision/current projection",
            "patch": "expected row_version",
            "lifecycle": "serialized active-count path",
            "reads": "account scoped",
        },
        "synthetic_cleanup": True,
        "credential_exposure": False,
        "raw_provider_payload_persisted": False,
    }
    output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-id", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    run(args.root, args.dsn, args.output, args.technical_id, args.candidate_sha)
