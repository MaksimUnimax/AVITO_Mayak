from __future__ import annotations

import json
from uuid import uuid4

import pytest

from mayak.modules.egress_routing import (
    AgentMessage,
    EgressAgentSimulator,
    EgressRF16RuntimeAuthority,
    MessageType,
    SimulatorScenario,
    TransportEffect,
)


def test_protocol_roundtrip_is_bounded_and_identity_bound() -> None:
    message = AgentMessage(
        MessageType.OUTCOME,
        uuid4(),
        uuid4(),
        uuid4(),
        "corr",
        TransportEffect.AMBIGUOUS,
        "reconcile",
    )
    assert AgentMessage.from_bytes(message.to_bytes()) == message
    with pytest.raises(ValueError, match="unknown protocol version"):
        AgentMessage.from_bytes(
            json.dumps({"protocol_version": "old", "message_type": "HEARTBEAT"}).encode()
        )
    with pytest.raises(ValueError, match="invalid correlation_id"):
        AgentMessage(MessageType.HEARTBEAT, uuid4(), correlation_id="x" * 20_000).to_bytes()
    with pytest.raises(ValueError, match="bounded"):
        AgentMessage.from_bytes(b"x" * 16_385)


@pytest.mark.parametrize("scenario", tuple(SimulatorScenario))
def test_simulator_scenarios_are_deterministic_and_no_transport_success_is_parser_success(
    scenario: SimulatorScenario,
) -> None:
    agent = EgressAgentSimulator(uuid4())
    first = agent.run(scenario)
    second = agent.run(scenario)
    assert first.agent_id == agent.agent_id
    if scenario is not SimulatorScenario.MISMATCHED_DUPLICATE:
        equivalent = EgressAgentSimulator(
            agent.agent_id, agent.assignment_id, agent.lease_id
        ).run(scenario)
        assert first.to_bytes() == equivalent.to_bytes()
    if scenario is SimulatorScenario.SUCCESS_TRANSPORT:
        assert first.effect in {
            TransportEffect.SUCCESS_TRANSPORT_ONLY,
        }
    if scenario is SimulatorScenario.RESULT_AMBIGUOUS:
        assert first.effect is TransportEffect.RESULT_AMBIGUOUS
    if scenario is SimulatorScenario.DUPLICATE:
        assert second.assignment_id == first.assignment_id


def test_simulator_restart_replays_durable_identity_not_memory() -> None:
    agent = EgressAgentSimulator(uuid4())
    committed = agent.run(SimulatorScenario.DISPATCH_AMBIGUOUS)
    restarted = agent.restart()
    replayed = restarted.run(SimulatorScenario.RESTART_REPLAY)
    assert replayed.to_bytes() == committed.to_bytes()
    assert replayed.assignment_id == committed.assignment_id


def test_rf16_authority_supersedes_only_historical_runtime_gate() -> None:
    authority = EgressRF16RuntimeAuthority()
    assert authority.task_id.startswith("RF-16-")
    assert authority.durable_server_runtime_authorized
    assert authority.transport_neutral_agent_boundary_authorized
    assert not authority.live_networking_authorized
    assert not authority.production_readiness_inferred
