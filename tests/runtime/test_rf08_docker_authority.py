# ruff: noqa: E501
import ast
from pathlib import Path

import pytest

from scripts.runtime.rf08_docker_authority import (
    DockerCommandClass,
    MutationAuthority,
    classify_docker_argv,
)

PROJECT = "avito-mayak-rf08-secret-delivery"
BASE = ("docker", "compose", "-f", "compose.yaml", "-p", PROJECT, "--profile", "runtime-foundation")


def mutation(*args: str) -> tuple[str, ...]:
    return BASE + args


def test_authorization_is_appended_before_subprocess_callback() -> None:
    authority = MutationAuthority()
    seen: list[int] = []

    def callback(_argv: tuple[str, ...]) -> tuple[int, bool, bool]:
        seen.append(len(authority.ledger))
        return 0, True, False

    authority.execute(mutation("up", "mayak-postgres"), stage="create", runner=callback)
    assert seen == [1]


def test_execution_result_references_prior_authorization() -> None:
    authority = MutationAuthority()
    authority.execute(mutation("stop", "mayak-postgres"), stage="stop", runner=lambda _: (0, True, False))
    assert authority.ledger[1].authorization_sequence == authority.ledger[0].authorization_sequence
    assert authority.ledger[1].execution_result_sequence == 2


def test_read_only_does_not_create_mutation_record() -> None:
    assert classify_docker_argv(("docker", "inspect", "abc")) == DockerCommandClass.READ_ONLY
    assert classify_docker_argv(mutation("config", "--format", "json")) == DockerCommandClass.READ_ONLY


@pytest.mark.parametrize("argv", [
    ("docker", "system", "prune", "-f"),
    ("docker", "compose", "up", "-d"),
    ("docker", "nonsense"),
])
def test_broad_unscoped_and_unknown_fail_closed(argv: tuple[str, ...]) -> None:
    authority = MutationAuthority()
    with pytest.raises((PermissionError, ValueError)):
        authority.authorize(argv, stage="negative")
    assert authority.ledger == []


def test_foreign_and_unresolved_targets_fail_before_execution() -> None:
    authority = MutationAuthority()
    for ownership in ("FOREIGN", "UNRESOLVED"):
        with pytest.raises(PermissionError):
            authority.execute(mutation("rm", "-f", "mayak-postgres"), stage="cleanup",
                              ownership=ownership, runner=lambda _: (0, True, False))
    assert authority.ledger == []


def test_ledger_rejects_empty_missing_duplicate_and_reordered_results() -> None:
    authority = MutationAuthority()
    with pytest.raises(ValueError):
        authority.validate_complete(1)
    authority.execute(mutation("up", "mayak-postgres"), stage="up", runner=lambda _: (0, True, False))
    authority.validate_complete(1)
    authority.ledger.pop()
    with pytest.raises(ValueError):
        authority.validate_complete(1)


def test_static_docker_mutation_routing_and_no_preflight_literals() -> None:
    root = Path(__file__).parents[2]
    source = (root / "scripts/runtime/safe_compose_bootstrap.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert '"stale_task_resources_absent": True' not in source
    assert '"foreign_snapshot_equal": True' not in source
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"
        and node.func.attr == "run" and any(
            isinstance(arg, ast.Tuple) and any(isinstance(x, ast.Constant) and x.value == "docker" for x in ast.walk(arg))
            for arg in node.args
        )
        for node in ast.walk(tree)
    )
