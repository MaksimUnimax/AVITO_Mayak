# Маяк Авито — метод выбора технологий

**Версия:** 1.0
**Статус:** APPROVED decision method
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Security and Privacy Model v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Reference Regression Policy v1.0, Environment Matrix v1.0, ADR-0001, ADR-0002, ADR-0006, TASK-001 evidence, Avito Reference Evidence v1.0.
**Не является:** product-code, dependency manifest, lockfile, installation task, runtime proof, provisioning permission или разрешением закрывать product open decisions.

---

## 1. Назначение

Этот документ задаёт обязательный способ выбора implementation technologies для проекта.

Он предотвращает четыре класса ошибки:

1. выбор технологии только потому, что она уже установлена на shared host;
2. механическое копирование локального reference-проекта в многопользовательский SaaS;
3. скрытый выбор stack внутри module playbook или product-code;
4. одновременное связывание нескольких независимых решений без evidence и пути пересмотра.

## 2. Классы решений

| Класс | Примеры | Где принимается |
|---|---|---|
| Core baseline | язык, package manager, API framework, validation, persistence, migrations, HTTP client, test runner, static checks | Technical Baseline |
| Module-specific | provider SDK, HTML parser, browser automation, bot framework, payment SDK | соответствующий module playbook после current evidence |
| Operations-specific | container runtime, service manager, ingress, TLS, secrets delivery, monitoring backend, deployment tooling | отдельный operations decision/task |
| Product-interface | frontend framework, Mini App runtime, public-site build system | Web Cabinet/adapter playbook |

Core baseline не выбирает module-specific или operations-specific technology без доказанной необходимости для первого разрешённого implementation scope.

## 3. Иерархия evidence

Для каждого кандидата используются в порядке приоритета:

1. official language/project documentation;
2. official project repository and release/support policy;
3. approved first-party provider documentation, когда технология provider-specific;
4. exact-revision primary implementation reference;
5. approved read-only environment evidence;
6. isolated reproducible proof task после отдельного разрешения.

Blog post, memory, popularity ranking, случайно установленный binary или один успешный локальный запуск не являются достаточным evidence.

## 4. Обязательная карточка кандидата

Каждый кандидат должен иметь:

- название и decision class;
- selected major/minor line или явно deferred version;
- official documentation URL;
- official repository URL, когда применимо;
- evidence date и exact revision/tag, если решение зависит от revision;
- license identity и ограничения распространения;
- support/lifecycle status;
- совместимость с выбранным language/runtime;
- security and privacy implications;
- module-boundary implications;
- data/migration implications;
- testability and fake-dependency boundary;
- operations, recovery and rollback implications;
- known blockers and revisit triggers.

Отсутствие обязательного поля означает `BLOCKED`, а не разрешение заполнить его предположением.

## 5. Hard gates

Кандидат не может быть выбран, если:

- project/source identity не доказана official или primary source;
- support line закончилась либо нет приемлемой update policy;
- license запрещает предполагаемое использование или не установлена для планируемого code reuse;
- технология требует использования foreign/shared-host resource;
- технология нарушает one-owner database/module boundary;
- внешний ответ, exception или retry нельзя представить утверждёнными error contracts;
- технология не позволяет deterministic tests и approved fake dependency;
- secret handling требует хранения raw secret в Git, log, fixture или ordinary report;
- upgrade/rollback path отсутствует;
- выбор молча закрывает OD-001–OD-014;
- выбор создаёт второй source of truth или прямые cross-module writes.

## 6. Сравнение кандидатов

Сравнение проводится без ложной числовой точности. Для каждого критерия ставится `PASS`, `CONDITIONAL` или `FAIL` и даётся буквальное обоснование.

