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


def _route(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["executable_content_flows"][0]


def test_exact_production_identity_passes() -> None:
    payload = _result(lambda value: value)
    assert payload["finding_count"] == 0
    assert payload["task_verifier_executable_content"] == "PASS"
    route = _route(payload)
    assert route["unresolved_relations"] == []
    assert all(route["witnesses"][name] for name in
               ("source", "root", "digest", "issue_validation", "execute_revalidation",
                "fixed_shape", "mode_separation", "transport"))


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
    payload = _result(lambda value: _replace_execute(value, "        self._validate_semantic_scope(semantic)\n", "        self._validate_binding(cast(ComposeBinding, semantic.binding))\n"))
    assert _route(payload)["witnesses"]["execute_revalidation"]["present"] is False
    assert _route(payload)["witnesses"]["root"]["same_source"] is True
    assert _route(payload)["witnesses"]["digest"]["same_source"] is True
    assert payload["finding_count"] > 0


def test_unrelated_root_and_digest_operations_do_not_complete_witnesses() -> None:
    root_payload = _result(lambda value: value.replace(
        "    if root not in path.parents:\n",
        "    if root not in Path('/tmp/rf08-unrelated-b').parents:\n", 1))
    digest_payload = _result(lambda value: value.replace(
        "    if capability.digest != _sha_bytes(path.read_bytes()):",
        "    if capability.digest != _sha_bytes(Path('/tmp/rf08-unrelated-b').read_bytes()):", 1))
    self_payload = _result(lambda value: value.replace(
        "    if capability.digest != _sha_bytes(path.read_bytes()):",
        "    if capability.digest != capability.digest:", 1))
    assert _route(root_payload)["witnesses"]["root"]["same_source"] is False
    assert _route(digest_payload)["witnesses"]["digest"]["same_source"] is False
    assert _route(self_payload)["witnesses"]["digest"]["same_source"] is False
    assert all(p["finding_count"] > 0 for p in (root_payload, digest_payload, self_payload))


def test_cached_execute_validator_keeps_dominance_but_lacks_fresh_read() -> None:
    payload = _result(lambda value: value.replace(
        "_sha_bytes(path.read_bytes())", "_sha_bytes(cached_bytes)", 1))
    route = _route(payload)
    assert route["validation_dominates"] is True
    assert route["witnesses"]["execute_revalidation"]["ordering_before_transport"] is True
    assert route["witnesses"]["execute_revalidation"]["present"] is False
    assert payload["finding_count"] > 0


def test_safe_mode_local_rename_preserves_relation_proof() -> None:
    payload = _result(lambda value: value.replace("task_mode", "neutral_mode"))
    assert payload["finding_count"] == 0
    assert _route(payload)["witnesses"]["mode_separation"]["rejects_before_dispatch"] is True


def test_neutral_dynamic_execution_fields_fail_closed() -> None:
    mutations = (
        ("semantic.service.value,", "semantic.context.alpha,"),
        ('                "python",', "                semantic.context.beta,"),
        ('"10001:10001",', "semantic.context.gamma,"),
        ('"/opt/mayak",', "semantic.context.delta,"),
        ("*((semantic.correlation_id,) if semantic.probe == ComposeProbeKind.AUTH_REJECTION else ()),", "*semantic.context.epsilon,"),
    )
    for old, new in mutations:
        def mutation(value: str, old: str = old, new: str = new) -> str:
            return value.replace(old, new, 1)

        payload = _result(mutation)
        route = _route(payload)
        assert route["witnesses"]["fixed_shape"]["fixed"] is False
        assert "fixed_shape.fixed" in route["unresolved_relations"]
        assert payload["finding_count"] > 0


def test_safe_and_unsafe_neutral_topologies_are_rename_invariant() -> None:
    source = AUTHORITY.read_text(encoding="utf-8")
    safe = (source.replace("GatewayAuthority", "NeutralAuthority")
            .replace("_build_docker_tokens", "assemble_tokens")
            .replace("_validate_task_verifier", "check_source")
            .replace("_validate_semantic_scope", "check_scope")
            .replace("task_mode", "mode_flag")
            .replace("path = Path(capability.path)", "candidate = Path(capability.path)")
            .replace("path.parents", "candidate.parents")
            .replace("path.read_bytes()", "candidate.read_bytes()"))
    unsafe = safe.replace(
        "if capability.digest != _sha_bytes(candidate.read_bytes()):",
        "if capability.digest != capability.digest:", 1)
    def safe_mutation(_value: str) -> str:
        return safe

    def unsafe_mutation(_value: str) -> str:
        return unsafe

    safe_payload = _result(safe_mutation)
    unsafe_payload = _result(unsafe_mutation)
    assert safe_payload["finding_count"] == 0
    assert _route(safe_payload)["status"] == "PASS"
    assert _route(safe_payload)["witnesses"]["digest"]["same_source"] is True
    assert unsafe_payload["finding_count"] > 0
    assert _route(unsafe_payload)["status"] == "FAIL"
    assert "digest.same_source" in _route(unsafe_payload)["unresolved_relations"]


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
