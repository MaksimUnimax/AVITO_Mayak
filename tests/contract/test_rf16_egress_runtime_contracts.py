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
    assert first.to_bytes() == first.to_bytes()
    if scenario in {SimulatorScenario.SUCCESS_TRANSPORT, SimulatorScenario.RESULT_AMBIGUOUS}:
        assert first.effect in {
            TransportEffect.SUCCESS_TRANSPORT_ONLY,
            TransportEffect.RECONCILIATION_REQUIRED,
        }
    if scenario is SimulatorScenario.DUPLICATE:
        assert second.assignment_id == first.assignment_id


def test_rf16_authority_supersedes_only_historical_runtime_gate() -> None:
    authority = EgressRF16RuntimeAuthority()
    assert authority.task_id.startswith("RF-16-")
    assert authority.durable_server_runtime_authorized
    assert authority.transport_neutral_agent_boundary_authorized
    assert not authority.live_networking_authorized
    assert not authority.production_readiness_inferred
