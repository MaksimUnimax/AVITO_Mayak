"""Public contract primitives for Mayak."""

from mayak.contracts.errors import CommonErrorOutcome, ErrorCategory, RetryClass
from mayak.contracts.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionOutcome,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.contracts.metadata import ContractMetadata
from mayak.contracts.results import CommonOutcome, Result, ResultOutcome
from mayak.platform.boundaries import PLATFORM_AND_CONTRACTS_MODULE_ID

MODULE_ID = PLATFORM_AND_CONTRACTS_MODULE_ID

__all__ = [
    "CommonErrorOutcome",
    "CommonOutcome",
    "ContractMetadata",
    "ErrorCategory",
    "IdempotencyDecision",
    "IdempotencyDecisionOutcome",
    "IdempotencyFingerprint",
    "IdempotencyKey",
    "IdempotencyScope",
    "MODULE_ID",
    "Result",
    "ResultOutcome",
    "RetryClass",
]
