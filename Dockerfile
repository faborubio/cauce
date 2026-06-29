# Cauce — imagen de la app (Fase 0: base reproducible con uv).
FROM python:3.12-slim AS base

# uv: gestor de dependencias y entorno (rápido, lockfile reproducible).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Capa de dependencias (cacheable): solo manifiestos primero.
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev 2>/dev/null || uv sync --no-install-project --no-dev

# Código de la app.
COPY src ./src
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

# Placeholder de arranque (la REST se implementa en Fase 2).
CMD ["python", "-c", "import cauce; print(f'Cauce {cauce.__version__} — esqueleto Fase 0')"]
