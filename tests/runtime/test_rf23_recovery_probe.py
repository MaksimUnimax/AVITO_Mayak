import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.runtime.probe_rf23_runtime import _task_owned_db_identity, _wait_until_healthy


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


def _observer(values: list[str]) -> Callable[[], str]:
    iterator: Iterator[str] = iter(values)
    last = values[-1]

    def observe() -> str:
        nonlocal last
        last = next(iterator, last)
        return last

    return observe


def test_delayed_postgres_health_waits_between_observations() -> None:
    clock = _Clock()

    result = _wait_until_healthy(
        _observer(["starting", "unhealthy", "healthy"]),
        timeout=10,
        interval=2,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert result["status"] == "healthy"
    assert result["attempts"] == 3
    assert clock.sleeps == [2, 2]


def test_delayed_api_readiness_after_db_health_is_healthy() -> None:
    clock = _Clock()

    result = _wait_until_healthy(
        _observer(["unhealthy", "unhealthy", "healthy"]),
        timeout=10,
        interval=1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert result["status"] == "healthy"
    assert result["attempts"] == 3
    assert clock.sleeps == [1, 1]


@pytest.mark.parametrize("last_observation", ["starting", "unhealthy", "missing"])
def test_database_never_becomes_healthy_is_bounded_and_fail_closed(last_observation: str) -> None:
    clock = _Clock()

    result = _wait_until_healthy(
        _observer([last_observation]),
        timeout=3,
        interval=1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert result["status"] == "unhealthy"
    assert result["attempts"] == 4
    assert clock.value == 3


def test_api_never_recovers_after_database_health_is_bounded_and_fail_closed() -> None:
    clock = _Clock()

    result = _wait_until_healthy(
        _observer(["unhealthy"]),
        timeout=2,
        interval=1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )

    assert result["status"] == "unhealthy"
    assert result["attempts"] == 3
    assert clock.sleeps == [1, 1]


def test_foreign_database_identity_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    inspection = {
        "Id": "foreign-id",
        "Config": {"Labels": {"com.mayak.owner": "different-task"}},
        "NetworkSettings": {"Networks": {"rf23-task-network": {}}},
    }
    monkeypatch.setattr(
        "subprocess.check_output",
        lambda *args, **kwargs: json.dumps([inspection]),
    )

    with pytest.raises(AssertionError):
        _task_owned_db_identity("foreign-db", "rf23-task-network", "expected-task")
