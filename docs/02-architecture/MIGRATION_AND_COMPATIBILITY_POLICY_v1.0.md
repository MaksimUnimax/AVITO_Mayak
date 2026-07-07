# Маяк Авито — Migration and Compatibility Policy

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Data Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Contract Change Policy v1.0, Security and Privacy Model v1.0, OPEN_DECISIONS.md.
**Не является:** migration implementation, SQL/DDL, ORM migration, release procedure, backup runbook, deployment topology, database provisioning или разрешением изменять runtime.

---

## 1. Назначение

Эта policy задаёт обязательный процесс для будущих изменений данных, contracts и совместимости. Её цель — не допустить скрытого breaking change, необратимой потери данных, обхода module ownership или ложного успеха после неполной migration.

Policy действует до выбора конкретного technology stack и поэтому описывает semantic gates, evidence и состояния, а не команды, инструменты или physical schema operations.

## 2. Область действия

Policy применяется к будущим:

- изменениям conceptual data model;
- изменениям physical schema после отдельного approval;
- backfill, data correction and data repair;
- изменению identifier semantics;
- изменению module ownership;
- contract version transition;
- event/read-model compatibility;
- provider mapping transition;
- retention, deletion, anonymization or archival change;
- migration of secret references without disclosure;
- rebuild of derived projections;
- import/export or account merge после отдельного решения;
- transfer of authoritative state between modules.

Policy не создаёт ни одной migration и не определяет, что migration уже нужна.

## 3. Термины

| Термин | Значение |
|---|---|
| Data change | Любое изменение semantic meaning, required relation, ownership, validation или lifecycle данных |
| Physical migration | Будущее controlled изменение storage structures or persisted records |
| Backfill | Заполнение нового authoritative/derived значения из доказанного источника |
| Repair | Исправление подтверждённо неверного persisted state с evidence trail |
| Compatibility window | Явно ограниченный период поддержки старого и нового contract/data form |
| Expand | Additive подготовка, не делающая старый путь немедленно недействительным |
| Migrate | Контролируемое преобразование/копирование/пересчёт с validation |
| Contract | Удаление legacy form только после доказанной готовности и rollback decision |
| Reconciliation | Проверка фактического результата после ambiguous interruption |
| Rollback | Возврат к доказанно совместимому предыдущему состоянию без скрытой потери |
| Roll-forward | Исправляющее движение вперёд, когда безопасный rollback невозможен |

## 4. Источник истины и приоритет

1. Public GitHub `main` и approved governance documents.
2. Approved append-only decisions.
3. Approved architecture, data, contract, security and operations policies.
4. Approved module playbook and exact task packet.
5. Runtime evidence конкретной migration после её выполнения.

Migration script, ORM state, local database, staging data или CLI report не могут самостоятельно переопределить approved model.

## 5. Классы изменений

### 5.1. Additive compatible

Примеры semantic class:

- новый optional concept/field с определённым default/absence meaning;
- новый read model;
- новый contract version, не меняющий существующий meaning;
- новый index или derived representation после physical approval.

Additive не означает автоматически безопасный. Нужны ownership, privacy, validation, backfill and rollback checks.

### 5.2. Behavioral or semantic

Изменяется meaning существующего state, validation, lifecycle, deduplication, baseline/difference или entitlement rule.

Требует:

- explicit decision/source;
- affected contracts and fixtures;
- compatibility analysis;
- historical-data interpretation;
- user/support impact;
- rollback/roll-forward decision.

### 5.3. Breaking structural

Примеры:

- required value без безопасного source;
- removal/rename, меняющий consumer contract;
- identifier meaning change;
- incompatible uniqueness/isolation rule;
- loss of old representation.

Такое изменение запрещено без approved compatibility window, migration plan, validation and recovery evidence.

### 5.4. Ownership or boundary change

Передача authoritative state другому модулю, изменение account/Beacon scope или разрешение direct foreign mutation.

Требует append-only architecture decision, обновления Module Registry, Data Model, contracts, playbooks and acceptance matrix до implementation.

### 5.5. Security/privacy sensitive

Изменение credential references, personal data, audit, retention, deletion, provider identity, authorization scope или redaction.

Требует Security and Privacy review. Не допускается migration через ordinary logs, plaintext export, task prompt или unprotected temporary files.

### 5.6. External-reference dependent

Изменение Avito, Telegram, MAX или другого provider mapping.

