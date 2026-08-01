from __future__ import annotations

"""Exact production-identity mutations for the reusable structural gate."""
# ruff: noqa: E402,E501,I001

from pathlib import Path
from typing import Any, Callable

from scripts.runtime.rf08_verify_structural_gateway import verify_source


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "scripts/runtime/rf08_docker_authority.py"


def _result(mutator: Callable[[str], str]) -> dict[str, Any]:
    source = mutator(AUTHORITY.read_text(encoding="utf-8"))
    # The verifier scans only this task-owned synthetic source tree.  The
    # production file itself is never written or imported by the fixture.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="rf08-exact-identity-") as name:
        root = Path(name)
        target = root / "scripts/runtime/rf08_docker_authority.py"
        target.parent.mkdir(parents=True)
        target.write_text(source, encoding="utf-8")
        return verify_source(root)


def _execute_section(source: str) -> str:
    start = source.index("    def execute(")
    end = source.index("    def observe(", start)
    return source[start:end]


def _replace_execute(source: str, old: str, new: str) -> str:
    section = _execute_section(source)
    if old not in section:
        raise AssertionError(f"mutation target missing: {old}")
    return source.replace(section, section.replace(old, new, 1), 1)


def _fails(mutator: Callable[[str], str]) -> None:
    payload = _result(mutator)
    assert payload["finding_count"] > 0
    assert payload["unresolved_executable_content_flow_count"] > 0


def test_exact_production_identity_passes() -> None:
    payload = _result(lambda value: value)
    assert payload["finding_count"] == 0
    assert payload["task_verifier_executable_content"] == "PASS"


def test_exact_production_identity_missing_validation_edge_fails() -> None:
    _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", ""))


def test_exact_production_identity_wrong_value_fails() -> None:
    _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", "        self._validate_semantic_scope(object())\n"))


def test_exact_production_identity_no_root_fails() -> None:
    _fails(lambda value: value.replace("    if root not in path.parents:\n", "    if False:\n", 1))


def test_exact_production_identity_no_digest_fails() -> None:
    _fails(lambda value: value.replace("    if capability.digest != _sha_bytes(path.read_bytes()):\n", "    if False:\n", 1))


def test_exact_production_identity_issue_only_fails() -> None:
    _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", ""))


def test_exact_production_identity_one_read_no_revalidation_fails() -> None:
    _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", "        self._validate_binding(cast(ComposeBinding, semantic.binding))\n"))


def test_exact_production_identity_fake_mode_separation_fails() -> None:
    _fails(lambda value: value.replace('            if task_mode:\n                raise PermissionError("BootstrapAction is sealed RF-08-only")\n', "            if task_mode:\n                pass\n", 1))


def test_exact_production_identity_dynamic_service_fails() -> None:
    _fails(lambda value: value.replace("                semantic.service.value,\n", "                semantic.context.service,\n", 1))


def test_exact_production_identity_dynamic_entrypoint_fails() -> None:
    _fails(lambda value: value.replace('                "python",\n', "                semantic.context.entrypoint,\n", 1))


def test_exact_production_identity_dynamic_user_workdir_fails() -> None:
    _fails(lambda value: value.replace('                "10001:10001",\n                "--workdir",\n                "/opt/mayak",\n', '                semantic.context.user,\n                "--workdir",\n                semantic.context.workdir,\n', 1))


def test_exact_production_identity_dynamic_env_argv_fails() -> None:
    _fails(lambda value: value.replace("                *((semantic.correlation_id,) if semantic.probe == ComposeProbeKind.AUTH_REJECTION else ()),  # noqa: E501\n", "                *semantic.context.argv,\n", 1))


def test_exact_production_identity_second_route_fails() -> None:
    _fails(lambda value: value.replace("        if isinstance(semantic, ComposeRunAction):\n", "        if isinstance(semantic, TaskAcceptanceVerifierAction):\n            return (\"docker\", \"run\", semantic.verifier_path.path)\n        if isinstance(semantic, ComposeRunAction):\n", 1))


def test_exact_production_identity_dead_validator_fails() -> None:
    _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", "        pass\n"))


def test_exact_production_identity_validator_after_dispatch_fails() -> None:
    return _fails(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", "        self._execute_with_transport(semantic, stage=stage, env=self._default_env, stdin=stdin, stdout=stdout, stderr=stderr, timeout=effective_timeout)\n        self._validate_semantic_scope(semantic)\n"))


def test_renamed_unsafe_topology_remains_rejected() -> None:
    _fails(lambda value: _replace_execute(value.replace("class GatewayAuthority:", "class RenamedAuthority:", 1).replace("def _build_docker_tokens(", "def _assemble_tokens(", 1).replace("self._build_docker_tokens(semantic)", "self._assemble_tokens(semantic)", 1), "        self._validate_semantic_scope(semantic)\n", ""))
