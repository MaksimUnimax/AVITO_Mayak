# Маяк Авито — протокол постановки и контроля задач CLI

**Версия:** 1.1
**Статус:** APPROVED

ChatGPT controls work; CLI is literal executor and never chooses architecture, content or next step.

Allowed modes: `docs_only`, `proof_only`, `design_only`, `fix_after_approved_design`, `combined_proof_design_fix`, `repeat_proof`.

Every task has: ID, mode, goal, proven baseline, ChatGPT decision, allowed/forbidden scope, exact files/text, checks, acceptance criteria, report format and commit/push permission.

Before writes CLI verifies branch, local/remote baseline and clean worktree. Mismatch stops without self-repair. A task report states status, evidence, changed/unchanged scope, checks, commit/push state, blockers and next safe step.

A replay applies the packet idempotency rule and never creates duplicate work. CLI returns `CHANGE_REQUEST_REQUIRED` rather than resolving an architecture, contract, security, ownership or open-decision issue.