Требует current official/primary evidence с датой, URL, scope, status and limitations. Memory или старый provider payload не являются достаточным evidence.

## 6. Обязательный change package

До implementation любой data/compatibility change должен иметь единый approved package:

1. Change identifier and owner.
2. Current source and target semantic model.
3. Reason and authoritative evidence.
4. Affected modules, contracts, identifiers and data classes.
5. Classification по разделу 5.
6. Preconditions and blocked open decisions.
7. Compatibility strategy.
8. Backfill/repair source and deterministic mapping.
9. Idempotency and restart behavior.
10. Validation and acceptance queries/checks без раскрытия secrets.
11. Rollback or roll-forward boundary.
12. Backup/recovery dependency.
13. Observability and safe progress evidence.
14. Fixtures/test vectors and failure cases.
15. Exact allowed and forbidden paths/actions.
16. Human/ChatGPT acceptance gate.
17. Append-only audit/decision record when required.

Отсутствующий пункт не заполняется предположением. Change остаётся blocked.

## 7. Compatibility strategy

### 7.1. Default sequence

Предпочтительная semantic sequence:

```text
expand
→ verify new representation can coexist
→ migrate/backfill in bounded steps
→ validate and reconcile
→ switch approved readers/writers
→ observe compatibility window
→ contract legacy representation only after acceptance
```

Это не предписывает конкретный database command or deployment mechanism.

### 7.2. Reader compatibility

- Новый reader не должен считать absence старого/нового значения valid default без documented meaning.
- Старый reader должен оставаться безопасным в declared compatibility window либо быть остановлен до incompatible write.
- Read model migration не подтверждает authoritative-state migration.
- Mixed-version behavior должен быть описан до rollout.

### 7.3. Writer compatibility

- Dual-write допускается только как отдельно approved bounded mechanism.
- Неопределённый порядок двух writes создаёт `AMBIGUOUS`, а не success.
- Один authoritative owner сохраняется на каждом этапе.
- Legacy writer отключается только после доказательства, что он больше не создаёт несовместимое state.
- Infinite dual-write без owner, exit criteria and reconciliation запрещён.

### 7.4. Contract compatibility

Contract transition следует `CONTRACT_CHANGE_POLICY_v1.0.md`:

- version is explicit;
- producer and consumer support matrix известна;
- semantic meaning не меняется под тем же version silently;
- breaking transition имеет adoption evidence and retirement gate;
- old contract не удаляется только потому, что migration script завершился.

## 8. Migration lifecycle states

Будущий migration run должен различать минимум:

| State | Meaning |
|---|---|
| PROPOSED | Scope drafted; execution forbidden |
| APPROVED | Change package accepted; execution task ещё отдельно требуется |
| PREPARED | Preconditions, backup/recovery and exact target verified |
| RUNNING | Controlled execution in progress |
| PAUSED | Safe checkpoint reached; no assumption of completion |
| RECONCILIATION_REQUIRED | Effect or progress ambiguous |
| VALIDATING | Mutation stopped; evidence checks running |
| ACCEPTED | Target semantic and operational criteria proven |
| ROLLBACK_REQUIRED | Approved rollback path must run |
| ROLL_FORWARD_REQUIRED | Safe rollback unavailable; approved repair path required |
| FAILED | Defined failure with preserved evidence; not accepted |

Exact persisted enum and transport are not selected.

## 9. Idempotency and restartability

Каждая future migration обязана определить stable migration identifier и unit-of-work identity.

Требования:

- повторный запуск same unit не создаёт второй business effect;
- completed unit распознаётся по authoritative evidence, а не только по process memory;
- same identifier with different plan fingerprint is rejected;
- progress checkpoint не объявляется committed, пока target effect не доказан;
- interrupted unit переходит в reconciliation before retry, если commit point неизвестен;
- retries не обходят authorization, ownership or validation;
- batch result перечисляет succeeded, failed, pending and ambiguous units;
- migration logs не содержат secrets or unnecessary personal data.

Exact idempotency storage and TTL остаются невыбранными.

## 10. Backfill rules

Backfill разрешён только когда:

1. Source value authoritative and provenance known.
2. Mapping deterministic or explicitly human-reviewed.
3. Missing/ambiguous source не заменяется fabricated default.
4. Account and Beacon isolation preserved.
5. Cross-module reads do not become unauthorized writes.
6. Historical source snapshot and mapping version are recorded safely.
7. Re-run produces the same semantic result.
8. Validation can detect partial completion and wrong scope.
9. Retention/privacy policy allows source and target processing.
10. Rollback or correction approach is documented.

