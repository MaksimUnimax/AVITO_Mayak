# Маяк Авито — журнал работы (append-only)

**Статус:** APPROVED append-only log  
**Правило:** существующие записи не редактируются, не удаляются и не переставляются. Корректировка оформляется новой записью в конце журнала с ссылкой на исправляемую запись.

---

## WL-0001 — 2026-07-06 — Project documentation bootstrap started

**Тип:** governance / repository bootstrap  
**Источник доказательства:** отчёт CLI-исполнителя `AVITO_MAYAK_REPOSITORY_ACCESS_AND_BASELINE_INSPECTION`.

**Подтверждено:**

- создан отдельный SSH deploy key для `MaksimUnimax/AVITO_Mayak`;
- права ключевого материала проверены: каталог `.ssh` `700`, private key `600`, public key `644`;
- создан отдельный `known_hosts` для GitHub с strict host-key verification;
- доступ к `git@github.com/MaksimUnimax/AVITO_Mayak.git` проверен;
- репозиторий клонирован в `/opt/avito-mayak`;
- remote `main` на момент проверки был пустым (`HEAD=UNBORN_OR_EMPTY_REPOSITORY`);
- в рабочем дереве не было файлов проекта;
- на этапе проверки не выполнялись commit, push, изменение ветки, tag, rebase, reset, stash или редактирование repository files.

**Решение ChatGPT:**

- начать только Documentation Bootstrap;
- не создавать код продукта, инфраструктуру, схему БД, внешние интеграции или deploy;
- переносить каждый документ в репозиторий только из полного текста, переданного CLI-исполнителю ChatGPT.

**Следующий безопасный шаг:**

Создать и проверить первый documentation-bootstrap commit с точным набором governance/product/architecture документов.
