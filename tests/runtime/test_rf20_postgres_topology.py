"""Fail-closed RF20 PostgreSQL endpoint and publication proof matrix."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from mayak.runtime import rf20_acceptance_scenario as scenario

OWNER = "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-04"


def _container(
    name: str = "rf20-postgres",
    *,
    alias: str = "postgres",
    network: str = "rf20-net",
    owner: str = OWNER,
    network_ports: object = {"5432/tcp": None},
    host_bindings: object = None,
    container_id: str = "a" * 64,
) -> dict[str, object]:
    return {
        "Id": container_id,
        "Name": f"/{name}",
        "Config": {"Image": "postgres:18-bookworm", "Labels": {"com.mayak.owner": owner}},
        "NetworkSettings": {
            "Networks": {network: {"Aliases": [alias], "IPAddress": "172.30.0.2"}},
            "Ports": network_ports,
        },
        "HostConfig": {"PortBindings": host_bindings},
    }


def _docker(
    monkeypatch: pytest.MonkeyPatch, containers: list[dict[str, object]]
) -> list[tuple[str, ...]]:
    seen: list[tuple[str, ...]] = []
    by_id = {str(item["Id"]): item for item in containers}

    def fake_check_output(command: list[str], **_: object) -> str:
        seen.append(tuple(command))
        if command[:3] == ["docker", "ps", "-q"]:
            return "\n".join(by_id) + "\n"
        return json.dumps([by_id[command[-1]]])

    monkeypatch.setattr(scenario.subprocess, "check_output", fake_check_output)
    return seen


@pytest.fixture
def owned(monkeypatch: pytest.MonkeyPatch):
    container = _container()
    seen = _docker(monkeypatch, [container])
    return container, seen


def test_owned_unbound_endpoint_succeeds(owned) -> None:
    _, proof, provenance = scenario.host_postgres_publication_proof(
        endpoint_host="postgres", expected_owner=OWNER
    )
    assert proof.endswith("unpublished")
    assert provenance["candidate_count"] == 1
    assert provenance["host_publication"] is False


@pytest.mark.parametrize(
    "surface",
    ["network", "host"],
    ids=["NetworkSettings.Ports", "HostConfig.PortBindings"],
)
@pytest.mark.parametrize(
    "host_ip", ["0.0.0.0", "127.0.0.1", "::"], ids=["all", "localhost", "ipv6"]
)
def test_any_actual_host_publication_fails_closed(
    monkeypatch: pytest.MonkeyPatch, surface: str, host_ip: str
) -> None:
    binding = [{"HostIp": host_ip, "HostPort": "15432"}]
    info = _container(
        network_ports={"5432/tcp": binding} if surface == "network" else {"5432/tcp": None},
        host_bindings={"5432/tcp": binding} if surface == "host" else None,
    )
    _docker(monkeypatch, [info])
    with pytest.raises(RuntimeError, match="publication|contradictory"):
        scenario.host_postgres_publication_proof(endpoint_host="postgres", expected_owner=OWNER)


@pytest.mark.parametrize(
    "network_ports,host_bindings",
    [
        ({}, None),
        ({"5432/tcp": "not-a-list"}, None),
        ({"5432/tcp": None}, {"5432/tcp": [{"HostPort": "15432"}]}),
        ({"5432/tcp": [{"HostPort": ""}]}, None),
    ],
    ids=["missing-port-key", "bad-network-value", "contradictory-surfaces", "bad-binding"],
)
def test_malformed_or_contradictory_publication_fails_closed(
    monkeypatch: pytest.MonkeyPatch, network_ports: object, host_bindings: object
) -> None:
    _docker(monkeypatch, [_container(network_ports=network_ports, host_bindings=host_bindings)])
    with pytest.raises(RuntimeError):
        scenario.host_postgres_publication_proof(endpoint_host="postgres", expected_owner=OWNER)


def test_unrelated_foreign_postgres_outside_network_is_not_mutated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _container()
    foreign = _container(
        name="foreign",
        alias="foreign-postgres",
        network="foreign-net",
        owner="foreign",
        container_id="b" * 64,
    )
    seen = _docker(monkeypatch, [selected, foreign])
    _, _, provenance = scenario.host_postgres_publication_proof(
        endpoint_host="postgres", expected_owner=OWNER
    )
    assert provenance["candidate_count"] == 1
    assert all(command[:2] != ("docker", "rm") for command in seen)


def test_foreign_postgres_on_actual_network_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _container()
    foreign = _container(
        name="foreign", alias="foreign-postgres", owner="foreign", container_id="b" * 64
    )
    _docker(monkeypatch, [selected, foreign])
    with pytest.raises(RuntimeError, match="collision"):
        scenario.host_postgres_publication_proof(endpoint_host="postgres", expected_owner=OWNER)


def test_multiple_historical_owned_containers_do_not_select_arbitrarily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _container(container_id="a" * 64)
    second = _container(name="old", container_id="b" * 64)
    _docker(monkeypatch, [first, second])
    with pytest.raises(RuntimeError, match="ambiguous"):
        scenario.host_postgres_publication_proof(endpoint_host="postgres", expected_owner=OWNER)


def test_endpoint_association_ambiguity_and_identity_mismatch_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _container(alias="db", container_id="a" * 64)
    second = _container(name="postgres", alias="db", container_id="b" * 64)
    _docker(monkeypatch, [first, second])
    with pytest.raises(RuntimeError, match="ambiguous"):
        scenario.host_postgres_publication_proof(endpoint_host="db", expected_owner=OWNER)

    mismatch = deepcopy(first)
    mismatch["Config"]["Labels"]["com.mayak.owner"] = "RF20-ADMIN-SUPPORT-RUNTIME-01-CORRECTIVE-03"
    _docker(monkeypatch, [mismatch])
    with pytest.raises(RuntimeError, match="outside"):
        scenario.host_postgres_publication_proof(endpoint_host="db", expected_owner=OWNER)