Если source не позволяет доказать значение, target остаётся explicit unknown/pending according to approved model; запрещено угадывать.

## 11. Data repair and correction

Repair отличается от ordinary migration тем, что first wrong object/value/action должен быть доказан.

Repair package содержит:

- observed symptom;
- authoritative expected value;
- first wrong persisted object/value/action;
- provenance chain;
- affected scope count;
- minimal correction;
- proof that unrelated state is unchanged;
- replay/idempotency rule;
- before/after validation;
- audit entry and operator authorization.

Mass normalization «для порядка» без proven defect запрещена, особенно для append-only history.

## 12. Validation and acceptance

Migration не принимается по exit code alone.

Обязательные evidence categories:

- target revision/version identity;
- exact scope processed;
- counts with explained differences;
- account/Beacon isolation checks;
- uniqueness/reference integrity according to approved model;
- no unexpected null/unknown fabrication;
- idempotency replay proof;
- ambiguous and failed item inventory;
- contract producer/consumer compatibility;
- privacy/redaction checks;
- read-model rebuild/provenance checks when applicable;
- clean rollback/roll-forward decision;
- no forbidden infrastructure or foreign resource use.

CLI report является evidence, но acceptance выполняет ChatGPT независимым чтением source and required proof.

## 13. Rollback and roll-forward

### 13.1. Rollback requirements

Rollback считается допустимым только если:

- previous representation remains readable and semantically valid;
- no accepted user/provider effect would be duplicated or lost;
- reverse mapping is deterministic;
- restored state passes current authorization/privacy requirements;
- rollback does not rewrite protected append-only history;
- exact rollback boundary and evidence are defined before execution.

### 13.2. Irreversible change

Если reverse mapping невозможен или would lose accepted data, change is irreversible.

До execution нужны:

- explicit irreversible classification;
- owner approval;
- verified backup/recovery boundary;
- dry-run or equivalent non-mutating proof;
- roll-forward repair plan;
- maintenance/user-impact decision;
- stricter acceptance criteria.

### 13.3. Compensation

Compensation не считается rollback автоматически. Она является новым controlled business effect с собственными authorization, idempotency, audit and failure semantics.

## 14. Backup and recovery dependency

До появления approved `BACKUP_AND_RECOVERY_v1.0.md` нельзя утверждать, что physical migration имеет production-ready backup/recovery path.

Future execution task обязан ссылаться на конкретный approved recovery evidence. Shared-host foreign backup, snapshot, database, volume or service запрещено считать project recovery asset.

## 15. Module ownership during migration

- Owning module утверждает semantic mapping своего authoritative state.
- Platform & Contracts может предоставить future approved migration tooling, но не принимает business decision за module owner.
- Adapter может нормализовать external data, но не мигрирует state другого модуля напрямую.
- Admin & Support инициирует только protected action через owning service.
- Web/Telegram/MAX UI не становится migration controller.
- Data ownership не передаётся temporary script.
- Cross-module migration должна иметь explicit order, intermediate authority and reconciliation.

## 16. Account, Beacon and external identity safety

Migration обязана сохранять:

- `account_id` as internal ownership boundary;
- one Beacon owner;
- Beacon-scoped listing and notification history;
- prohibition on automatic account merge by weak correlation;
- source URL provenance and separate override history;
- external provider identity verification;
- no cross-account deduplication based only on external display data.

OD-006–OD-008 остаются открытыми; migration не может реализовать account merge/recovery policy silently.

## 17. Retention, deletion and anonymization

OD-013 блокирует конкретные retention periods and deletion behavior.

До его закрытия запрещено:

- придумывать TTL;
- автоматически удалять audit/listing/notification/personal history;
- считать archive равным deletion;
- обещать full erasure без dependency analysis;
- удалять idempotency evidence, если это может создать duplicate effect;
- хранить raw provider evidence indefinitely by default.

Future retention change проходит эту policy как security/privacy-sensitive migration.

## 18. External provider compatibility

Для Avito, Telegram и MAX transition package должен содержать:

