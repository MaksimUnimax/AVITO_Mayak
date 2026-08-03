"""Explicit, inert RF16 agent entry point for the bounded protocol package."""

from __future__ import annotations

from .protocol import PROTOCOL_VERSION, SOURCE_RELEASE


def main() -> int:
    # Transport selection, installation, auto-start, proxy and credentials are
    # intentionally outside this package and require future accepted gates.
    print(f"{SOURCE_RELEASE}:{PROTOCOL_VERSION}")
    return 0


__all__ = ["main"]
