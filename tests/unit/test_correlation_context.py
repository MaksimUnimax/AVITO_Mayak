"""Tests for execution-context-local correlation propagation."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

import mayak.platform as platform
from mayak.platform.correlation import CorrelationContext, CorrelationId, RequestId
from mayak.platform.correlation_context import (
    CorrelationContextError,
    correlation_context_scope,
    current_correlation_context,
    require_correlation_context,
)


def _context(value: str, *, request: str | None = None) -> CorrelationContext:
    return CorrelationContext(
        correlation_id=CorrelationId(value=value),
        request_id=RequestId(value=request) if request is not None else None,
    )


def test_current_correlation_context_is_none_when_unbound() -> None:
    assert current_correlation_context() is None


def test_require_correlation_context_fails_safely_when_unbound() -> None:
    with pytest.raises(CorrelationContextError, match="^correlation context is not bound$"):
        require_correlation_context()


def test_correlation_context_scope_rejects_non_context_input() -> None:
    assert current_correlation_context() is None
    with pytest.raises(
        CorrelationContextError,
        match="^correlation context must be a CorrelationContext$",
    ):
        with correlation_context_scope(object()):  # type: ignore[arg-type]
            pass
    assert current_correlation_context() is None


def test_correlation_context_scope_yields_exact_context() -> None:
    context = _context("scope", request="request")
    with correlation_context_scope(context) as yielded:
        assert yielded is context


def test_current_correlation_context_returns_exact_bound_context() -> None:
    context = _context("current")
    with correlation_context_scope(context):
        assert current_correlation_context() is context


def test_require_correlation_context_returns_exact_bound_context() -> None:
    context = _context("required")
    with correlation_context_scope(context):
        assert require_correlation_context() is context


def test_nested_scope_temporarily_overrides_outer_context() -> None:
    outer = _context("outer")
    inner = _context("inner")
    with correlation_context_scope(outer):
        with correlation_context_scope(inner):
            assert current_correlation_context() is inner


def test_nested_scope_restores_outer_context() -> None:
    outer = _context("outer")
    inner = _context("inner")
    with correlation_context_scope(outer):
        with correlation_context_scope(inner):
            pass
        assert current_correlation_context() is outer


def test_scope_restores_unbound_state_after_normal_exit() -> None:
    with correlation_context_scope(_context("normal")):
        assert current_correlation_context() is not None
    assert current_correlation_context() is None


def test_scope_restores_prior_context_after_exception() -> None:
    outer = _context("outer")
    error = ValueError("sentinel")
    with correlation_context_scope(outer):
        with pytest.raises(ValueError) as caught:
            with correlation_context_scope(_context("inner")):
                raise error
        assert caught.value is error
        assert current_correlation_context() is outer


def test_scope_restores_prior_context_after_base_exception() -> None:
    outer = _context("outer")
    error = KeyboardInterrupt()
    with correlation_context_scope(outer):
        with pytest.raises(KeyboardInterrupt) as caught:
            with correlation_context_scope(_context("inner")):
                raise error
        assert caught.value is error
        assert current_correlation_context() is outer


def test_repeated_scope_entry_does_not_leak_context() -> None:
    for value in ("first", "second", "third"):
        with correlation_context_scope(_context(value)):
            assert current_correlation_context() is not None
        assert current_correlation_context() is None


def test_context_binding_does_not_mutate_frozen_contract() -> None:
    context = _context("frozen", request="request")
    before = context.model_dump(mode="python")
    with correlation_context_scope(context):
        pass
    assert context.model_dump(mode="python") == before


@pytest.mark.asyncio
async def test_async_child_task_inherits_context_at_creation() -> None:
    parent = _context("parent")
    later = _context("later")
    ready = asyncio.Event()
    release = asyncio.Event()

    async def child() -> CorrelationContext | None:
        ready.set()
        await release.wait()
        return current_correlation_context()

    with correlation_context_scope(parent):
        task = asyncio.create_task(child())
        await ready.wait()
        with correlation_context_scope(later):
            release.set()
            assert await task is parent


@pytest.mark.asyncio
async def test_async_sibling_tasks_keep_isolated_contexts() -> None:
    first = _context("first")
    second = _context("second")
    barrier = asyncio.Barrier(2)

    async def worker(context: CorrelationContext) -> CorrelationContext | None:
        with correlation_context_scope(context):
            await barrier.wait()
            return current_correlation_context()

    results = await asyncio.gather(worker(first), worker(second))
    assert results[0] is first
    assert results[1] is second


@pytest.mark.asyncio
async def test_async_nested_scope_restores_task_local_context() -> None:
    outer = _context("outer")
    inner = _context("inner")

    async def worker() -> tuple[CorrelationContext | None, CorrelationContext | None]:
        with correlation_context_scope(outer):
            with correlation_context_scope(inner):
                inside = current_correlation_context()
            return inside, current_correlation_context()

    inside, after = await asyncio.create_task(worker())
    assert inside is inner
    assert after is outer
    assert current_correlation_context() is None


def test_new_thread_does_not_inherit_bound_context() -> None:
    parent_context = _context("thread-parent")
    child_context = _context("thread-child")
    worker_started = Event()
    worker_scope_active = Event()
    release_worker = Event()

    def worker() -> tuple[
        CorrelationContext | None,
        CorrelationContext | None,
        CorrelationContext | None,
    ]:
        initial = current_correlation_context()
        worker_started.set()
        with correlation_context_scope(child_context):
            inside = current_correlation_context()
            worker_scope_active.set()
            assert release_worker.wait(timeout=5)
        after = current_correlation_context()
        return initial, inside, after

    with correlation_context_scope(parent_context):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(worker)
            try:
                assert worker_started.wait(timeout=5)
                assert worker_scope_active.wait(timeout=5)
                assert current_correlation_context() is parent_context
                assert current_correlation_context() is not child_context
            finally:
                release_worker.set()
            initial, inside, after = future.result(timeout=5)
            assert initial is None
            assert inside is child_context
            assert after is None
        assert current_correlation_context() is parent_context
    assert current_correlation_context() is None


def test_public_platform_package_exports_correlation_context_api() -> None:
    expected = {
        "CorrelationContextError",
        "correlation_context_scope",
        "current_correlation_context",
        "require_correlation_context",
    }
    assert expected <= set(platform.__all__)
    assert all(hasattr(platform, name) for name in expected)
    assert not any(name.startswith("_") for name in platform.__all__)
