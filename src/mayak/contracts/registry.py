"""Exact contract identity registration and validation primitives."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from pydantic import BaseModel

from mayak.contracts.metadata import ContractMetadata
from mayak.contracts.serialization import ContractSerializationError, decode_contract_json


class ContractRegistryError(ValueError):
    """Raised when an exact contract identity or payload is unsafe."""


class ContractValidationStatus(str, Enum):
    VALID = "VALID"
    UNKNOWN_CONTRACT = "UNKNOWN_CONTRACT"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    MODEL_MISMATCH = "MODEL_MISMATCH"


_REASONS: Mapping[ContractValidationStatus, str] = MappingProxyType(
    {
        ContractValidationStatus.VALID: "CONTRACT_IDENTITY_VALID",
        ContractValidationStatus.UNKNOWN_CONTRACT: "CONTRACT_NAME_UNKNOWN",
        ContractValidationStatus.UNSUPPORTED_VERSION: "CONTRACT_VERSION_UNSUPPORTED",
        ContractValidationStatus.MODEL_MISMATCH: "CONTRACT_MODEL_MISMATCH",
    }
)


@dataclass(frozen=True, slots=True)
class ContractValidationOutcome:
    status: ContractValidationStatus
    reason_code: str

    def __post_init__(self) -> None:
        if _REASONS.get(self.status) != self.reason_code:
            raise ValueError("status and reason_code are inconsistent")


@dataclass(frozen=True, slots=True)
class ContractRegistration:
    contract_name: str
    contract_version: str
    model_type: type[BaseModel]

    def __post_init__(self) -> None:
        if type(self.contract_name) is not str or not self.contract_name.strip():
            raise ContractRegistryError("registration contract_name must be non-empty")
        if type(self.contract_version) is not str or not self.contract_version.strip():
            raise ContractRegistryError("registration contract_version must be non-empty")
        if not isinstance(self.model_type, type) or not issubclass(self.model_type, BaseModel):
            raise ContractRegistryError("registration model_type must be a Pydantic model class")
        object.__setattr__(self, "contract_name", self.contract_name.strip())
        object.__setattr__(self, "contract_version", self.contract_version.strip())


class ContractRegistry:
    """Caller-composed immutable registry of exact contract identities."""

    def __init__(self, registrations: Iterable[ContractRegistration]) -> None:
        entries: dict[tuple[str, str], type[BaseModel]] = {}
        for registration in registrations:
            if not isinstance(registration, ContractRegistration):
                raise ContractRegistryError(
                    "registration model_type must be a Pydantic model class"
                )
            identity = (registration.contract_name, registration.contract_version)
            if identity in entries:
                raise ContractRegistryError("duplicate contract identity registration")
            entries[identity] = registration.model_type
        self._registrations: Mapping[tuple[str, str], type[BaseModel]] = MappingProxyType(entries)
        self._contract_names = frozenset(name for name, _version in entries)

    def validate_metadata(self, metadata: ContractMetadata) -> ContractValidationOutcome:
        if not isinstance(metadata, ContractMetadata):
            raise ContractRegistryError("metadata must be ContractMetadata")
        identity = (metadata.contract_name, metadata.contract_version)
        if metadata.contract_name not in self._contract_names:
            return ContractValidationOutcome(
                ContractValidationStatus.UNKNOWN_CONTRACT,
                _REASONS[ContractValidationStatus.UNKNOWN_CONTRACT],
            )
        if identity not in self._registrations:
            return ContractValidationOutcome(
                ContractValidationStatus.UNSUPPORTED_VERSION,
                _REASONS[ContractValidationStatus.UNSUPPORTED_VERSION],
            )
        return ContractValidationOutcome(
            ContractValidationStatus.VALID, _REASONS[ContractValidationStatus.VALID]
        )

    def validate_contract(
        self, metadata: ContractMetadata, contract: BaseModel
    ) -> ContractValidationOutcome:
        metadata_outcome = self.validate_metadata(metadata)
        if metadata_outcome.status is not ContractValidationStatus.VALID:
            return metadata_outcome
        if not isinstance(contract, BaseModel):
            raise ContractRegistryError("contract instance must be a Pydantic model")
        if (
            type(contract)
            is not self._registrations[(metadata.contract_name, metadata.contract_version)]
        ):
            return ContractValidationOutcome(
                ContractValidationStatus.MODEL_MISMATCH,
                _REASONS[ContractValidationStatus.MODEL_MISMATCH],
            )
        return ContractValidationOutcome(
            ContractValidationStatus.VALID, _REASONS[ContractValidationStatus.VALID]
        )

    def decode(self, metadata: ContractMetadata, payload: bytes | str) -> BaseModel:
        metadata_outcome = self.validate_metadata(metadata)
        if metadata_outcome.status is ContractValidationStatus.UNKNOWN_CONTRACT:
            raise ContractRegistryError("contract name is not registered")
        if metadata_outcome.status is ContractValidationStatus.UNSUPPORTED_VERSION:
            raise ContractRegistryError("contract version is not supported")
        model_type = self._registrations[(metadata.contract_name, metadata.contract_version)]
        try:
            return decode_contract_json(model_type, payload)
        except ContractSerializationError:
            raise ContractRegistryError(
                "contract payload does not match registered identity"
            ) from None


__all__ = [
    "ContractRegistration",
    "ContractRegistry",
    "ContractRegistryError",
    "ContractValidationOutcome",
    "ContractValidationStatus",
]
