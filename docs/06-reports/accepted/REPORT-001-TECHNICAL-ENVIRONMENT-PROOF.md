# REPORT-001 — TASK-001 Technical Environment Proof

**Статус:** ACCEPTED
**Источник:** `mayak-task001-proof-20260706-001`
**Проверил ChatGPT:** 2026-07-06
**Граница:** proof-only evidence; не architecture, stack, deploy или infrastructure approval.

## Принятые факты

TASK-001 подтвердил snapshot shared development host: Ubuntu 24.04.3 x86_64; 4 CPU; 7.7 GiB memory; 79 GiB disk with about 33 GiB free; Git 2.43.0; Python 3.12.3; Node 18.19.1/npm 9.2.0; Docker Engine 29.2.1/Compose v5.0.2; Nginx 1.26.3.

В command path отсутствовали `uv`, `pip3`, PostgreSQL CLI/server, Redis CLI/server, SQLite CLI, Podman, Poetry и Docker Compose v1.

Host shared: foreign Docker/containerd/Nginx resources exist; public 80/443 and local 127.0.0.1:5432 are occupied. Их inventory намеренно не публикуется.

## Ограничения

Evidence не выбирает язык, framework, package manager, database, queue, ingress, TLS, ports, deployment, secrets delivery, Telegram/MAX/Avito implementation или production readiness. Existing approved ADRs остаются отдельно действующими; этот report их не изменяет.

CLI reported `main`, remote `main` and clean worktree at `e017241824b3b3e90db1116faefc466791bef2e5`; no project resource, code, configuration, server or repository change was made.

## Следующий шаг

После независимого acceptance текущего governance package перейти к Run 2: Architecture Foundation documentation only.

---

## CORRECTION-001 — 2026-07-07 — TASK-001 toolchain evidence correction

**Статус:** APPROVED append-only correction
**Область:** исправляет только перечисленные ниже факты toolchain snapshot.
**Источник:** исходный read-only output TASK-001 `mayak-task001-proof-20260706-001`.

Ранее в разделе «Принятые факты» были ошибочно указаны Node.js `18.19.1`, npm `9.2.0` и отсутствие `uv`/`pip3`. Эти значения не подтверждаются исходным evidence.

Подтверждённый TASK-001 snapshot:

- `pip3` доступен;
- Node.js: `v22.22.1`;
- npm: `10.9.4`;
- `uv`: `0.11.11`.

Остальные ограничения REPORT-001 сохраняются: это proof-only snapshot на момент TASK-001, а не утверждение о текущем состоянии хоста, выборе stack, architecture, deploy, infrastructure, ports, secrets, database, queue или production readiness.

Никакая существующая строка REPORT-001 не переписывается. Эта append-only correction является авторитетной для перечисленных выше toolchain facts.