| Критерий | Что проверяется |
|---|---|
| Architecture fit | modular monolith, отдельные API/worker/scheduler процессы, Windows agent boundary |
| Reference fit | стоимость независимой реализации подтверждённой Avito-механики без копирования code |
| Contract fit | typed inputs/outputs, explicit error/result classes, versioning |
| Data fit | PostgreSQL, ownership, transactions, idempotency, migrations |
| Async/network fit | external I/O, timeouts, cancellation, connection pools |
| Testability | unit/contract/integration/architecture tests, fake dependencies |
| Security | validation, secrets, dependency supply chain, redaction |
| Operations | deterministic install, logs/metrics/traces, health, graceful shutdown |
| Windows fit | возможность поддержать отдельный egress agent без второго core language |
| Lifecycle | support window, upgrade cadence, rollback implications |
| Complexity | число обязательных services, runtimes and package managers |
| Exit cost | возможность заменить компонент без переписывания domain model |

`FAIL` по hard gate запрещает selection независимо от остальных преимуществ.

## 7. Decision outcomes

Допустимы только:

- `SELECTED` — обязательный core component;
- `SELECTED_WITH_GATE` — выбран, но использование начинается только после named proof/task;
- `DEFERRED` — не нужен для первого разрешённого scope или evidence недостаточно;
- `REJECTED` — рассмотрен и не подходит в текущих границах.

`DEFAULT`, `LIKELY`, `MAYBE` и «использовать при необходимости» без owner/gate запрещены.

## 8. Version policy

1. Baseline выбирает supported major/minor line, а не навсегда фиксированный patch.
2. Первый implementation task обязан создать exact reproducible dependency lock.
3. Runtime patch выбирается как current supported patch на дату lock generation.
4. Unbounded dependencies запрещены.
5. Major upgrade требует отдельного compatibility decision и affected test matrix.
6. Security patch требует lock diff, tests и rollback evidence.
7. Pre-1.0 tool pin-ится exact version в implementation toolchain.
8. Host-installed version не переопределяет repository-declared version.

## 9. Dependency placement

Каждая dependency имеет единственного owner и минимальный installation scope:

- core API dependency не попадает автоматически в Windows agent;
- parser/browser dependency не попадает в identity/billing/notification processes;
- development/test tool не становится runtime dependency;
- provider SDK не становится common contract dependency;
- ORM entity и framework object не становятся public intermodule contract;
- optional integration dependency находится в отдельной dependency group/package.

## 10. Proof перед первым product-code

Technical Baseline разрешает подготовить отдельный proof-only toolchain task, но сам не создаёт code.

Перед первой product-code task должны быть доказаны:

1. exact supported runtime installation in an isolated project-owned environment;
2. deterministic dependency resolution and lock verification;
3. import/startup proof для core framework packages;
4. minimal synthetic unit and contract test execution;
5. static/lint/type/architecture-check invocation;
6. database driver and migration-tool compatibility against an isolated test PostgreSQL;
7. отсутствие provider calls, production credentials и foreign resources;
8. clean teardown и exact evidence report.

Proof skeleton не содержит domain behavior, real schema, provider integration или production configuration.

## 11. Revisit triggers

Решение пересматривается при:

- end-of-support или security-only transition, влияющем на planned lifecycle;
- incompatible dependency release;
- reference regression, которую выбранный adapter stack не может обработать;
- невозможности выполнить approved contract, migration, observability или security requirement;
- необходимости нового stateful service;
- подтверждённой нагрузке, которую baseline process model не выдерживает;
- Windows/runtime incompatibility;
- license or supply-chain incident;
- появлении официального provider contract, меняющего adapter design.

## 12. Change control

Technology change требует:

1. нового evidence snapshot;
2. comparison с текущим решением;
3. compatibility and migration classification;
4. affected modules/contracts/tests/operations inventory;
5. rollback or roll-forward plan;
6. append-only ADR;
7. обновления Technical Baseline и current manifest/state;
8. independent GitHub acceptance.

## 13. Acceptance criteria

Метод принят, когда:

- decision classes и evidence hierarchy определены;
- hard gates запрещают host-driven и reference-copy decisions;
- version, dependency placement and proof rules explicit;
- module/operations/product-specific решения не присвоены core baseline;
- change and revisit procedure определены;
- документ не создаёт code, dependencies, runtime или infrastructure.

## 14. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Первый обязательный evidence-based метод выбора core, module-specific и operations technologies. |
