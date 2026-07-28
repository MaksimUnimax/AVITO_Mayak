"""Tests for the exact contract identity registry primitive."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest
from pydantic import BaseModel, ConfigDict

import mayak.contracts.registry as registry_module
from mayak.contracts import (
    ContractMetadata,
    ContractRegistration,
    ContractRegistry,
    ContractRegistryError,
    ContractValidationOutcome,
    ContractValidationStatus,
)


class _Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str


class _SiblingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str


class _PayloadChild(_Payload):
    pass


def _metadata(name: str = "sample.contract", version: str = "v 1.0") -> ContractMetadata:
    return ContractMetadata(
        contract_name=name,
        contract_version=version,
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="registry-tests",
    )


def _registration(
    name: str = "sample.contract", version: str = "v 1.0", model: type[BaseModel] = _Payload
) -> ContractRegistration:
    return ContractRegistration(name, version, model)


def test_registration_accepts_stripped_opaque_identity_and_model() -> None:
    registration = ContractRegistration("  sample  ", "  release-odd  ", _Payload)
    assert registration.contract_name == "sample"
    assert registration.contract_version == "release-odd"
    assert registration.model_type is _Payload
    with pytest.raises(FrozenInstanceError):
        registration.contract_version = "other"  # type: ignore[misc]


def test_registration_rejects_blank_name_and_version_safely() -> None:
    for name, version, message in (
        ("  ", "1", "registration contract_name must be non-empty"),
        ("name", "  ", "registration contract_version must be non-empty"),
    ):
        with pytest.raises(ContractRegistryError, match=f"^{message}$"):
            ContractRegistration(name, version, _Payload)


def test_registration_rejects_non_model_type_safely() -> None:
    with pytest.raises(
        ContractRegistryError, match="^registration model_type must be a Pydantic model class$"
    ):
        ContractRegistration("sample", "1", object)  # type: ignore[arg-type]


def test_registry_is_order_independent_and_detached_from_input_collection() -> None:
    registrations = [_registration("a", "1"), _registration("b", "1", _SiblingPayload)]
    first = ContractRegistry(registrations)
    second = ContractRegistry(reversed(registrations))
    registrations.clear()
    assert first.validate_metadata(_metadata("a", "1")) == second.validate_metadata(
        _metadata("a", "1")
    )
    assert first.validate_metadata(_metadata("b", "1")) == second.validate_metadata(
        _metadata("b", "1")
    )


def test_registry_rejects_duplicate_exact_identity() -> None:
    with pytest.raises(ContractRegistryError, match="^duplicate contract identity registration$"):
        ContractRegistry([_registration(), _registration()])


def test_registry_allows_same_name_with_multiple_exact_versions() -> None:
    registry = ContractRegistry([_registration(version="1"), _registration(version="2")])
    assert (
        registry.validate_metadata(_metadata(version="1")).status is ContractValidationStatus.VALID
    )
    assert (
        registry.validate_metadata(_metadata(version="2")).status is ContractValidationStatus.VALID
    )


def test_registry_allows_explicit_model_reuse_across_identities() -> None:
    registry = ContractRegistry([_registration("a", "1"), _registration("b", "2")])
    assert (
        registry.validate_contract(_metadata("a", "1"), _Payload(value="x")).status
        is ContractValidationStatus.VALID
    )
    assert (
        registry.validate_contract(_metadata("b", "2"), _Payload(value="x")).status
        is ContractValidationStatus.VALID
    )


def test_validate_metadata_accepts_exact_registered_identity() -> None:
    outcome = ContractRegistry([_registration()]).validate_metadata(_metadata())
    assert outcome == ContractValidationOutcome(
        ContractValidationStatus.VALID, "CONTRACT_IDENTITY_VALID"
    )
    with pytest.raises(ValueError):
        ContractValidationOutcome(ContractValidationStatus.VALID, "CONTRACT_NAME_UNKNOWN")


def test_validate_metadata_distinguishes_unknown_name() -> None:
    outcome = ContractRegistry([_registration()]).validate_metadata(_metadata("other"))
    assert outcome.status is ContractValidationStatus.UNKNOWN_CONTRACT
    assert outcome.reason_code == "CONTRACT_NAME_UNKNOWN"
    assert "other" not in repr(outcome)


def test_validate_metadata_distinguishes_unsupported_version() -> None:
    outcome = ContractRegistry([_registration()]).validate_metadata(_metadata(version="2"))
    assert outcome.status is ContractValidationStatus.UNSUPPORTED_VERSION
    assert outcome.reason_code == "CONTRACT_VERSION_UNSUPPORTED"


def test_validate_metadata_never_falls_back_to_latest_or_equivalent_version() -> None:
    registry = ContractRegistry([_registration(version="1.0"), _registration(version="v1")])
    for version in ("1", "1.1", "v1.0"):
        assert (
            registry.validate_metadata(_metadata(version=version)).status
            is ContractValidationStatus.UNSUPPORTED_VERSION
        )


def test_validate_contract_accepts_only_exact_registered_model_type() -> None:
    registry = ContractRegistry([_registration()])
    assert (
        registry.validate_contract(_metadata(), _Payload(value="ok")).status
        is ContractValidationStatus.VALID
    )
    with pytest.raises(ContractRegistryError, match="^contract instance must be a Pydantic model$"):
        registry.validate_contract(_metadata(), {"value": "ok"})  # type: ignore[arg-type]


def test_validate_contract_rejects_subclass_and_structural_match() -> None:
    registry = ContractRegistry([_registration()])
    for contract in (_PayloadChild(value="x"), _SiblingPayload(value="x")):
        outcome = registry.validate_contract(_metadata(), contract)
        assert outcome.status is ContractValidationStatus.MODEL_MISMATCH
        assert outcome.reason_code == "CONTRACT_MODEL_MISMATCH"


def test_validate_contract_resolves_identity_before_inspecting_contract() -> None:
    registry = ContractRegistry([_registration()])
    outcome = registry.validate_contract(_metadata("unknown"), object())  # type: ignore[arg-type]
    assert outcome.status is ContractValidationStatus.UNKNOWN_CONTRACT


def test_decode_uses_registered_model_and_canonical_decoder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ContractRegistry([_registration()])
    calls: list[tuple[type[BaseModel], bytes | str]] = []

    def fake_decoder(model_type: type[BaseModel], payload: bytes | str) -> BaseModel:
        calls.append((model_type, payload))
        return _Payload(value="decoded")

    monkeypatch.setattr(registry_module, "decode_contract_json", fake_decoder)
    result = registry.decode(_metadata(), b"canonical-payload")
    assert result == _Payload(value="decoded")
    assert calls == [(_Payload, b"canonical-payload")]


def test_decode_rejects_unknown_and_unsupported_identity_before_payload_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ContractRegistry([_registration()])
    called = False

    def forbidden_decoder(_model_type: type[BaseModel], _payload: bytes | str) -> BaseModel:
        nonlocal called
        called = True
        raise AssertionError("decoder called")

    monkeypatch.setattr(registry_module, "decode_contract_json", forbidden_decoder)
    for metadata, message in (
        (_metadata("unknown"), "contract name is not registered"),
        (_metadata(version="2"), "contract version is not supported"),
    ):
        with pytest.raises(ContractRegistryError, match=f"^{message}$"):
            registry.decode(metadata, b"PAYLOAD-MARKER")
    assert called is False


def test_decode_rejects_invalid_payload_without_payload_or_validation_disclosure() -> None:
    marker = "PAYLOAD-MARKER-SECRET"
    error = None
    try:
        ContractRegistry([_registration()]).decode(_metadata(), marker)
    except ContractRegistryError as caught:
        error = caught
    assert error is not None
    assert str(error) == "contract payload does not match registered identity"
    assert marker not in str(error)
    assert "validation" not in str(error).lower()
    assert "_Payload" not in str(error)


def test_public_contract_package_exports_registry_api() -> None:
    import mayak.contracts as contracts

    expected = {
        "ContractRegistration",
        "ContractRegistry",
        "ContractRegistryError",
        "ContractValidationOutcome",
        "ContractValidationStatus",
    }
    assert expected <= set(contracts.__all__)
    assert set(registry_module.__all__) == expected
