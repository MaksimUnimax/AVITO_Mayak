"""Literal Web Cabinet public exports, enum and reload contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import mayak.modules.web_cabinet as package
from mayak.modules.web_cabinet import (
    admin_analytics,
    auth_context,
    beacon_commands,
    channel_linking,
    entitlement_projections,
    notification_history,
    read_models,
    security_privacy,
    status_display,
    support_handoff,
)

_OWNER_MODULES: dict[str, types.ModuleType] = {
    "read_models": read_models,
    "beacon_commands": beacon_commands,
    "auth_context": auth_context,
    "entitlement_projections": entitlement_projections,
    "notification_history": notification_history,
    "status_display": status_display,
    "channel_linking": channel_linking,
    "admin_analytics": admin_analytics,
    "support_handoff": support_handoff,
    "security_privacy": security_privacy,
}

_SENSITIVE_PREFIXES = (
    "SECRET", "TOKEN", "PASSWORD", "PASSWD", "PRIVATE", "CREDENTIAL",
    "API_KEY", "AUTH", "COOKIE", "SESSION", "SSH_", "GITHUB_",
    "AWS_", "AZURE_", "GOOGLE_",
)


def _safe_environ() -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, value in os.environ.items():
        upper_key = key.upper()
        if any(prefix in upper_key for prefix in _SENSITIVE_PREFIXES):
            continue
        safe[key] = value
    repo_src = str(Path(__file__).resolve().parents[2] / "src")
    safe["PYTHONPATH"] = repo_src
    return safe


def _snapshot_parent_state() -> dict[str, Any]:
    pkg_id = id(package)
    module_ids = {name: id(mod) for name, mod in _OWNER_MODULES.items()}
    export_ids = {name: id(package.__dict__[name]) for name in package.__all__}
    owner_export_ids: dict[tuple[str, str], int] = {}
    owner_all_lists: dict[str, tuple[str, ...]] = {}
    for mod_name, mod in _OWNER_MODULES.items():
        owner_all_lists[mod_name] = tuple(mod.__all__)
        for export_name in mod.__all__:
            owner_export_ids[(mod_name, export_name)] = id(mod.__dict__[export_name])
    pkg_all_before = tuple(package.__all__)
    env_before = dict(os.environ)
    assert pkg_all_before == tuple(PACKAGE_EXPORTS), (
        f"Package exports mismatch before snapshot: {len(pkg_all_before)} vs {len(PACKAGE_EXPORTS)}"
    )
    for mod in _OWNER_MODULES.values():
        mod_name = mod.__name__.rsplit(".", 1)[-1]
        assert tuple(mod.__all__) == tuple(MODULE_EXPORTS[mod]), (
            f"Module {mod_name} exports mismatch before snapshot"
        )
    for name in package.__all__:
        if name == "MODULE_ID":
            continue
        for mod in _OWNER_MODULES.values():
            if name in mod.__dict__:
                assert package.__dict__[name] is mod.__dict__[name], (
                    f"Package-to-owner identity broken for {name}"
                )
                break
    seen_names: set[str] = set()
    for mod in _OWNER_MODULES.values():
        for name in mod.__all__:
            assert name not in seen_names, f"Duplicate owner export: {name}"
            seen_names.add(name)
    assert package.MODULE_ID == "12-web-cabinet", (
        f"MODULE_ID mismatch: {package.MODULE_ID}"
    )
    return {
        "pkg_id": pkg_id,
        "module_ids": module_ids,
        "export_ids": export_ids,
        "owner_export_ids": owner_export_ids,
        "owner_all_lists": owner_all_lists,
        "pkg_all": pkg_all_before,
        "env": env_before,
    }


def _compare_parent_state(snapshot: dict[str, Any]) -> None:
    assert id(package) == snapshot["pkg_id"], "Package identity changed"
    for name, expected_id in snapshot["module_ids"].items():
        current_mod = _OWNER_MODULES[name]
        assert id(current_mod) == expected_id, (
            f"Module {name} identity changed: {id(current_mod)} != {expected_id}"
        )
    for name, expected_id in snapshot["export_ids"].items():
        assert id(package.__dict__[name]) == expected_id, (
            f"Package export {name} identity changed"
        )
    for (mod_name, exp_name), expected_id in snapshot["owner_export_ids"].items():
        mod = _OWNER_MODULES[mod_name]
        assert id(mod.__dict__[exp_name]) == expected_id, (
            f"Owner export {mod_name}.{exp_name} identity changed"
        )
    assert tuple(package.__all__) == snapshot["pkg_all"], "Package __all__ changed"
    for mod_name, expected_all in snapshot["owner_all_lists"].items():
        mod = _OWNER_MODULES[mod_name]
        assert tuple(mod.__all__) == expected_all, (
            f"Owner module {mod_name} __all__ changed"
        )
    for name in package.__all__:
        if name == "MODULE_ID":
            continue
        for mod in _OWNER_MODULES.values():
            if name in mod.__dict__:
                assert package.__dict__[name] is mod.__dict__[name], (
                    f"Package-to-owner identity broken for {name} after subprocess"
                )
                break
    assert dict(os.environ) == snapshot["env"], "Parent environment changed"

MODULE_EXPORTS = {
    read_models: [
        "RequestWebCabinetViewQuery",
        "WebCabinetViewResult",
        "WebCabinetViewState",
        "WebReadFreshness",
        "WebReadModelFamily",
        "WebReadModelSourceReference",
        "WebSourceState",
        "WebViewAudience",
    ],
    beacon_commands: [
        "SubmitBeaconWebCommandCommand",
        "WebBeaconCommandKind",
        "WebBeaconCommandSubmitOutcome",
        "WebBeaconCommandSubmitState",
        "WebBeaconPatchField",
    ],
    auth_context: [
        "RequestWebPresentationContextQuery",
        "WebIdentityAuthorityReference",
        "WebPresentationActorState",
        "WebPresentationContextResult",
        "WebPresentationContextState",
        "WebSessionReferenceState",
    ],
    entitlement_projections: [
        "RequestWebEntitlementProjectionQuery",
        "WebEntitlementAccessState",
        "WebEntitlementCapabilityProjection",
        "WebEntitlementProjectionResult",
        "WebEntitlementProjectionState",
        "WebTariffOptionProjection",
        "WebTariffOptionState",
    ],
    notification_history: [
        "RequestWebNotificationHistoryQuery",
        "WebNotificationDeliveryHistoryEntry",
        "WebNotificationDeliveryState",
        "WebNotificationHistoryResult",
        "WebNotificationHistoryResultState",
        "WebNotificationListingReferenceProjection",
    ],
    status_display: [
        "RequestWebStatusDisplayQuery",
        "WebStatusDisplayFamily",
        "WebStatusDisplayItem",
        "WebStatusDisplayResult",
        "WebStatusDisplayResultState",
        "WebStatusEvidenceClass",
        "WebStatusEvidenceReference",
        "WebStatusSourceFamily",
    ],
    channel_linking: [
        "RequestWebChannelSurfaceQuery",
        "SubmitWebChannelCommandCommand",
        "WebChannelCommandKind",
        "WebChannelCommandSubmitOutcome",
        "WebChannelCommandSubmitState",
        "WebChannelKind",
        "WebChannelNotificationPreferenceState",
        "WebChannelSurfaceProjection",
        "WebChannelSurfaceResult",
        "WebChannelSurfaceResultState",
        "WebChannelSurfaceState",
    ],
    admin_analytics: [
        "RequestWebAdminAnalyticsQuery",
        "WebAdminAnalyticsFilterKind",
        "WebAdminAnalyticsFilterReference",
        "WebAdminAnalyticsMetricKind",
        "WebAdminAnalyticsMetricProjection",
        "WebAdminAnalyticsMetricRequest",
        "WebAdminAnalyticsMetricState",
        "WebAdminAnalyticsResult",
        "WebAdminAnalyticsResultState",
        "WebAdminAnalyticsSortDirection",
        "WebAdminAnalyticsSortField",
    ],
    support_handoff: [
        "RequestWebSupportHandoffQuery",
        "WebSupportHandoffItemKind",
        "WebSupportHandoffItemState",
        "WebSupportHandoffProjection",
        "WebSupportHandoffResult",
        "WebSupportHandoffResultState",
    ],
    security_privacy: [
        "RequestWebSecurityPrivacyAssessmentQuery",
        "WebPrivacyControlProjection",
        "WebPrivacyProjectionState",
        "WebPrivacySurfaceKind",
        "WebSecurityPrivacyAssessmentResult",
        "WebSecurityPrivacyResultState",
    ],
}
PACKAGE_EXPORTS = ["MODULE_ID"] + [name for module in MODULE_EXPORTS.values() for name in module]


_EXPECTED_RESULT_KEYS = frozenset({
    "module_name",
    "reload_count",
    "module_object_same",
    "expected_export_count",
    "pre_exports_match",
    "pre_export_count",
    "post_exports_match",
    "post_export_count",
    "export_order_same",
    "exports_unique",
    "env_unchanged",
    "module_id",
    "errors",
})

_INTEGER_FIELDS = frozenset({
    "reload_count",
    "expected_export_count",
    "pre_export_count",
    "post_export_count",
})

_BOOLEAN_FIELDS = frozenset({
    "module_object_same",
    "pre_exports_match",
    "post_exports_match",
    "export_order_same",
    "exports_unique",
    "env_unchanged",
})

_KNOWN_ERROR_CODES = frozenset({
    "pre_exports_mismatch",
    "pre_export_count_mismatch",
    "module_object_changed",
    "post_exports_mismatch",
    "export_order_changed",
    "duplicate_exports",
    "env_changed",
    "module_id_mismatch",
    "package_export_count_mismatch",
})


def _validate_child_result_schema(
    result: dict,
    import_path: str,
    package_target: bool = False,
) -> None:
    if type(result) is not dict:
        raise AssertionError(
            f"Child result is not a dict: {type(result).__name__}"
        )
    actual_keys = frozenset(result.keys())
    if actual_keys != _EXPECTED_RESULT_KEYS:
        missing = _EXPECTED_RESULT_KEYS - actual_keys
        extra = actual_keys - _EXPECTED_RESULT_KEYS
        parts = []
        if missing:
            parts.append(f"missing={sorted(missing)}")
        if extra:
            parts.append(f"unknown={sorted(extra)}")
        raise AssertionError(
            f"Child result schema mismatch: {'; '.join(parts)}"
        )
    for field in _INTEGER_FIELDS:
        if type(result[field]) is not int:
            raise AssertionError(
                f"Child result field {field!r} type "
                f"{type(result[field]).__name__} != int"
            )
    for field in _BOOLEAN_FIELDS:
        if type(result[field]) is not bool:
            raise AssertionError(
                f"Child result field {field!r} type "
                f"{type(result[field]).__name__} != bool"
            )
    if type(result["module_name"]) is not str:
        raise AssertionError(
            f"Child result field 'module_name' type "
            f"{type(result['module_name']).__name__} != str"
        )
    if result["module_name"] != import_path:
        raise AssertionError(
            f"Child module_name {result['module_name']!r} "
            f"!= requested import_path {import_path!r}"
        )
    if package_target:
        if type(result["module_id"]) is not str:
            raise AssertionError(
                f"Child result field 'module_id' type "
                f"{type(result['module_id']).__name__} != str for package target"
            )
        if result["module_id"] != "12-web-cabinet":
            raise AssertionError(
                f"Child module_id {result['module_id']!r} "
                f"!= expected '12-web-cabinet'"
            )
    else:
        if result["module_id"] is not None:
            raise AssertionError(
                f"Child result field 'module_id' "
                f"must be None for non-package target, got {result['module_id']!r}"
            )
    if type(result["errors"]) is not list:
        raise AssertionError(
            f"Child result field 'errors' type "
            f"{type(result['errors']).__name__} != list"
        )
    seen_codes: set[str] = set()
    for code in result["errors"]:
        if type(code) is not str:
            raise AssertionError(
                f"Child error code type {type(code).__name__} != str"
            )
        if code not in _KNOWN_ERROR_CODES:
            raise AssertionError(
                f"Child unknown error code {code!r}"
            )
        if code in seen_codes:
            raise AssertionError(
                f"Child duplicate error code {code!r}"
            )
        seen_codes.add(code)


def _validate_child_result_binding(
    result: dict,
    import_path: str,
    expected_exports: list[str],
    package_target: bool,
    return_code: int,
) -> None:
    if result["module_name"] != import_path:
        raise AssertionError(
            f"Binding failure: module_name {result['module_name']!r} "
            f"!= requested import_path {import_path!r}"
        )
    if result["reload_count"] != 1:
        raise AssertionError(
            f"Binding failure: reload_count {result['reload_count']} != 1"
        )
    if result["expected_export_count"] != len(expected_exports):
        raise AssertionError(
            f"Binding failure: expected_export_count "
            f"{result['expected_export_count']} != len(expected_exports) "
            f"{len(expected_exports)}"
        )
    errors = result["errors"]
    if return_code == 0 and errors:
        raise AssertionError(
            f"Return-code consistency failure: rc=0 but errors={errors}"
        )
    if return_code != 0 and not errors:
        raise AssertionError(
            f"Return-code consistency failure: rc={return_code} but errors=[]"
        )
    if return_code == 0:
        if result["pre_export_count"] != len(expected_exports):
            raise AssertionError(
                f"Success binding failure: pre_export_count "
                f"{result['pre_export_count']} != len(expected_exports) "
                f"{len(expected_exports)}"
            )
        if result["post_export_count"] != len(expected_exports):
            raise AssertionError(
                f"Success binding failure: post_export_count "
                f"{result['post_export_count']} != len(expected_exports) "
                f"{len(expected_exports)}"
            )
        if not result["pre_exports_match"]:
            raise AssertionError(
                "Success binding failure: pre_exports_match is False"
            )
        if not result["post_exports_match"]:
            raise AssertionError(
                "Success binding failure: post_exports_match is False"
            )
        if not result["module_object_same"]:
            raise AssertionError(
                "Success binding failure: module_object_same is False"
            )
        if not result["export_order_same"]:
            raise AssertionError(
                "Success binding failure: export_order_same is False"
            )
        if not result["exports_unique"]:
            raise AssertionError(
                "Success binding failure: exports_unique is False"
            )
        if not result["env_unchanged"]:
            raise AssertionError(
                "Success binding failure: env_unchanged is False"
            )
        if package_target:
            if result["module_id"] != "12-web-cabinet":
                raise AssertionError(
                    f"Success binding failure: module_id "
                    f"{result['module_id']!r} != '12-web-cabinet'"
                )
            if result["expected_export_count"] != 75:
                raise AssertionError(
                    f"Success binding failure: expected_export_count "
                    f"{result['expected_export_count']} != 75"
                )
            if result["pre_export_count"] != 75:
                raise AssertionError(
                    f"Success binding failure: pre_export_count "
                    f"{result['pre_export_count']} != 75"
                )
            if result["post_export_count"] != 75:
                raise AssertionError(
                    f"Success binding failure: post_export_count "
                    f"{result['post_export_count']} != 75"
                )
        else:
            if result["module_id"] is not None:
                raise AssertionError(
                    f"Success binding failure: module_id "
                    f"{result['module_id']!r} != None for non-package target"
                )
    if return_code != 0:
        if not errors:
            raise AssertionError(
                f"Negative result with rc={return_code} must have errors, "
                f"got empty errors list"
            )
        for code in errors:
            if code not in _KNOWN_ERROR_CODES:
                raise AssertionError(
                    f"Negative result with unknown error code {code!r}"
                )
        raise AssertionError(
            f"Negative child result: rc={return_code}, errors={errors}"
        )


def _run_isolated_reload_check(
    import_path: str,
    expected_exports: list[str],
    package_target: bool = False,
) -> dict:
    parent_snapshot = _snapshot_parent_state()
    child_script = (
        "import sys, json, importlib, os\n"
        "args = json.loads(sys.argv[1])\n"
        "import_path = args['import_path']\n"
        "expected_exports = args['expected_exports']\n"
        "package_target = args.get('package_target', False)\n"
        "\n"
        "before_env = dict(os.environ)\n"
        "target = importlib.import_module(import_path)\n"
        "\n"
        "pre_all = list(target.__all__)\n"
        "pre_matches = pre_all == expected_exports\n"
        "pre_count = len(pre_all)\n"
        "module_object_id = id(target)\n"
        "\n"
        "reloaded = importlib.reload(target)\n"
        "\n"
        "post_all = list(target.__all__)\n"
        "post_matches = post_all == expected_exports\n"
        "obj_same = reloaded is target\n"
        "order_same = pre_all == post_all\n"
        "unique = len(post_all) == len(set(post_all))\n"
        "env_unchanged = dict(os.environ) == before_env\n"
        "\n"
        "module_id = None\n"
        "if package_target:\n"
        "    module_id = getattr(target, 'MODULE_ID', None)\n"
        "\n"
        "result = {\n"
        "    'module_name': import_path,\n"
        "    'reload_count': 1,\n"
        "    'module_object_same': obj_same,\n"
        "    'expected_export_count': len(expected_exports),\n"
        "    'pre_exports_match': pre_matches,\n"
        "    'pre_export_count': pre_count,\n"
        "    'post_exports_match': post_matches,\n"
        "    'post_export_count': len(post_all),\n"
        "    'export_order_same': order_same,\n"
        "    'exports_unique': unique,\n"
        "    'env_unchanged': env_unchanged,\n"
        "    'module_id': module_id,\n"
        "    'errors': [],\n"
        "}\n"
        "if not pre_matches:\n"
        "    result['errors'].append('pre_exports_mismatch')\n"
        "if pre_count != len(expected_exports):\n"
        "    result['errors'].append('pre_export_count_mismatch')\n"
        "if not obj_same:\n"
        "    result['errors'].append('module_object_changed')\n"
        "if not post_matches:\n"
        "    result['errors'].append('post_exports_mismatch')\n"
        "if not order_same:\n"
        "    result['errors'].append('export_order_changed')\n"
        "if not unique:\n"
        "    result['errors'].append('duplicate_exports')\n"
        "if not env_unchanged:\n"
        "    result['errors'].append('env_changed')\n"
        "if package_target:\n"
        "    if module_id != '12-web-cabinet':\n"
        "        result['errors'].append('module_id_mismatch')\n"
        "    if len(post_all) != 75:\n"
        "        result['errors'].append('package_export_count_mismatch')\n"
        "print(json.dumps(result))\n"
        "sys.exit(0 if result['errors'] == [] else 1)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", child_script, json.dumps({
            "import_path": import_path,
            "expected_exports": expected_exports,
            "package_target": package_target,
        })],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parents[2]),
        env=_safe_environ(),
        timeout=30,
        shell=False,
    )
    child_defect: AssertionError | None = None
    parent_defect: AssertionError | None = None
    result: dict | None = None
    try:
        try:
            result = json.loads(proc.stdout.strip())
        except (json.JSONDecodeError, ValueError) as exc:
            safe_stderr = proc.stderr[:500] if proc.stderr else ""
            child_defect = AssertionError(
                f"Child JSON parse error: {exc}; "
                f"returncode={proc.returncode}; stderr={safe_stderr!r}"
            )
        if child_defect is None and type(result) is not dict:
            child_defect = AssertionError(
                f"Child result is not a dict: {type(result).__name__}"
            )
        if child_defect is None and result is not None:
            _validate_child_result_schema(result, import_path, package_target)
        if child_defect is None and result is not None:
            try:
                _validate_child_result_binding(
                    result, import_path, expected_exports, package_target, proc.returncode
                )
            except AssertionError as exc:
                child_defect = exc
        if child_defect is None and proc.returncode != 0:
            safe_errors = result.get("errors", [])  # type: ignore[union-attr]
            safe_stderr = proc.stderr[:200] if proc.stderr else ""
            child_defect = AssertionError(
                f"Child returned nonzero rc={proc.returncode}: "
                f"errors={safe_errors}; stderr={safe_stderr!r}"
            )
        if child_defect is None and result is not None and result.get("errors"):
            child_defect = AssertionError(
                f"Child reported errors: {result['errors']}"
            )
    except AssertionError as exc:
        child_defect = exc
    try:
        _compare_parent_state(parent_snapshot)
    except AssertionError as exc:
        parent_defect = exc
    if child_defect is not None and parent_defect is not None:
        raise AssertionError(
            f"Combined child_result_defect and parent_state_defect: "
            f"child={child_defect!s}; parent={parent_defect!s}"
        )
    if child_defect is not None:
        raise child_defect
    if parent_defect is not None:
        raise parent_defect
    return result  # type: ignore[return-value]


ENUM_VALUES = {
    "WebCabinetViewState": (
        "AUTHORIZED",
        "REDACTED",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
    ),
    "WebReadFreshness": ("FRESH", "STALE", "UNKNOWN", "AMBIGUOUS"),
    "WebReadModelFamily": (
        "ACCOUNT_SUMMARY",
        "ACTIVE_BEACONS",
        "BEACON_HISTORY",
        "TARIFF_ACCESS_LIMITS",
        "LAST_SCAN_STATUS",
        "MESSAGE_RESULT_HISTORY",
        "TELEGRAM_CHANNEL",
        "MAX_CHANNEL",
        "CUSTOMER_SUPPORT_STATUS",
        "ADMIN_ANALYTICS_PLACEHOLDER",
    ),
    "WebSourceState": (
        "AVAILABLE",
        "REDACTED",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "UNKNOWN",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
    "WebViewAudience": ("CUSTOMER", "ADMIN_AUTHORIZED"),
    "WebBeaconCommandKind": (
        "PATCH_CURRENT_CONFIGURATION",
        "ARCHIVE_TO_HISTORY",
        "DELETE_TO_HISTORY",
        "RESTORE_FROM_HISTORY",
        "PERMANENT_DELETE",
    ),
    "WebBeaconCommandSubmitState": (
        "SUBMITTED",
        "REPLAYED",
        "REJECTED",
        "FORBIDDEN",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "RECONCILIATION_REQUIRED",
        "UNSUPPORTED",
    ),
    "WebPresentationActorState": ("VERIFIED", "UNAUTHENTICATED", "FORBIDDEN", "AMBIGUOUS", "STALE"),
    "WebPresentationContextState": (
        "AUTHORIZED",
        "UNAUTHENTICATED",
        "FORBIDDEN",
        "SESSION_REVOKED",
        "SESSION_EXPIRED",
        "SESSION_INVALID",
        "STALE",
        "AMBIGUOUS",
    ),
    "WebSessionReferenceState": (
        "ABSENT",
        "ISSUED",
        "ACTIVE",
        "REVOKED",
        "EXPIRED",
        "INVALID",
        "UNKNOWN",
        "AMBIGUOUS",
    ),
    "WebEntitlementAccessState": (
        "ALLOWED",
        "DENIED",
        "BLOCKED",
        "EXPIRED",
        "USER_CHOICE_REQUIRED",
        "FREE_COMPLIANCE_REQUIRED",
        "CONFLICT",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebEntitlementProjectionState": (
        "AVAILABLE",
        "DENIED",
        "BLOCKED",
        "EXPIRED",
        "USER_CHOICE_REQUIRED",
        "FREE_COMPLIANCE_REQUIRED",
        "CONFLICT",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebTariffOptionState": (
        "CURRENT",
        "AVAILABLE",
        "UNAVAILABLE",
        "POLICY_BLOCKED",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebNotificationDeliveryState": (
        "PLANNED",
        "REPLAYED",
        "SUPPRESSED",
        "BLOCKED",
        "DELIVERED",
        "FAILED",
        "RECONCILIATION_REQUIRED",
    ),
    "WebNotificationHistoryResultState": (
        "AVAILABLE",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
        "RECONCILIATION_REQUIRED",
    ),
    "WebStatusDisplayFamily": (
        "NO_NEW_LISTINGS",
        "EXTERNAL_UNAVAILABLE_CONTINUING_SCAN",
        "RECOVERY_COMPLETED",
        "LOST_ANCHORS_STATE_RESTORED",
        "ACCESS_RESTRICTED",
        "FREE_COMPLIANCE_REQUIRED",
        "CHANNEL_NOT_CONNECTED",
        "CHANNEL_NOT_VERIFIED",
        "CHANNEL_DISABLED_BY_USER",
        "NOTIFICATION_NOT_DELIVERED",
        "NOTIFICATION_STATUS_UNKNOWN",
        "RECONCILIATION_REQUIRED",
        "READ_MODEL_STALE",
        "NOT_AUTHORIZED_OR_NOT_FOUND_SAFE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebStatusDisplayResultState": (
        "AVAILABLE",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebStatusEvidenceClass": (
        "SCAN_NO_NEW_PROVEN",
        "SCAN_EXTERNAL_UNAVAILABLE",
        "SCAN_RECOVERY_COMPLETED",
        "SCAN_LOST_ANCHORS_RECOVERED",
        "ENTITLEMENT_ACCESS_RESTRICTED",
        "ENTITLEMENT_FREE_COMPLIANCE_REQUIRED",
        "CHANNEL_NOT_CONNECTED",
        "CHANNEL_NOT_VERIFIED",
        "CHANNEL_DISABLED_BY_USER",
        "NOTIFICATION_DELIVERY_FAILED",
        "NOTIFICATION_DELIVERY_UNKNOWN",
        "NOTIFICATION_RECONCILIATION_REQUIRED",
        "WEB_READ_MODEL_STALE",
        "SAFE_NOT_AUTHORIZED_OR_NOT_FOUND",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebStatusSourceFamily": (
        "SCAN_ORCHESTRATION",
        "NOTIFICATION_DELIVERY",
        "ENTITLEMENTS",
        "CHANNEL_ADAPTER",
        "WEB_READ_MODEL",
    ),
    "WebChannelCommandKind": ("START_CONNECTION", "ENABLE_NOTIFICATIONS", "DISABLE_NOTIFICATIONS"),
    "WebChannelCommandSubmitState": (
        "SUBMITTED",
        "REPLAYED",
        "REJECTED",
        "FORBIDDEN",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "RECONCILIATION_REQUIRED",
        "UNSUPPORTED",
    ),
    "WebChannelKind": ("TELEGRAM", "MAX"),
    "WebChannelNotificationPreferenceState": (
        "ENABLED",
        "DISABLED_BY_USER",
        "NOT_APPLICABLE",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebChannelSurfaceResultState": (
        "AVAILABLE",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebChannelSurfaceState": (
        "NOT_CONNECTED",
        "LINK_CHALLENGE_REQUIRED",
        "LINKED_ENABLED",
        "LINKED_DISABLED_BY_USER",
        "LINKED_TARGET_UNVERIFIED",
        "LINKED_TARGET_UNAVAILABLE",
        "FUTURE_GATED",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebAdminAnalyticsFilterKind": ("PERIOD", "TARIFF", "ACCOUNT_USE_STATUS"),
    "WebAdminAnalyticsMetricKind": (
        "VISITOR_COUNT",
        "REGISTERED_LINKED_USER_COUNT",
        "ACTIVE_USING_USER_COUNT",
        "FREE_TARIFF_ACCOUNT_COUNT",
        "PAID_TARIFF_ACCOUNT_COUNT",
    ),
    "WebAdminAnalyticsMetricState": ("AVAILABLE", "PRIVACY_SUPPRESSED", "STALE", "AMBIGUOUS"),
    "WebAdminAnalyticsResultState": (
        "AVAILABLE",
        "REDACTED",
        "FORBIDDEN",
        "POLICY_BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "WebAdminAnalyticsSortDirection": ("ASCENDING", "DESCENDING"),
    "WebAdminAnalyticsSortField": ("METRIC_KIND", "TARIFF", "COUNT"),
    "WebSupportHandoffItemKind": ("SUPPORT_ENTRY", "CASE_STATUS", "PUBLIC_ANSWER"),
    "WebSupportHandoffItemState": ("AVAILABLE", "REDACTED", "STALE", "AMBIGUOUS"),
    "WebSupportHandoffResultState": (
        "AVAILABLE",
        "REDACTED",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
    "WebPrivacyProjectionState": (
        "SAFE",
        "REDACTED",
        "STALE",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
    "WebPrivacySurfaceKind": (
        "BROWSER_VISIBLE_DATA",
        "SAFE_ERROR",
        "ANALYTICS_COLLECTION",
        "RETENTION_POLICY",
        "DELETION_EXPORT_POLICY",
    ),
    "WebSecurityPrivacyResultState": (
        "SAFE",
        "REDACTED",
        "FORBIDDEN",
        "STALE",
        "AMBIGUOUS",
        "POLICY_BLOCKED",
        "UNSUPPORTED",
    ),
}
MODEL_FIELDS = {
    "RequestWebCabinetViewQuery": (
        "web_cabinet_view_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "audience",
        "requested_families",
        "view_policy_reference_id",
        "reason_code",
        "verified_actor_required",
        "read_only",
        "client_state_authority",
        "direct_write_authority",
        "provider_call_authority",
        "raw_resource_access_authority",
        "foreign_host_access_authority",
    ),
    "WebCabinetViewResult": (
        "web_cabinet_view_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "sources",
        "composition_policy_reference_id",
        "redaction_policy_reference_id",
        "ambiguity_reference_id",
        "provenance_aware",
        "freshness_aware",
        "ownership_scoped",
        "authorization_required",
        "redacted",
        "minimal_personal_data",
        "contains_secret_material",
        "raw_provider_payload_retained",
        "full_private_message_retained",
        "full_listing_archive_retained",
        "mutation_authority",
        "provider_call_authority",
        "business_success_authority",
    ),
    "WebReadModelSourceReference": (
        "web_source_reference_id",
        "family",
        "owning_module_id",
        "account_id",
        "tenant_scope_reference_id",
        "state",
        "freshness",
        "safe_projection_reference_id",
        "provenance_reference_ids",
        "reason_code",
        "ambiguity_reference_id",
        "redaction_policy_reference_id",
        "safe_reference_only",
        "redacted",
        "minimal_personal_data",
        "contains_secret_material",
        "raw_provider_payload_retained",
        "full_private_message_retained",
        "full_listing_archive_retained",
        "mutation_authority",
        "provider_call_authority",
    ),
    "SubmitBeaconWebCommandCommand": (
        "web_beacon_command_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "beacon_id",
        "command_kind",
        "owning_module_id",
        "owning_module_command_family_reference_id",
        "web_observed_state_reference_id",
        "patch_fields",
        "history_entry_reference_id",
        "confirmation_reference_id",
        "entitlement_recheck_reference_id",
        "idempotency_key",
        "idempotency_scope",
        "idempotency_fingerprint",
        "correlation_id",
        "causation_id",
        "reason_code",
        "verified_actor_required",
        "ownership_scope_validation_required",
        "server_side_validation_required",
        "owning_module_current_state_reload_required",
        "client_validation_authority",
        "web_observed_state_authority",
        "direct_write_authority",
        "provider_call_authority",
        "entitlement_mutation_authority",
        "scan_mutation_authority",
        "notification_mutation_authority",
        "stale_full_form_overwrite",
        "source_url_only_idempotency",
        "raw_provider_payload_retained",
        "business_success_authority",
    ),
    "WebBeaconCommandSubmitOutcome": (
        "web_beacon_command_submit_outcome_id",
        "metadata",
        "command",
        "state",
        "owning_module_id",
        "owning_module_outcome_reference_id",
        "authoritative_state_reference_id",
        "replay_of_outcome_reference_id",
        "rejection_reason_code",
        "ambiguity_reference_id",
        "applied_field_names",
        "owning_module_accepted",
        "authoritative_state_reloaded",
        "safe_display_outcome",
        "explicit_owning_module_outcome_required",
        "web_business_success_authority",
        "direct_write_authority",
        "provider_call_authority",
        "raw_provider_payload_retained",
        "full_form_state_retained",
        "committed_scan_audit_facts_rewritten",
        "physical_delete_implementation_claimed",
    ),
    "WebBeaconPatchField": (
        "web_patch_field_id",
        "field_name",
        "requested_value_reference_id",
        "owning_module_validation_family_reference_id",
        "client_validation_reference_id",
        "explicitly_supplied",
        "server_validation_required",
        "client_validation_authority",
        "field_support_authority",
        "raw_value_retained",
        "provider_payload_retained",
    ),
    "RequestWebPresentationContextQuery": (
        "web_presentation_context_query_id",
        "metadata",
        "actor_context_reference_id",
        "requested_audience",
        "tenant_scope_reference_id",
        "identity_validation_policy_reference_id",
        "reason_code",
        "identity_authority_required",
        "read_only",
        "client_account_authority",
        "client_role_authority",
        "client_session_authority",
        "provider_identity_authority",
        "phone_requirement_defined",
        "password_policy_defined",
        "recovery_policy_defined",
        "account_merge_policy_defined",
        "raw_credential_material_present",
        "raw_session_token_present",
        "raw_provider_payload_present",
        "cookie_jwt_oauth_implementation_claimed",
        "session_storage_implementation_claimed",
        "direct_identity_write_authority",
    ),
    "WebIdentityAuthorityReference": (
        "web_identity_authority_reference_id",
        "owning_module_id",
        "actor_context_reference_id",
        "actor_state",
        "account_id",
        "authorization_decision_reference_id",
        "auth_session_reference_id",
        "session_state",
        "role_scope_reference_id",
        "target_scope_reference_id",
        "audit_reference_id",
        "reason_code",
        "ambiguity_reference_id",
        "internal_account_id_authority",
        "provider_identity_authority",
        "web_local_account_authority",
        "client_role_authority",
        "client_session_authority",
        "contact_point_is_account_authority",
        "phone_requirement_defined",
        "raw_credential_retained",
        "raw_session_token_retained",
        "raw_provider_payload_retained",
        "account_merge_authority",
        "identity_mutation_authority",
        "session_implementation_authority",
        "safe_reference_only",
    ),
    "WebPresentationContextResult": (
        "web_presentation_context_result_id",
        "metadata",
        "query",
        "state",
        "authority",
        "resolved_account_id",
        "safe_identity_summary_reference_id",
        "ambiguity_reference_id",
        "reason_code",
        "identity_authoritative",
        "account_scope_preserved",
        "presentation_only",
        "session_transport_neutral",
        "authentication_implementation_present",
        "authorization_implementation_present",
        "separate_customer_database",
        "direct_identity_write_authority",
        "provider_call_authority",
        "business_success_authority",
        "raw_credential_material_present",
        "raw_session_token_present",
        "raw_provider_payload_present",
        "phone_requirement_defined",
        "password_recovery_policy_defined",
        "account_merge_policy_defined",
    ),
    "RequestWebEntitlementProjectionQuery": (
        "web_entitlement_projection_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "requested_capability_reference_ids",
        "include_tariff_options",
        "entitlement_evaluation_policy_reference_id",
        "tariff_visibility_policy_reference_id",
        "reason_code",
        "verified_actor_required",
        "account_scope_required",
        "read_only",
        "entitlements_authority_required",
        "client_entitlement_authority",
        "client_tariff_authority",
        "web_entitlement_evaluator",
        "direct_entitlement_write_authority",
        "subscription_mutation_authority",
        "grant_mutation_authority",
        "payment_mutation_authority",
        "usage_counter_mutation_authority",
        "provider_call_authority",
        "payment_response_is_entitlement_authority",
        "invented_tariff_values_allowed",
        "raw_payment_payload_present",
    ),
    "WebEntitlementCapabilityProjection": (
        "web_entitlement_capability_projection_id",
        "account_id",
        "capability_reference_id",
        "access_state",
        "effective_entitlement_decision_reference_id",
        "safe_limit_display_reference_id",
        "effective_interval_reference_id",
        "source_reference_ids",
        "reason_code",
        "ambiguity_reference_id",
        "derived_from_entitlements",
        "safe_reference_only",
        "web_recomputed",
        "web_limit_authority",
        "raw_limit_value_retained",
        "payment_evidence_authority",
        "raw_payment_payload_retained",
        "direct_mutation_authority",
        "provider_call_authority",
    ),
    "WebEntitlementProjectionResult": (
        "web_entitlement_projection_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "effective_entitlement_summary_reference_id",
        "current_tariff_definition_reference_id",
        "capabilities",
        "tariff_options",
        "payment_upgrade_placeholder_reference_id",
        "source_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "safe_projection_only",
        "entitlements_authoritative",
        "web_entitlement_authority",
        "web_tariff_definition_authority",
        "effective_entitlement_recomputed_by_web",
        "prices_limits_names_invented",
        "subscription_mutation_authority",
        "grant_mutation_authority",
        "payment_mutation_authority",
        "usage_counter_mutation_authority",
        "direct_write_authority",
        "provider_call_authority",
        "payment_provider_integration_present",
        "payment_response_is_entitlement_authority",
        "raw_payment_payload_retained",
        "card_data_retained",
        "minimal_personal_data",
        "redacted",
        "business_success_authority",
    ),
    "WebTariffOptionProjection": (
        "web_tariff_option_projection_id",
        "owning_module_id",
        "account_id",
        "tariff_definition_reference_id",
        "semantic_version_reference_id",
        "state",
        "safe_name_display_reference_id",
        "safe_price_display_reference_id",
        "safe_billing_period_display_reference_id",
        "safe_limit_summary_reference_ids",
        "source_reference_ids",
        "reason_code",
        "ambiguity_reference_id",
        "approved_definition_reference_required",
        "safe_display_references_only",
        "web_tariff_authority",
        "web_price_authority",
        "web_limit_authority",
        "payment_provider_authority",
        "payment_response_is_entitlement_authority",
        "raw_payment_payload_retained",
        "future_tariff_invention_authority",
        "provider_call_authority",
        "direct_mutation_authority",
    ),
    "RequestWebNotificationHistoryQuery": (
        "web_notification_history_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "requested_audience",
        "beacon_scope_ids",
        "notification_read_policy_reference_id",
        "freshness_policy_reference_id",
        "reason_code",
        "verified_actor_required",
        "account_scope_required",
        "read_only",
        "notification_authority_required",
        "client_history_authority",
        "web_delivery_evaluator",
        "direct_notification_write_authority",
        "outbox_mutation_authority",
        "attempt_mutation_authority",
        "retry_authority",
        "reconciliation_execution_authority",
        "provider_mapping_authority",
        "provider_call_authority",
        "read_tracking_authority",
        "click_tracking_authority",
        "retention_policy_defined",
        "raw_provider_payload_present",
        "full_message_history_requested",
        "full_listing_archive_requested",
    ),
    "WebNotificationDeliveryHistoryEntry": (
        "web_notification_delivery_history_entry_id",
        "account_id",
        "beacon_id",
        "notification_history_entry_reference_id",
        "notification_batch_item_reference_id",
        "notification_source_decision_reference_id",
        "notification_outbox_item_reference_id",
        "notification_attempt_reference_id",
        "channel_class_reference_id",
        "safe_result_reference_id",
        "delivery_state",
        "safe_error_category_reference_id",
        "safe_reason_codes",
        "listing_references",
        "listing_count",
        "reconciliation_required",
        "reconciliation_reference_id",
        "retry_policy_required",
        "retry_policy_reference_id",
        "evidence_reference_ids",
        "freshness_reference_ids",
        "provenance_reference_ids",
        "derived_from_notification",
        "safe_projection_only",
        "per_item_outcome_exposed",
        "listing_references_preserved",
        "web_delivery_authority",
        "delivery_execution_authority",
        "provider_mapping_authority",
        "provider_call_authority",
        "outbox_mutation_authority",
        "attempt_mutation_authority",
        "retry_execution_authority",
        "reconciliation_execution_authority",
        "read_tracking_authority",
        "click_tracking_authority",
        "retention_authority",
        "raw_message_content_retained",
        "full_chat_history_retained",
        "full_listing_archive_retained",
        "raw_listing_payload_retained",
        "raw_provider_payload_retained",
        "business_success_authority",
    ),
    "WebNotificationHistoryResult": (
        "web_notification_history_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "notification_read_model_reference_id",
        "notification_projection_decision_reference_id",
        "history_entries",
        "safe_listing_references",
        "listing_count",
        "history_entry_count",
        "replay_visible",
        "failure_visible",
        "reconciliation_required",
        "source_reference_ids",
        "freshness_reference_ids",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "safe_projection_only",
        "notification_authoritative",
        "web_notification_authority",
        "per_item_outcomes_exposed",
        "listing_references_preserved",
        "preview_truncation_applied",
        "delivery_execution_authority",
        "provider_mapping_authority",
        "provider_call_authority",
        "outbox_mutation_authority",
        "attempt_mutation_authority",
        "retry_execution_authority",
        "reconciliation_execution_authority",
        "read_tracking_authority",
        "click_tracking_authority",
        "retention_policy_defined",
        "full_listing_archive_retained",
        "full_message_history_retained",
        "full_chat_history_retained",
        "raw_listing_payload_retained",
        "raw_provider_payload_retained",
        "credentials_retained",
        "minimal_personal_data",
        "redacted",
        "business_success_authority",
    ),
    "WebNotificationListingReferenceProjection": (
        "web_notification_listing_reference_projection_id",
        "account_id",
        "beacon_id",
        "safe_listing_reference_id",
        "notification_listing_card_reference_id",
        "source_event_reference_id",
        "source_fact_reference_id",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "reason_code",
        "safe_reference_only",
        "notification_projection_source",
        "listing_reference_preserved",
        "raw_listing_value_retained",
        "raw_avito_payload_retained",
        "raw_provider_payload_retained",
        "contact_data_retained",
        "full_listing_archive_authority",
        "fetch_authority",
        "parse_authority",
        "enrichment_authority",
        "provider_call_authority",
        "retention_authority",
    ),
    "RequestWebStatusDisplayQuery": (
        "web_status_display_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "requested_audience",
        "beacon_scope_ids",
        "requested_status_reference_ids",
        "status_mapping_policy_reference_id",
        "freshness_policy_reference_id",
        "reason_code",
        "verified_actor_required",
        "account_scope_required",
        "read_only",
        "owning_module_status_authority_required",
        "client_status_authority",
        "browser_state_authority",
        "web_business_outcome_evaluator",
        "direct_foreign_state_write_authority",
        "delivery_execution_authority",
        "retry_execution_authority",
        "reconciliation_execution_authority",
        "provider_call_authority",
        "raw_error_requested",
        "stack_trace_requested",
        "raw_provider_payload_requested",
        "actual_message_text_requested",
        "retention_policy_defined",
    ),
    "WebStatusDisplayItem": (
        "web_status_display_item_id",
        "account_id",
        "beacon_id",
        "family",
        "safe_status_title_reference_id",
        "safe_status_message_reference_id",
        "safe_action_reference_ids",
        "source_evidence_reference_ids",
        "reason_code",
        "safe_display_references_only",
        "redacted",
        "localization_value_embedded",
        "raw_error_present",
        "stack_trace_present",
        "raw_provider_payload_present",
        "secret_value_present",
        "personal_contact_data_present",
        "business_success_authority",
        "delivery_success_authority",
        "provider_call_authority",
        "mutation_authority",
    ),
    "WebStatusDisplayResult": (
        "web_status_display_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "status_mapping_policy_reference_id",
        "source_evidence",
        "display_items",
        "external_unavailable_visible",
        "recovery_visible",
        "lost_anchors_state_restored_visible",
        "access_or_channel_problem_visible",
        "delivery_problem_visible",
        "reconciliation_visible",
        "stale_warning_visible",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "safe_projection_only",
        "web_presentation_authority_only",
        "source_modules_authoritative",
        "web_business_outcome_authority",
        "false_no_new_prevented",
        "false_confirmed_new_prevented",
        "notification_failure_does_not_rollback_scan",
        "unknown_delivery_is_reconciliation_first",
        "safe_display_references_only",
        "actual_ui_copy_embedded",
        "direct_foreign_state_write_authority",
        "delivery_execution_authority",
        "retry_execution_authority",
        "reconciliation_execution_authority",
        "provider_call_authority",
        "raw_error_present",
        "stack_trace_present",
        "raw_provider_payload_present",
        "secret_value_present",
        "personal_contact_data_present",
        "retention_policy_defined",
        "minimal_personal_data",
        "redacted",
        "business_success_authority",
    ),
    "WebStatusEvidenceReference": (
        "web_status_evidence_reference_id",
        "account_id",
        "beacon_id",
        "source_family",
        "source_module_id",
        "evidence_class",
        "source_status_reference_id",
        "source_decision_reference_id",
        "source_outcome_reference_id",
        "source_reason_codes",
        "freshness",
        "safe_evidence_reference_ids",
        "safe_latest_fresh_listing_reference_ids",
        "no_new_claim_allowed",
        "state_restored_latest_fresh_only",
        "continuing_scan_visible",
        "reconciliation_reference_id",
        "ambiguity_reference_id",
        "safe_reference_only",
        "source_module_authoritative",
        "web_status_authority",
        "web_scan_authority",
        "web_notification_authority",
        "web_entitlement_authority",
        "web_channel_authority",
        "confirmed_new_claim_allowed",
        "delivery_success_claim_allowed",
        "user_receipt_claim_allowed",
        "provider_call_authority",
        "mutation_authority",
        "raw_error_present",
        "stack_trace_present",
        "raw_provider_payload_present",
        "secret_value_present",
        "personal_contact_data_present",
        "retention_authority",
    ),
    "RequestWebChannelSurfaceQuery": (
        "web_channel_surface_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "requested_audience",
        "requested_channels",
        "channel_read_policy_reference_id",
        "identity_link_policy_reference_id",
        "notification_preference_policy_reference_id",
        "freshness_policy_reference_id",
        "reason_code",
        "verified_actor_required",
        "account_scope_required",
        "read_only",
        "identity_authority_required",
        "adapter_authority_required",
        "notification_authority_required",
        "client_identity_authority",
        "client_link_authority",
        "client_preference_authority",
        "browser_state_authority",
        "provider_identifier_requested",
        "raw_link_requested",
        "raw_mini_app_data_requested",
        "telegram_runtime_capability_requested",
        "runtime_execution_requested",
        "direct_foreign_state_write_authority",
        "provider_call_authority",
        "retention_policy_defined",
    ),
    "SubmitWebChannelCommandCommand": (
        "web_channel_command_id",
        "metadata",
        "idempotency_key",
        "idempotency_scope",
        "fingerprint",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "channel",
        "command_kind",
        "requested_owning_module_id",
        "current_channel_projection_reference_id",
        "expected_source_version_reference_id",
        "adapter_action_reference_id",
        "adapter_runtime_gate_safe_reference_id",
        "identity_link_contract_reference_id",
        "identity_decision_reference_id",
        "notification_preference_contract_reference_id",
        "notification_channel_gate_decision_reference_id",
        "reason_code",
        "verified_actor_account_server_validation",
        "web_draft_client_identity_authority",
        "web_draft_client_link_authority",
        "web_draft_client_preference_authority",
        "direct_identity_adapter_notification_write_authority",
        "runtime_gate_reference_only",
        "runtime_capability_requested",
        "runtime_execution_requested",
        "provider_authority",
        "raw_provider_data_present",
        "raw_link_data_present",
        "raw_mini_app_data_present",
        "account_merge_authority",
        "phone_requirement_defined",
        "business_success_authority",
    ),
    "WebChannelCommandSubmitOutcome": (
        "web_channel_command_submit_outcome_id",
        "metadata",
        "command",
        "state",
        "owning_module_id",
        "owning_command_reference_id",
        "replayed_outcome_reference_id",
        "safe_owning_outcome_reference_id",
        "reconciliation_reference_id",
        "ambiguity_reference_id",
        "safe_status_reference_id",
        "reason_code",
        "safe_outcome",
        "owning_module_authority",
        "web_submission_only_authority",
        "runtime_gate_reference_only",
        "runtime_gate_satisfied",
        "runtime_execution_completed",
        "link_established",
        "preference_applied",
        "target_verified",
        "provider_operation_completed",
        "user_receipt_confirmed",
        "business_success_authority",
        "direct_write_authority",
        "provider_authority",
        "raw_provider_payload_present",
        "secret_authority",
    ),
    "WebChannelSurfaceProjection": (
        "web_channel_surface_projection_id",
        "account_id",
        "channel",
        "state",
        "preference_state",
        "freshness",
        "owning_adapter_module_id",
        "adapter_projection_reference_id",
        "adapter_eligibility_reference_id",
        "adapter_runtime_gate_safe_reference_id",
        "provider_identity_safe_reference_id",
        "adapter_account_link_reference_id",
        "identity_decision_reference_id",
        "identity_account_reference_id",
        "identity_link_challenge_reference_id",
        "notification_channel_gate_decision_reference_id",
        "notification_target_safe_reference_id",
        "notification_push_eligible",
        "safe_start_connection_action_reference_id",
        "safe_enable_notifications_action_reference_id",
        "safe_disable_notifications_action_reference_id",
        "safe_cross_interface_return_reference_id",
        "safe_mini_app_surface_reference_id",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "safe_projection_only",
        "same_internal_account_required",
        "identity_authoritative",
        "adapter_provider_mapping_authoritative",
        "notification_preference_authoritative",
        "telegram_runtime_gate_reference_only",
        "web_identity_authority",
        "web_link_authority",
        "web_preference_authority",
        "web_target_authority",
        "web_runtime_authority",
        "provider_identifier_present",
        "raw_link_present",
        "raw_mini_app_data_present",
        "runtime_capability_present",
        "runtime_execution_authority",
        "weak_correlation_link_allowed",
        "automatic_account_merge_allowed",
        "phone_requirement_defined",
        "provider_call_authority",
        "direct_mutation_authority",
        "business_success_authority",
        "minimal_personal_data",
        "redacted",
    ),
    "WebChannelSurfaceResult": (
        "web_channel_surface_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "channel_read_policy_reference_id",
        "channel_projections",
        "linked_channel_count",
        "push_eligible_channel_count",
        "disabled_channel_count",
        "future_gated_channel_count",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "safe_presentation_boundary",
        "single_account_boundary",
        "identity_authoritative",
        "adapters_authoritative",
        "notification_authoritative",
        "eligible_channel_set_from_notification",
        "telegram_runtime_gate_reference_only",
        "web_foreign_authority",
        "runtime_authority",
        "provider_call_authority",
        "direct_write_authority",
        "business_success_authority",
        "raw_provider_data_present",
        "raw_link_data_present",
        "raw_mini_app_data_present",
        "automatic_account_merge_allowed",
        "minimal_personal_data",
        "redacted",
    ),
    "RequestWebAdminAnalyticsQuery": (
        "web_admin_analytics_query_id",
        "metadata",
        "actor_context_reference_id",
        "identity_authorization_decision_reference_id",
        "identity_role_scope_reference_id",
        "admin_analytics_capability_reference_id",
        "tenant_scope_reference_id",
        "requested_audience",
        "metric_requests",
        "filters",
        "sort_field",
        "sort_direction",
        "sort_policy_reference_id",
        "admin_support_read_policy_reference_id",
        "analytics_aggregation_policy_reference_id",
        "privacy_aggregation_policy_reference_id",
        "privacy_suppression_policy_reference_id",
        "freshness_policy_reference_id",
        "reason_code",
        "verified_admin_required",
        "server_assigned_role_required",
        "admin_support_policy_required",
        "read_only",
        "aggregate_only",
        "user_level_rows_requested",
        "user_level_export_requested",
        "tracker_runtime_requested",
        "event_collection_runtime_requested",
        "marketing_pixel_requested",
        "external_analytics_provider_requested",
        "consent_implementation_requested",
        "retention_policy_defined",
        "browser_admin_flag_authority",
        "provider_identity_admin_authority",
        "impersonation_requested",
        "direct_foreign_state_write_authority",
        "exact_period_definition_invented",
        "exact_active_user_definition_invented",
    ),
    "WebAdminAnalyticsFilterReference": (
        "web_admin_analytics_filter_reference_id",
        "filter_kind",
        "filter_authority_module_id",
        "filter_definition_reference_id",
        "selected_value_reference_ids",
        "policy_approval_reference_id",
        "safe_filter_display_reference_id",
        "exact_filter_definition_reference_only",
        "web_selected_value_authority",
        "raw_filter_value_present",
        "tracking_runtime_authority",
    ),
    "WebAdminAnalyticsMetricProjection": (
        "web_admin_analytics_metric_projection_id",
        "metric_kind",
        "state",
        "freshness",
        "source_authority_module_id",
        "metric_definition_reference_id",
        "aggregation_policy_reference_id",
        "count_value",
        "tariff_definition_reference_id",
        "safe_tariff_display_reference_id",
        "source_aggregate_reference_id",
        "source_reference_ids",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "privacy_suppression_decision_reference_id",
        "ambiguity_reference_id",
        "reason_code",
        "aggregate_only",
        "safe_reference_only",
        "source_authoritative",
        "web_count_authority",
        "web_recomputed_from_user_rows",
        "user_level_row_present",
        "account_identifier_present",
        "session_identifier_present",
        "ip_address_present",
        "cookie_present",
        "device_fingerprint_present",
        "raw_event_payload_present",
        "marketing_identifier_present",
        "external_analytics_payload_present",
        "minimal_personal_data",
        "redacted",
        "tracker_runtime_authority",
        "retention_policy_defined",
    ),
    "WebAdminAnalyticsMetricRequest": (
        "metric_kind",
        "source_authority_module_id",
        "metric_definition_reference_id",
        "aggregation_policy_reference_id",
        "approved_tariff_catalog_reference_id",
        "exact_definition_reference_only",
        "web_metric_definition_authority",
        "raw_event_definition_present",
        "tracking_runtime_authority",
        "retention_policy_defined",
    ),
    "WebAdminAnalyticsResult": (
        "web_admin_analytics_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "admin_policy_owner_module_id",
        "safe_table_projection_reference_id",
        "safe_sort_application_reference_id",
        "sort_field",
        "sort_direction",
        "sort_policy_reference_id",
        "applied_filter_reference_ids",
        "metric_projections",
        "projection_count",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "admin_only",
        "identity_authorization_authoritative",
        "admin_support_policy_authoritative",
        "web_presentation_boundary",
        "aggregate_only",
        "privacy_suppression_policy_required",
        "user_level_rows_present",
        "user_level_export_present",
        "tracker_implementation_present",
        "event_collection_runtime_present",
        "external_analytics_provider_present",
        "marketing_pixel_present",
        "consent_implementation_present",
        "retention_policy_defined",
        "direct_foreign_state_write_authority",
        "cross_metric_sum_authority",
        "screen_or_route_authority",
        "business_success_authority",
        "minimal_personal_data",
        "redacted",
    ),
    "RequestWebSupportHandoffQuery": (
        "web_support_handoff_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "identity_authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "requested_audience",
        "requested_item_kinds",
        "support_case_reference_id",
        "web_support_handoff_policy_reference_id",
        "admin_support_customer_read_policy_reference_id",
        "customer_visibility_policy_reference_id",
        "customer_publication_policy_reference_id",
        "redaction_policy_reference_id",
        "freshness_policy_reference_id",
        "reason_code",
        "verified_customer_required",
        "read_only",
        "customer_publication_required",
        "support_case_mutation_requested",
        "operator_action_requested",
        "internal_note_requested",
        "private_audit_requested",
        "raw_log_requested",
        "provider_call_requested",
        "raw_resource_access_requested",
        "exact_customer_visibility_policy_invented",
        "business_success_authority",
    ),
    "WebSupportHandoffProjection": (
        "web_support_handoff_projection_id",
        "item_kind",
        "state",
        "freshness",
        "owning_module_id",
        "account_id",
        "tenant_scope_reference_id",
        "support_case_reference_id",
        "customer_visibility_policy_reference_id",
        "customer_publication_policy_reference_id",
        "customer_publication_decision_reference_id",
        "support_entry_reference_id",
        "customer_status_reference_id",
        "customer_public_answer_reference_id",
        "source_reference_ids",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "redaction_policy_reference_id",
        "ambiguity_reference_id",
        "reason_code",
        "customer_visible",
        "separate_customer_publication",
        "admin_support_authoritative",
        "web_presentation_boundary",
        "safe_reference_only",
        "redacted",
        "minimal_personal_data",
        "admin_support_safe_explanation_record_exposed",
        "admin_support_internal_case_record_exposed",
        "internal_note_present",
        "private_audit_present",
        "operator_only_field_present",
        "raw_log_present",
        "secret_material_present",
        "raw_provider_payload_present",
        "full_private_message_present",
        "mutation_authority",
        "business_state_authority",
    ),
    "WebSupportHandoffResult": (
        "web_support_handoff_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "source_owner_module_id",
        "projections",
        "projection_count",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "customer_only",
        "admin_support_publication_authoritative",
        "web_presentation_boundary",
        "read_only",
        "safe_reference_only",
        "redacted",
        "minimal_personal_data",
        "internal_note_present",
        "private_audit_present",
        "operator_action_present",
        "raw_log_present",
        "secret_material_present",
        "raw_provider_payload_present",
        "full_private_message_present",
        "support_case_mutation_authority",
        "operator_action_authority",
        "route_or_ui_authority",
        "business_success_authority",
    ),
    "RequestWebSecurityPrivacyAssessmentQuery": (
        "web_security_privacy_query_id",
        "metadata",
        "account_id",
        "actor_context_reference_id",
        "authorization_decision_reference_id",
        "tenant_scope_reference_id",
        "audience",
        "requested_surface_kinds",
        "open_decision_reference_ids",
        "web_security_policy_reference_id",
        "browser_minimization_policy_reference_id",
        "redaction_policy_reference_id",
        "safe_error_policy_reference_id",
        "analytics_policy_gate_reference_id",
        "retention_policy_gate_reference_id",
        "deletion_export_policy_gate_reference_id",
        "reason_code",
        "verified_actor_required",
        "read_only",
        "untrusted_input",
        "external_string_shell_authority",
        "analytics_collection_requested",
        "consent_assumed",
        "retention_period_selected",
        "deletion_export_policy_selected",
        "raw_secret_requested",
        "raw_provider_payload_requested",
        "raw_personal_data_requested",
        "runtime_authority",
        "persistence_authority",
        "business_success_authority",
    ),
    "WebPrivacyControlProjection": (
        "web_privacy_control_projection_id",
        "surface_kind",
        "state",
        "freshness",
        "account_id",
        "tenant_scope_reference_id",
        "web_security_policy_reference_id",
        "browser_minimization_policy_reference_id",
        "redaction_policy_reference_id",
        "safe_error_policy_reference_id",
        "policy_gate_reference_id",
        "policy_decision_reference_id",
        "safe_display_reference_id",
        "redaction_evidence_reference_id",
        "source_reference_ids",
        "provenance_reference_ids",
        "evidence_reference_ids",
        "open_decision_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "browser_visible",
        "safe_reference_only",
        "minimal_personal_data",
        "redaction_enforced",
        "safe_error_semantics",
        "foreign_object_existence_disclosed",
        "stack_trace_present",
        "internal_exception_present",
        "secret_material_present",
        "password_present",
        "one_time_code_present",
        "token_present",
        "cookie_present",
        "session_material_present",
        "private_key_present",
        "environment_secret_present",
        "raw_provider_payload_present",
        "raw_avito_payload_present",
        "full_private_message_present",
        "internal_support_note_present",
        "private_audit_present",
        "unnecessary_personal_data_present",
        "shell_command_constructed",
        "analytics_event_recorded",
        "consent_assumed",
        "retention_period_selected",
        "deletion_export_policy_selected",
        "runtime_authority",
        "persistence_authority",
        "business_success_authority",
    ),
    "WebSecurityPrivacyAssessmentResult": (
        "web_security_privacy_result_id",
        "metadata",
        "query",
        "state",
        "freshness",
        "owning_module_id",
        "projections",
        "projection_count",
        "source_reference_ids",
        "evidence_reference_ids",
        "ambiguity_reference_id",
        "reason_code",
        "browser_minimized",
        "redaction_enforced",
        "safe_error_enforced",
        "untrusted_input_preserved",
        "secret_material_present",
        "raw_provider_payload_present",
        "raw_personal_data_present",
        "internal_support_data_present",
        "stack_trace_present",
        "foreign_object_existence_disclosed",
        "shell_command_constructed",
        "analytics_event_recorded",
        "consent_selected",
        "retention_period_selected",
        "deletion_export_policy_selected",
        "runtime_authority",
        "persistence_authority",
        "route_or_ui_authority",
        "business_success_authority",
    ),
}


def test_literal_module_exports() -> None:
    for module, expected in MODULE_EXPORTS.items():
        assert module.__all__ == expected
        assert len(module.__all__) == len(set(module.__all__))
        assert all(not name.startswith("_") for name in module.__all__)


def test_literal_package_exports_and_identity() -> None:
    assert package.__all__ == PACKAGE_EXPORTS
    assert len(package.__all__) == 75
    assert len(set(package.__all__)) == 75
    assert all(not name.startswith("_") for name in package.__all__)
    assert package.MODULE_ID == "12-web-cabinet"
    for module, names in MODULE_EXPORTS.items():
        for name in names:
            assert getattr(package, name) is getattr(module, name)


def test_enum_names_and_serialized_values_are_ordered_literals() -> None:
    modules = tuple(MODULE_EXPORTS)
    for module in modules:
        for name in MODULE_EXPORTS[module]:
            value = getattr(module, name)
            if isinstance(value, type) and issubclass(value, Enum):
                assert tuple(member.name for member in value) == tuple(
                    member.value for member in value
                )
    exported_enums = {
        name
        for module, names in MODULE_EXPORTS.items()
        for name in names
        if isinstance(getattr(module, name), type) and issubclass(getattr(module, name), Enum)
    }
    assert set(ENUM_VALUES) == exported_enums
    for name, values in ENUM_VALUES.items():
        enum = getattr(package, name)
        assert tuple(member.name for member in enum) == values
        assert tuple(member.value for member in enum) == values


def test_public_models_are_frozen_extra_forbid_and_whitespace_stripping() -> None:
    exported_models = {
        name
        for module, names in MODULE_EXPORTS.items()
        for name in names
        if isinstance(getattr(module, name), type) and issubclass(getattr(module, name), BaseModel)
    }
    assert set(MODEL_FIELDS) == exported_models
    for module, names in MODULE_EXPORTS.items():
        for name in names:
            value = getattr(module, name)
            if isinstance(value, type) and issubclass(value, BaseModel):
                assert value.model_config["extra"] == "forbid"
                assert value.model_config["frozen"] is True
                assert value.model_config["str_strip_whitespace"] is True
                assert tuple(value.model_fields) == MODEL_FIELDS[name]


def test_exports_are_exact_and_no_alias_or_private_names() -> None:
    owners = {name for names in MODULE_EXPORTS.values() for name in names}
    assert set(package.__all__) == owners | {"MODULE_ID"}
    assert not any(name.startswith("_") for name in owners)


@pytest.mark.parametrize("module", tuple(MODULE_EXPORTS))
def test_reload_preserves_order_without_environment_side_effect(module: types.ModuleType) -> None:
    import_path = f"mayak.modules.web_cabinet.{module.__name__.rsplit('.', 1)[-1]}"
    expected = list(MODULE_EXPORTS[module])
    result = _run_isolated_reload_check(import_path, expected)
    assert result["reload_count"] == 1, result["errors"]
    assert result["expected_export_count"] == len(expected), result["errors"]
    assert result["pre_export_count"] == len(expected), result["errors"]
    assert result["errors"] == [], result["errors"]
    assert result["module_object_same"], result["errors"]
    assert result["pre_exports_match"], result["errors"]
    assert result["post_exports_match"], result["errors"]
    assert result["export_order_same"], result["errors"]
    assert result["exports_unique"], result["errors"]
    assert result["env_unchanged"], result["errors"]


@pytest.mark.parametrize("module", (package, *MODULE_EXPORTS))
def test_reload_package_and_modules_are_deterministic(module: types.ModuleType) -> None:
    is_package = module is package
    if is_package:
        import_path = "mayak.modules.web_cabinet"
        expected = list(PACKAGE_EXPORTS)
    else:
        import_path = f"mayak.modules.web_cabinet.{module.__name__.rsplit('.', 1)[-1]}"
        expected = list(MODULE_EXPORTS[module])
    result = _run_isolated_reload_check(import_path, expected, package_target=is_package)
    assert result["reload_count"] == 1, result["errors"]
    assert result["expected_export_count"] == len(expected), result["errors"]
    assert result["pre_export_count"] == len(expected), result["errors"]
    assert result["errors"] == [], result["errors"]
    assert result["module_object_same"], result["errors"]
    assert result["pre_exports_match"], result["errors"]
    assert result["post_exports_match"], result["errors"]
    assert result["export_order_same"], result["errors"]
    assert result["exports_unique"], result["errors"]
    assert result["env_unchanged"], result["errors"]
    if is_package:
        assert result["module_id"] == "12-web-cabinet", result["errors"]
        assert result["expected_export_count"] == 75, result["errors"]
        assert result["post_export_count"] == 75, result["errors"]


def test_literal_field_order_controls_reject_obvious_contract_mutations() -> None:
    assert (
        tuple(package.WebReadModelSourceReference.model_fields)
        == MODEL_FIELDS["WebReadModelSourceReference"]
    )
    assert tuple(package.WebBeaconPatchField.model_fields) == MODEL_FIELDS["WebBeaconPatchField"]
    with pytest.raises(ValidationError):
        package.WebBeaconPatchField(
            web_patch_field_id=" ",
            field_name="x",
            requested_value_reference_id="v",
            owning_module_validation_family_reference_id="o",
        )


def test_models_reject_extra_and_mutation() -> None:
    model = package.WebBeaconPatchField
    with pytest.raises(ValidationError):
        model.model_validate(
            {
                "web_patch_field_id": "id",
                "field_name": "x",
                "requested_value_reference_id": "v",
                "owning_module_validation_family_reference_id": "o",
                "extra_field": "x",
            }
        )
