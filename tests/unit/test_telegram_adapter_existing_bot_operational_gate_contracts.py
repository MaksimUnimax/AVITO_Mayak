from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.telegram_adapter import (
    TelegramExistingBotEvidenceState,
    TelegramExistingBotMetadata,
    TelegramExistingBotOperationalGate,
    TelegramProtectedSecretPresenceEvidence,
    TelegramPublicBotMetadataPresenceEvidence,
)


def meta() -> ContractMetadata:
    return ContractMetadata(
        contract_name="telegram.existing-bot-gate",
        contract_version="1",
        message_id=uuid4(),
        correlation_id=uuid4(),
        producer="telegram-adapter",
    )


def bot(**changes: object) -> TelegramExistingBotMetadata:
    values: dict[str, object] = dict(
        telegram_existing_bot_metadata_id="bot-metadata",
        telegram_bot_username="@signalings_bot",
        telegram_bot_numeric_id="8664835407",
        owner_provisioning_reference_id="owner-provisioning",
    )
    values.update(changes)
    return TelegramExistingBotMetadata.model_validate(values)


def secret(**changes: object) -> TelegramProtectedSecretPresenceEvidence:
    values: dict[str, object] = dict(
        telegram_protected_secret_presence_evidence_id="secret-evidence",
        protected_secret_reference="/etc/avito-mayak/secrets/telegram_bot_token",
        observed_owner="root",
        observed_group="root",
        observed_mode="0600",
        observed_size_bytes=46,
        server_evidence_reference_id="server-evidence",
    )
    values.update(changes)
    return TelegramProtectedSecretPresenceEvidence.model_validate(values)


def public(**changes: object) -> TelegramPublicBotMetadataPresenceEvidence:
    values: dict[str, object] = dict(
        telegram_public_bot_metadata_presence_evidence_id="public-evidence",
        public_metadata_reference="/etc/avito-mayak/telegram-bot.conf",
        observed_owner="root",
        observed_group="root",
        observed_mode="0644",
        observed_size_bytes=65,
        server_evidence_reference_id="server-evidence",
    )
    values.update(changes)
    return TelegramPublicBotMetadataPresenceEvidence.model_validate(values)


def gate(
    state: TelegramExistingBotEvidenceState, **changes: object
) -> TelegramExistingBotOperationalGate:
    values: dict[str, object] = dict(
        telegram_existing_bot_operational_gate_id="gate",
        metadata=meta(),
        owner_direction_reference_id="owner-direction",
        state=state,
        bot_metadata=bot(),
        protected_secret_presence_evidence=secret(),
        public_bot_metadata_presence_evidence=public(),
        reason_code="runtime-remains-closed",
    )
    values.update(changes)
    return TelegramExistingBotOperationalGate.model_validate(values)


def test_exact_enum_and_verified_current_bot() -> None:
    assert [member.value for member in TelegramExistingBotEvidenceState] == [
        "VERIFIED_REDACTED_EVIDENCE", "EVIDENCE_INCOMPLETE", "EVIDENCE_MISMATCH"
    ]
    value = gate(TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE)
    assert value.bot_metadata is not None
    assert value.protected_secret_presence_evidence is not None
    assert value.public_bot_metadata_presence_evidence is not None
    assert value.bot_metadata.telegram_bot_numeric_id_is_external_provider_identifier is True
    assert value.bot_metadata.telegram_bot_numeric_id_is_internal_account_id is False
    assert value.protected_secret_presence_evidence.protected_secret_reference == (
        "/etc/avito-mayak/secrets/telegram_bot_token"
    )
    assert value.public_bot_metadata_presence_evidence.public_metadata_reference == (
        "/etc/avito-mayak/telegram-bot.conf"
    )


def test_exact_contract_fields_are_redacted_and_complete() -> None:
    assert set(TelegramExistingBotMetadata.model_fields) == {
        "telegram_existing_bot_metadata_id", "telegram_bot_username", "telegram_bot_numeric_id",
        "owner_provisioning_reference_id", "botfather_creation_completed",
        "telegram_bot_numeric_id_is_external_provider_identifier",
        "telegram_bot_numeric_id_is_internal_account_id", "botfather_reconfiguration_authorized",
    }
    assert set(TelegramProtectedSecretPresenceEvidence.model_fields) == {
        "telegram_protected_secret_presence_evidence_id", "protected_secret_reference",
        "observed_owner", "observed_group", "observed_mode", "observed_size_bytes",
        "server_evidence_reference_id", "evidence_is_presence_and_metadata_only",
        "secret_content_read", "secret_content_printed", "secret_content_hashed",
        "secret_content_fingerprinted", "secret_content_encoded", "secret_content_copied",
        "secret_content_transmitted", "secret_modified",
    }
    assert set(TelegramPublicBotMetadataPresenceEvidence.model_fields) == {
        "telegram_public_bot_metadata_presence_evidence_id", "public_metadata_reference",
        "observed_owner", "observed_group", "observed_mode", "observed_size_bytes",
        "server_evidence_reference_id", "evidence_is_presence_and_metadata_only",
        "file_content_read", "file_modified",
    }
    assert "metadata" in TelegramExistingBotOperationalGate.model_fields


