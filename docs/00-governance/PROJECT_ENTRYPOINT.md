# Маяк Авито — точка входа в проект

**Версия:** 1.1
**Статус:** APPROVED

При входе ChatGPT independently reads public `main`, records branch/SHA and files actually read, then reads README, MANIFEST, CURRENT_STATE, ROADMAP, DOCUMENTATION_BACKLOG, remote-supervision protocol, relevant logs, OPEN_DECISIONS and task-specific evidence.

Before a CLI task ChatGPT states proven baseline, goal, decision, allowed scope, forbidden scope, checks and acceptance. CLI is never a substitute for GitHub reading and never chooses the next step.

Next work follows current state, roadmap, accepted evidence and unresolved decisions; it is not chosen from memory. Missing evidence requires `proof_only`; a needed design requires literal documentation first. Product code remains gated by accepted documentation.
