"""Idempotency primitives shared by the platform."""

from typing import NewType

IdempotencyFingerprint = NewType("IdempotencyFingerprint", str)
IdempotencyKey = NewType("IdempotencyKey", str)
IdempotencyScope = NewType("IdempotencyScope", str)
