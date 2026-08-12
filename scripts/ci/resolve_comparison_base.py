"""Fail-closed GitHub Actions comparison-base resolver."""

from __future__ import annotations

import argparse
import re
import subprocess

HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def resolve(
    event_name: str,
    pull_request_base: str = "",
    push_before: str = "",
    manual_base: str = "",
    *,
    candidate_sha: str = "",
    repository: str = ".",
) -> str:
    if event_name == "pull_request":
        value = pull_request_base
    elif event_name == "push":
        value = push_before
    elif event_name == "workflow_dispatch":
        value = manual_base
    else:
        raise ValueError("unsupported event for comparison base")
    if not HEX40.fullmatch(value) or int(value, 16) == 0:
        raise ValueError("comparison base must be a non-zero 40-hex commit")
    if candidate_sha and (not HEX40.fullmatch(candidate_sha) or int(candidate_sha, 16) == 0):
        raise ValueError("candidate SHA must be a non-zero 40-hex commit")
    if candidate_sha:
        for ref in (value, candidate_sha):
            if subprocess.run(
                ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
                cwd=repository,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode:
                raise ValueError("comparison base or candidate commit is unresolvable")
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", value, candidate_sha],
            cwd=repository,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode:
            raise ValueError("comparison base is not an ancestor of candidate")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--pull-request-base", default="")
    parser.add_argument("--push-before", default="")
    parser.add_argument("--manual-base", default="")
    parser.add_argument("--candidate-sha", default="")
    parser.add_argument("--repository", default=".")
    args = parser.parse_args()
    print(
        resolve(
            args.event_name,
            args.pull_request_base,
            args.push_before,
            args.manual_base,
            candidate_sha=args.candidate_sha,
            repository=args.repository,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
