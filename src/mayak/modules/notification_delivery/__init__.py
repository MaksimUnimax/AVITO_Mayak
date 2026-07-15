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
