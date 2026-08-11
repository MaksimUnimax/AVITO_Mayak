"""Fail-closed RF26 PostgreSQL container identity parsing."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

EXPECTED_CONFIG_IMAGE = (
    "postgres:18-bookworm@sha256:"
    "882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"
)
EXPECTED_REPO_DIGEST = (
    "postgres@sha256:"
    "882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382"
)


class DiscoveryError(ValueError):
    """Raised when Docker inspect data cannot prove the RF26 identity."""


def _object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DiscoveryError(f"{field} is not an object")
    return value


def _one_inspect(payload: str) -> dict[str, Any]:
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DiscoveryError("malformed Docker inspect JSON") from exc
    if not isinstance(decoded, list) or len(decoded) != 1:
        raise DiscoveryError("Docker inspect must contain exactly one object")
    return _object(decoded[0], field="inspect entry")


def _repo_digests(payload: str) -> list[str]:
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DiscoveryError("malformed Docker RepoDigests JSON") from exc
    if not isinstance(decoded, list) or any(not isinstance(item, str) for item in decoded):
        raise DiscoveryError("RepoDigests must be a JSON string list")
    return decoded


def prove_match(inspect_payload: str, repo_digests_payload: str) -> str:
    """Return the image ID only when every RF26 identity property is proven."""
    entry = _one_inspect(inspect_payload)
    config = _object(entry.get("Config"), field="Config")
    if config.get("Image") != EXPECTED_CONFIG_IMAGE:
        raise DiscoveryError("unexpected Config.Image")
    image_id = entry.get("Image")
    if not isinstance(image_id, str) or not image_id:
        raise DiscoveryError("missing container Image")
    state = _object(entry.get("State"), field="State")
    health = _object(state.get("Health"), field="State.Health")
    if health.get("Status") != "healthy":
        raise DiscoveryError("container is not healthy")
    network_settings = _object(entry.get("NetworkSettings"), field="NetworkSettings")
    networks = _object(network_settings.get("Networks"), field="NetworkSettings.Networks")
    aliases: list[str] = []
    for network_name, network in networks.items():
        network_object = _object(network, field=f"network {network_name}")
        network_aliases = network_object.get("Aliases")
        if network_aliases is None:
            continue
        if not isinstance(network_aliases, list) or any(
            not isinstance(alias, str) for alias in network_aliases
        ):
            raise DiscoveryError("network aliases are malformed")
        aliases.extend(network_aliases)
    if "mayak-postgres" not in aliases:
        raise DiscoveryError("required network alias is absent")
    if EXPECTED_REPO_DIGEST not in _repo_digests(repo_digests_payload):
        raise DiscoveryError("expected RepoDigest is absent")
    return image_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-digests", required=True)
    args = parser.parse_args()
    try:
        print(prove_match(sys.stdin.read(), args.repo_digests))
    except DiscoveryError as exc:
        print(f"RF26 Docker discovery rejected candidate: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
