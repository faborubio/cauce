# CLAUDE.md — Hub de contexto de Cauce

> Punto de entrada para cualquier sesión de trabajo (humana o IA). Mantener
> sincronizado con [`SAD_Cauce_pensiones.md`](./SAD_Cauce_pensiones.md), que es la
> **fuente de verdad** de la arquitectura.

## Qué es Cauce

Motor de simulación del **ciclo de vida previsional** chileno: acumulación (senda de
planeo de fondos generacionales) + des-acumulación (comparar modalidades del SCOMP al
jubilar), unidos por un núcleo estocástico compartido y el contrato
`TrayectoriaDeRiqueza`. Incluye una capa **MCP** read-only para interrogar y simular en
lenguaje natural.

**MVP = des-acumulación.** **Es un simulador educativo, NO asesoría previsional** (ADR-009).

## Arquitectura en una pantalla (SAD §5)

```
interfaces/      REST (FastAPI) + MCP (FastMCP)   ← entrega
application/     casos de uso (orquestan puertos) ← sin NumPy, sin adaptadores
domain/          núcleo PURO stdlib-only          ← qué es / cómo se evalúa
infrastructure/  adaptadores (NumPy, ORM, tablas) ← cómo se genera / tarifica
```

**Frontera dura (ADR-010):** el dominio *define y evalúa*; la infraestructura *genera*
(Monte Carlo NumPy vive en `infrastructure/simulacion`, nunca en `domain/`). Blindado
por `import-linter` (ver `pyproject.toml` → `[tool.importlinter]`).

## Convenciones

- Dominio en **español** (Afiliado, SaldoPrevisional, Modalidad, Mesada...).
- Dinero del dominio en `Decimal` UF; el cómputo masivo es NumPy en infraestructura.
- **Determinismo:** toda simulación se reproduce fijando `(perfil, tabla_mortalidad, semilla)` (ADR-006).
- Toda salida lleva supuestos + métricas de riesgo + **disclaimer de no-asesoría**.

## Toolchain

```bash
uv sync --all-extras            # entorno (incluye dev)
uv run ruff check .             # lint
uv run ruff format .            # formato
uv run mypy                     # tipos (--strict, configurado en pyproject)
uv run lint-imports             # fronteras de capas (import-linter)
uv run pytest                   # tests
docker compose up -d postgres   # base de datos local
```

## Estado por fases (SAD §13)

| Fase | Estado |
|------|--------|
| 0 — Scaffolding | ✅ cerrada (`a772c5d`) |
| 1 — Núcleo de simulación | ✅ cerrada (mortalidad + retornos + simulador) |
| 2 — MVP Des-acumulación | ✅ cerrada (tarificador + comparador RP/RV + REST, 47 tests) |
| 3 — Capa MCP | **siguiente** |
| 4 — Acumulación | pendiente |

## Documentación viva (SAD §12)

- [`SAD_Cauce_pensiones.md`](./SAD_Cauce_pensiones.md) — arquitectura (fuente de verdad).
- [`MEMORY.md`](./MEMORY.md) — bitácora de decisiones y aprendizajes.
- [`docs/AUDIT.md`](./docs/AUDIT.md) — auditoría por fase (*Vista de halcón* + sign-off).
- [`docs/COMPLIANCE.md`](./docs/COMPLIANCE.md) — registro del encuadre de no-asesoría.
- [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) · [`docs/CASES.md`](./docs/CASES.md)
- [`README.md`](./README.md) · [`DEPLOY.md`](./DEPLOY.md)

## Pendientes externos (no bloquean arquitectura)

- ✅ **Tablas reguladas 2020 obtenidas y extraídas** a [`data/mortalidad/`](./data/mortalidad/) (RV/CB/B/MI con `q_x` + matriz `AA_{x,t}` 2021–2036). Validadas. Fuente: planilla SP.
- Revisión legal del encuadre de no-asesoría antes de publicar.
