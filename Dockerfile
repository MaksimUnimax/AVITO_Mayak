# syntax=docker/dockerfile:1.10
FROM --platform=linux/amd64 python:3.14.6-slim-bookworm@sha256:86f975aca15cf04a40b399eebede9aea7c82eae084d1f1a0a6ef6bcaae871a30
ARG SOURCE_SHA
ARG LOCK_IDENTITY
LABEL org.opencontainers.image.source="https://github.com/MaksimUnimax/AVITO_Mayak" org.opencontainers.image.revision="${SOURCE_SHA}" com.avito-mayak.project-owned="true" com.avito-mayak.lock-identity="${LOCK_IDENTITY}"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PATH="/opt/mayak/.venv/bin:$PATH"
WORKDIR /opt/mayak
RUN test -n "${SOURCE_SHA}" && test "$(printf '%s' "${SOURCE_SHA}" | tr -d '0-9a-f')" = "" && test "${#SOURCE_SHA}" = 40 && test -n "${LOCK_IDENTITY}" && test "$(printf '%s' "${LOCK_IDENTITY}" | tr -d '0-9a-f')" = "" && test "${#LOCK_IDENTITY}" = 64 && python -m pip install --no-cache-dir --disable-pip-version-check uv==0.11.31
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
RUN test "$(sha256sum uv.lock | cut -d' ' -f1)" = "${LOCK_IDENTITY}" \
    && test "$(uv --version | awk '{print $2}')" = "0.11.31"
RUN uv sync --frozen --no-dev
RUN find /opt/mayak -type d -name __pycache__ -prune -exec rm -rf {} + \
    && find /opt/mayak -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete \
    && groupadd --system --gid 10001 mayak \
    && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin mayak \
    && chown -R 10001:10001 /opt/mayak
USER 10001:10001
CMD ["sh", "-c", "echo 'mayak: no process role command supplied; refusing to start' >&2; exit 78"]
