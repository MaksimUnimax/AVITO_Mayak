FROM python:3.14.6-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uv /uvx /usr/local/bin/

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl git tar \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-29.2.1.tgz \
       | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL https://github.com/docker/buildx/releases/download/v0.31.1/buildx-v0.31.1.linux-amd64 \
       -o /usr/local/lib/docker/cli-plugins/docker-buildx \
    && chmod 0755 /usr/local/lib/docker/cli-plugins/docker-buildx \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/opt/rf23-venv \
    UV_CACHE_DIR=/opt/uv-cache \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
ENTRYPOINT ["/bin/bash"]
