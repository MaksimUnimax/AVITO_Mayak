# Reports and handoffs

**Статус:** ACTIVE structure; отчёты по product-code ещё не созданы.

CLI-исполнитель возвращает отчёт в чат. После проверки ChatGPT exact text отчёта/hand-off может быть сохранён в репозитории в одном из каталогов:

```text
accepted/
rejected/
handoffs/
```

Отчёт не становится доказательством только потому, что CLI его написал. ChatGPT проверяет diff, файлы, commit, tests и evidence до размещения в `accepted/`.

Шаблон: `REPORT_TEMPLATE.md`.
