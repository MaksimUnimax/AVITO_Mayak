---

## WL-0014 — 2026-07-07 — Technical Baseline published; server-sync acceptance pending

**Тип:** technical foundation acceptance / governance route correction

**Источник доказательства:**

- current public GitHub baseline at `3e907314826eaa10b26c038a5ff88e9945ecd86a`;
- Architecture Baseline v1.0 technology-selection boundary;
- Platform & Contracts README prerequisite;
- TASK-001 evidence and correction;
- Avito Reference Evidence v1.0;
- official/current sources recorded in `TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- governance-state reconciliation in the same Run 10 publication change set.

**Опубликовано и независимо подлежит проверке:**

- `docs/02-architecture/TECHNOLOGY_SELECTION_METHOD_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_EVIDENCE_v1.0.md`;
- `docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`;
- `docs/02-architecture/ARCHITECTURE_BASELINE_v1.1.md`;
- `docs/08-operations/ENVIRONMENT_MATRIX_v1.1.md`;
- `docs/07-quality/ACCEPTANCE_MATRIX_v1.1.md`;
- route correction from 23 to 24 runs.

**Принятый core baseline:**

- CPython 3.14 supported line;
- `uv`, `pyproject.toml`, committed `uv.lock`;
- FastAPI, Uvicorn, Pydantic v2, pydantic-settings;
- HTTPX;
- PostgreSQL 18, SQLAlchemy 2, Psycopg 3, Alembic;
- initial PostgreSQL-backed durable work claims and transactional outbox without mandatory external broker;
- pytest, pytest-asyncio, RESpx, Ruff, mypy, import-linter, coverage.py;
- OpenTelemetry Python API/SDK instrumentation boundary.

**Границы принятия:**

- `Duff89/parser_avito` is used as exact-revision behavioral evidence and language/ecosystem compatibility input, not copied as SaaS architecture or source code;
- Flet, SQLite, Excel/VK/local-TOML design and direct parser-to-notification coupling are not adopted;
- provider SDKs, browser/anti-block stack, frontend, external broker/cache, deployment, ingress/TLS, secrets delivery, observability backend, Windows packaging and payment technology remain deferred;
- Run 11 is Telegram and MAX reference policy; module playbooks are Runs 12–24;
- OD-001–OD-014 remain unresolved;
- no product-code, `pyproject.toml`, lockfile, executable test, migration, database, Dockerfile, CI/CD, service, container, port, credential, provider call, deployment or runtime configuration is created.

**Run acceptance:**

GitHub publication is documented, but Run 10 is not fully accepted until the server checkout is synchronized to the exact published SHA and the Codex report is independently verified.

**Следующий безопасный шаг:**

Synchronize `/opt/avito-mayak` to the exact published Run 10 GitHub SHA using server-sync-only Codex rules. After independent sync acceptance, resume the documentation agent at Run 11 — Telegram and MAX reference policies — using the 24-run route.
