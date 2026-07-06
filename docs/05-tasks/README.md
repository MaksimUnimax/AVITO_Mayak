# Task packets

**Статус:** ACTIVE structure; task packets ещё не созданы.

Каждая конкретная работа CLI-исполнителя хранится отдельным `TASK-xxx.md` в одном из каталогов:

```text
active/
completed/
blocked/
change-requests/
```

Task packet создаётся только ChatGPT и содержит полный точный scope. CLI не создаёт себе task packet и не переносит task между каталогами самостоятельно.

Шаблон: `TASK_TEMPLATE.md`.
