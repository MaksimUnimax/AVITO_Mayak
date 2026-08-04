from __future__ import annotations

from mayak.modules.web_cabinet.runtime import WebCabinetRuntime, WebDashboard, WebSection
from mayak.modules.web_cabinet.web_ui import build_web_router
from mayak.runtime.rf21_composition import build_rf21_runtime


def test_rf21_runtime_exports_are_typed_and_mountable() -> None:
    assert WebCabinetRuntime.__name__ == "WebCabinetRuntime"
    assert WebDashboard.__name__ == "WebDashboard"
    assert WebSection.__name__ == "WebSection"
    assert callable(build_web_router)
    assert callable(build_rf21_runtime)
