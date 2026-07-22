"""Contract export tests for Filter Catalog FC-02–FC-07 public semantic surface."""

from __future__ import annotations

import importlib

import pytest

MODULE_NAME = "mayak.modules.filter_catalog"


def _get_all():
    return list(importlib.import_module(MODULE_NAME).__all__)


class TestFC02ContractsExports:
    def test_fc02_enums_models_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.contracts import (
            CatalogPublicationState,
            FilterDefinitionState,
            FilterValueKind,
            FilterEvidenceState,
            FilterCapabilityState,
            FilterDependencyKind,
            BuilderDraftValidationState,
            BeaconOverrideCandidateState,
            CatalogCompatibilityState,
            FilterEvidenceReference,
            FilterCatalogVersion,
            FilterDefinition,
            FilterOptionDefinition,
            FilterRangeDefinition,
            FilterDependencyRule,
            FilterCapabilityProfile,
            BuilderFieldDefinition,
            BuilderDraftValidationResult,
            BeaconOverrideCandidateOutcome,
            CatalogCompatibilityWarning,
            CatalogReadModel,
        )
        assert CatalogPublicationState.DRAFT == "DRAFT"
        assert FilterDefinitionState.APPROVED == "APPROVED"
        assert FilterValueKind.MULTIVALUE == "MULTIVALUE"
        assert FilterEvidenceState.CURRENT == "CURRENT"
        assert FilterCapabilityState.EDITABLE == "EDITABLE"
        assert FilterDependencyKind.REQUIRES == "REQUIRES"
        assert BuilderDraftValidationState.VALID == "VALID"
        assert BeaconOverrideCandidateState.PREPARED == "PREPARED"
        assert CatalogCompatibilityState.COMPATIBLE == "COMPATIBLE"
        for cls in [
            FilterEvidenceReference, FilterCatalogVersion, FilterDefinition,
            FilterOptionDefinition, FilterRangeDefinition, FilterDependencyRule,
            FilterCapabilityProfile, BuilderFieldDefinition, BuilderDraftValidationResult,
            BeaconOverrideCandidateOutcome, CatalogCompatibilityWarning, CatalogReadModel,
        ]:
            assert hasattr(cls, "model_config")
        all_exports = _get_all()
        for name in [
            "FilterCatalogVersion", "FilterDefinition", "FilterEvidenceReference",
            "FilterCapabilityProfile", "BuilderFieldDefinition",
            "BuilderDraftValidationResult", "BeaconOverrideCandidateOutcome",
            "CatalogReadModel", "CatalogCompatibilityWarning",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestFC03EvidenceApprovalExports:
    def test_fc03_function_models_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.evidence_approval import (
            evaluate_filter_evidence_approval,
            FilterEvidenceApprovalRequest,
            FilterEvidenceApprovalOutcome,
            EvidenceAuthorityClass,
            FilterEvidenceTransition,
            FilterEvidenceApprovalDecision,
            ExactFilterApprovalGateState,
        )
        assert callable(evaluate_filter_evidence_approval)
        assert EvidenceAuthorityClass.OFFICIAL_REFERENCE == "OFFICIAL_REFERENCE"
        assert FilterEvidenceTransition.PROPOSE == "PROPOSE"
        assert FilterEvidenceApprovalDecision.APPROVABLE == "APPROVABLE"
        assert ExactFilterApprovalGateState.BLOCKED_OPEN_DECISION == "BLOCKED_OPEN_DECISION"
        all_exports = _get_all()
        for name in [
            "evaluate_filter_evidence_approval",
            "FilterEvidenceApprovalRequest",
            "FilterEvidenceApprovalOutcome",
            "EvidenceAuthorityClass",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestFC04BuilderValidationExports:
    def test_fc04_functions_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.builder_validation import (
            project_builder_field_definition,
            validate_builder_draft,
            BuilderFieldProjectionRequest,
            BuilderDraftValidationRequest,
        )
        assert callable(project_builder_field_definition)
        assert callable(validate_builder_draft)
        all_exports = _get_all()
        for name in [
            "project_builder_field_definition",
            "validate_builder_draft",
            "BuilderFieldProjectionRequest",
            "BuilderDraftValidationRequest",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestFC05ValueDependencyExports:
    def test_fc05_functions_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.value_dependency_semantics import (
            evaluate_multivalue_preservation,
            validate_range_value,
            evaluate_filter_semantic_exposure,
            MultivaluePreservationRequest,
            RangeValueValidationRequest,
            FilterSemanticExposureRequest,
        )
        assert callable(evaluate_multivalue_preservation)
        assert callable(validate_range_value)
        assert callable(evaluate_filter_semantic_exposure)
        all_exports = _get_all()
        for name in [
            "evaluate_multivalue_preservation",
            "validate_range_value",
            "evaluate_filter_semantic_exposure",
            "MultivaluePreservationRequest",
            "RangeValueValidationRequest",
            "FilterSemanticExposureRequest",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestFC06BeaconOverrideExports:
    def test_fc06_function_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.beacon_override_candidate import (
            prepare_beacon_override_candidate,
            BeaconOverrideCandidatePreparationRequest,
            BeaconOverrideCandidatePreparationResult,
        )
        assert callable(prepare_beacon_override_candidate)
        all_exports = _get_all()
        for name in [
            "prepare_beacon_override_candidate",
            "BeaconOverrideCandidatePreparationRequest",
            "BeaconOverrideCandidatePreparationResult",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestFC07SafeReadModelExports:
    def test_fc07_function_enums_and_package_exports(self) -> None:
        from mayak.modules.filter_catalog.safe_read_models import (
            project_catalog_safe_filter_read,
            CatalogSafeReadAudience,
            CatalogSafeReadSurfaceState,
            CatalogSafeReadFreshnessState,
            CatalogSafeExplanationCode,
            CatalogSafeReadAccessContext,
            CatalogSafeFilterReadRequest,
            CatalogSafeFilterReadModel,
        )
        assert callable(project_catalog_safe_filter_read)
        assert CatalogSafeReadAudience.WEB_CUSTOMER == "WEB_CUSTOMER"
        assert CatalogSafeReadSurfaceState.AVAILABLE == "AVAILABLE"
        assert CatalogSafeReadFreshnessState.CURRENT == "CURRENT"
        assert CatalogSafeExplanationCode.EDITABLE == "EDITABLE"
        all_exports = _get_all()
        for name in [
            "project_catalog_safe_filter_read",
            "CatalogSafeReadAccessContext",
            "CatalogSafeFilterReadRequest",
            "CatalogSafeFilterReadModel",
        ]:
            assert name in all_exports, f"{name} not in package __all__"


class TestPackageLevelExports:
    def test_module_id_exported(self) -> None:
        from mayak.modules.filter_catalog import MODULE_ID
        assert MODULE_ID is not None
        all_exports = _get_all()
        assert "MODULE_ID" in all_exports

    def test_type_annotations_exported(self) -> None:
        from mayak.modules.filter_catalog.contracts import OpaqueReferenceId, SafeCode, Sha256Hex, SafeLabel
        all_exports = _get_all()
        for name in ["OpaqueReferenceId", "SafeCode", "Sha256Hex", "SafeLabel"]:
            assert name in all_exports, f"{name} not in package __all__"

    def test_model_config_consistency(self) -> None:
        from mayak.modules.filter_catalog.contracts import FilterCatalogVersion, FilterDefinition
        from mayak.modules.filter_catalog.evidence_approval import FilterEvidenceApprovalRequest
        from mayak.modules.filter_catalog.builder_validation import BuilderDraftValidationRequest
        from mayak.modules.filter_catalog.value_dependency_semantics import MultivaluePreservationRequest
        from mayak.modules.filter_catalog.beacon_override_candidate import BeaconOverrideCandidatePreparationRequest
        from mayak.modules.filter_catalog.safe_read_models import CatalogSafeFilterReadModel
        for cls in [
            FilterCatalogVersion, FilterDefinition, FilterEvidenceApprovalRequest,
            BuilderDraftValidationRequest, MultivaluePreservationRequest,
            BeaconOverrideCandidatePreparationRequest, CatalogSafeFilterReadModel,
        ]:
            cfg = cls.model_config
            assert cfg.get("extra") == "forbid", f"{cls.__name__} extra != forbid"
            assert cfg.get("frozen") is True, f"{cls.__name__} not frozen"

    def test_all_six_modules_exported_in_package_all(self) -> None:
        all_exports = _get_all()
        contract_exports = {"FilterCatalogVersion", "FilterDefinition", "FilterEvidenceReference"}
        evidence_exports = {"evaluate_filter_evidence_approval", "FilterEvidenceApprovalRequest"}
        builder_exports = {"project_builder_field_definition", "validate_builder_draft"}
        value_exports = {"evaluate_multivalue_preservation", "validate_range_value", "evaluate_filter_semantic_exposure"}
        beacon_exports = {"prepare_beacon_override_candidate"}
        safe_read_exports = {"project_catalog_safe_filter_read", "CatalogSafeFilterReadModel"}
        for group_name, symbols in [
            ("contracts", contract_exports), ("evidence_approval", evidence_exports),
            ("builder_validation", builder_exports), ("value_dependency", value_exports),
            ("beacon_override", beacon_exports), ("safe_read_models", safe_read_exports),
        ]:
            for sym in symbols:
                assert sym in all_exports, f"{sym} from {group_name} not in package __all__"
