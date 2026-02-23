FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml por_server.py ./

RUN uv sync

RUN useradd -m app
USER app

# MCP communicates over stdio; no ports exposed.
ENTRYPOINT ["uv", "run", "por_server.py"]
