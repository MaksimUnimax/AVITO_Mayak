# TASK-001 — errata к историческому критерию commit

**Версия:** 1.0
**Статус:** APPROVED
**Дата:** 2026-07-06
**Относится к:** `TASK-001-TECHNICAL-ENVIRONMENT-PROOF.md`

## Уточнение

Исходный TASK-001 требовал один commit с единственным task-file. Фактический commit `e017241824b3b3e90db1116faefc466791bef2e5` одновременно создал task и обновил необходимые governance state files.

Для TASK-001 допустим этот единственный state-sync commit с task-file и его necessary governance updates. Это не создаёт product-code, infrastructure, database, queue, integrations, deploy files или новый technology decision.

Исходный task text не переписывается. Terminal status определяется accepted report и переносом packet в `docs/05-tasks/completed/`.
