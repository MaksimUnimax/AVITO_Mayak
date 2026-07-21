from __future__ import annotations

import ast
import inspect

import mayak.modules.telegram_adapter as package
from mayak.modules.telegram_adapter import contracts

TG15 = (
    "TelegramRuntimeCapability",
    "TelegramPreGateAllowedSurface",
    "TelegramRuntimeGateKind",
    "TelegramRuntimeGateState",
    "TelegramRuntimeGateReasonCode",
    "TelegramRuntimeGateReference",
    "TelegramRuntimeBoundaryRequest",
    "TelegramRuntimeBoundaryOutcome",
)


def test_eight_symbols_are_public_at_both_boundaries() -> None:
    assert all(hasattr(package, name) and hasattr(contracts, name) for name in TG15)
    assert tuple(name for name in contracts.__all__ if name in TG15) == TG15
    assert tuple(name for name in package.__all__ if name in TG15) == TG15
    assert len(set(TG15)) == 8
    contract_tree = ast.parse(inspect.getsource(contracts))
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id in TG15 for target in node.targets)
        for node in contract_tree.body
    )
    assert tuple(name for name in contracts.__all__ if name in TG15) == TG15


def test_existing_exports_remain_present() -> None:
    assert set(contracts.__all__) <= set(dir(package))
    assert tuple(package.__all__[:1]) == ("MODULE_ID",)
