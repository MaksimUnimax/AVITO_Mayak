from __future__ import annotations

import json
from uuid import uuid4

import pytest

from mayak.modules.egress_routing import AgentMessage, MessageType, TransportEffect


def _base(message_type: str = "HEARTBEAT") -> dict[str, object]:
    return {
        "protocol_version": "rf16-egress-v1",
        "message_type": message_type,
        "agent_id": str(uuid4()),
        "correlation_id": "corr",
        "heartbeat_state": "ONLINE",
        "source_release": "rf16-egress-routing-durable-runtime-20260803-01",
    }


@pytest.mark.parametrize(
    "change",
    (
        {"unexpected": 1},
        {"message_type": "UNKNOWN"},
        {"protocol_version": "rf16-egress-v0"},
        {"agent_id": "not-a-uuid"},
        {"heartbeat_state": {"unsafe": True}},
    ),
)
def test_protocol_rejects_adversarial_heartbeat_shapes(change: dict[str, object]) -> None:
    value = _base()
    value.update(change)
    with pytest.raises(ValueError):
        AgentMessage.from_bytes(json.dumps(value).encode())


def test_protocol_rejects_incompatible_effect_and_assignment_fields() -> None:
    value = _base("ASSIGNMENT")
    value.update(
        {
            "assignment_id": str(uuid4()),
            "lease_id": str(uuid4()),
            "purpose": "scan",
            "capability_scope": ["listing_read"],
            "request_reference": "safe-ref",
            "size_limit_bytes": 1024,
            "timeout_seconds": 10,
            "effect": TransportEffect.SUCCESS_TRANSPORT_ONLY.value,
        }
    )
    with pytest.raises(ValueError):
        AgentMessage.from_bytes(json.dumps(value).encode())


def test_assignment_serialization_is_canonical_and_bounded() -> None:
    message = AgentMessage(
        MessageType.ASSIGNMENT,
        uuid4(),
        uuid4(),
        uuid4(),
        "corr",
        purpose="scan",
        capability_scope=("listing_read",),
        request_reference="safe-ref",
        size_limit_bytes=1024,
        timeout_seconds=10,
    )
    raw = message.to_bytes()
    assert raw == message.to_bytes()
    assert AgentMessage.from_bytes(raw) == message
