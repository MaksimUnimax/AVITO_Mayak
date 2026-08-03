"""Deterministic in-process Windows Egress Agent simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from .protocol import AgentMessage, MessageType, TransportEffect


class SimulatorScenario(StrEnum):
    HEARTBEAT = "heartbeat"
    ACCEPTED_ASSIGNMENT = "accepted_assignment"
    NOT_SENT = "not_sent"
    FAILURE = "failure"
    SUCCESS_TRANSPORT = "success_transport"
    RESTRICTED = "restricted"
    MALFORMED = "malformed"
    DISPATCH_AMBIGUOUS = "dispatch_ambiguous"
    RESULT_AMBIGUOUS = "result_ambiguous"
    DUPLICATE = "duplicate"
    EXPIRED_LEASE = "expired_lease"
    RESTART_REPLAY = "restart_replay"


@dataclass(slots=True)
class EgressAgentSimulator:
    agent_id: UUID
    assignment_id: UUID = field(default_factory=uuid4)
    lease_id: UUID = field(default_factory=uuid4)
    _last: AgentMessage | None = None

    def run(self, scenario: SimulatorScenario | str) -> AgentMessage:
        name = SimulatorScenario(scenario)
        if name is SimulatorScenario.HEARTBEAT:
            message = AgentMessage(
                MessageType.HEARTBEAT,
                self.agent_id,
                correlation_id="sim-heartbeat",
                heartbeat_state="ONLINE",
            )
        else:
            effects = {
                SimulatorScenario.ACCEPTED_ASSIGNMENT: None,
                SimulatorScenario.NOT_SENT: TransportEffect.NOT_SENT,
                SimulatorScenario.FAILURE: TransportEffect.FAILURE,
                SimulatorScenario.SUCCESS_TRANSPORT: TransportEffect.SUCCESS_TRANSPORT_ONLY,
                SimulatorScenario.RESTRICTED: TransportEffect.RESTRICTED,
                SimulatorScenario.MALFORMED: TransportEffect.MALFORMED,
                SimulatorScenario.DISPATCH_AMBIGUOUS: TransportEffect.AMBIGUOUS,
                SimulatorScenario.RESULT_AMBIGUOUS: TransportEffect.RECONCILIATION_REQUIRED,
                SimulatorScenario.EXPIRED_LEASE: TransportEffect.RECONCILIATION_REQUIRED,
                SimulatorScenario.RESTART_REPLAY: TransportEffect.RECONCILIATION_REQUIRED,
                SimulatorScenario.DUPLICATE: self._last.effect
                if self._last
                else TransportEffect.RECONCILIATION_REQUIRED,
            }
            message = AgentMessage(
                MessageType.RECEIPT if effects[name] is None else MessageType.OUTCOME,
                self.agent_id,
                self.assignment_id,
                self.lease_id,
                "sim-assignment",
                effects[name],
                name.value,
            )
        if name is SimulatorScenario.RESTART_REPLAY and self._last is not None:
            return self._last
        self._last = message
        return message


__all__ = ["EgressAgentSimulator", "SimulatorScenario"]
