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
uv run pytest                   # tests (53, verdes)
docker compose up -d postgres   # base de datos local (deuda: persistencia real)
```

### Correr el MVP

```bash
# REST + Web de orientación familiar (Fase 2/2.5)
uv run uvicorn cauce.interfaces.rest.app:app --port 8077
#   → http://127.0.0.1:8077/ (web) · POST /comparar (RP vs RV + disclaimer)

# MCP para Claude Desktop (Fase 3, stdio): comparar_modalidades + simular_escenario
uv run python -m cauce.interfaces.mcp.server   # config en DEPLOY.md
```

## Estado por fases (SAD §13)

| Fase | Estado |
|------|--------|
| 0 — Scaffolding | ✅ cerrada (`a772c5d`) |
| 1 — Núcleo de simulación | ✅ cerrada (mortalidad + retornos + simulador) |
| 2 — MVP Des-acumulación | ✅ cerrada (tarificador + comparador RP/RV + REST) |
| 2.5 — Orientación familiar | ✅ cerrada (web + disclaimer en la fuente + calibración SP/CMF, `053fdf1`) |
| 3 — Capa MCP | ✅ cerrada (FastMCP stdio: comparar_modalidades + simular_escenario, 53 tests) |
| 4 — Acumulación | **siguiente** |

## Retomar aquí — próximo: Fase 4 (módulo de acumulación)

**Dónde estamos:** el MVP de des-acumulación está completo y demostrable por **tres canales
hermanos** sobre el mismo `CompararModalidades`: REST, Web de orientación familiar (cero
instalación) y MCP (Claude Desktop). Todo con mortalidad regulada validada, supuestos
calibrados a tasas públicas SP/CMF, y disclaimer + guardrail C-22 en la fuente. 53 tests verdes.

**Fase 3 entregada:** `interfaces/mcp/server.py` (FastMCP stdio) expone `comparar_modalidades`
y `simular_escenario`; el caso borde C-22 vive en las `instructions` del servidor y en el
campo `no_recomendacion` de cada salida. `explicar_comparacion`/`metricas_pension`/`evaluar_senda`
quedan diferidas (SAD §5.3). Config Claude Desktop en `DEPLOY.md`.

**Plan de Fase 4** (el momento "wow": ciclo de vida completo, SAD §13): módulo de acumulación
que produce una `TrayectoriaDeRiqueza` terminando en el saldo a la jubilación — exactamente el
insumo del comparador. `SendaDePlaneo`/glide path de fondo generacional según edad **y riqueza**.
Se enchufa sobre el mismo núcleo sin tocar la des-acumulación (ADR-001). El proyecto **ya está
completo y demostrable sin la Fase 4**; es profundización, no requisito.

**Atajos:** el contrato `TrayectoriaDeRiqueza` ya es la frontera; el `PuertoSimulador` ya genera
trayectorias. Ver `docs/AUDIT.md` (sign-offs) y `docs/CASES.md` (casos).

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
