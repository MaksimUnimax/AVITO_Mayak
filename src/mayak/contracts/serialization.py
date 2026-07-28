"""Deterministic JSON serialization for public Pydantic contracts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import BaseModel

ContractModelT = TypeVar("ContractModelT", bound=BaseModel)


class ContractSerializationError(ValueError):
    """Raised when a contract cannot be safely serialized or decoded."""


def canonical_contract_bytes(contract: BaseModel) -> bytes:
    """Return the deterministic UTF-8 JSON representation of a contract."""
    if not isinstance(contract, BaseModel):
        raise ContractSerializationError("contract must be a Pydantic model")

    try:
        dumped = contract.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=False,
            round_trip=True,
        )
        if not isinstance(dumped, Mapping):
            raise ContractSerializationError("contract cannot be serialized as canonical JSON")
        text = json.dumps(
            dumped,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        return text.encode("utf-8", errors="strict")
    except ContractSerializationError:
        raise
    except (TypeError, ValueError, UnicodeError, OverflowError):
        raise ContractSerializationError(
            "contract cannot be serialized as canonical JSON"
        ) from None


def canonical_contract_text(contract: BaseModel) -> str:
    """Return canonical contract bytes decoded as UTF-8."""
    return canonical_contract_bytes(contract).decode("utf-8", errors="strict")


def canonical_contract_sha256(contract: BaseModel) -> str:
    """Return the SHA-256 digest of the canonical contract bytes."""
    return hashlib.sha256(canonical_contract_bytes(contract)).hexdigest()


def decode_contract_json(
    model_type: type[ContractModelT],
    payload: bytes | str,
) -> ContractModelT:
    """Decode a JSON object into the explicitly requested contract model."""
    if not isinstance(model_type, type) or not issubclass(model_type, BaseModel):
        raise ContractSerializationError("model_type must be a Pydantic model class")
    if not isinstance(payload, (bytes, str)):
        raise ContractSerializationError("contract payload must be UTF-8 JSON")

    try:
        text = payload.decode("utf-8", errors="strict") if isinstance(payload, bytes) else payload
        parsed: Any = json.loads(
            text,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError),
        )
        if not isinstance(parsed, dict):
            raise ContractSerializationError("contract payload must be a JSON object")
        return model_type.model_validate(parsed)
    except ContractSerializationError:
        raise
    except (UnicodeError, TypeError, ValueError, OverflowError):
        raise ContractSerializationError(
            "contract payload does not match the requested model"
        ) from None


__all__ = [
    "ContractSerializationError",
    "canonical_contract_bytes",
    "canonical_contract_text",
    "canonical_contract_sha256",
    "decode_contract_json",
]
