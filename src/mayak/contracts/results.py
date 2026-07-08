"""Result primitives for public contracts."""

from enum import Enum


class Result(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_NON_RETRYABLE = "FAILED_NON_RETRYABLE"
    AMBIGUOUS = "AMBIGUOUS"
    PARTIAL = "PARTIAL"
