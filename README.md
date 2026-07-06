# Маяк Авито

**Статус репозитория:** Documentation Bootstrap. Код продукта ещё не создан.

«Маяк Авито» — сервис мониторинга поисковой выдачи Avito. Клиент создаёт отдельный Маяк из готовой ссылки поиска и получает уведомления о новых объявлениях и новых для этого Маяка парах `listing_id + price`.

## Точка входа

Перед любой работой в репозитории сначала читать:

1. [`docs/00-governance/PROJECT_ENTRYPOINT.md`](docs/00-governance/PROJECT_ENTRYPOINT.md)
2. [`docs/00-governance/CURRENT_STATE.md`](docs/00-governance/CURRENT_STATE.md)
3. [`docs/00-governance/ROADMAP.md`](docs/00-governance/ROADMAP.md)
4. [`docs/MANIFEST.md`](docs/MANIFEST.md)

## Неподвижные правила

- Владелец продукта задаёт цели, ограничения и принимает продуктовые решения.
- ChatGPT является разработчиком, архитектором и руководителем проекта.
- Codex или другой CLI является техническим исполнителем и не принимает архитектурных, продуктовых или межмодульных решений.
- Любая документация создаётся или изменяется только из полного буквального текста, переданного ChatGPT в конкретной задаче CLI-исполнителю.
- Код и документация не создаются по догадке.
- При любой проблеме сначала ищется подтверждённая причина на уровень выше симптома; постоянные костыли, скрывающие следствие, запрещены.

Полные правила: [`docs/00-governance/CHATGPT_PROJECT_LEADERSHIP_RULES_v1.1.md`](docs/00-governance/CHATGPT_PROJECT_LEADERSHIP_RULES_v1.1.md).

## Текущие документы продукта

- Целевая модель: [`docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md`](docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md)
- Архитектурная карта: [`docs/02-architecture/MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md`](docs/02-architecture/MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md)
- Открытые решения: [`docs/00-governance/OPEN_DECISIONS.md`](docs/00-governance/OPEN_DECISIONS.md)

## Запрет до следующего решения

До принятия технического baseline запрещено создавать production-код, выбирать язык/фреймворк/ORM/очередь, проектировать физическую схему БД, внедрять внешние интеграции или делать deploy. Следующий этап — авторство и утверждение контрактного пакета, модели данных, тестовой стратегии и технического baseline.
