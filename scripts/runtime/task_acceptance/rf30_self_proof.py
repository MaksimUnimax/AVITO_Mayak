"""Non-authoritative developer wrapper for the in-image RF30 verifier.

The gateway never mounts or executes this host file. Production task
acceptance uses ``python -m mayak.runtime.task_acceptance`` from the image.
"""

from __future__ import annotations

import sys

from mayak.runtime.task_acceptance import run_task_acceptance


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    return run_task_acceptance(*sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
