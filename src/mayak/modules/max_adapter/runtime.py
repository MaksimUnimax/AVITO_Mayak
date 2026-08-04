"""RF19 MAX runtime orchestration over the existing MAX-owned schema."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID, uuid4

from sqlalchemy import Table, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mayak.persistence.metadata import metadata
from mayak.runtime.settings import MayakRuntimeSettings, ProviderUpdateMode, RuntimeProfile

from .transport import MaxTransportClass, MaxTransportResult

MAX_UPDATE_BYTES = 2_097_152
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$")


class MaxRuntimeError(RuntimeError):
    """Safe runtime boundary error."""


class MaxInputRejected(MaxRuntimeError):
    pass


class MaxIdentityConflict(MaxRuntimeError):
    pass


class MaxIntakeOutcome(StrEnum):
    FIRST_ACCEPTED = "NORMALIZED_UPDATE_ACCEPTED"
    REPLAY = "DUPLICATE_UPDATE"
    CONFLICT = "AMBIGUOUS_REPLAY_CONFLICT"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED_UPDATE"
    AMBIGUOUS = "AMBIGUOUS_IDENTITY"


@dataclass(frozen=True, slots=True)
class MaxIntakeResult:
    outcome: MaxIntakeOutcome
    record_id: UUID | None
    provider_event_id: str
    fingerprint: str
    normalized_data: Mapping[str, Any]
    reason_code: str = ""


@dataclass(frozen=True, slots=True)
class MaxIdentityMappingResult:
    mapping_id: UUID
    provider_link_id: UUID
    max_user_ref: str
    replay: bool = False


@dataclass(frozen=True, slots=True)
class MaxDeliveryMappingResult:
    mapping_id: UUID
    attempt_id: UUID
    message_ref: str
    replay: bool = False


@dataclass(frozen=True, slots=True)
class MaxReadiness:
    state: str
    enabled: bool
    update_mode: str
    fake: bool
    credential_present: bool


@dataclass(frozen=True, slots=True)
class MaxNonceResult:
    accepted: bool
    replay: bool = False


def _table(name: str) -> Table:
    return metadata.tables[f"mayak.{name}"]


def _now() -> datetime:
    return datetime.now(UTC)


def _lock_key(value: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"max-inbound:{value}".encode()).digest()[:8], "big", signed=True
    )


def webhook_authenticity(received: str | None, expected: str | None) -> str:
    if not expected:
        return "BLOCKED_EXPECTED_SECRET_UNAVAILABLE"
    if not received:
        return "REJECTED_MISSING_SECRET"
    return "VERIFIED" if hmac.compare_digest(received, expected) else "REJECTED_MISMATCH"


def _event_identity(update: Mapping[str, Any], fingerprint: str) -> tuple[str | None, str]:
    for key in ("update_id", "event_id", "id"):
        value = update.get(key)
        if type(value) is int or (isinstance(value, str) and _SAFE_REF.fullmatch(value)):
            return str(value), "provider_event_reference"
    return None, "ambiguous_event_identity"


def _normalize(
    update: Mapping[str, Any], bot_ref: str
) -> tuple[dict[str, Any], MaxIntakeOutcome, str]:
    update_type = update.get("update_type") or update.get("type")
    if not isinstance(update_type, str):
        return (
            {"schema_version": "rf19.v1", "update_class": "UNSUPPORTED", "bot_ref": bot_ref},
            MaxIntakeOutcome.UNSUPPORTED,
            "unsupported_update_type",
        )
    user = update.get("user") or update.get("from")
    user_ref = user.get("user_id") or user.get("id") if isinstance(user, Mapping) else None
    chat = update.get("chat")
    chat_ref = chat.get("chat_id") or chat.get("id") if isinstance(chat, Mapping) else None
    normalized: dict[str, Any] = {
        "schema_version": "rf19.v1",
        "update_class": update_type[:64],
        "bot_ref": bot_ref,
    }
    if isinstance(user_ref, (str, int)):
        normalized["max_user_ref"] = str(user_ref)
    if isinstance(chat_ref, (str, int)):
        normalized["max_chat_ref"] = str(chat_ref)
    if isinstance(update.get("text"), str):
        normalized["text_length"] = len(update["text"])
    return normalized, MaxIntakeOutcome.FIRST_ACCEPTED, "accepted"


class MaxAdapterRuntime:
    """Owns only MAX tables; Identity and Notification remain foreign authorities."""

    def __init__(
        self,
        session: Session,
        *,
        bot_ref: str = "synthetic-bot",
        max_input_bytes: int = MAX_UPDATE_BYTES,
    ) -> None:
        if not _SAFE_REF.fullmatch(bot_ref):
            raise ValueError("bot_ref is unsafe")
        self.session, self.bot_ref, self.max_input_bytes = session, bot_ref, max_input_bytes

    def ingest_webhook(
        self,
        payload: bytes | Mapping[str, Any],
        *,
        received_secret: str | None,
        expected_secret: str | None,
        received_at: datetime | None = None,
    ) -> MaxIntakeResult:
        if webhook_authenticity(received_secret, expected_secret) != "VERIFIED":
            raise MaxInputRejected("webhook authenticity rejected")
        try:
            raw = (
                payload
                if isinstance(payload, bytes)
                else json.dumps(
                    payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode()
            )
            if len(raw) > self.max_input_bytes:
                raise MaxInputRejected("update exceeds bounded input")
            update = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise MaxInputRejected("update is malformed") from exc
        if not isinstance(update, Mapping):
            raise MaxInputRejected("update must be an object")
        fingerprint = hashlib.sha256(raw).hexdigest()
        provider_id, reason = _event_identity(update, fingerprint)
        normalized, outcome, normalize_reason = _normalize(update, self.bot_ref)
        if provider_id is None:
            provider_id = f"ambiguous:{fingerprint}"
            outcome, normalize_reason = MaxIntakeOutcome.AMBIGUOUS, reason
        scoped = f"{self.bot_ref}:{provider_id}"
        inbound = _table("max_inbound_events")
        with self.session.begin():
            self.session.execute(
                text("SELECT pg_advisory_xact_lock(:key)"), {"key": _lock_key(scoped)}
            )
            existing = (
                self.session.execute(
                    select(inbound).where(inbound.c.provider_event_id == scoped).with_for_update()
                )
                .mappings()
                .first()
            )
            if existing:
                if existing["event_fingerprint"] == fingerprint:
                    return MaxIntakeResult(
                        MaxIntakeOutcome.REPLAY,
                        existing["id"],
                        scoped,
                        fingerprint,
                        existing["normalized_data"],
                        "replay_same",
                    )
                return MaxIntakeResult(
                    MaxIntakeOutcome.CONFLICT,
                    existing["id"],
                    scoped,
                    fingerprint,
                    normalized,
                    "replay_fingerprint_conflict",
                )
            record_id = uuid4()
            self.session.execute(
                insert(inbound).values(
                    id=record_id,
                    provider_event_id=scoped,
                    event_fingerprint=fingerprint,
                    schema_version="rf19.v1",
                    normalized_data=normalized,
                    received_at=received_at or _now(),
                )
            )
        return MaxIntakeResult(
            outcome, record_id, scoped, fingerprint, normalized, normalize_reason
        )

    def bind_identity(
        self, provider_link_id: UUID, max_user_ref: str, *, authorized_handoff: bool
    ) -> MaxIdentityMappingResult:
        if not authorized_handoff or not _SAFE_REF.fullmatch(max_user_ref):
            raise MaxRuntimeError("identity handoff blocked")
        links, mappings = _table("identity_provider_links"), _table("max_identity_mappings")
        with self.session.begin():
            if (
                self.session.execute(
                    select(links.c.id).where(links.c.id == provider_link_id)
                ).first()
                is None
            ):
                raise MaxRuntimeError("identity provider link unavailable")
            existing_user = (
                self.session.execute(
                    select(mappings)
                    .where(mappings.c.max_user_ref == max_user_ref)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            existing_link = (
                self.session.execute(
                    select(mappings)
                    .where(mappings.c.provider_link_id == provider_link_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if existing_user and existing_user["provider_link_id"] != provider_link_id:
                raise MaxIdentityConflict("MAX user already bound")
            if existing_link and existing_link["max_user_ref"] != max_user_ref:
                raise MaxIdentityConflict("provider link already bound")
            if existing_user:
                return MaxIdentityMappingResult(
                    existing_user["id"], provider_link_id, max_user_ref, True
                )
            mapping_id, now = uuid4(), _now()
            self.session.execute(
                insert(mappings).values(
                    id=mapping_id,
                    provider_link_id=provider_link_id,
                    max_user_ref=max_user_ref,
                    created_at=now,
                    updated_at=now,
                )
            )
        return MaxIdentityMappingResult(mapping_id, provider_link_id, max_user_ref)

    def record_delivery(
        self, attempt_id: UUID, result: MaxTransportResult
    ) -> MaxDeliveryMappingResult | None:
        if result.outcome is not MaxTransportClass.ACCEPTED or not result.provider_ref:
            return None
        attempts, mappings = (
            _table("notification_delivery_attempts"),
            _table("max_delivery_mappings"),
        )
        with self.session.begin():
            if (
                self.session.execute(
                    select(attempts.c.id).where(attempts.c.id == attempt_id)
                ).first()
                is None
            ):
                raise MaxRuntimeError("notification attempt unavailable")
            existing = (
                self.session.execute(
                    select(mappings).where(mappings.c.attempt_id == attempt_id).with_for_update()
                )
                .mappings()
                .first()
            )
            if existing:
                if existing["max_message_ref"] != result.provider_ref:
                    raise MaxRuntimeError("delivery mapping conflict")
                return MaxDeliveryMappingResult(
                    existing["id"], attempt_id, result.provider_ref, True
                )
            mapping_id = uuid4()
            self.session.execute(
                insert(mappings).values(
                    id=mapping_id,
                    attempt_id=attempt_id,
                    max_message_ref=result.provider_ref,
                    created_at=_now(),
                )
            )
        return MaxDeliveryMappingResult(mapping_id, attempt_id, result.provider_ref)

    def record_miniapp_nonce(
        self,
        nonce_hash: str,
        *,
        account_id: UUID | None,
        expires_at: datetime,
        created_at: datetime | None = None,
    ) -> MaxNonceResult:
        if re.fullmatch(r"[0-9a-f]{64}", nonce_hash) is None:
            raise MaxRuntimeError("nonce hash is invalid")
        created = created_at or _now()
        nonces = _table("max_miniapp_nonces")
        with self.session.begin():
            self.session.execute(
                text("SELECT pg_advisory_xact_lock(:key)"),
                {"key": _lock_key(f"nonce:{nonce_hash}")},
            )
            existing = self.session.execute(
                select(nonces).where(nonces.c.nonce_hash == nonce_hash).with_for_update()
            ).mappings().first()
            if existing:
                return MaxNonceResult(False, True)
            self.session.execute(
                insert(nonces).values(
                    id=uuid4(),
                    nonce_hash=nonce_hash,
                    account_id=account_id,
                    expires_at=expires_at,
                    created_at=created,
                )
            )
        return MaxNonceResult(True, False)

    def poll_once(
        self,
        transport: Any,
        *,
        mode: ProviderUpdateMode,
        profile: RuntimeProfile,
        webhook_active: bool = False,
        marker: int | None = None,
        limit: int = 10,
        timeout: int = 1,
    ) -> tuple[Any, tuple[MaxIntakeResult, ...]]:
        if mode is not ProviderUpdateMode.LONG_POLLING_TEST or profile not in {
            RuntimeProfile.TEST,
            RuntimeProfile.SYNTHETIC_ACCEPTANCE,
        }:
            raise MaxRuntimeError("long polling is test-only")
        if webhook_active:
            raise MaxRuntimeError("updates unavailable while webhook is active")
        batch = transport.get_updates(
            marker=marker, limit=max(1, min(limit, 1000)), timeout=max(0, min(timeout, 90))
        )
        if batch.outcome is not MaxTransportClass.ACCEPTED:
            return batch, ()
        results = tuple(
            self.ingest_webhook(item, received_secret="synthetic", expected_secret="synthetic")
            for item in batch.updates
        )
        if any(
            result.outcome in {MaxIntakeOutcome.CONFLICT, MaxIntakeOutcome.AMBIGUOUS}
            for result in results
        ):
            return batch, results
        return batch, results


def max_readiness(
    settings: MayakRuntimeSettings,
    *,
    fake: bool = False,
    credential_present: bool = False,
    eligibility_configured: bool = False,
) -> MaxReadiness:
    enabled = settings.providers.max_enabled
    mode = settings.providers.max_update_mode.value
    if fake:
        state = "AVAILABLE_FAKE"
    elif not enabled:
        state = "PROVIDER_DISABLED_CONTINUE"
    elif not credential_present:
        state = "BLOCKED_CREDENTIAL"
    elif not eligibility_configured:
        state = "BLOCKED_ELIGIBILITY"
    else:
        state = "OPERATOR_LIVE_ELIGIBLE"
    return MaxReadiness(state, enabled, mode, fake, credential_present)


__all__ = [
    "MaxAdapterRuntime",
    "MaxDeliveryMappingResult",
    "MaxIdentityConflict",
    "MaxIdentityMappingResult",
    "MaxInputRejected",
    "MaxIntakeOutcome",
    "MaxIntakeResult",
    "MaxNonceResult",
    "MaxReadiness",
    "MaxRuntimeError",
    "max_readiness",
    "webhook_authenticity",
]
