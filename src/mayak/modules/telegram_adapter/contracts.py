"""Transport-neutral semantic contracts for Telegram identity handoff."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)


class _TelegramContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class TelegramIdentityResolutionState(str, Enum):
    RESOLVED_ACCOUNT = "RESOLVED_ACCOUNT"
    NEW_ACCOUNT_REQUESTED = "NEW_ACCOUNT_REQUESTED"
    LINK_CHALLENGE_REQUIRED = "LINK_CHALLENGE_REQUIRED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class TelegramProviderIdentity(_TelegramContract):
    """External Telegram identifiers; none is internal account authority."""

    telegram_provider_identity_ref: str = Field(min_length=1)
    telegram_bot_ref: str = Field(min_length=1)
    telegram_user_id: str = Field(min_length=1)
    telegram_chat_id: str | None = Field(default=None, min_length=1)


class VerifiedTelegramIdentityEvidence(_TelegramContract):
    """Safe evidence references, never a Telegram update or provider payload."""

    verified_identity_evidence_ref: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    verification_method_ref: str = Field(min_length=1)
    verification_result_ref: str = Field(min_length=1)


class TelegramAccountLinkReference(_TelegramContract):
    """Telegram-owned reference to an already accepted Identity decision."""

    telegram_account_link_reference_id: str = Field(min_length=1)
    provider_identity: TelegramProviderIdentity
    account_id: str = Field(min_length=1)
    identity_account_reference_id: str = Field(min_length=1)
    identity_provider_identity_id: str = Field(min_length=1)
    identity_provider: Literal["TELEGRAM"] = "TELEGRAM"

    @model_validator(mode="after")
    def _provider_identity_matches(self) -> "TelegramAccountLinkReference":
        if self.identity_provider_identity_id != self.provider_identity.telegram_user_id:
            raise ValueError("identity_provider_identity_id must match telegram_user_id")
        return self


class TelegramIdentityResolutionRequest(_TelegramContract):
    """Idempotent request reference for Identity-owned resolution."""

    telegram_identity_resolution_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    verified_identity_evidence: VerifiedTelegramIdentityEvidence
    identity_resolution_contract_ref: str = Field(min_length=1)


class TelegramIdentityResolutionOutcome(_TelegramContract):
    """Safe outcome projection; account decisions remain Identity-owned."""

    telegram_identity_resolution_reference_id: str = Field(min_length=1)
    telegram_identity_resolution_request_id: str = Field(min_length=1)
    identity_decision_reference_id: str = Field(min_length=1)
    state: TelegramIdentityResolutionState
    provider_identity: TelegramProviderIdentity
    reason_code: str = Field(min_length=1)
    account_link: TelegramAccountLinkReference | None = None
    identity_link_challenge_ref: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_state_matrix(self) -> "TelegramIdentityResolutionOutcome":
        if self.state is TelegramIdentityResolutionState.RESOLVED_ACCOUNT:
            if self.account_link is None or self.identity_link_challenge_ref is not None:
                raise ValueError("resolved account requires only account_link")
            if self.provider_identity != self.account_link.provider_identity:
                raise ValueError("provider_identity must match account_link")
        elif self.state is TelegramIdentityResolutionState.LINK_CHALLENGE_REQUIRED:
            if self.identity_link_challenge_ref is None or self.account_link is not None:
                raise ValueError("link challenge requires only challenge reference")
        elif self.account_link is not None or self.identity_link_challenge_ref is not None:
            raise ValueError("this outcome state cannot contain account or challenge reference")
        return self


__all__ = [
    "TelegramAccountLinkReference",
    "TelegramIdentityResolutionOutcome",
    "TelegramIdentityResolutionRequest",
    "TelegramIdentityResolutionState",
    "TelegramProviderIdentity",
    "VerifiedTelegramIdentityEvidence",
]
