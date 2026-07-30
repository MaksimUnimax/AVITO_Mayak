from copy import deepcopy
from typing import Any

from scripts.runtime.rf08_foreign_snapshot import classify_delta


def _snapshot() -> dict[str, Any]:
    return {
        "collection_complete": True,
        "unresolved_resource_records": {"containers": [], "networks": [], "volumes": []},
        "container_records": [
            {
                "stable": {"id": "c1", "fingerprint": "opaque-c1"},
                "runtime": {"id": "c1", "status": "running"},
            }
        ],
        "network_records": [],
        "volume_records": [],
    }


def test_reordered_foreign_records_are_canonicalized_by_collector() -> None:
    left = _snapshot()
    right = deepcopy(left)
    right["container_records"] = list(reversed(right["container_records"]))
    assert classify_delta(left, right) == "NO_CHANGE"


def test_foreign_runtime_change_fails_equality() -> None:
    left = _snapshot()
    right = deepcopy(left)
    right["container_records"][0]["runtime"]["status"] = "exited"  # type: ignore[index]
    assert classify_delta(left, right) == "FOREIGN_RUNTIME_STATE_CHANGED"


def test_foreign_structure_and_unresolved_resources_fail_closed() -> None:
    left = _snapshot()
    structure = deepcopy(left)
    structure["container_records"][0]["stable"]["fingerprint"] = "opaque-c2"  # type: ignore[index]
    assert classify_delta(left, structure) == "FOREIGN_STRUCTURE_CHANGED"
    unresolved = deepcopy(left)
    unresolved["unresolved_resource_records"] = {
        "containers": [{"id": "u1"}],
        "networks": [],
        "volumes": [],
    }
    assert classify_delta(left, unresolved) == "UNRESOLVED_RESOURCE_PRESENT"


def test_incomplete_snapshot_fails_closed() -> None:
    left = _snapshot()
    right = deepcopy(left)
    right["collection_complete"] = False
    assert classify_delta(left, right) == "SNAPSHOT_INCOMPLETE"
