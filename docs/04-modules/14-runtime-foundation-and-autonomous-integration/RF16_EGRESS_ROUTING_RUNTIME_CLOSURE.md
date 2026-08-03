# RF16 Egress Routing durable runtime closure

Technical ID: `RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01`

This package adds the PostgreSQL-backed Module-07 service boundary, bounded
transport-neutral agent protocol, deterministic simulator, Parser fail-closed
adapter, and Linux-side package build validation. It does not select or deploy
production networking.

## Authority and physical model

Base SHA: `696ecc9c6759f14c81a512af6f1c0d71a81e552f`.

The accepted four tables remain authoritative: `egress_agents`,
`egress_routes`, `egress_agent_heartbeats`, and `egress_route_leases`.
No migration or schema change is included. Heartbeat is liveness only; READY
is an explicit synthetic/project-owned route and agent state.

The pre-RF16 gate is not deleted or rewritten. `rf16_authority.py` is the
traceable higher-authority boundary for this exact task. Live listeners,
firewall/DNS/TLS, tunnel/VPN/proxy, external traffic and Windows installation
remain unauthorized.

## Protocol and package

Protocol identity is `rf16-egress-v1`; messages are bounded to 16 KiB and use
JSON with explicit UUID assignment/lease identity. The simulator is
`EgressAgentSimulator` and covers liveness, accepted assignment, failures,
restriction, malformed/ambiguous effects, duplicate replay and restart replay.
The build validation entry point is `scripts/runtime/build_rf16_agent.py` and
the future operator command is `uv run python scripts/runtime/build_rf16_agent.py`.
The resulting wheel is an operator artifact only; it does not install a service,
touch the database, or configure a Windows host.

## Verdict

Automatic tests and PostgreSQL 18 hosted evidence are recorded by the publishing
report. External residual: `WINDOWS_LIVE_PROOF_OPERATOR_ONLY_CONTINUE`.

`PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
