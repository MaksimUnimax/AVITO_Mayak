"""Process-boundary simulator exercising the real RF16 protocol contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from .protocol import SOURCE_RELEASE, AgentMessage, MessageType, TransportEffect


class SimulatorScenario(StrEnum):
    HEARTBEAT = "heartbeat"
    ACCEPTED_ASSIGNMENT = "accepted_assignment"
    NOT_SENT = "not_sent"
    UNAVAILABLE = "unavailable"
    FAILURE = "failure"
    SUCCESS_TRANSPORT = "success_transport"
    RESTRICTED = "restricted"
    MALFORMED = "malformed"
    DISPATCH_AMBIGUOUS = "dispatch_ambiguous"
    RESULT_AMBIGUOUS = "result_ambiguous"
    DUPLICATE = "duplicate"
    MISMATCHED_DUPLICATE = "mismatched_duplicate"
    EXPIRED_LEASE = "expired_lease"
    REVOKED_LEASE = "revoked_lease"
    RESTART_REPLAY = "restart_replay"


@dataclass(slots=True)
class EgressAgentSimulator:
    agent_id: UUID
    assignment_id: UUID = field(default_factory=uuid4)
    lease_id: UUID = field(default_factory=uuid4)
    _durable: dict[str, AgentMessage] = field(default_factory=dict, repr=False)

    def restart(self) -> "EgressAgentSimulator":
        """Create a new process-equivalent object over durable state."""
        return EgressAgentSimulator(
            self.agent_id, self.assignment_id, self.lease_id, dict(self._durable)
        )

    def run(self, scenario: SimulatorScenario | str) -> AgentMessage:
        name = SimulatorScenario(scenario)
        if name is SimulatorScenario.HEARTBEAT:
            return AgentMessage(
                MessageType.HEARTBEAT,
                self.agent_id,
                correlation_id="sim-heartbeat",
                heartbeat_state="ONLINE",
                source_release=SOURCE_RELEASE,
            )
        if name is SimulatorScenario.RESTART_REPLAY and "sim-assignment" in self._durable:
            return self._durable["sim-assignment"]
        if name is SimulatorScenario.DUPLICATE and "sim-assignment" in self._durable:
            return self._durable["sim-assignment"]
        assignment = self.assignment_id
        lease = self.lease_id
        effects = {
            SimulatorScenario.NOT_SENT: TransportEffect.NOT_SENT,
            SimulatorScenario.UNAVAILABLE: TransportEffect.UNAVAILABLE,
            SimulatorScenario.FAILURE: TransportEffect.FAILURE,
            SimulatorScenario.SUCCESS_TRANSPORT: TransportEffect.SUCCESS_TRANSPORT_ONLY,
            SimulatorScenario.RESTRICTED: TransportEffect.RESTRICTED,
            SimulatorScenario.MALFORMED: TransportEffect.MALFORMED_UNUSABLE,
            SimulatorScenario.DISPATCH_AMBIGUOUS: TransportEffect.DISPATCH_AMBIGUOUS,
            SimulatorScenario.RESULT_AMBIGUOUS: TransportEffect.RESULT_AMBIGUOUS,
            SimulatorScenario.EXPIRED_LEASE: TransportEffect.RECONCILIATION_REQUIRED,
            SimulatorScenario.REVOKED_LEASE: TransportEffect.RECONCILIATION_REQUIRED,
            SimulatorScenario.MISMATCHED_DUPLICATE: TransportEffect.RESULT_AMBIGUOUS,
            SimulatorScenario.DUPLICATE: TransportEffect.RECONCILIATION_REQUIRED,
            SimulatorScenario.RESTART_REPLAY: TransportEffect.RECONCILIATION_REQUIRED,
        }
        if name is SimulatorScenario.ACCEPTED_ASSIGNMENT:
            message = AgentMessage(
                MessageType.RECEIPT,
                self.agent_id,
                assignment,
                lease,
                "sim-assignment",
                source_release=SOURCE_RELEASE,
            )
        else:
            if name is SimulatorScenario.MISMATCHED_DUPLICATE:
                assignment = uuid4()
            message = AgentMessage(
                MessageType.OUTCOME,
                self.agent_id,
                assignment,
                lease,
                "sim-assignment",
                effects[name],
                name.value,
                source_release=SOURCE_RELEASE,
            )
        self._durable["sim-assignment"] = message
        return message


__all__ = ["EgressAgentSimulator", "SimulatorScenario"]
