"""Deterministic public export checks for MAX semantic contracts."""
import importlib
import sys

import mayak.modules.max_adapter as package
import mayak.modules.max_adapter.contracts as contracts

CONTRACTS = [
    "MaxAccountLinkReference", "MaxAdapterReadModel", "MaxCommandEnvelope",
    "MaxCommandNormalizationState", "MaxCommandSourceKind", "MaxCommandSurfaceKind",
    "MaxContactValidationResult", "MaxContactValidationState",
    "MaxEligibilityEvidenceReference", "MaxEligibilityState",
    "MaxMiniAppValidationResult", "MaxMiniAppValidationState", "MaxOutboundRequest",
    "MaxOutboundRequestState", "MaxProviderIdentity", "MaxProviderOutcome",
    "MaxProviderOutcomeState", "MaxReconciliationRecord", "MaxReconciliationState",
    "MaxRetryRecommendation", "MaxUpdateDeduplicationRecord",
    "MaxUpdateDeduplicationState", "MaxUpdateIntakeRecord", "MaxUpdateIntakeState",
    "MaxUpdateAdmissionState", "MaxUpdateSourceKind", "MaxUpdateStructuralClass",
]
RECORDS = ["MaxProviderIdentity", "MaxAccountLinkReference", "MaxEligibilityEvidenceReference",
           "MaxUpdateIntakeRecord", "MaxUpdateDeduplicationRecord", "MaxCommandEnvelope",
           "MaxContactValidationResult", "MaxMiniAppValidationResult", "MaxOutboundRequest",
           "MaxProviderOutcome", "MaxReconciliationRecord", "MaxAdapterReadModel"]
ENUMS = ["MaxEligibilityState", "MaxUpdateIntakeState", "MaxUpdateAdmissionState",
         "MaxUpdateSourceKind", "MaxUpdateStructuralClass", "MaxUpdateDeduplicationState",
         "MaxCommandSourceKind", "MaxCommandSurfaceKind", "MaxCommandNormalizationState",
         "MaxContactValidationState", "MaxMiniAppValidationState", "MaxOutboundRequestState",
         "MaxProviderOutcomeState", "MaxRetryRecommendation", "MaxReconciliationState"]

def test_contract_exports_are_exact_and_ordered():
    assert contracts.__all__ == CONTRACTS

def test_package_exports_are_exact_and_ordered():
    assert package.__all__ == ["MODULE_ID", *CONTRACTS]

def test_package_reexports_preserve_identity():
    assert all(getattr(package, n) is getattr(contracts, n) for n in CONTRACTS)

def test_module_id_is_stable():
    assert package.MODULE_ID == "10-max-adapter"

def test_authoritative_records_and_enums_are_exact():
    assert len(RECORDS) == 12 and len(ENUMS) == 15
    assert all(getattr(contracts, n).__module__.endswith("max_adapter.contracts")
               for n in RECORDS + ENUMS)

def test_no_extra_public_max_symbols():
    public = {n for n in vars(contracts) if n.startswith("Max") and not n.startswith("_")}
    assert public == set(CONTRACTS)

def test_repeated_import_is_deterministic():
    first = importlib.import_module("mayak.modules.max_adapter")
    second = importlib.reload(first)
    assert all(getattr(first, n) is getattr(second, n) for n in CONTRACTS)

def test_import_has_no_provider_runtime_side_effect():
    before = set(sys.modules)
    importlib.reload(contracts)
    added = set(sys.modules) - before
    assert not any(n.split(".")[0] in {"requests", "httpx", "aiohttp", "sqlalchemy"}
                   for n in added)
