"""Notification Delivery module package."""

# ruff: noqa: E501

from mayak.platform.boundaries import NOTIFICATION_DELIVERY_MODULE_ID

from . import attempt as _attempt
from . import batch as _batch
from . import deduplication as _deduplication
from . import delivery_plan as _delivery_plan
from . import eligibility as _eligibility
from . import external_recovery as _external_recovery
from . import listing_card as _listing_card
from . import no_new_status as _no_new_status
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
NotificationDeduplicationDecisionStatus = _deduplication.NotificationDeduplicationDecisionStatus
NotificationDeduplicationRequest = _deduplication.NotificationDeduplicationRequest
NotificationDeduplicationRecord = _deduplication.NotificationDeduplicationRecord
NotificationDeduplicationDecision = _deduplication.NotificationDeduplicationDecision
evaluate_notification_deduplication = _deduplication.evaluate_notification_deduplication

ND08_TASK_ID = _no_new_status.ND08_TASK_ID
NotificationNoNewStatusAuthority = _no_new_status.NotificationNoNewStatusAuthority
NotificationNoNewMinimumFrequencyGateStatus = (
    _no_new_status.NotificationNoNewMinimumFrequencyGateStatus
)
NotificationNoNewStatusDecisionStatus = _no_new_status.NotificationNoNewStatusDecisionStatus
NotificationNoNewStatusPolicyContext = _no_new_status.NotificationNoNewStatusPolicyContext
NotificationNoNewStatusPolicyDecision = _no_new_status.NotificationNoNewStatusPolicyDecision
evaluate_no_new_status_policy = _no_new_status.evaluate_no_new_status_policy

ND09_TASK_ID = _external_recovery.ND09_TASK_ID
NotificationExternalRecoveryAuthority = _external_recovery.NotificationExternalRecoveryAuthority
NotificationExternalRecoveryEffectClass = _external_recovery.NotificationExternalRecoveryEffectClass
NotificationExternalProblemGateStatus = _external_recovery.NotificationExternalProblemGateStatus
NotificationExternalRecoveryDecisionStatus = (
    _external_recovery.NotificationExternalRecoveryDecisionStatus
)
NotificationExternalRecoveryPolicyContext = (
    _external_recovery.NotificationExternalRecoveryPolicyContext
)
NotificationExternalRecoveryPolicyDecision = (
    _external_recovery.NotificationExternalRecoveryPolicyDecision
)
evaluate_external_recovery_policy = _external_recovery.evaluate_external_recovery_policy

ND10_TASK_ID = _listing_card.ND10_TASK_ID
NotificationListingCardAuthority = _listing_card.NotificationListingCardAuthority
NotificationListingCardReasonClass = _listing_card.NotificationListingCardReasonClass
NotificationListingCardFieldClass = _listing_card.NotificationListingCardFieldClass
NotificationListingCardValueClass = _listing_card.NotificationListingCardValueClass
NotificationListingCardProvenanceTier = _listing_card.NotificationListingCardProvenanceTier
NotificationListingCardProjectionStatus = _listing_card.NotificationListingCardProjectionStatus
NotificationListingCardFieldFact = _listing_card.NotificationListingCardFieldFact
NotificationListingCardInput = _listing_card.NotificationListingCardInput
NotificationListingCard = _listing_card.NotificationListingCard
NotificationListingCardProjectionDecision = _listing_card.NotificationListingCardProjectionDecision
project_notification_listing_cards = _listing_card.project_notification_listing_cards

ND11_TASK_ID = _batch.ND11_TASK_ID
NotificationBatchAuthority = _batch.NotificationBatchAuthority
NotificationBatchStage = _batch.NotificationBatchStage
NotificationBatchDisposition = _batch.NotificationBatchDisposition
NotificationBatchSafeErrorCategory = _batch.NotificationBatchSafeErrorCategory
NotificationBatchDecisionStatus = _batch.NotificationBatchDecisionStatus
NotificationBatchItemInput = _batch.NotificationBatchItemInput
NotificationBatchItemResult = _batch.NotificationBatchItemResult
NotificationBatchDecision = _batch.NotificationBatchDecision
project_notification_batch_outcomes = _batch.project_notification_batch_outcomes

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
    "ND08_TASK_ID",
    "NotificationNoNewStatusAuthority",
    "NotificationNoNewMinimumFrequencyGateStatus",
    "NotificationNoNewStatusDecisionStatus",
    "NotificationNoNewStatusPolicyContext",
    "NotificationNoNewStatusPolicyDecision",
    "evaluate_no_new_status_policy",
    "ND09_TASK_ID",
    "NotificationExternalRecoveryAuthority",
    "NotificationExternalRecoveryEffectClass",
    "NotificationExternalProblemGateStatus",
    "NotificationExternalRecoveryDecisionStatus",
    "NotificationExternalRecoveryPolicyContext",
    "NotificationExternalRecoveryPolicyDecision",
    "evaluate_external_recovery_policy",
    "ND10_TASK_ID",
    "NotificationListingCardAuthority",
    "NotificationListingCardReasonClass",
    "NotificationListingCardFieldClass",
    "NotificationListingCardValueClass",
    "NotificationListingCardProvenanceTier",
    "NotificationListingCardProjectionStatus",
    "NotificationListingCardFieldFact",
    "NotificationListingCardInput",
    "NotificationListingCard",
    "NotificationListingCardProjectionDecision",
    "project_notification_listing_cards",
    "ND11_TASK_ID",
    "NotificationBatchAuthority",
    "NotificationBatchStage",
    "NotificationBatchDisposition",
    "NotificationBatchSafeErrorCategory",
    "NotificationBatchDecisionStatus",
    "NotificationBatchItemInput",
    "NotificationBatchItemResult",
    "NotificationBatchDecision",
    "project_notification_batch_outcomes",
)
