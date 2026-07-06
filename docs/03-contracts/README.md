# Контракты — статус

**Статус:** RESERVED — canonical contract package ещё не утверждён.

Эта директория будет содержать нормативные интерфейсы между модулями: команды, события, DTO, error envelopes, idempotency keys, schemas, test vectors и mocks.

До принятия `Technical Baseline and Contract Package v1.0` запрещено:

- создавать product-code, который предполагает формат межмодульного API;
- выбирать реальные DTO/schema/event payload;
- создавать физические таблицы/миграции как источник общего контракта;
- выдавать candidate playbook за утверждённый контракт.

Будущая структура:

```text
schemas/       machine-readable schemas
events/        versioned event contracts
test-vectors/  exact input/output vectors
mocks/         fake ports/adapters for isolated tests
```

Каждый файл появится только из полного текста ChatGPT в отдельной documentation task.
