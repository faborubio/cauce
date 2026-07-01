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
uv run pytest                   # tests (67, verdes)
docker compose up -d postgres   # base de datos local (deuda: persistencia real)
```

### Correr el MVP

```bash
# REST + Web de orientación familiar (Fase 2/2.5) + ciclo de vida (Fase 4)
uv run uvicorn cauce.interfaces.rest.app:app --port 8077
#   → http://127.0.0.1:8077/ (web) · POST /comparar (RP vs RV) · POST /ciclo-vida (25→mesada)

# MCP para Claude Desktop (Fase 3/4, stdio): comparar_modalidades · simular_escenario · proyectar_ciclo_vida
uv run python -m cauce.interfaces.mcp.server   # config en DEPLOY.md
```

## Estado por fases (SAD §13)

| Fase | Estado |
|------|--------|
| 0 — Scaffolding | ✅ cerrada (`a772c5d`) |
| 1 — Núcleo de simulación | ✅ cerrada (mortalidad + retornos + simulador) |
| 2 — MVP Des-acumulación | ✅ cerrada (tarificador + comparador RP/RV + REST) |
| 2.5 — Orientación familiar | ✅ cerrada (web + disclaimer en la fuente + calibración SP/CMF, `053fdf1`) |
| 3 — Capa MCP | ✅ cerrada (FastMCP stdio: comparar_modalidades + simular_escenario) |
| 4 — Acumulación | ✅ cerrada (glide path edad+riqueza + ciclo de vida completo, 67 tests) |
| 5 — Opcional | pendiente (dashboard, CVaR, MCP remoto + OAuth) |

## Retomar aquí — próximo: Fase 5 (opcional) o pulido

**Dónde estamos:** el **ciclo de vida completo** está implementado y demostrable — de los 25 a
la mesada — por **canales hermanos** (REST, Web, MCP) sobre el mismo núcleo. 67 tests verdes;
ruff/mypy/import-linter limpios. El proyecto está **completo y demostrable** (fases 1–4).

**Fase 4 entregada (SAD §5.2/§6.2, ADR-015):**
- `SendaDePlaneo` (dominio puro): glide path por **edad + riqueza** (backbone lineal por edad
  + ajuste por distancia a la riqueza de referencia; `sensibilidad_riqueza=0` = clásica por edad).
- `SimuladorAcumulacion` (infra NumPy, determinista): cotizaciones + retornos guiados por el glide.
- Casos de uso `ProyectarAcumulacion` y `SimularCicloDeVida` (toma p10/p50/p90 del saldo a la
  jubilación → compara modalidades → **rango de pensiones**).
- Expuesto por REST `POST /ciclo-vida` y MCP `proyectar_ciclo_vida`. Disclaimer + C-22 heredados.

**Nota de modelado:** el glide es **paramétrico y determinista**, no un optimizador `cvxpy`
(ese riesgo de §11/ADR-006 no aplica). Continuidad por saldo representativo + percentiles.

**Si sigue Fase 5 (opcional, SAD §13):** dashboard de trayectorias/percentiles, límite de riesgo
vía CVaR, benchmark de fondos generacionales, MCP remoto + OAuth. Ver `docs/AUDIT.md` · `docs/CASES.md`.

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