@pytest.mark.parametrize(
    "factory,field",
    [
        (bot, "botfather_reconfiguration_authorized"),
        (secret, "secret_content_read"), (secret, "secret_content_printed"),
        (secret, "secret_content_hashed"), (secret, "secret_content_fingerprinted"),
        (secret, "secret_content_encoded"), (secret, "secret_content_copied"),
        (secret, "secret_content_transmitted"), (secret, "secret_modified"),
        (public, "file_content_read"), (public, "file_modified"),
    ],
)
def test_each_evidence_safety_literal_rejects_true(
    factory: Callable[..., object], field: str
) -> None:
    with pytest.raises(ValidationError):
        factory(**{field: True})


@pytest.mark.parametrize(
    "field",
    [
        "provider_runtime_authorized", "provider_call_authorized", "webhook_authorized",
        "get_updates_authorized", "mini_app_authorized", "protected_secret_consumption_authorized",
        "botfather_reconfiguration_authorized", "token_rotation_authorized",
        "token_revocation_authorized", "token_deletion_authorized", "secret_relocation_authorized",
        "secret_permission_change_authorized",
    ],
)
def test_each_operational_authorization_flag_rejects_true(field: str) -> None:
    with pytest.raises(ValidationError):
        gate(TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE, **{field: True})


def test_all_safety_literals_are_closed_and_models_are_frozen() -> None:
    value = gate(TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE)
    assert value.protected_secret_presence_evidence is not None
    assert value.public_bot_metadata_presence_evidence is not None
    assert all(v is False for k, v in value.model_dump().items() if k.endswith("authorized"))
    assert value.protected_secret_presence_evidence.secret_content_read is False
    assert value.protected_secret_presence_evidence.secret_content_hashed is False
    assert value.protected_secret_presence_evidence.secret_content_copied is False
    assert value.public_bot_metadata_presence_evidence.file_content_read is False
    with pytest.raises(ValidationError):
        value.provider_runtime_authorized = True  # type: ignore[assignment]


@pytest.mark.parametrize("field", [
    "telegram_bot_username", "telegram_bot_numeric_id", "owner_provisioning_reference_id",
])
def test_whitespace_and_numeric_id_rejections(field: str) -> None:
    with pytest.raises(ValidationError):
        bot(**{field: "   "})


@pytest.mark.parametrize(
    "invalid", ("0", "08664835407", "8664835407x", "-8664835407", "８６６４８３５４０７")
)
def test_numeric_provider_id_is_ascii_nonzero_decimal(invalid: str) -> None:
    with pytest.raises(ValidationError):
        bot(telegram_bot_numeric_id=invalid)


def test_modes_sizes_extras_and_secret_material_are_rejected() -> None:
    for mode in ("600", "060", "0800", "0o600"):
        with pytest.raises(ValidationError):
            secret(observed_mode=mode)
    for size in (0, -1):
        with pytest.raises(ValidationError):
            public(observed_size_bytes=size)
    with pytest.raises(ValidationError):
        bot(unapproved_field="x")
    with pytest.raises(ValidationError):
        secret(secret_content_read=True)
    assert not any(
        "token_value" in name or "secret_value" in name or "digest" in name
        for name in TelegramProtectedSecretPresenceEvidence.model_fields
    )


@pytest.mark.parametrize(
    "missing",
    ["bot_metadata", "protected_secret_presence_evidence", "public_bot_metadata_presence_evidence"],
)
def test_incomplete_requires_block_and_cannot_be_verified(missing: str) -> None:
    value = gate(
        TelegramExistingBotEvidenceState.EVIDENCE_INCOMPLETE,
        **{missing: None},
        blocking_decision_reference_id="block",
    )
    assert value.state is TelegramExistingBotEvidenceState.EVIDENCE_INCOMPLETE
    with pytest.raises(ValidationError):
        gate(TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE, **{missing: None})


@pytest.mark.parametrize("changes", [
    {"telegram_bot_username": "@other_bot"},
    {"telegram_bot_numeric_id": "8664835408"},
])
def test_metadata_mismatch_branch(changes: dict[str, object]) -> None:
    value = gate(
        TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH,
        bot_metadata=bot(**changes),
        blocking_decision_reference_id="block",
    )
    assert value.state is TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH
    with pytest.raises(ValidationError):
        gate(
            TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE,
            bot_metadata=bot(**changes),
        )


@pytest.mark.parametrize("evidence,field", [
    ("secret", "protected_secret_reference"), ("secret", "observed_owner"),
    ("secret", "observed_group"), ("secret", "observed_mode"),
    ("public", "public_metadata_reference"), ("public", "observed_owner"),
    ("public", "observed_group"), ("public", "observed_mode"),
])
def test_each_approved_path_owner_group_mode_mismatch_is_blocked(evidence: str, field: str) -> None:
    factory = secret if evidence == "secret" else public
    changed = {field: "0640" if field == "observed_mode" else "wrong"}
    item = factory(**changed)
    key = (
        "protected_secret_presence_evidence"
        if evidence == "secret"
        else "public_bot_metadata_presence_evidence"
    )
    value = gate(
        TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH,
        **{key: item},
        blocking_decision_reference_id="block",
    )
    assert value.state is TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH


def test_complete_mismatch_cannot_be_unblocked_and_dump_is_redacted() -> None:
    with pytest.raises(ValidationError):
        gate(TelegramExistingBotEvidenceState.EVIDENCE_MISMATCH)
    with pytest.raises(ValidationError):
        gate(TelegramExistingBotEvidenceState.EVIDENCE_INCOMPLETE)
    dumped = gate(TelegramExistingBotEvidenceState.VERIFIED_REDACTED_EVIDENCE).model_dump_json()
    assert "token_value" not in dumped and "credential_material" not in dumped
    assert "@signalings_bot" in dumped and "8664835407" in dumped
