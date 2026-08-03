"""Bounded, serializable RF16 server/Windows-agent application protocol."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

PROTOCOL_VERSION = "rf16-egress-v1"
MAX_MESSAGE_BYTES = 16_384


class MessageType(StrEnum):
    HEARTBEAT = "HEARTBEAT"
    ASSIGNMENT = "ASSIGNMENT"
    RECEIPT = "RECEIPT"
    OUTCOME = "OUTCOME"
    RECONCILIATION = "RECONCILIATION"


class TransportEffect(StrEnum):
    NOT_SENT = "NOT_SENT"
    UNAVAILABLE = "UNAVAILABLE"
    FAILURE = "FAILURE"
    RESTRICTED = "RESTRICTED"
    MALFORMED = "MALFORMED"
    SUCCESS_TRANSPORT_ONLY = "SUCCESS_TRANSPORT_ONLY"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


def _text(value: object, name: str, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"invalid {name}")
    return value


@dataclass(frozen=True, slots=True)
class AgentMessage:
    message_type: MessageType
    agent_id: UUID
    assignment_id: UUID | None = None
    lease_id: UUID | None = None
    correlation_id: str = ""
    effect: TransportEffect | None = None
    safe_reason: str | None = None
    heartbeat_state: str | None = None

    def __post_init__(self) -> None:
        _text(self.correlation_id, "correlation_id", 128)
        if self.message_type in {
            MessageType.ASSIGNMENT,
            MessageType.RECEIPT,
            MessageType.OUTCOME,
        } and (self.assignment_id is None or self.lease_id is None):
            raise ValueError("assignment and lease identity are required")
        if self.safe_reason is not None:
            _text(self.safe_reason, "safe_reason", 128)

    def to_bytes(self) -> bytes:
        value = {
            "protocol_version": PROTOCOL_VERSION,
            "message_type": self.message_type.value,
            "agent_id": str(self.agent_id),
            "assignment_id": str(self.assignment_id) if self.assignment_id else None,
            "lease_id": str(self.lease_id) if self.lease_id else None,
            "correlation_id": self.correlation_id,
            "effect": self.effect.value if self.effect else None,
            "safe_reason": self.safe_reason,
            "heartbeat_state": self.heartbeat_state,
        }
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds bounded protocol size")
        return encoded

    @classmethod
    def from_bytes(cls, raw: bytes) -> "AgentMessage":
        if len(raw) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds bounded protocol size")
        try:
            value = json.loads(raw)
            if value.get("protocol_version") != PROTOCOL_VERSION:
                raise RuntimeError("unknown protocol version")
            message_type = MessageType(value["message_type"])
            effect = TransportEffect(value["effect"]) if value.get("effect") else None
            return cls(
                message_type=message_type,
                agent_id=UUID(value["agent_id"]),
                assignment_id=UUID(value["assignment_id"]) if value.get("assignment_id") else None,
                lease_id=UUID(value["lease_id"]) if value.get("lease_id") else None,
                correlation_id=value["correlation_id"],
                effect=effect,
                safe_reason=value.get("safe_reason"),
                heartbeat_state=value.get("heartbeat_state"),
            )
        except RuntimeError:
            raise ValueError("unknown protocol version")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed or unknown agent message") from exc


__all__ = [
    "AgentMessage",
    "MAX_MESSAGE_BYTES",
    "MessageType",
    "PROTOCOL_VERSION",
    "TransportEffect",
]
