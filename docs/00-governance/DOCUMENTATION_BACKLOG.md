# Маяк Авито — backlog необходимой документации

**Версия:** 1.0  
**Статус:** APPROVED planning register  
**Правило:** этот backlog не разрешает создавать документы по шаблону или догадке. Каждый документ будет написан ChatGPT после нужного proof/design этапа и передан CLI буквальным текстом.

## Следующие обязательные пакеты

### DB-01 — Technical Baseline and Contract Package v1.0

**Цель:** определить без догадок язык/рантайм/сборку, границы модульного монолита, API/command/event conventions, idempotency, error envelope и версионирование контрактов.

**Перед началом:** proof/design по доступным средам разработки и обоснование выбранного стека.

**Результаты:**

- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.0.md`;
- `docs/03-contracts/CONTRACT_PACKAGE_v1.0.md`;
- машиночитаемые schemas/events/test vectors/mocks;
- `docs/03-contracts/ERROR_AND_IDEMPOTENCY_POLICY_v1.0.md`;
- `docs/03-contracts/CONTRACT_CHANGE_POLICY_v1.0.md`.

### DB-02 — Data and compatibility governance

**Цель:** физическая модель БД, ownership, unique constraints, migration/retry/backward compatibility policy.

**Результаты:**

- `docs/02-architecture/DATA_MODEL_v1.0.md`;
- `docs/02-architecture/MIGRATION_AND_COMPATIBILITY_POLICY_v1.0.md`.

### DB-03 — Quality

**Цель:** определить уровни тестов, fixtures, contract tests, integration tests, manual acceptance и доказательства production-ready.

**Результаты:**

- `docs/07-quality/TEST_STRATEGY_v1.0.md`;
- `docs/07-quality/FIXTURE_REGISTRY_v1.0.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.0.md`;
- `docs/07-quality/REFERENCE_REGRESSION_POLICY_v1.0.md`.

### DB-04 — Security and operations

**Цель:** secrets, auth, webhooks, audit, environments, deploy, backup/recovery, observability, Windows Egress Agent operations.

**Результаты:**

- `docs/02-architecture/SECURITY_AND_PRIVACY_MODEL_v1.0.md`;
- `docs/08-operations/ENVIRONMENT_MATRIX_v1.0.md`;
- `docs/08-operations/DEPLOYMENT_AND_RELEASE_RUNBOOK_v1.0.md`;
- `docs/08-operations/BACKUP_AND_RECOVERY_v1.0.md`;
- `docs/08-operations/OBSERVABILITY_AND_ALERTING_v1.0.md`;
- `docs/08-operations/WINDOWS_EGRESS_AGENT_RUNBOOK_v1.0.md`.

### DB-05 — External references

**Цель:** зафиксировать проверяемые актуальные official/vendor источники и evidence по Avito reference.

**Результаты:**

- `docs/09-references/REFERENCE_REGISTRY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/AVITO_REFERENCE_EVIDENCE_v1.0.md`;
- `docs/09-references/TELEGRAM_REFERENCE_POLICY_v1.0.md`;
- `docs/09-references/MAX_REFERENCE_POLICY_v1.0.md`.

### DB-06 — Autonomous module playbooks

**Цель:** проверить existing candidate playbooks против утверждённых contracts/data/security и выпустить самодостаточные принятные файлы для 13 модулей.

**Неподвижное требование:** каждый playbook должен содержать точные входы/выходы, ownership, fakes/mocks, fixtures, test vectors, acceptance criteria, scope, запреты, roadmap, report/handoff и append-only history. Агент не должен читать общее ТЗ, чтобы реализовать свою изолированную задачу.

### DB-07 — Tasks and reports in use

**Цель:** после принятия playbooks начать создавать конкретные `TASK-xxx.md`, accepted/rejected reports и handoff только по шаблонам и exact text ChatGPT.
