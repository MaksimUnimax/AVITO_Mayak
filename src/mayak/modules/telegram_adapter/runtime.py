"""Durable RF18 Telegram Adapter runtime boundary."""

# ruff: noqa: E501, E701, I001

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

from .transport import TelegramTransportClass, TelegramTransportResult, TelegramUpdateBatchResult

MAX_UPDATE_BYTES = 2_097_152
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$")


class TelegramRuntimeError(RuntimeError): pass
class TelegramInputRejected(TelegramRuntimeError): pass
class TelegramReplayConflict(TelegramRuntimeError): pass
class TelegramIdentityConflict(TelegramRuntimeError): pass


class TelegramIntakeOutcome(StrEnum):
    FIRST_ACCEPTED = "NORMALIZED_UPDATE_ACCEPTED"
    REPLAY = "DUPLICATE_UPDATE"
    CONFLICT = "AMBIGUOUS_REPLAY_CONFLICT"
    REJECTED = "REJECTED"
    UNSUPPORTED = "UNSUPPORTED_UPDATE"


@dataclass(frozen=True, slots=True)
class TelegramIntakeResult:
    outcome: TelegramIntakeOutcome
    record_id: UUID | None
    provider_update_id: str
    fingerprint: str
    normalized_data: Mapping[str, Any]
    reason_code: str = ""


@dataclass(frozen=True, slots=True)
class TelegramIdentityMappingResult:
    mapping_id: UUID
    provider_link_id: UUID
    telegram_user_ref: str
    replay: bool = False


@dataclass(frozen=True, slots=True)
class TelegramDeliveryMappingResult:
    mapping_id: UUID
    attempt_id: UUID
    message_ref: str
    replay: bool = False


@dataclass(frozen=True, slots=True)
class TelegramReadiness:
    provider: str
    state: str
    enabled: bool
    update_mode: str
    fake: bool
    credential_present: bool
    public_ingress_deployed: bool = False


def _table(name: str) -> Table: return metadata.tables[f"mayak.{name}"]
def _lock_key(value: str) -> int:
    return int.from_bytes(hashlib.sha256(f"telegram-inbound:{value}".encode()).digest()[:8], "big", signed=True)
def _now() -> datetime: return datetime.now(UTC)


def webhook_authenticity(received: str | None, expected: str | None) -> str:
    if not expected: return "BLOCKED_EXPECTED_SECRET_UNAVAILABLE"
    if not received: return "REJECTED_MISSING_SECRET"
    return "VERIFIED" if hmac.compare_digest(received, expected) else "REJECTED_MISMATCH"


def _json_bytes(value: object) -> bytes:
    try: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    except (TypeError, ValueError) as exc: raise TelegramInputRejected("update is not JSON-safe") from exc


def _private_chat(update: Mapping[str, Any]) -> tuple[str, str] | None:
    message = update.get("message") or update.get("edited_message")
    if isinstance(message, Mapping):
        chat = message.get("chat")
        user = message.get("from")
        if isinstance(chat, Mapping) and chat.get("type") == "private" and type(chat.get("id")) is int and isinstance(user, Mapping) and type(user.get("id")) is int:
            return str(chat["id"]), str(user["id"])
    callback = update.get("callback_query")
    if isinstance(callback, Mapping):
        message = callback.get("message")
        chat = message.get("chat") if isinstance(message, Mapping) else None
        user = callback.get("from")
        if isinstance(chat, Mapping) and chat.get("type") == "private" and type(chat.get("id")) is int and isinstance(user, Mapping) and type(user.get("id")) is int:
            return str(chat["id"]), str(user["id"])
    return None


