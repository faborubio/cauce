# Cauce

**Motor de simulación del ciclo de vida previsional chileno** — acumulación (senda de
planeo de fondos generacionales) + des-acumulación (comparar modalidades del SCOMP),
unidos por un núcleo estocástico compartido. Con capa **MCP** para interrogar y simular
en lenguaje natural.

> ⚠️ **Simulador educativo. NO es asesoría previsional** ni recomendación personalizada.
> La elección de modalidad es irrevocable y materia de procesos regulados (SCOMP,
> asesores registrados, AFP). Ver [`docs/COMPLIANCE.md`](./docs/COMPLIANCE.md).

## Estado

**MVP de des-acumulación funcionando** (Fases 0–2 cerradas): comparar retiro programado
vs renta vitalicia por HTTP, con mortalidad regulada 2020 validada contra la fuente
(NCG/Compendio SP) y disclaimer de no-asesoría. **Fase 3 (capa MCP)** es lo siguiente.
47 tests; `ruff` + `mypy --strict` + `import-linter` verdes. Hoja de ruta: [SAD](./SAD_Cauce_pensiones.md) §13.

```bash
uv run uvicorn cauce.interfaces.rest.app:app --port 8077
curl -s -X POST http://127.0.0.1:8077/comparar \
  -H 'Content-Type: application/json' \
  -d '{"edad":65,"saldo_uf":"3000","genero":"M","n_trayectorias":5000}'
```

## Requisitos

- Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker + Docker Compose.

## Puesta en marcha

```bash
git clone <repo> && cd cauce
cp .env.example .env
uv sync --all-extras          # entorno + dev
docker compose up -d postgres # base de datos local

uv run pytest                 # tests
uv run mypy                   # tipos (--strict)
uv run ruff check .           # lint
uv run lint-imports           # fronteras de capas (import-linter)
```

## Arquitectura

Clean Architecture en cuatro capas; el dominio es **stdlib-only** y todo lo numérico
(Monte Carlo NumPy) vive en `infrastructure/` detrás de puertos (ADR-010). Detalle
completo en [`SAD_Cauce_pensiones.md`](./SAD_Cauce_pensiones.md) y el hub
[`CLAUDE.md`](./CLAUDE.md).

```
src/cauce/
├── domain/          # puro: entidades, value objects, puertos, evaluación
├── application/     # casos de uso
├── infrastructure/  # adaptadores: simulación, mortalidad, retornos, tarificación, persistencia
└── interfaces/      # REST (FastAPI) + MCP (FastMCP)
```

## Licencia

Proyecto de portafolio. Propietario.
