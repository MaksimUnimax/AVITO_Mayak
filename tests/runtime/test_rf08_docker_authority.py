import pytest

from scripts.runtime.rf08_docker_authority import (
    DockerCommandClass,
    MutationAuthority,
    classify_docker_argv,
)

PROJECT = "avito-mayak-rf08-secret-delivery"
BASE = (
    "docker",
    "compose",
    "-f",
    "compose.runtime.yaml",
    "-p",
    PROJECT,
    "--profile",
    "runtime-foundation",
)


def mutation(*args: str) -> tuple[str, ...]:
    return BASE + args


def test_authorization_is_appended_before_subprocess_callback() -> None:
    authority = MutationAuthority()
    seen: list[int] = []

    def callback(_argv: tuple[str, ...]) -> tuple[int, bool, bool]:
        seen.append(len(authority.entries))
        return 0, True, False

    authority.execute(mutation("up", "-d", "mayak-postgres"), stage="create", runner=callback)
    assert seen == [1]


def test_execution_result_references_prior_authorization() -> None:
    authority = MutationAuthority()
    authority.execute(
        mutation("stop", "mayak-postgres"), stage="stop", runner=lambda _: (0, True, False)
    )
    assert authority.entries[0].authorization_sequence == 1
    assert (
        authority.entries[1].authorization_sequence == authority.entries[0].authorization_sequence
    )
    assert authority.entries[1].execution_result_sequence == 1


def test_read_only_does_not_create_mutation_record() -> None:
    assert classify_docker_argv(("docker", "inspect", "abc")) == DockerCommandClass.READ_ONLY
    assert (
        classify_docker_argv(mutation("config", "--format", "json")) == DockerCommandClass.READ_ONLY
    )


@pytest.mark.parametrize(
    "argv",
    [
        ("docker", "system", "prune", "-f"),
        (
            "docker",
            "compose",
            "-f",
            "compose.runtime.yaml",
            "-p",
            PROJECT,
            "--profile",
            "runtime-foundation",
            "up",
            "-d",
        ),
        ("docker", "nonsense"),
    ],
)
def test_broad_unscoped_and_unknown_fail_closed(argv: tuple[str, ...]) -> None:
    authority = MutationAuthority()
    with pytest.raises((PermissionError, ValueError)):
        authority.authorize(argv, stage="negative")
    assert authority.entries == ()


def test_foreign_and_unresolved_targets_fail_before_execution() -> None:
    authority = MutationAuthority()
    foreign = (
        "docker",
        "run",
        "--rm",
        "--name",
        "apm-postgres",
        "--label",
        f"com.docker.compose.project={PROJECT}",
        "--label",
        "com.avito-mayak.technical-id=RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01",
        "--label",
        "com.avito-mayak.owner=rf08",
        "postgres",
        "true",
    )
    unresolved = (
        "docker",
        "run",
        "--rm",
        "--name",
        "rf08-unresolved-1",
        "--label",
        f"com.docker.compose.project={PROJECT}",
        "--label",
        "com.avito-mayak.technical-id=WRONG",
        "--label",
        "com.avito-mayak.owner=rf08",
        "postgres",
        "true",
    )
    with pytest.raises(PermissionError):
        authority.execute(foreign, stage="cleanup", runner=lambda _: (0, True, False))
    with pytest.raises((PermissionError, ValueError)):
        authority.authorize(unresolved, stage="cleanup")
    assert authority.entries == ()


def test_ledger_rejects_empty_missing_duplicate_and_reordered_results() -> None:
    authority = MutationAuthority()
    with pytest.raises(ValueError):
        authority.validate_complete(1)
    authority.execute(
        mutation("up", "-d", "mayak-postgres"), stage="up", runner=lambda _: (0, True, False)
    )
    authority.validate_complete(1)
    authority.ledger.pop()
    with pytest.raises(ValueError):
        authority.validate_complete(1)
