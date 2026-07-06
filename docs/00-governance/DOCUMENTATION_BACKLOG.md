# Маяк Авито — backlog необходимой документации

**Версия:** 1.1
**Статус:** APPROVED planning register
**Правило:** этот backlog не разрешает создавать документы по шаблону или догадке. Каждый документ будет написан ChatGPT после нужного proof/design этапа и передан CLI буквальным текстом.

## DB-00 — Доказательства технической среды

**Статус:** IN PROGRESS через `TASK-001`.

**Цель:** собрать доказанные сведения о сервере, Git baseline, доступных runtime-инструментах, container runtime, локальных database/queue tools, минимально релевантных service states и слушающих TCP endpoints.

**Граница:** задача не выбирает стек, не создаёт сервисы и не читает секреты, конфигурации, `.env`, process arguments или systemd unit contents.

**Результат:** основание для решения ChatGPT о technical baseline.

## DB-01 — Architecture, security and contract foundation v1.0

**Цель:** на основании DB-00 определить без догадок язык/рантайм/сборку, границы модульного монолита, security baseline, API/command/event conventions, idempotency, error envelope и версионирование контрактов.

**Результаты:**

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`;
- машиночитаемые schemas, events, test vectors и mocks только в объёме, подтверждённом принятым контрактом.

## DB-02 — Data and compatibility governance

**Цель:** физическая модель БД, ownership, unique constraints, migration/retry/backward compatibility policy.

**Результаты:**

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

## DB-03 — Quality

**Цель:** определить уровни тестов, fixtures, contract tests, integration tests, manual acceptance и доказательства production-ready.

**Результаты:**

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

## DB-04 — Operations and external references

**Цель:** определить среды, deploy, backup/recovery, observability, Windows Egress Agent operations и проверяемые vendor/reference источники.

**Результаты:**

- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`;
- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`;
- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

## DB-05 — Autonomous module playbooks

**Цель:** проверить existing candidate playbooks против утверждённых contracts/data/security и выпустить самодостаточные принятые файлы для 13 модулей.

**Неподвижное требование:** каждый playbook должен содержать точные входы/выходы, ownership, fakes/mocks, fixtures, test vectors, acceptance criteria, scope, запреты, roadmap, report/handoff и append-only history. Агент не должен читать общее ТЗ, чтобы реализовать свою изолированную задачу.

## DB-06 — Tasks and reports in use

**Цель:** после принятия playbooks начать создавать конкретные `TASK-xxx.md`, accepted/rejected reports и handoff только по шаблонам и exact text ChatGPT.
