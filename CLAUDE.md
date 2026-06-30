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
| 2.5 — Orientación familiar | **siguiente** (web cero-instalación + disclaimer en la fuente + calibración SP/CMF) |
| 3 — Capa MCP | pendiente |
| 4 — Acumulación | pendiente |

## Retomar aquí — próximo: Fase 2.5 (orientación familiar)

**Dónde estamos:** el MVP de des-acumulación funciona end-to-end (comparar RP vs RV por
HTTP, con mortalidad regulada validada contra la fuente y disclaimer). Último commit de
fase: Fase 2 cerrada.

**Por qué 2.5 antes que el MCP:** el uso real que motiva el proyecto es que la familia se
oriente sin instalar nada y llegue informada a la AFP. Eso lo sirve mejor una web sobre la
REST (cero instalación) que el MCP (requiere Claude Desktop). El MCP queda como capa
conversacional posterior. Ver SAD §13 (Fase 2.5) y ADR-012/013/014.

**Plan de Fase 2.5** (reusa la REST y el motor; no toca dominio salvo el disclaimer):

1. **Disclaimer en la fuente (ADR-013):** mover/reforzar el texto en el dominio
   (`RastroSimulacion`) con el encuadre paramétrico ("números ilustrativos, no la oferta
   real; la cifra exacta la da tu AFP/SCOMP"); REST/MCP/Web lo heredan. Registrar en
   `docs/COMPLIANCE.md`.
2. **Calibración (ADR-014):** fijar defaults citados — `tasa_rv` ← RV media Vejez (SP/CMF,
   `tasasRentasVitalicias.php`, mensual); `tasa_descuento` ← TITRP 3,31% ene-2026
   (`tasdescto.php`, cuatrimestral). Ambas son un solo número.
3. **Web mínima (ADR-012):** frontend estático servido por la misma app FastAPI; consume
   `POST /comparar`; traduce a lenguaje humano; saldo en pesos/UF. Ver `docs/EJEMPLO_MCP.md`
   para el tono de la traducción.

**Atajos:** el motor ya está (`application/comparar_modalidades.py::CompararModalidades`);
la web solo lo consume vía REST. Ver `docs/AUDIT.md` (sign-offs) y `docs/CASES.md` (casos).

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
