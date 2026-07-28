"""Execution-context-local propagation for correlation contexts."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from mayak.platform.correlation import CorrelationContext


class CorrelationContextError(RuntimeError):
    """Raised when a correlation context binding operation is invalid."""


_CURRENT_CORRELATION_CONTEXT: ContextVar[CorrelationContext | None] = ContextVar(
    "_CURRENT_CORRELATION_CONTEXT", default=None
)


def current_correlation_context() -> CorrelationContext | None:
    """Return the context bound to the current execution context, if any."""

    return _CURRENT_CORRELATION_CONTEXT.get()


def require_correlation_context() -> CorrelationContext:
    """Return the current context or raise a safe error when none is bound."""

    context = current_correlation_context()
    if context is None:
        raise CorrelationContextError("correlation context is not bound")
    return context


@contextmanager
def correlation_context_scope(
    context: CorrelationContext,
) -> Iterator[CorrelationContext]:
    """Temporarily bind an exact context and restore the prior binding."""

    if not isinstance(context, CorrelationContext):
        raise CorrelationContextError("correlation context must be a CorrelationContext")
    token = _CURRENT_CORRELATION_CONTEXT.set(context)
    try:
        yield context
    finally:
        _CURRENT_CORRELATION_CONTEXT.reset(token)


__all__ = [
    "CorrelationContextError",
    "correlation_context_scope",
    "current_correlation_context",
    "require_correlation_context",
]
