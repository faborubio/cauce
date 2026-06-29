# Cauce

**Motor de simulación del ciclo de vida previsional chileno** — acumulación (senda de
planeo de fondos generacionales) + des-acumulación (comparar modalidades del SCOMP),
unidos por un núcleo estocástico compartido. Con capa **MCP** para interrogar y simular
en lenguaje natural.

> ⚠️ **Simulador educativo. NO es asesoría previsional** ni recomendación personalizada.
> La elección de modalidad es irrevocable y materia de procesos regulados (SCOMP,
> asesores registrados, AFP). Ver [`docs/COMPLIANCE.md`](./docs/COMPLIANCE.md).

## Estado

**Fase 0 — Scaffolding.** Esqueleto navegable, fronteras de capas blindadas, dominio
puro. El núcleo de simulación (Fase 1) y el comparador de modalidades (Fase 2, MVP)
están pendientes. Ver hoja de ruta en el [SAD](./SAD_Cauce_pensiones.md) §13.

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
