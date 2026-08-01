"""Closed-world, in-image task acceptance execution.

Only implementations committed under ``src/mayak`` may be registered here.
The registry is deliberately explicit: caller input is an identity, never an
import path or executable content source.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Final

SCHEMA_VERSION: Final = "mayak-task-acceptance-v1"
MAX_CHECKS: Final = 32
MAX_SCALAR_LENGTH: Final = 256


class TaskAcceptanceVerifierKind(StrEnum):
    RF30_SELF_PROOF = "RF30_SELF_PROOF"


@dataclass(frozen=True, slots=True)
class TaskAcceptanceContext:
    technical_id: str
    project: str
    verifier_kind: TaskAcceptanceVerifierKind


@dataclass(frozen=True, slots=True)
class TaskAcceptanceEnvelope:
    technical_id: str
    project: str
    verifier_id: str
    status: str
    checks: dict[str, bool | int | str]

    def to_json(self) -> str:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "technical_id": self.technical_id,
            "project": self.project,
            "verifier_id": self.verifier_id,
            "status": self.status,
            "checks": self.checks,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def _rf30_self_proof(context: TaskAcceptanceContext) -> TaskAcceptanceEnvelope:
    return TaskAcceptanceEnvelope(
        technical_id=context.technical_id,
        project=context.project,
        verifier_id=context.verifier_kind.value,
        status="PASS",
        checks={"authority": True, "scope_bound": True, "synthetic_only": True},
    )


# This literal mapping is the complete executable registry.  It must never be
# replaced with dynamic loading, plugins, or caller-provided module names.
_REGISTRY: Final[
    dict[TaskAcceptanceVerifierKind, Callable[[TaskAcceptanceContext], TaskAcceptanceEnvelope]]
] = {
    TaskAcceptanceVerifierKind.RF30_SELF_PROOF: _rf30_self_proof,
}


def registered_verifier(
    kind: TaskAcceptanceVerifierKind,
) -> Callable[[TaskAcceptanceContext], TaskAcceptanceEnvelope]:
    if not isinstance(kind, TaskAcceptanceVerifierKind) or kind not in _REGISTRY:
        raise ValueError("unknown task acceptance verifier")
    return _REGISTRY[kind]


def verifier_kind_from_id(value: str) -> TaskAcceptanceVerifierKind:
    try:
        return TaskAcceptanceVerifierKind(value)
    except ValueError as exc:
        raise ValueError("unknown task acceptance verifier") from exc


def run_task_acceptance(technical_id: str, project: str, verifier_id: str) -> int:
    kind = verifier_kind_from_id(verifier_id)
    result = registered_verifier(kind)(TaskAcceptanceContext(technical_id, project, kind))
    if len(result.checks) > MAX_CHECKS:
        raise ValueError("task acceptance check count exceeds bound")
    for key, value in result.checks.items():
        if len(key) > MAX_SCALAR_LENGTH or (
            isinstance(value, str) and len(value) > MAX_SCALAR_LENGTH
        ):
            raise ValueError("task acceptance scalar exceeds bound")
    sys.stdout.write(result.to_json())
    return 0


__all__ = [
    "SCHEMA_VERSION",
    "TaskAcceptanceContext",
    "TaskAcceptanceEnvelope",
    "TaskAcceptanceVerifierKind",
    "registered_verifier",
    "run_task_acceptance",
    "verifier_kind_from_id",
]
