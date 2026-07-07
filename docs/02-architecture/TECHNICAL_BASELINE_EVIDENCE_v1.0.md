# Маяк Авито — evidence для Technical Baseline

**Версия:** 1.0
**Статус:** APPROVED evidence snapshot
**Дата:** 2026-07-07
**Retrieved at:** `2026-07-07T09:31:28+02:00`
**Основание:** Technology Selection Method v1.0, TASK-001 accepted evidence, Avito Reference Evidence v1.0.
**Не является:** runtime compatibility report, dependency lock, security audit, benchmark, provider permission, product implementation или installation approval.

---

## 1. Scope и метод

Проверялись:

- current official documentation/repository identities выбранных core technologies;
- release/support line языка и базы;
- exact revision обязательного Avito implementation reference;
- accepted TASK-001 host snapshot только как compatibility context;
- отсутствие необходимости переносить локальные GUI/storage/notification решения референса в SaaS.

Не выполнялись:

- package installation;
- dependency resolution;
- import/startup proof;
- database connection;
- migration;
- provider request;
- parser execution;
- benchmark;
- creation of code, lockfile, environment or infrastructure.

Следовательно, этот документ доказывает обоснованность документного выбора, но не заменяет отдельный isolated toolchain proof.

## 2. Mandatory Avito implementation reference

### AVITO-PRIMARY-PARSER-001

- **Repository:** `https://github.com/Duff89/parser_avito`
- **Revision:** `48441c352e36919abef13c436f41a3a62636da17`
- **Reported version:** `3.2.16`
- **Runtime statement:** Python `3.11+`
- **Reviewed relevant files:** `README.md`, `requirements.txt`, `docs/DOCS.md`, parser/request/model files listed in Avito Reference Evidence v1.0.
- **License evidence:** repository-root `LICENSE` was not present when checked at the named revision.
- **Authority:** primary third-party implementation reference, not Avito.

Confirmed technology signals:

- Python implementation;
- Pydantic models;
- HTTPX for parser requests;
- Requests for notification requests;
- BeautifulSoup, Playwright and `curl_cffi` in dependency set;
- local SQLite history;
- Flet GUI;
- TOML configuration;
- Excel export dependencies.

Interpretation:

- Python/Pydantic/HTTPX are relevant compatibility signals for the Avito adapter and core typed/network stack;
- two HTTP clients are unnecessary for the new system;
- SQLite, Flet, Excel, local TOML, VK and direct parser-to-notification behavior conflict with approved SaaS/module boundaries;
- Playwright, stealth/cookie and alternate transport dependencies remain parser-module candidates, not core dependencies;
- source code must not be copied or incorporated while reuse permission/license is unproven; behavior is reimplemented independently from evidence and contract tests.

## 3. Dated release facts

At retrieval time:

- Python.org listed Python `3.14.6` as the latest stable source release; Python 3.14 was in bugfix maintenance and Python 3.15 remained pre-release;
- PostgreSQL official versioning listed PostgreSQL `18.4` as the current minor of supported major 18 and recommends the current minor for the selected major;
- SQLAlchemy official 2.0 documentation identified `2.0.51` as the current 2.0 release series;
- Pydantic official documentation identified the stable v2 line and displayed `2.13.4`;
- OpenTelemetry Python documented traces and metrics as stable, logs as development, and Python 3.10+ support.

These patch values are evidence snapshots, not permanent repository pins. The first toolchain task must resolve current compatible patches, create the exact lock and record any deviation.

## 4. Core source registry

