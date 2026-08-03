"""Traceable supersession of the pre-RF16 persistence gate."""

from __future__ import annotations

from dataclasses import dataclass

RF16_TASK_ID = "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01"


@dataclass(frozen=True, slots=True)
class EgressRF16RuntimeAuthority:
    task_id: str = RF16_TASK_ID
    exact_base_sha: str = "696ecc9c6759f14c81a512af6f1c0d71a81e552f"
    durable_server_runtime_authorized: bool = True
    transport_neutral_agent_boundary_authorized: bool = True
    live_networking_authorized: bool = False
    production_readiness_inferred: bool = False


__all__ = ["EgressRF16RuntimeAuthority", "RF16_TASK_ID"]
