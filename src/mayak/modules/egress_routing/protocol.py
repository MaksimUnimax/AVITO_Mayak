"""Strict transport-neutral RF16 application protocol.

The wire format is deliberately small and typed.  It is an application
boundary, not a database, command, proxy, or credential transport.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

PROTOCOL_VERSION = "rf16-egress-v1"
SOURCE_RELEASE = "rf16-egress-routing-durable-runtime-20260803-01"
MAX_MESSAGE_BYTES = 16_384
_MAX_TEXT = 256
_COMMON = {"protocol_version", "message_type", "agent_id", "correlation_id"}


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
    MALFORMED_UNUSABLE = "MALFORMED_UNUSABLE"
    SUCCESS_TRANSPORT_ONLY = "SUCCESS_TRANSPORT_ONLY"
    DISPATCH_AMBIGUOUS = "DISPATCH_AMBIGUOUS"
    RESULT_AMBIGUOUS = "RESULT_AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    # Kept as an input-compatible alias for the original RF16 candidate.
    AMBIGUOUS = "AMBIGUOUS"


def _text(value: object, name: str, limit: int = _MAX_TEXT) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"invalid {name}")
    return value.strip()


def _uuid(value: object, name: str) -> UUID:
    if not isinstance(value, UUID):
        raise ValueError(f"invalid {name}")
    return value


@dataclass(frozen=True, slots=True)
class AgentMessage:
    """One strict server/agent message; ``to_bytes`` is canonical JSON."""

    message_type: MessageType
    agent_id: UUID
    assignment_id: UUID | None = None
    lease_id: UUID | None = None
    correlation_id: str = ""
    effect: TransportEffect | None = None
    safe_reason: str | None = None
    heartbeat_state: str | None = None
    purpose: str | None = None
    capability_scope: tuple[str, ...] = ()
    request_reference: str | None = None
    size_limit_bytes: int | None = None
    timeout_seconds: int | None = None
    source_release: str = SOURCE_RELEASE

    def __post_init__(self) -> None:
        if type(self.message_type) is not MessageType:
            raise ValueError("invalid message_type")
        _uuid(self.agent_id, "agent_id")
        _text(self.correlation_id, "correlation_id", 128)
        _text(self.source_release, "source_release", 128)
        if self.message_type in {
            MessageType.ASSIGNMENT,
            MessageType.RECEIPT,
            MessageType.OUTCOME,
            MessageType.RECONCILIATION,
        }:
            if self.assignment_id is None or self.lease_id is None:
                raise ValueError("assignment and lease identity are required")
            _uuid(self.assignment_id, "assignment_id")
            _uuid(self.lease_id, "lease_id")
        if self.message_type is MessageType.ASSIGNMENT:
            _text(self.purpose, "purpose")
            if type(self.capability_scope) is not tuple or not self.capability_scope:
                raise ValueError("capability_scope is required")
            for value in self.capability_scope:
                _text(value, "capability_scope", 64)
            _text(self.request_reference, "request_reference", 256)
            if (
                type(self.size_limit_bytes) is not int
                or not 1 <= self.size_limit_bytes <= MAX_MESSAGE_BYTES
            ):
                raise ValueError("invalid size_limit_bytes")
            if type(self.timeout_seconds) is not int or not 1 <= self.timeout_seconds <= 86_400:
                raise ValueError("invalid timeout_seconds")
            if self.effect is not None or self.heartbeat_state is not None:
                raise ValueError("assignment cannot contain an agent-only effect/heartbeat")
        if self.message_type is MessageType.HEARTBEAT and (
            self.effect is not None or self.assignment_id is not None or self.lease_id is not None
        ):
            raise ValueError("heartbeat cannot contain assignment or outcome")
        if self.message_type is MessageType.RECEIPT and self.effect is not None:
            raise ValueError("receipt cannot contain an outcome")
        if self.effect is not None and type(self.effect) is not TransportEffect:
            raise ValueError("invalid effect")
        if self.safe_reason is not None:
            _text(self.safe_reason, "safe_reason", 128)
        if self.heartbeat_state is not None:
            _text(self.heartbeat_state, "heartbeat_state", 64)

    def _value(self) -> dict[str, object]:
        value: dict[str, object] = {
            "protocol_version": PROTOCOL_VERSION,
            "message_type": self.message_type.value,
            "agent_id": str(self.agent_id),
            "correlation_id": self.correlation_id,
        }
        if self.message_type is MessageType.ASSIGNMENT:
            value.update(
                {
                    "assignment_id": str(self.assignment_id),
                    "lease_id": str(self.lease_id),
                    "purpose": self.purpose,
                    "capability_scope": list(self.capability_scope),
                    "request_reference": self.request_reference,
                    "size_limit_bytes": self.size_limit_bytes,
                    "timeout_seconds": self.timeout_seconds,
                    "source_release": self.source_release,
                }
            )
        elif self.message_type is not MessageType.HEARTBEAT:
            value.update(
                {
                    "assignment_id": str(self.assignment_id),
                    "lease_id": str(self.lease_id),
                    "effect": self.effect.value if self.effect else None,
                    "safe_reason": self.safe_reason,
                    "source_release": self.source_release,
                }
            )
        else:
            value.update(
                {"heartbeat_state": self.heartbeat_state, "source_release": self.source_release}
            )
        return value

    def to_bytes(self) -> bytes:
        encoded = json.dumps(
            self._value(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        if len(encoded) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds bounded protocol size")
        return encoded

    @classmethod
    def from_bytes(cls, raw: bytes) -> "AgentMessage":
        if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_MESSAGE_BYTES:
            raise ValueError("message exceeds bounded protocol size")
        try:
            value = json.loads(bytes(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("malformed agent message") from exc
        if type(value) is not dict:
            raise ValueError("message must be a JSON object")
        if value.get("protocol_version") != PROTOCOL_VERSION:
            raise ValueError("unknown protocol version")
        try:
            message_type = MessageType(value["message_type"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("unknown message type") from exc
        allowed = (
            _COMMON | {"source_release", "heartbeat_state"}
            if message_type is MessageType.HEARTBEAT
            else _COMMON | {"assignment_id", "lease_id", "effect", "safe_reason", "source_release"}
        )
        if message_type is MessageType.ASSIGNMENT:
            allowed = _COMMON | {
                "assignment_id",
                "lease_id",
                "purpose",
                "capability_scope",
                "request_reference",
                "size_limit_bytes",
                "timeout_seconds",
                "source_release",
            }
        unknown = set(value) - allowed
        if unknown:
            raise ValueError("forbidden or unexpected message field")
        required = allowed - {"source_release", "effect", "safe_reason", "heartbeat_state"}
        if any(field not in value for field in required):
            raise ValueError("missing required message field")
        try:
            effect = TransportEffect(value["effect"]) if value.get("effect") is not None else None
            return cls(
                message_type=message_type,
                agent_id=UUID(value["agent_id"]),
                assignment_id=UUID(value["assignment_id"])
                if value.get("assignment_id") is not None
                else None,
                lease_id=UUID(value["lease_id"]) if value.get("lease_id") is not None else None,
                correlation_id=value["correlation_id"],
                effect=effect,
                safe_reason=value.get("safe_reason"),
                heartbeat_state=value.get("heartbeat_state"),
                purpose=value.get("purpose"),
                capability_scope=tuple(value.get("capability_scope", ())),
                request_reference=value.get("request_reference"),
                size_limit_bytes=value.get("size_limit_bytes"),
                timeout_seconds=value.get("timeout_seconds"),
                source_release=value.get("source_release", SOURCE_RELEASE),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("malformed or identity-invalid agent message") from exc


__all__ = [
    "AgentMessage",
    "MAX_MESSAGE_BYTES",
    "MessageType",
    "PROTOCOL_VERSION",
    "SOURCE_RELEASE",
    "TransportEffect",
]
