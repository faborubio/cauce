# DEPLOY.md — Despliegue

> Fase local (portafolio, ~USD 0). El despliegue en nube y MCP remoto + OAuth son fase
> opcional (SAD §7, §13 fase 5).

## Fase local (actual)

Todo corre en la máquina del desarrollador (SAD §7.1):

```bash
cp .env.example .env
docker compose up -d postgres      # PostgreSQL en Docker
uv sync                            # entorno de la app
# REST + Web (Fase 2/2.5):  uv run uvicorn cauce.interfaces.rest.app:app --port 8077
#                           luego abrir http://127.0.0.1:8077/ (web de orientación familiar)
# MCP  (Fase 3):            uv run python -m cauce.interfaces.mcp.server   (stdio)
```

- **REST, Web y MCP** son adaptadores hermanos sobre los mismos casos de uso, en proceso.
- El **Monte Carlo** (Fase 1) se delega a un worker CPU-bound; un solo nodo soporta el MVP.

### Conectar el MCP a Claude Desktop (Fase 3)

El servidor MCP es **read-only + simulación** y codifica el caso borde C-22 (no recomienda;
redirige a AFP/asesor/SCOMP). Para usarlo desde Claude Desktop, agregar en su
`claude_desktop_config.json` (ajustar la ruta del repo):

```json
{
  "mcpServers": {
    "cauce": {
      "command": "uv",
      "args": ["run", "python", "-m", "cauce.interfaces.mcp.server"],
      "cwd": "/ruta/al/repo/cauce"
    }
  }
}
```

Tras `uv sync` también queda el script `cauce-mcp` (equivalente a `uv run cauce-mcp`).
Herramientas expuestas: `comparar_modalidades`, `simular_escenario` y `proyectar_ciclo_vida`
(ciclo de vida completo, Fase 4) — SAD §5.3.

## Imagen Docker de la app

```bash
docker build -t cauce:dev .
docker run --rm cauce:dev          # imprime versión (placeholder Fase 0)
```

## Pendiente (fase opcional, SAD §13 fase 5)

- [ ] MCP remoto (HTTP + OAuth 2.1).
- [ ] Despliegue en nube / free tier.
