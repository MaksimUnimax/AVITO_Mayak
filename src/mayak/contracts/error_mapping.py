"""Safe normalization of application exceptions into contract outcomes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType

from mayak.contracts.errors import CommonErrorOutcome, ErrorCategory, RetryClass
from mayak.platform.errors import (
    BoundaryViolationError,
    MayakError,
    UnsupportedDependencyError,
)


class ExceptionNormalizationError(ValueError):
    """Raised when an exception mapping or input is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class ExceptionMapping:
    """Static, exception-independent outcome mapping."""

    exception_type: type[Exception]
    error_category: ErrorCategory
    retry_class: RetryClass
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.exception_type, type) or not issubclass(
            self.exception_type, Exception
        ):
            raise ExceptionNormalizationError(
                "exception_type must be an Exception subclass"
            )
        if not isinstance(self.error_category, ErrorCategory):
            raise ExceptionNormalizationError("error_category must be ErrorCategory")
        if not isinstance(self.retry_class, RetryClass):
            raise ExceptionNormalizationError("retry_class must be RetryClass")
        if not isinstance(self.reason_code, str):
            raise ExceptionNormalizationError("reason_code must be non-empty")
        reason_code = self.reason_code.strip()
        if not reason_code:
            raise ExceptionNormalizationError("reason_code must be non-empty")
        object.__setattr__(self, "reason_code", reason_code)


class ExceptionNormalizer:
    """Resolve exact exception classes to immutable safe outcomes."""

    def __init__(self, mappings: Iterable[ExceptionMapping]) -> None:
        resolved: dict[type[Exception], ExceptionMapping] = {}
        for mapping in mappings:
            if not isinstance(mapping, ExceptionMapping):
                raise ExceptionNormalizationError("mapping must be ExceptionMapping")
            if mapping.exception_type in resolved:
                raise ExceptionNormalizationError(
                    "duplicate exception type registration"
                )
            resolved[mapping.exception_type] = mapping
        self._mappings = MappingProxyType(resolved)

    def normalize(self, exception: Exception) -> CommonErrorOutcome:
        if not isinstance(exception, Exception):
            raise ExceptionNormalizationError("exception must be an Exception instance")

        mapping = next(
            (
                self._mappings[exception_type]
                for exception_type in type(exception).__mro__
                if exception_type in self._mappings
            ),
            None,
        )
        if mapping is None:
            return CommonErrorOutcome(
                error_category=ErrorCategory.INTERNAL_FAILURE,
                retry_class=RetryClass.NEVER,
                reason_code="UNHANDLED_EXCEPTION",
                message=None,
                details=(),
            )
        return CommonErrorOutcome(
            error_category=mapping.error_category,
            retry_class=mapping.retry_class,
            reason_code=mapping.reason_code,
            message=None,
            details=(),
        )


def build_platform_exception_normalizer() -> ExceptionNormalizer:
    """Build the fixed platform exception mappings."""

    return ExceptionNormalizer(
        (
            ExceptionMapping(
                exception_type=BoundaryViolationError,
                error_category=ErrorCategory.PRECONDITION_FAILED,
                retry_class=RetryClass.NEVER,
                reason_code="BOUNDARY_VIOLATION",
            ),
            ExceptionMapping(
                exception_type=UnsupportedDependencyError,
                error_category=ErrorCategory.PRECONDITION_FAILED,
                retry_class=RetryClass.NEVER,
                reason_code="UNSUPPORTED_DEPENDENCY",
            ),
            ExceptionMapping(
                exception_type=MayakError,
                error_category=ErrorCategory.INTERNAL_FAILURE,
                retry_class=RetryClass.NEVER,
                reason_code="MAYAK_ERROR",
            ),
        )
    )


__all__ = [
    "ExceptionMapping",
    "ExceptionNormalizationError",
    "ExceptionNormalizer",
    "build_platform_exception_normalizer",
]
