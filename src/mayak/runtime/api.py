"""Executable mayak-api process entrypoint."""

from __future__ import annotations

import uvicorn

from mayak.entrypoints.api import create_app
from mayak.runtime.settings import load_runtime_settings


def main() -> None:
    settings = load_runtime_settings()
    if settings.runtime.process_kind.value != "mayak-api":
        raise RuntimeError("invalid process kind")
    uvicorn.run(
        create_app(settings=settings),
        host=settings.api.bind_host,
        port=settings.api.internal_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()


__all__ = ["main"]
