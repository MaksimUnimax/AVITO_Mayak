"""Platform primitives for Mayak."""

from mayak.platform.boundaries import MODULE_IDS, PLATFORM_AND_CONTRACTS_MODULE_ID
from mayak.platform.idempotency import (
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)

MODULE_ID = PLATFORM_AND_CONTRACTS_MODULE_ID

__all__ = [
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
    "MODULE_ID",
    "MODULE_IDS",
]
