"""Notification Delivery module package."""

from mayak.platform.boundaries import NOTIFICATION_DELIVERY_MODULE_ID

from . import source_intake as _source_intake

MODULE_ID = NOTIFICATION_DELIVERY_MODULE_ID

ND02_TASK_ID = _source_intake.ND02_TASK_ID
NotificationSourceProducer = _source_intake.NotificationSourceProducer
NotificationSourceFamily = _source_intake.NotificationSourceFamily
NotificationSourceIntakeAuthority = _source_intake.NotificationSourceIntakeAuthority
NotificationSourceIntakeStatus = _source_intake.NotificationSourceIntakeStatus
NotificationSourceEvent = _source_intake.NotificationSourceEvent
NotificationSourceIntakeDecision = _source_intake.NotificationSourceIntakeDecision
evaluate_notification_source_intake = _source_intake.evaluate_notification_source_intake

_ND03_EXPORT_NAMES = (
    "ND03_TASK_ID",
    "NO_NEW_MINIMUM_FREQUENCY_MINUTES",
    "NotificationEligibilityAuthority",
    "NotificationBeaconLifecycleStatus",
    "NotificationEntitlementStatus",
    "NotificationChannelClass",
    "NotificationChannelGateStatus",
    "NotificationEligibilityStatus",
    "NotificationChannelEligibilityEvidence",
    "NotificationRecoveryGraceEvidence",
    "NotificationEligibilityContext",
    "NotificationChannelGateDecision",
    "NotificationEligibilityDecision",
    "evaluate_notification_eligibility",
)


def _load_eligibility_exports() -> None:
    if "ND03_TASK_ID" in globals():
        return

    from . import eligibility as _eligibility

    globals().update(
        {
            "ND03_TASK_ID": _eligibility.ND03_TASK_ID,
            "NO_NEW_MINIMUM_FREQUENCY_MINUTES": _eligibility.NO_NEW_MINIMUM_FREQUENCY_MINUTES,
            "NotificationEligibilityAuthority": _eligibility.NotificationEligibilityAuthority,
            "NotificationBeaconLifecycleStatus": _eligibility.NotificationBeaconLifecycleStatus,
            "NotificationEntitlementStatus": _eligibility.NotificationEntitlementStatus,
            "NotificationChannelClass": _eligibility.NotificationChannelClass,
            "NotificationChannelGateStatus": _eligibility.NotificationChannelGateStatus,
            "NotificationEligibilityStatus": _eligibility.NotificationEligibilityStatus,
            "NotificationChannelEligibilityEvidence": (
                _eligibility.NotificationChannelEligibilityEvidence
            ),
            "NotificationRecoveryGraceEvidence": _eligibility.NotificationRecoveryGraceEvidence,
            "NotificationEligibilityContext": _eligibility.NotificationEligibilityContext,
            "NotificationChannelGateDecision": _eligibility.NotificationChannelGateDecision,
            "NotificationEligibilityDecision": _eligibility.NotificationEligibilityDecision,
            "evaluate_notification_eligibility": _eligibility.evaluate_notification_eligibility,
        }
    )

    globals()["__all__"] = (
        "MODULE_ID",
        "ND02_TASK_ID",
        "NotificationSourceProducer",
        "NotificationSourceFamily",
        "NotificationSourceIntakeAuthority",
        "NotificationSourceIntakeStatus",
        "NotificationSourceEvent",
        "NotificationSourceIntakeDecision",
        "evaluate_notification_source_intake",
        *_ND03_EXPORT_NAMES,
    )


def __getattr__(name: str) -> object:
    if name in _ND03_EXPORT_NAMES:
        _load_eligibility_exports()
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = (
    "MODULE_ID",
    "ND02_TASK_ID",
    "NotificationSourceProducer",
    "NotificationSourceFamily",
    "NotificationSourceIntakeAuthority",
    "NotificationSourceIntakeStatus",
    "NotificationSourceEvent",
    "NotificationSourceIntakeDecision",
    "evaluate_notification_source_intake",
)
