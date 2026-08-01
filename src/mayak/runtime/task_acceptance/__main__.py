"""Fixed application-image task acceptance entrypoint."""

from __future__ import annotations

import argparse

from . import run_task_acceptance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("technical_id")
    parser.add_argument("project")
    parser.add_argument("verifier_id")
    args = parser.parse_args()
    return run_task_acceptance(args.technical_id, args.project, args.verifier_id)


if __name__ == "__main__":
    raise SystemExit(main())