| ID | Source | Authority | Scope used |
|---|---|---|---|
| `TECH-PY-001` | `https://www.python.org/downloads/`, `https://peps.python.org/pep-0745/` and `https://docs.python.org/3.14/` | Python official | Python 3.14 release/support line and language runtime |
| `TECH-UV-001` | `https://docs.astral.sh/uv/` and `https://github.com/astral-sh/uv` | official project | project/dependency management and lock workflow |
| `TECH-FASTAPI-001` | `https://fastapi.tiangolo.com/`, `https://pypi.org/project/fastapi/` and `https://github.com/fastapi/fastapi` | official project/PyPI | ASGI API framework, OpenAPI integration and Python 3.14 classifier |
| `TECH-PYDANTIC-001` | `https://docs.pydantic.dev/`, `https://pypi.org/project/pydantic/` and `https://github.com/pydantic/pydantic` | official project/PyPI | validation, serialized boundary models and Python 3.14 support |
| `TECH-HTTPX-001` | `https://www.python-httpx.org/`, `https://pypi.org/project/httpx/` and `https://github.com/encode/httpx` | official project/PyPI | sync/async HTTP client boundary; exact Python 3.14 compatibility remains a toolchain-proof gate because current classifiers stop at 3.12 |
| `TECH-PG-001` | `https://www.postgresql.org/support/versioning/` and `https://www.postgresql.org/docs/18/` | PostgreSQL official | PostgreSQL 18 supported major line |
| `TECH-SA-001` | `https://docs.sqlalchemy.org/en/20/`, `https://pypi.org/project/SQLAlchemy/` and `https://github.com/sqlalchemy/sqlalchemy` | official project/PyPI | persistence toolkit/ORM boundary and CPython 3.14 wheels |
| `TECH-PSYCOPG-001` | `https://www.psycopg.org/psycopg3/docs/`, `https://pypi.org/project/psycopg/` and `https://github.com/psycopg/psycopg` | official project/PyPI | PostgreSQL driver, async support and Python 3.14 classifier |
| `TECH-ALEMBIC-001` | `https://alembic.sqlalchemy.org/`, `https://pypi.org/project/alembic/` and `https://github.com/sqlalchemy/alembic` | official project/PyPI | migration tooling |
| `TECH-PYTEST-001` | `https://docs.pytest.org/`, `https://pypi.org/project/pytest/` and `https://github.com/pytest-dev/pytest` | official project/PyPI | test runner, fixtures and Python 3.14 classifier |
| `TECH-PYTEST-ASYNCIO-001` | `https://pytest-asyncio.readthedocs.io/`, `https://pypi.org/project/pytest-asyncio/` and its official repository | official project/PyPI | asyncio test integration and Python 3.14 classifier |
| `TECH-RUFF-001` | `https://docs.astral.sh/ruff/` and `https://github.com/astral-sh/ruff` | official project | formatter/linter/import checks |
| `TECH-MYPY-001` | `https://mypy.readthedocs.io/`, `https://pypi.org/project/mypy/` and `https://github.com/python/mypy` | official project/PyPI | static type checking and CPython 3.14 wheels |
| `TECH-IMPORT-001` | `https://import-linter.readthedocs.io/`, `https://pypi.org/project/import-linter/` and `https://github.com/seddonym/import-linter` | official project/PyPI | executable import-boundary rules and Python 3.14 classifier |
| `TECH-OTEL-001` | `https://opentelemetry.io/docs/languages/python/` and `https://github.com/open-telemetry/opentelemetry-python` | official project | vendor-neutral traces/metrics context |
| `TECH-RESPX-001` | `https://lundberg.github.io/respx/`, `https://pypi.org/project/respx/` and `https://github.com/lundberg/respx` | official project/PyPI | HTTPX request fakes and Python 3.14 classifier |

## 5. Language comparison

| Candidate | Result | Evidence-based assessment |
|---|---|---|
| Python 3.14 | `SELECTED` | Direct family match with mandatory reference; mature parsing/network/data/testing ecosystem; one language can cover API, workers, scheduler and Windows agent; current stable line with longer remaining lifecycle than 3.13. |
| Python 3.13 | `REJECTED_FOR_NEW_BASELINE` | Compatible and conservative, but its bugfix phase ends earlier; no benefit justifies starting a new codebase on the shorter remaining line. |
| TypeScript/Node.js | `REJECTED_AS_CORE` | Host availability is not approval; moving Avito behavior away from the reference language increases independent reimplementation cost and creates a second runtime if Python is still needed for parser compatibility. |
| Go | `REJECTED_AS_CORE` | Strong deployment characteristics, but higher porting cost for the mandatory Python reference and less value for the first modular-monolith scope. It may be reconsidered only for a proven isolated component. |

Selected Python runtime means standard CPython build. Experimental free-threaded/JIT modes are not part of the baseline.

## 6. API framework comparison