- official/primary source URL and retrieval date;
- affected API/page/payload scope;
- old and new mapping;
- uncertainty/limitations;
- provider rollout/deprecation deadline, если официально подтверждён;
- fixture/reference regression updates;
- fallback or explicit unsupported state;
- evidence that provider error is not converted to empty success.

Time-sensitive DRAFT claims не используются как migration approval без current evidence.

## 19. Read-model rebuild

Derived read model может быть rebuilt без изменения authoritative semantics только если:

- source authoritative records and version are known;
- rebuild is idempotent;
- old projection is not used as hidden source of truth;
- authorization filters are preserved;
- freshness/provenance state is visible;
- partial rebuild is explicit;
- swap/activation boundary is defined;
- validation checks compare semantic results, not only row counts.

## 20. Observability requirements

Future migration exposes safe evidence:

- migration id and plan fingerprint;
- state from section 8;
- started/updated/completed timestamps after time policy approval;
- processed/succeeded/failed/ambiguous counts;
- current bounded unit reference;
- retry/reconciliation count;
- safe reason codes;
- validation status;
- rollback/roll-forward readiness.

Metrics/logs do not expose raw personal data, tokens, credentials, source payloads or foreign-host details.

## 21. Testing requirements

Before execution required tests include:

- empty dataset;
- minimum valid record;
- mixed old/new versions;
- duplicate replay;
- interrupted before commit;
- interrupted after possible commit;
- malformed/ambiguous source;
- cross-account and cross-Beacon isolation;
- unauthorized mutation attempt;
- partial batch;
- rollback/roll-forward branch;
- read-model rebuild;
- provider mapping regression when applicable;
- secret/redaction checks.

Canonical fixture names and acceptance matrix will be defined in Run 5 quality documents. Until then no implementation task may claim these gates are complete.

## 22. Change approval matrix

| Change | Minimum approval dependencies |
|---|---|
| Additive conceptual data | Data Model + owning playbook + contracts/tests |
| Physical schema | Approved physical design + migration package + quality/operations gates |
| Contract breaking change | Contract Change Policy + consumer matrix + compatibility window |
| Ownership transfer | ADR + Module Registry + Data Model + affected playbooks/contracts |
| Personal/secret data change | Security/Privacy + retention/recovery evidence |
| Provider mapping | Current official evidence + reference regression fixtures |
| Account merge/import | OD-008 decision + security/audit/migration package |
| Retention/deletion | OD-013 decision + privacy/backup/recovery acceptance |

## 23. Failure handling

- Validation failure stops acceptance.
- Unknown effect becomes `RECONCILIATION_REQUIRED`.
- Remote/provider failure is not clean empty result.
- Local divergence, wrong target revision, dirty worktree or missing backup gate stops execution before mutation.
- Partial batch is reported per unit.
- Failure does not authorize destructive reset, unreviewed manual editing or use of foreign resources.
- Corrective action targets the first proven wrong object/value/action and remains within approved scope.

## 24. Explicit non-decisions

Эта policy не выбирает:

- migration framework/tool;
- SQL dialect or ORM;
- physical schema version table;
- deployment ordering mechanism;
- lock/maintenance strategy;
- batch size;
- retry delay/backoff;
- transaction isolation;
- backup technology;
- database topology;
- retention/TTL;
- identifier encoding;
- data export format;
- provider-specific migration endpoint.

## 25. Explicit prohibitions

До отдельного approved implementation task запрещено:

- создавать migration files, DDL, SQL or ORM entities;
- подключаться к database;
- выполнять backfill or repair;
- создавать backup/snapshot;
- менять runtime, service, container, port or credential;
- использовать foreign database, volume, queue, Nginx or secret;
- скрывать breaking change под additive wording;
- объявлять migration successful без independent acceptance evidence;
- закрывать OPEN_DECISIONS implementation default.

## 26. Acceptance criteria для future migration task

Task может быть создан только если:

- exact current and target SHA/revision named;
- approved change package complete;
- target environment isolated and identified;
- backup/recovery gate accepted;
- data owner and contract versions identified;
- idempotency/restart/reconciliation defined;
- fixtures and acceptance matrix approved;
- no unresolved decision is silently required;
- dry-run/read-only proof exists where applicable;
- allowed and forbidden commands/paths explicit;
- rollback or roll-forward decision explicit;
- independent ChatGPT review required after report.

## 27. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первая migration/compatibility policy: classification, expand-migrate-contract, idempotency, validation, recovery and acceptance gates без migration implementation. |
