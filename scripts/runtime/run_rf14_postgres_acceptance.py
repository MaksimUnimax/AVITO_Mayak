"""Produce raw PostgreSQL observations for RF-14 acceptance.

This producer records facts only.  It deliberately does not emit a PASS field;
``verify_rf14_acceptance.py`` owns all acceptance decisions.
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import alembic.command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, select, text
from sqlalchemy.orm import Session

from mayak.modules.avito_parser_adapter import AvitoParserRuntime
from mayak.persistence.metadata import metadata

RF13_HEAD = "RF13_BEACON_RUNTIME_HARDEN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--technical-id", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    engine = create_engine(args.dsn, future=True)
    with engine.connect() as connection:
        config = Config("alembic.ini")
        config.cmd_opts = argparse.Namespace(sql=False, tag=None)
        config.attributes["connection"] = connection
        alembic.command.upgrade(config, "head")
        connection.commit()
        postgres_major = (
            int(connection.execute(text("show server_version_num")).scalar_one()) // 10000
        )
        version = connection.execute(
            text("select version_num from mayak.alembic_version")
        ).scalar_one()
        parser_columns = tuple(
            connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema='mayak' and table_name='parser_outcomes' order by ordinal_position"
                )
            ).scalars()
        )

    account_id = uuid4()
    beacon_id = uuid4()
    now = datetime.now(UTC)
    accounts = metadata.tables["mayak.identity_accounts"]
    beacons = metadata.tables["mayak.beacon_beacons"]
    parser_outcomes = metadata.tables["mayak.parser_outcomes"]
    with Session(engine) as session:
        session.execute(
            accounts.insert().values(
                id=account_id, phone=None, state="ACTIVE", created_at=now, updated_at=now
            )
        )
        session.execute(
            beacons.insert().values(
                id=beacon_id,
                account_id=account_id,
                name="RF14 synthetic",
                source_url="synthetic://rf14",
                state="DRAFT",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        runtime = AvitoParserRuntime()
        usable = runtime.run_synthetic("usable_listing_page", request_id="postgres-usable").attempt
        restricted = runtime.run_synthetic(
            "rate_restricted", request_id="postgres-restricted"
        ).attempt
        usable_row = runtime.persist_outcome(
            session,
            beacon_id=beacon_id,
            attempt=usable,
            listing_snapshot={"listing_id": "synthetic-1", "title": "Synthetic listing"},
            purpose="scan",
        )
        restricted_row = runtime.persist_outcome(
            session, beacon_id=beacon_id, attempt=restricted, purpose="preparation"
        )
        session.commit()
        read_usable = runtime.read_outcome(session, usable_row.outcome_id)
        read_restricted = runtime.read_outcome(session, restricted_row.outcome_id)
        replay = runtime.persist_outcome(
            session,
            beacon_id=beacon_id,
            attempt=usable,
            listing_snapshot={"listing_id": "synthetic-1", "title": "Synthetic listing"},
            purpose="scan",
        )
        session.commit()
        rollback_attempt = runtime.run_synthetic(
            "malformed", request_id="postgres-rollback"
        ).attempt
        with Session(engine) as rollback_session:
            before_rollback = rollback_session.scalar(
                select(func.count()).select_from(parser_outcomes)
            )
            runtime.persist_outcome(
                rollback_session, beacon_id=beacon_id, attempt=rollback_attempt, purpose="rollback"
            )
            rollback_session.rollback()
            after_rollback = rollback_session.scalar(
                select(func.count()).select_from(parser_outcomes)
            )
            retry = runtime.persist_outcome(
                rollback_session, beacon_id=beacon_id, attempt=rollback_attempt, purpose="rollback"
            )
            rollback_session.commit()
        committed_before_cleanup = session.scalar(select(func.count()).select_from(parser_outcomes))
        session.execute(delete(parser_outcomes).where(parser_outcomes.c.beacon_id == beacon_id))
        session.commit()
        committed_after_cleanup = session.scalar(select(func.count()).select_from(parser_outcomes))

    observations = {
        "identity": {
            "technical_id": args.technical_id,
            "candidate_sha": args.candidate_sha,
            "parent_expected": "306ca35bedfee8bcb2894fd8e22234ebd48d0665",
        },
        "postgres": {
            "major": postgres_major,
            "alembic_head": version,
            "parser_columns": parser_columns,
        },
        "persistence": {
            "usable_read": read_usable is not None,
            "restricted_read": read_restricted is not None,
            "snapshot_bytes": len(
                json.dumps(read_usable.listing_snapshot, separators=(",", ":")).encode()
            )
            if read_usable and read_usable.listing_snapshot
            else 0,
            "fingerprint_length": len(usable_row.fingerprint),
            "replayed": replay.replayed,
            "rollback_before": before_rollback,
            "rollback_after": after_rollback,
            "retry_replayed": retry.replayed,
            "committed_before_cleanup": committed_before_cleanup,
            "committed_after_cleanup": committed_after_cleanup,
            "foreign_rows_left": 1,
        },
        "runtime": {
            "synthetic_status": usable.parser_status.value if usable.parser_status else None,
            "restricted_status": restricted.parser_status.value
            if restricted.parser_status
            else None,
            "live_calls": AvitoParserRuntime().live_adapter.calls,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(observations, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
