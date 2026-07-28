from __future__ import annotations

from types import MappingProxyType

import pytest

import mayak.contracts as contracts
from mayak.contracts.error_mapping import (
    ExceptionMapping,
    ExceptionNormalizationError,
    ExceptionNormalizer,
    build_platform_exception_normalizer,
)
from mayak.contracts.errors import CommonErrorOutcome, ErrorCategory, RetryClass
from mayak.platform.errors import (
    BoundaryViolationError,
    MayakError,
    UnsupportedDependencyError,
)


def mapping(exception_type: type[Exception], reason_code: str) -> ExceptionMapping:
    return ExceptionMapping(
        exception_type, ErrorCategory.CONFLICT, RetryClass.CONDITIONAL, reason_code
    )


def test_exception_mapping_accepts_stripped_safe_mapping() -> None:
    result = ExceptionMapping(ValueError, ErrorCategory.NOT_FOUND, RetryClass.NEVER, "  SAFE  ")
    assert result.reason_code == "SAFE"


def test_exception_mapping_rejects_non_exception_types() -> None:
    for value in (object, BaseException, SystemExit, KeyboardInterrupt, 42):
        with pytest.raises(
            ExceptionNormalizationError,
            match="^exception_type must be an Exception subclass$",
        ):
            ExceptionMapping(value, ErrorCategory.INTERNAL_FAILURE, RetryClass.NEVER, "X")  # type: ignore[arg-type]


def test_exception_mapping_rejects_invalid_category_retry_and_reason() -> None:
    with pytest.raises(ExceptionNormalizationError, match="^error_category must be ErrorCategory$"):
        ExceptionMapping(ValueError, "INVALID", RetryClass.NEVER, "X")  # type: ignore[arg-type]
    with pytest.raises(ExceptionNormalizationError, match="^retry_class must be RetryClass$"):
        ExceptionMapping(ValueError, ErrorCategory.INTERNAL_FAILURE, "NEVER", "X")  # type: ignore[arg-type]
    for reason in ("", "   ", 1):
        with pytest.raises(ExceptionNormalizationError, match="^reason_code must be non-empty$"):
            ExceptionMapping(ValueError, ErrorCategory.INTERNAL_FAILURE, RetryClass.NEVER, reason)  # type: ignore[arg-type]


def test_normalizer_rejects_duplicate_exact_exception_type() -> None:
    with pytest.raises(
        ExceptionNormalizationError,
        match="^duplicate exception type registration$",
    ):
        ExceptionNormalizer([mapping(ValueError, "A"), mapping(ValueError, "B")])


def test_normalizer_is_order_independent_and_detached_from_input_collection() -> None:
    class RootError(Exception):
        pass

    class LeafError(RootError):
        pass

    items = [mapping(RootError, "ROOT"), mapping(LeafError, "LEAF")]
    first = ExceptionNormalizer(items)
    second = ExceptionNormalizer(reversed(items))
    items.clear()
    assert first.normalize(LeafError()).reason_code == "LEAF"
    assert second.normalize(LeafError()).reason_code == "LEAF"


def test_normalizer_maps_exact_registered_exception() -> None:
    result = ExceptionNormalizer([mapping(ValueError, "VALUE")]).normalize(ValueError())
    assert result.reason_code == "VALUE"


def test_normalizer_uses_most_specific_registered_mro_mapping() -> None:
    class Parent(Exception):
        pass

    class Child(Parent):
        pass

    result = ExceptionNormalizer(
        [mapping(Parent, "PARENT"), mapping(Child, "CHILD")]
    ).normalize(Child())
    assert result.reason_code == "CHILD"


def test_normalizer_uses_registered_base_mapping_for_unregistered_subclass() -> None:
    class Parent(Exception):
        pass

    class Child(Parent):
        pass

    result = ExceptionNormalizer([mapping(Parent, "PARENT")]).normalize(Child())
    assert result.reason_code == "PARENT"


