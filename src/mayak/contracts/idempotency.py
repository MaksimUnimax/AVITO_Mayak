"""Idempotency decision primitives for public contracts."""

from enum import Enum


class IdempotencyDecision(str, Enum):
    NEW = "NEW"
    REPLAY_TERMINAL = "REPLAY_TERMINAL"
    PENDING = "PENDING"
    MISMATCH = "MISMATCH"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
