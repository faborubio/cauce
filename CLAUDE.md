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
uv run pytest                   # tests (47, verdes)
docker compose up -d postgres   # base de datos local (deuda: persistencia real)
```

### Correr el MVP (REST)

```bash
uv run uvicorn cauce.interfaces.rest.app:app --port 8077
curl -s -X POST http://127.0.0.1:8077/comparar \
  -H 'Content-Type: application/json' \
  -d '{"edad":65,"saldo_uf":"3000","genero":"M","n_trayectorias":5000}'
# → RP vs RV con mesada, herencia, erosión, riesgo dominante + disclaimer
```

## Estado por fases (SAD §13)

| Fase | Estado |
|------|--------|
| 0 — Scaffolding | ✅ cerrada (`a772c5d`) |
| 1 — Núcleo de simulación | ✅ cerrada (mortalidad + retornos + simulador) |
| 2 — MVP Des-acumulación | ✅ cerrada (tarificador + comparador RP/RV + REST, 47 tests) |
| 3 — Capa MCP | **siguiente** |
| 4 — Acumulación | pendiente |

## Retomar aquí — próximo: Fase 3 (capa MCP)

**Dónde estamos:** el MVP de des-acumulación funciona end-to-end (comparar RP vs RV por
HTTP, con mortalidad regulada validada contra la fuente y disclaimer). Último commit de
fase: Fase 2 cerrada. Backlog: 21 ✅ · 5 🟡 (declarados/diferidos) · 5 🔲 (Fase 3/4).

**Plan de Fase 3** (servidor MCP read-only sobre el mismo caso de uso — REST y MCP son
adaptadores hermanos):

1. `interfaces/mcp/` con **FastMCP** (stdio local), como composition root análogo a la REST.
2. Herramientas (envuelven casos de uso existentes, SAD §5.3): `comparar_modalidades`,
   `explicar_comparacion`, `metricas_pension`, `simular_escenario`.
3. **Caso borde C-22** (clave de la fase): ante "¿cuál me conviene?", muestra números y
   **redirige** a AFP/asesor/SCOMP — nunca recomienda. Disclaimer en cada salida (C-21).
4. Claude Desktop como host; demo: preguntar en lenguaje natural y obtener la comparación.

**Atajos:** el motor ya está (`application/comparar_modalidades.py::CompararModalidades`);
el MCP solo lo expone. Ver `docs/AUDIT.md` (sign-offs) y `docs/CASES.md` (casos abiertos).

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
