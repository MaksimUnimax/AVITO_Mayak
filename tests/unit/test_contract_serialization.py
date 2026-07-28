from __future__ import annotations

import hashlib
import json
from enum import Enum
from uuid import UUID

import pytest
from pydantic import BaseModel, ConfigDict, Field

from mayak.contracts import (
    CommonOutcome,
    ContractMetadata,
    ContractSerializationError,
    Result,
    canonical_contract_bytes,
    canonical_contract_sha256,
    canonical_contract_text,
    decode_contract_json,
)


class _Colour(str, Enum):
    BLUE = "blue"


class _NestedContract(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    zeta: dict[str, int]
    alpha: str = Field(alias="displayName")
    colour: _Colour
    values: tuple[int, ...]
    ratio: float = 1.0
    optional: str | None = None


def _nested() -> _NestedContract:
    return _NestedContract(
        displayName="Привет, мир 🌍",
        colour=_Colour.BLUE,
        values=(1, 2, 3),
        zeta={"z": 3, "a": 1},
    )


def test_canonical_contract_text_is_stable_and_recursively_sorted() -> None:
    assert canonical_contract_text(_nested()) == (
        '{"colour":"blue","displayName":"Привет, мир 🌍","optional":null,'
        '"ratio":1.0,"values":[1,2,3],"zeta":{"a":1,"z":3}}'
    )


def test_canonical_contract_bytes_are_utf8_without_bom_or_newline() -> None:
    payload = canonical_contract_bytes(_nested())
    assert payload == canonical_contract_text(_nested()).encode("utf-8")
    assert payload.startswith(b"\xef\xbb\xbf") is False
    assert payload.endswith(b"\n") is False
    assert payload == payload.rstrip()


def test_canonical_contract_sha256_matches_exact_canonical_bytes() -> None:
    payload = canonical_contract_bytes(_nested())
    assert canonical_contract_sha256(_nested()) == hashlib.sha256(payload).hexdigest()


def test_canonical_contract_serializes_uuid_enum_tuple_and_none() -> None:
    assert json.loads(canonical_contract_text(_nested())) == {
        "colour": "blue",
        "displayName": "Привет, мир 🌍",
        "optional": None,
        "ratio": 1.0,
        "values": [1, 2, 3],
        "zeta": {"a": 1, "z": 3},
    }
    metadata = ContractMetadata(
        contract_name="scan.requested",
        contract_version="1.0",
        message_id=UUID(int=1),
        correlation_id=UUID(int=2),
        producer="mayak.tests",
    )
    assert json.loads(canonical_contract_text(metadata))["message_id"] == str(UUID(int=1))


def test_canonical_contract_preserves_unicode_without_ascii_escaping() -> None:
    assert "Привет" in canonical_contract_text(_nested())
    assert "\\u" not in canonical_contract_text(_nested())


def test_canonical_contract_repeated_calls_do_not_mutate_model() -> None:
    model = _nested()
    before = model.model_dump()
    canonical_contract_bytes(model)
    assert model.model_dump() == before


def test_canonical_contract_rejects_non_model_input_without_payload() -> None:
    marker = "payload-marker-serialization"
    with pytest.raises(ContractSerializationError, match="Pydantic model") as exc_info:
        canonical_contract_bytes({"value": marker})  # type: ignore[arg-type]
    assert marker not in str(exc_info.value)


def test_canonical_contract_rejects_non_finite_values_without_payload() -> None:
    model = _NestedContract.model_construct(
        alpha="safe", colour=_Colour.BLUE, values=(1,), ratio=float("nan"), zeta={"number": 1}
    )
    with pytest.raises(ContractSerializationError) as exc_info:
        canonical_contract_bytes(model)
    assert "nan" not in str(exc_info.value).lower()


def test_decode_contract_json_round_trips_contract_metadata() -> None:
    model = ContractMetadata(
        contract_name="scan.requested",
        contract_version="1.0",
        message_id=UUID(int=1),
        correlation_id=UUID(int=2),
        producer="mayak.tests",
    )
    assert decode_contract_json(ContractMetadata, canonical_contract_bytes(model)) == model


def test_decode_contract_json_round_trips_common_outcome() -> None:
    model = CommonOutcome(result=Result.SUCCEEDED, reason_code="DONE", details=("one", "two"))
    assert decode_contract_json(CommonOutcome, canonical_contract_text(model)) == model


def test_decode_contract_json_accepts_bytes_and_text() -> None:
    model = _nested()
    payload = canonical_contract_text(model)
    assert decode_contract_json(_NestedContract, payload.encode("utf-8")) == model
    assert decode_contract_json(_NestedContract, payload) == model


def test_decode_contract_json_rejects_malformed_utf8_without_payload() -> None:
    with pytest.raises(ContractSerializationError) as exc_info:
        decode_contract_json(_NestedContract, b'{"alpha":"\xff"}')
    assert "ff" not in str(exc_info.value).lower()


def test_decode_contract_json_rejects_malformed_json_and_non_finite_constants() -> None:
    for payload in ('{"alpha":', '{"alpha":NaN}'):
        with pytest.raises(ContractSerializationError) as exc_info:
            decode_contract_json(_NestedContract, payload)
        assert "NaN" not in str(exc_info.value)


def test_decode_contract_json_rejects_non_object_top_level() -> None:
    with pytest.raises(ContractSerializationError, match="JSON object"):
        decode_contract_json(_NestedContract, "[]")


def test_decode_contract_json_rejects_unknown_fields_and_model_mismatch_without_payload() -> None:
    marker = "payload-marker-validation"
    with pytest.raises(ContractSerializationError) as exc_info:
        decode_contract_json(_NestedContract, json.dumps({"unknown": marker}))
    assert marker not in str(exc_info.value)
    with pytest.raises(ContractSerializationError, match="requested model"):
        decode_contract_json(ContractMetadata, canonical_contract_text(_nested()))


def test_public_contract_package_exports_canonical_serialization_api() -> None:
    import mayak.contracts as contracts

    names = {
        "ContractSerializationError",
        "canonical_contract_bytes",
        "canonical_contract_text",
        "canonical_contract_sha256",
        "decode_contract_json",
    }
    assert names <= set(contracts.__all__)
    assert all(hasattr(contracts, name) for name in names)