| Candidate | Result | Assessment |
|---|---|---|
| FastAPI + Uvicorn | `SELECTED` | Direct Pydantic/OpenAPI integration, ASGI and async network fit, small framework surface, suitable for explicit module routers and typed boundary schemas. |
| Django | `REJECTED_AS_CORE` | Batteries/admin/ORM are useful, but create a larger framework ownership surface and encourage coupling of persistence, framework models and domain concerns not required by the first scope. |
| Litestar | `REJECTED_AS_CORE` | Technically viable, but offers no proven project-specific advantage over FastAPI sufficient to offset ecosystem/reference alignment. |

## 7. Persistence comparison

| Candidate | Result | Assessment |
|---|---|---|
| PostgreSQL 18 + SQLAlchemy 2 + Psycopg 3 + Alembic | `SELECTED_WITH_GATE` | Matches ADR-0001, supports explicit transactions and async application access, keeps ORM/persistence internal, and has a defined migration tool. Use begins only after isolated PostgreSQL/toolchain proof and exact migration task. |
| Django ORM/migrations | `REJECTED` | Would couple the selected persistence layer to the rejected core web framework. |
| Raw SQL only | `REJECTED_AS_DEFAULT` | Allowed for narrowly justified queries, but insufficient as the sole project-wide mapping/migration discipline. |
| SQLite from reference | `REJECTED` | Local single-user history is incompatible with approved multi-account ownership, concurrency and migration boundaries. |

## 8. Work execution comparison

| Candidate | Result | Assessment |
|---|---|---|
| PostgreSQL-backed durable work claims and outbox | `SELECTED_WITH_GATE` | Uses the already approved authoritative database, preserves transactional commit points and avoids adding a stateful broker before load evidence. Exact tables/claims remain module-playbook work. |
| Celery + Redis/RabbitMQ | `DEFERRED` | Adds another stateful service, operational ownership and recovery surface without current load evidence. |
| In-memory tasks/timers | `REJECTED` | Lose durable state across restart and cannot satisfy replay/reconciliation requirements. |
| APScheduler as business source of truth | `REJECTED` | Scheduler library state must not replace authoritative module-owned schedules and durable work records. |

## 9. Test and static-analysis comparison

Selected:

- pytest;
- pytest-asyncio;
- RESpx;
- Ruff;
- mypy;
- import-linter;
- coverage.py.

Rationale:

- one Python-native toolchain;
- fixtures and parameterization align with approved Fixture Registry;
- HTTPX fakes are provider-independent;
- import-linter turns modular-monolith import boundaries into executable checks;
- Ruff does not replace static type checking, therefore mypy remains separate;
- coverage is evidence only and no global percentage is invented here.

## 10. Observability evidence

OpenTelemetry Python API/SDK is selected as the vendor-neutral instrumentation boundary.

Not selected:

- collector topology;
- exporter endpoint;
- metrics/log/tracing backend;
- dashboard;
- paging provider;
- retention and production thresholds.

Application logs remain structured and use standard Python logging compatibility. A higher-level logging facade may be selected only if Platform & Contracts proves a concrete need.

## 11. TASK-001 interpretation

Accepted host evidence observed Python/pip/uv and Node/npm availability, including corrected `uv 0.11.11`.

This proves only that commands existed in PATH at the observed time. It does not:

- select a runtime;
- prove required patch availability;
- prove dependency compatibility;
- authorize package installation;
- authorize use of foreign services or databases;
- replace an isolated environment/toolchain proof.

## 12. Evidence gaps preserved

This snapshot does not select:

- Telegram or MAX SDK/framework;
- Avito browser/stealth/cookie/proxy implementation;
- frontend framework;
- container runtime;
- service manager;
- ingress, TLS or ports;
- secrets delivery product;
- monitoring backend;
- object storage;
- external queue/cache;
- Windows executable/service packaging;
- payment provider or SDK.

## 13. Verdict

**Verdict:** `APPROVED_DOCUMENTATION_EVIDENCE_ONLY`.

Evidence is sufficient to select the core Technical Baseline and identify deferred/rejected components. It is insufficient to install dependencies, create a lockfile, connect PostgreSQL, execute migrations, contact providers or begin product-code without the remaining gates.

## 14. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First core technology evidence snapshot using official project sources, TASK-001 context and exact Avito reference revision. |
