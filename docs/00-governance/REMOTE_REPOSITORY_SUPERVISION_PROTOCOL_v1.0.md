# Маяк Авито — протокол независимого контроля удалённого репозитория

**Версия:** 1.0
**Статус:** APPROVED
**Дата:** 2026-07-06

## Назначение

Публичная ветка `main` — фактический источник истины о составе репозитория. Handoff, локальная копия и отчёт CLI могут быть evidence, но не заменяют независимое чтение GitHub ChatGPT.

## Обязанности

- Владелец задаёт цель и ограничения.
- ChatGPT принимает решения, передаёт literal text и независимо принимает результат.
- CLI исполняет только переданный scope и не выбирает архитектуру, следующий шаг или содержание документации.

## До task

ChatGPT фиксирует repository, branch, current SHA, прочитанные документы, active state, open decisions, allowed/forbidden scope, checks и acceptance criteria.

CLI проверяет branch, local HEAD, remote main, clean worktree и exact baseline. Несовпадение не исправляется автоматически.

## После task

ChatGPT независимо проверяет public `main`: commit SHA/subject, changed paths, literal content, append-only integrity, отсутствие forbidden changes и remote state. Отчёт CLI сам по себе не является acceptance.

## Replay

Повторный отчёт не создаёт новую работу. Следующий уже определённый prompt повторяется с тем же technical ID.

## Недопустимо

Нельзя считать handoff заменой `main`, local worktree заменой remote state, candidate/fixture доказательством production или отчёт CLI независимой проверкой.
