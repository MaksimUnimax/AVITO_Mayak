# Маяк Авито — протокол постановки и контроля задач CLI

**Версия:** 1.0  
**Статус:** APPROVED

## 1. Принцип

ChatGPT управляет разработкой. Codex/CLI исполняет строго ограниченную задачу. После каждого отчёта управление возвращается к ChatGPT; CLI никогда не выбирает следующий шаг самостоятельно.

## 2. Допустимые режимы задач

- `docs_only` — создание/изменение только документов из полного текста ChatGPT.
- `proof_only` — только доказательство состояния, без правок.
- `design_only` — только проектирование/сравнение вариантов, без правок.
- `fix_after_approved_design` — локальное изменение после отдельного принятого решения.
- `combined_proof_design_fix` — только для узкой низкорисковой задачи с заранее доказанным baseline, ясным scope и тестами.
- `repeat_proof` — повторная проверка после изменения.

## 3. Обязательные части каждого задания

```text
TASK_ID:
RUN_MODE:
GOAL:
PROVEN BASELINE:
SYMPTOM AND HIGHER LEVEL:
CHATGPT DECISION:
ALLOWED SCOPE:
FORBIDDEN SCOPE:
EXACT DOCUMENTS / FILES TO READ:
EXACT CHANGES:
REQUIRED CHECKS:
ACCEPTANCE CRITERIA:
REPORT FORMAT:
COMMIT/PUSH PERMISSION:
```

В document-задаче `EXACT CHANGES` содержит полный текст каждого документа или exact append-block.

## 4. Обязательный handoff

Незавершённая задача должна вернуть:

- текущий статус;
- что доказано;
- что изменено и что не изменено;
- команды/тесты и результаты;
- branch/commit/push status;
- блокеры;
- точный следующий безопасный шаг.

## 5. Change request

Если CLI видит необходимость изменить контракт, архитектуру, модульную границу, security policy, data ownership или открытое решение, он не внедряет это. Он возвращает `CHANGE_REQUEST_REQUIRED` с доказательствами. ChatGPT принимает решение и пишет точный документный/кодовый task.
