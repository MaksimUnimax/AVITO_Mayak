# Маяк Авито — точка входа в проект

**Версия:** 2.0
**Статус:** `MODULE_14_AUTONOMOUS_RUNTIME_COMPLETION_ACTIVE`
**Дата:** 2026-07-23

## 1. Source-of-truth order

Before every task ChatGPT independently reads current public GitHub `main`, records the exact branch and SHA, checks recent commits and parallel-main changes, then reads:

1. `README.md`;
2. `docs/00-governance/CURRENT_STATE.md`;
3. `docs/00-governance/ROADMAP.md`;
4. `docs/MANIFEST.md`;
5. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`;
6. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/OWNER_DECISIONS_v1.0.md`;
7. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_AUDIT_v1.0.md`;
8. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CURRENT_MAIN_RECONCILIATION_CLOSURE_v1.0.md`;
9. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/THIRTEEN_MODULES_COMPLETION_MATRIX_v1.0.md`;
10. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CROSS_MODULE_RUNTIME_GAP_MATRIX_v1.0.md`;
11. append-only decisions and worklog;
12. `docs/00-governance/OPEN_DECISIONS.md`;
13. affected architecture, contracts, module playbooks, handoffs, quality and operations evidence.

Current GitHub `main` has precedence over stale summaries.

Accepted append-only decisions, the approved Module 14 playbook and accepted module 01–13 ownership boundaries must not be silently rewritten.

## 2. Current phase

The active phase is:

`AUTONOMOUS_RUNTIME_COMPLETION`

The target environment is:

`SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`

The completion boundary is:

`READY_FOR_OPERATOR_ACCEPTANCE`

RF-03-01 is independently accepted through corrective SHA `23e73707b14b220da98beade93ee2d13021ba1b9`; RF-03-02 is published for independent acceptance; RF-03 remains active, RF-03-03 and RF-03 closure remain pending, and RF-04 remains not started. Runtime mutation remains none. `PRODUCTION_READY` is not an allowed Module 14 verdict.

## 3. Current repository facts

The repository contains semantic product source, executable tests, synthetic fixtures, `pyproject.toml` and `uv.lock`.

Modules 01–13 are accepted semantic and ownership prerequisites.

Module 14 is the active cross-cutting implementation and integration module.

The existence of semantic code and tests must not be confused with completed physical persistence, runtime assembly, deployment or production launch.

Historical documentation-cycle reports remain evidence. They do not override current Module 14 governance.

## 4. Task selection

ChatGPT owns the roadmap.

Before issuing a CLI task ChatGPT determines:

- exact current SHA;
- current RF step;
- prerequisites;
- one atomic scope;
- exact allowed and forbidden paths;
- server boundaries when applicable;
- tests and acceptance;
- parallel-main gates;
- rollback or roll-forward behavior;
- exact final marker.

CLI never chooses the next roadmap step and never expands scope.

After each CLI report ChatGPT independently verifies GitHub and applicable server evidence, accepts or rejects the result and automatically continues.

## 5. Runtime and server boundary

The existing project server is the authorized runtime host.

A separate server is neither required nor authorized.

Project-owned paths and resources may be created only by exact later RF tasks.

Foreign containers, networks, volumes, databases, Nginx, listeners, services and data must not be altered or reused.

Global Docker prune, public ingress, firewall, DNS and certificate changes are forbidden.

## 6. Implementation gates

Runtime, dependency, CI, Docker, database, migration, API, worker, scheduler, Web, Admin, provider and deployment mutations are authorized only when:

1. the applicable RF prerequisite is accepted;
2. GitHub `main` is freshly verified;
3. the Module 14 playbook permits the scope;
4. one exact task explicitly allows the paths and actions;
5. parallel-main and security gates pass.

Missing optional provider credentials disable only that provider and do not stop unrelated Module 14 work.
