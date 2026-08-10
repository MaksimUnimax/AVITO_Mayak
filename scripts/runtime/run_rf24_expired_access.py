"""Run RF24 acceptance probes against the task-owned database.

The producer records observations only.  It does not contain a verifier and it
does not write owner business tables directly; setup is delegated to public
owner runtimes in the composition layer.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text

TECHNICAL_ID = "RF24-EXPIRED-ACCESS-SCENARIO-01"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-postgres", action="store_true")
    parser.add_argument("--artifacts", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not args.real_postgres:
        raise SystemExit("real PostgreSQL is required")
    host = os.environ.get("MAYAK_DATABASE_HOST", "postgres")
    name = os.environ.get("MAYAK_DATABASE_NAME", "mayak_rf24")
    user = os.environ.get("MAYAK_DATABASE_APPLICATION_USER", "mayak_application")
    engine = create_engine(f"postgresql+psycopg://{user}@{host}:5432/{name}")
    with engine.connect() as connection:
        version = connection.execute(
            text("select version_num from mayak.alembic_version")
        ).scalar_one()
    observations = {
        "technical_id": TECHNICAL_ID,
        "source_sha": os.environ.get("MAYAK_SOURCE_SHA", "unknown"),
        "acceptance_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "postgres_migration_head": version,
        "provider_live_calls": 0,
        "raw_provider_payload_persisted": False,
        "status": "SETUP_REQUIRED",
        "limitation": (
            "public owner setup and P0-P8 execution must be supplied by the runtime harness"
        ),
    }
    args.artifacts.mkdir(parents=True, exist_ok=True)
    (args.artifacts / "rf24-expired-access-provider-observations.json").write_text(
        json.dumps(observations, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    raise SystemExit("RF24 P0-P8 harness setup is incomplete")


if __name__ == "__main__":
    main()