def test_normalizer_returns_fixed_unknown_exception_fallback() -> None:
    assert ExceptionNormalizer([]).normalize(RuntimeError("secret")) == CommonErrorOutcome(
        error_category=ErrorCategory.INTERNAL_FAILURE,
        retry_class=RetryClass.NEVER,
        reason_code="UNHANDLED_EXCEPTION",
        message=None,
        details=(),
    )


def test_normalizer_never_reads_exception_str_repr_or_args() -> None:
    class Hostile(Exception):
        @property
        def args(self) -> tuple[str, ...]:  # type: ignore[override]
            raise AssertionError("SECRET_ARGS")

        def __str__(self) -> str:
            raise AssertionError("SECRET_STR")

        def __repr__(self) -> str:
            raise AssertionError("SECRET_REPR")

    result = ExceptionNormalizer([]).normalize(Hostile("SECRET_VALUE"))
    assert result.reason_code == "UNHANDLED_EXCEPTION"


def test_normalizer_never_reads_custom_exception_attributes() -> None:
    class Hostile(Exception):
        @property
        def secret(self) -> str:
            raise AssertionError("SECRET_ATTRIBUTE")

    result = ExceptionNormalizer([]).normalize(Hostile())
    assert result.error_category is ErrorCategory.INTERNAL_FAILURE


def test_normalizer_ignores_exception_cause_context_and_traceback() -> None:
    cause = RuntimeError("SECRET_CAUSE")
    context = RuntimeError("SECRET_CONTEXT")
    exception = ValueError("SECRET_MAIN")
    exception.__cause__ = cause
    exception.__context__ = context
    assert ExceptionNormalizer([]).normalize(exception).reason_code == "UNHANDLED_EXCEPTION"


def test_normalizer_rejects_non_exception_input_safely() -> None:
    with pytest.raises(
        ExceptionNormalizationError,
        match="^exception must be an Exception instance$",
    ):
        ExceptionNormalizer([]).normalize(object())  # type: ignore[arg-type]


def test_normalizer_rejects_system_exit_and_keyboard_interrupt() -> None:
    normalizer = ExceptionNormalizer([])
    for exception in (SystemExit("SECRET_EXIT"), KeyboardInterrupt()):
        with pytest.raises(
            ExceptionNormalizationError,
            match="^exception must be an Exception instance$",
        ):
            normalizer.normalize(exception)  # type: ignore[arg-type]


def test_platform_normalizer_maps_boundary_violation() -> None:
    result = build_platform_exception_normalizer().normalize(BoundaryViolationError())
    assert result.reason_code == "BOUNDARY_VIOLATION"


def test_platform_normalizer_maps_unsupported_dependency() -> None:
    result = build_platform_exception_normalizer().normalize(UnsupportedDependencyError())
    assert result.reason_code == "UNSUPPORTED_DEPENDENCY"


def test_platform_normalizer_maps_generic_mayak_error() -> None:
    result = build_platform_exception_normalizer().normalize(MayakError())
    assert result.reason_code == "MAYAK_ERROR"


def test_platform_normalizer_keeps_builtin_exception_on_unknown_fallback() -> None:
    result = build_platform_exception_normalizer().normalize(ValueError("SECRET_BUILTIN"))
    assert result.reason_code == "UNHANDLED_EXCEPTION"
    assert result.retry_class is RetryClass.NEVER


def test_platform_normalizer_builder_returns_independent_immutable_instances() -> None:
    first = build_platform_exception_normalizer()
    second = build_platform_exception_normalizer()
    assert first is not second
    assert isinstance(first._mappings, MappingProxyType)  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        first._mappings[ValueError] = mapping(ValueError, "X")  # type: ignore[attr-defined,index]


def test_public_contract_package_exports_exception_normalization_api() -> None:
    names = {
        "ExceptionMapping",
        "ExceptionNormalizationError",
        "ExceptionNormalizer",
        "build_platform_exception_normalizer",
    }
    assert names <= set(contracts.__all__)
    assert all(getattr(contracts, name) is globals()[name] for name in names)
