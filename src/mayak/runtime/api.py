"""Executable mayak-api process entrypoint."""

from __future__ import annotations

import logging

import uvicorn

from mayak.entrypoints.api import create_app
from mayak.runtime.settings import load_runtime_settings

LOGGER = logging.getLogger("mayak.api")


def main() -> None:
    settings = load_runtime_settings()
    if settings.runtime.process_kind.value != "mayak-api":
        raise RuntimeError("invalid process kind")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    LOGGER.info(
        "api process start environment=%s source_sha=%s process=%s",
        settings.build.environment_id,
        settings.build.source_sha,
        settings.runtime.process_kind.value,
    )
    uvicorn.run(
        create_app(settings=settings),
        host=settings.api.bind_host,
        port=settings.api.internal_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()


__all__ = ["main"]