def _normalized(update: Mapping[str, Any], bot_ref: str, update_id: int) -> tuple[dict[str, Any], bool, str]:
    allowed = ("message", "edited_message", "callback_query")
    kinds = [key for key in allowed if key in update]
    if len(kinds) != 1: return {"schema_version": "rf18.v1", "update_class": "UNSUPPORTED"}, False, "unsupported_top_level"
    private = _private_chat(update)
    if private is None: return {"schema_version": "rf18.v1", "update_class": "UNSUPPORTED"}, False, "private_chat_only"
    chat_ref, user_ref = private
    item: dict[str, Any] = {"schema_version": "rf18.v1", "update_class": kinds[0], "bot_ref": bot_ref, "telegram_update_id": update_id, "telegram_user_ref": user_ref, "telegram_private_chat_ref": chat_ref, "intent_family": "UNSUPPORTED"}
    if kinds[0] in {"message", "edited_message"}:
        message = update[kinds[0]]
        if isinstance(message, Mapping) and isinstance(message.get("text"), str):
            command = message["text"].split(maxsplit=1)[0].lower()
            item["intent_family"] = {"/start": "START", "/help": "HELP"}.get(command, "UNSUPPORTED")
    return item, True, "accepted"


class TelegramAdapterRuntime:
    """Owns only M09 tables and accepted provider boundary evidence."""

    def __init__(self, session: Session, *, bot_ref: str = "synthetic-bot", max_input_bytes: int = MAX_UPDATE_BYTES) -> None:
        if not _SAFE_REF.fullmatch(bot_ref): raise ValueError("bot_ref is unsafe")
        self.session, self.bot_ref, self.max_input_bytes = session, bot_ref, max_input_bytes

    def ingest_update(self, update: Mapping[str, Any], *, received_at: datetime | None = None) -> TelegramIntakeResult:
        raw = _json_bytes(update)
        if len(raw) > self.max_input_bytes: raise TelegramInputRejected("update exceeds bounded input")
        update_id = update.get("update_id")
        if type(update_id) is not int or update_id < 0: raise TelegramInputRejected("update_id must be integral")
        scoped = f"{self.bot_ref}:{update_id}"
        fingerprint = hashlib.sha256(raw).hexdigest()
        normalized, accepted, reason = _normalized(update, self.bot_ref, update_id)
        inbound = _table("telegram_inbound_updates")
        with self.session.begin():
            self.session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _lock_key(scoped)})
            existing = self.session.execute(select(inbound).where(inbound.c.provider_update_id == scoped).with_for_update()).mappings().first()
            if existing:
                if existing["event_fingerprint"] == fingerprint:
                    return TelegramIntakeResult(TelegramIntakeOutcome.REPLAY, existing["id"], scoped, fingerprint, existing["normalized_data"], "replay_same")
                return TelegramIntakeResult(TelegramIntakeOutcome.CONFLICT, existing["id"], scoped, fingerprint, normalized, "replay_fingerprint_conflict")
            record_id = uuid4()
            self.session.execute(insert(inbound).values(id=record_id, provider_update_id=scoped, event_fingerprint=fingerprint, schema_version="rf18.v1", normalized_data=normalized, received_at=received_at or _now()))
            outcome = TelegramIntakeOutcome.FIRST_ACCEPTED if accepted else TelegramIntakeOutcome.UNSUPPORTED
            return TelegramIntakeResult(outcome, record_id, scoped, fingerprint, normalized, reason)

    def bind_identity(self, provider_link_id: UUID, telegram_user_ref: str, *, authorized_handoff: bool) -> TelegramIdentityMappingResult:
        if not authorized_handoff or not _SAFE_REF.fullmatch(telegram_user_ref): raise TelegramRuntimeError("identity handoff blocked")
        links, mappings = _table("identity_provider_links"), _table("telegram_identity_mappings")
        with self.session.begin():
            if self.session.execute(select(links.c.id).where(links.c.id == provider_link_id)).first() is None: raise TelegramRuntimeError("identity provider link unavailable")
            existing_user = self.session.execute(select(mappings).where(mappings.c.telegram_user_ref == telegram_user_ref).with_for_update()).mappings().first()
            existing_link = self.session.execute(select(mappings).where(mappings.c.provider_link_id == provider_link_id).with_for_update()).mappings().first()
            if existing_user and existing_user["provider_link_id"] != provider_link_id: raise TelegramIdentityConflict("telegram user already bound")
            if existing_link and existing_link["telegram_user_ref"] != telegram_user_ref: raise TelegramIdentityConflict("provider link already bound")
            if existing_user: return TelegramIdentityMappingResult(existing_user["id"], provider_link_id, telegram_user_ref, True)
            mapping_id = uuid4()
            now = _now()
            self.session.execute(insert(mappings).values(id=mapping_id, provider_link_id=provider_link_id, telegram_user_ref=telegram_user_ref, created_at=now, updated_at=now))
            return TelegramIdentityMappingResult(mapping_id, provider_link_id, telegram_user_ref)

    def record_delivery(self, attempt_id: UUID, result: TelegramTransportResult) -> TelegramDeliveryMappingResult | None:
        if result.outcome is not TelegramTransportClass.ACCEPTED or not result.message_ref: return None
        attempts, mappings = _table("notification_delivery_attempts"), _table("telegram_delivery_mappings")
        with self.session.begin():
            if self.session.execute(select(attempts.c.id).where(attempts.c.id == attempt_id)).first() is None: raise TelegramRuntimeError("notification attempt unavailable")
            existing = self.session.execute(select(mappings).where(mappings.c.attempt_id == attempt_id).with_for_update()).mappings().first()
            if existing:
                if existing["telegram_message_ref"] != result.message_ref: raise TelegramRuntimeError("delivery mapping conflict")
                return TelegramDeliveryMappingResult(existing["id"], attempt_id, result.message_ref, True)
            mapping_id = uuid4()
            self.session.execute(insert(mappings).values(id=mapping_id, attempt_id=attempt_id, telegram_message_ref=result.message_ref, created_at=_now()))
            return TelegramDeliveryMappingResult(mapping_id, attempt_id, result.message_ref)

    def poll_once(self, transport: Any, *, mode: ProviderUpdateMode, profile: RuntimeProfile, webhook_active: bool = False, offset: int | None = None, limit: int = 10, timeout: int = 1) -> tuple[TelegramUpdateBatchResult, tuple[TelegramIntakeResult, ...]]:
        if mode is not ProviderUpdateMode.LONG_POLLING_TEST or profile not in {RuntimeProfile.TEST, RuntimeProfile.SYNTHETIC_ACCEPTANCE}: raise TelegramRuntimeError("long polling is test-only")
        if webhook_active: raise TelegramRuntimeError("getUpdates unavailable while webhook is active")
        batch = transport.get_updates(offset=offset, limit=max(1, min(limit, 100)), timeout=max(0, min(timeout, 30)))
        if batch.outcome is not TelegramTransportClass.ACCEPTED: return batch, ()
        results: list[TelegramIntakeResult] = []
        for update in batch.updates:
            results.append(self.ingest_update(update))
        accepted_ids = [int(r.provider_update_id.rsplit(":", 1)[1]) for r in results if r.outcome in {TelegramIntakeOutcome.FIRST_ACCEPTED, TelegramIntakeOutcome.REPLAY, TelegramIntakeOutcome.UNSUPPORTED}]
        next_offset = max(accepted_ids, default=-1) + 1 if accepted_ids else None
        return TelegramUpdateBatchResult(batch.outcome, batch.updates, next_offset, batch.reason_code), tuple(results)


def telegram_readiness(settings: MayakRuntimeSettings, *, fake: bool = False, credential_present: bool = False) -> TelegramReadiness:
    enabled = settings.providers.telegram_enabled
    mode = settings.providers.telegram_update_mode.value
    if fake: state = "AVAILABLE_FAKE"
    elif not enabled: state = "DISABLED"
    elif not credential_present: state = "BLOCKED_CREDENTIAL"
    else: state = "AVAILABLE_LIVE"
    return TelegramReadiness("telegram", state, enabled, mode, fake, credential_present)


__all__ = ["TelegramAdapterRuntime", "TelegramIdentityConflict", "TelegramIdentityMappingResult", "TelegramDeliveryMappingResult", "TelegramInputRejected", "TelegramIntakeOutcome", "TelegramIntakeResult", "TelegramReadiness", "TelegramReplayConflict", "TelegramRuntimeError", "telegram_readiness", "webhook_authenticity"]
