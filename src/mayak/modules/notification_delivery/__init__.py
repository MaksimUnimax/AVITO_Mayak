"""Notification Delivery module package."""

from mayak.platform.boundaries import NOTIFICATION_DELIVERY_MODULE_ID

from . import attempt as _attempt
from . import deduplication as _deduplication
from . import delivery_plan as _delivery_plan
from . import eligibility as _eligibility
from . import outbox as _outbox
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

ND03_TASK_ID = _eligibility.ND03_TASK_ID
NO_NEW_MINIMUM_FREQUENCY_MINUTES = _eligibility.NO_NEW_MINIMUM_FREQUENCY_MINUTES
NotificationEligibilityAuthority = _eligibility.NotificationEligibilityAuthority
NotificationBeaconLifecycleStatus = _eligibility.NotificationBeaconLifecycleStatus
NotificationEntitlementStatus = _eligibility.NotificationEntitlementStatus
NotificationChannelClass = _eligibility.NotificationChannelClass
NotificationChannelGateStatus = _eligibility.NotificationChannelGateStatus
NotificationEligibilityStatus = _eligibility.NotificationEligibilityStatus
NotificationChannelEligibilityEvidence = _eligibility.NotificationChannelEligibilityEvidence
NotificationRecoveryGraceEvidence = _eligibility.NotificationRecoveryGraceEvidence
NotificationEligibilityContext = _eligibility.NotificationEligibilityContext
NotificationChannelGateDecision = _eligibility.NotificationChannelGateDecision
NotificationEligibilityDecision = _eligibility.NotificationEligibilityDecision
evaluate_notification_eligibility = _eligibility.evaluate_notification_eligibility

ND04_TASK_ID = _outbox.ND04_TASK_ID
NotificationOutboxAuthority = _outbox.NotificationOutboxAuthority
NotificationOutboxLifecycleStatus = _outbox.NotificationOutboxLifecycleStatus
NotificationOutboxCreationStatus = _outbox.NotificationOutboxCreationStatus
NotificationOutboxChannelIntent = _outbox.NotificationOutboxChannelIntent
NotificationOutboxItem = _outbox.NotificationOutboxItem
NotificationOutboxCreationDecision = _outbox.NotificationOutboxCreationDecision
create_notification_outbox_item = _outbox.create_notification_outbox_item

ND05_TASK_ID = _delivery_plan.ND05_TASK_ID
NotificationDeliveryPlanAuthority = _delivery_plan.NotificationDeliveryPlanAuthority
NotificationDeliveryChannelPlanStatus = _delivery_plan.NotificationDeliveryChannelPlanStatus
NotificationDeliveryPlanDecisionStatus = _delivery_plan.NotificationDeliveryPlanDecisionStatus
NotificationDeliveryChannelPlanEntry = _delivery_plan.NotificationDeliveryChannelPlanEntry
NotificationDeliveryPlan = _delivery_plan.NotificationDeliveryPlan
NotificationDeliveryPlanDecision = _delivery_plan.NotificationDeliveryPlanDecision
plan_notification_delivery = _delivery_plan.plan_notification_delivery

ND06_TASK_ID = _attempt.ND06_TASK_ID
NotificationAttemptAuthority = _attempt.NotificationAttemptAuthority
NotificationAttemptLifecycleStatus = _attempt.NotificationAttemptLifecycleStatus
NotificationAttemptPlanningStatus = _attempt.NotificationAttemptPlanningStatus
NotificationProviderOutcomeClass = _attempt.NotificationProviderOutcomeClass
NotificationProviderOutcomeAcceptanceStatus = _attempt.NotificationProviderOutcomeAcceptanceStatus
NotificationAttempt = _attempt.NotificationAttempt
NotificationAttemptPlanningDecision = _attempt.NotificationAttemptPlanningDecision
NotificationProviderOutcomeReference = _attempt.NotificationProviderOutcomeReference
NotificationProviderOutcomeAcceptanceDecision = (
    _attempt.NotificationProviderOutcomeAcceptanceDecision
)
plan_notification_attempt = _attempt.plan_notification_attempt
accept_notification_provider_outcome = _attempt.accept_notification_provider_outcome

ND07_TASK_ID = _deduplication.ND07_TASK_ID
NotificationDeduplicationAuthority = _deduplication.NotificationDeduplicationAuthority
NotificationDeduplicationStage = _deduplication.NotificationDeduplicationStage
NotificationDeduplicationRecordState = _deduplication.NotificationDeduplicationRecordState
NotificationDeduplicationDecisionStatus = (
    _deduplication.NotificationDeduplicationDecisionStatus
)
NotificationDeduplicationRequest = _deduplication.NotificationDeduplicationRequest
NotificationDeduplicationRecord = _deduplication.NotificationDeduplicationRecord
NotificationDeduplicationDecision = _deduplication.NotificationDeduplicationDecision
evaluate_notification_deduplication = _deduplication.evaluate_notification_deduplication

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
    "ND04_TASK_ID",
    "NotificationOutboxAuthority",
    "NotificationOutboxLifecycleStatus",
    "NotificationOutboxCreationStatus",
    "NotificationOutboxChannelIntent",
    "NotificationOutboxItem",
    "NotificationOutboxCreationDecision",
    "create_notification_outbox_item",
    "ND05_TASK_ID",
    "NotificationDeliveryPlanAuthority",
    "NotificationDeliveryChannelPlanStatus",
    "NotificationDeliveryPlanDecisionStatus",
    "NotificationDeliveryChannelPlanEntry",
    "NotificationDeliveryPlan",
    "NotificationDeliveryPlanDecision",
    "plan_notification_delivery",
    "ND06_TASK_ID",
    "NotificationAttemptAuthority",
    "NotificationAttemptLifecycleStatus",
    "NotificationAttemptPlanningStatus",
    "NotificationProviderOutcomeClass",
    "NotificationProviderOutcomeAcceptanceStatus",
    "NotificationAttempt",
    "NotificationAttemptPlanningDecision",
    "NotificationProviderOutcomeReference",
    "NotificationProviderOutcomeAcceptanceDecision",
    "plan_notification_attempt",
    "accept_notification_provider_outcome",
    "ND07_TASK_ID",
    "NotificationDeduplicationAuthority",
    "NotificationDeduplicationStage",
    "NotificationDeduplicationRecordState",
    "NotificationDeduplicationDecisionStatus",
    "NotificationDeduplicationRequest",
    "NotificationDeduplicationRecord",
    "NotificationDeduplicationDecision",
    "evaluate_notification_deduplication",
)
