# DEPLOY.md — Despliegue

> Fase local (portafolio, ~USD 0). El despliegue en nube y MCP remoto + OAuth son fase
> opcional (SAD §7, §13 fase 5).

## Fase local (actual)

Todo corre en la máquina del desarrollador (SAD §7.1):

```bash
cp .env.example .env
docker compose up -d postgres      # PostgreSQL en Docker
uv sync                            # entorno de la app
# REST (Fase 2):  uv run uvicorn cauce.interfaces.rest.app:app --reload
# MCP  (Fase 3):  Claude Desktop como host vía stdio
```

- **MCP y REST** son adaptadores hermanos sobre los mismos casos de uso, en proceso.
- El **Monte Carlo** (Fase 1) se delega a un worker CPU-bound; un solo nodo soporta el MVP.

## Imagen Docker de la app

```bash
docker build -t cauce:dev .
docker run --rm cauce:dev          # imprime versión (placeholder Fase 0)
```

## Pendiente (fase opcional, SAD §13 fase 5)

- [ ] MCP remoto (HTTP + OAuth 2.1).
- [ ] Despliegue en nube / free tier.
