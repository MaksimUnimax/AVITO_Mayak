"""Strict RF20 evidence producer; the scenario lives in rf20_acceptance_scenario.
The shared implementation builds the production ``build_rf20_composition`` and
executes tariff/access/beacon owner commands.
Legacy compatibility names intentionally point at the shared callable:
``bootstrap = runtime.execute_tariff_action`` and
``runtime.execute_access_action``/``runtime.execute_beacon_support_patch``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text

from mayak.runtime.rf20_acceptance_scenario import run_rf20_acceptance_scenario


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("RF20_DATABASE_URL"))
    parser.add_argument("--fixture-dsn", default=os.environ.get("RF20_MIGRATION_DSN"))
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--output", default="rf20-acceptance-evidence.json")
    args = parser.parse_args()
    if not args.dsn or not args.fixture_dsn or not args.candidate_sha:
        return 2
    application_engine = create_engine(args.dsn, pool_pre_ping=True)
    fixture_engine = create_engine(args.fixture_dsn, pool_pre_ping=True)
    with application_engine.connect() as connection:
        if not str(connection.execute(text("select version()")).scalar_one()).startswith(
            "PostgreSQL 18"
        ):
            return 2
    evidence = run_rf20_acceptance_scenario(
        application_engine=application_engine,
        fixture_engine=fixture_engine,
        candidate_sha=args.candidate_sha,
        namespace=f"producer:{args.candidate_sha}",
    )
    Path(args.output).write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
