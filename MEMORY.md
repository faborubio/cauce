# MEMORY.md — Bitácora de Cauce

> Registro cronológico de decisiones, correcciones y aprendizajes. Lo estable se
> promueve al SAD; aquí queda el *por qué* y el camino recorrido.

## 2026-06-29 — Fase 0: Scaffolding

- Repo inicializado (rama `main`), toolchain `uv` + `ruff` + `mypy --strict` +
  `import-linter` + `pytest`.
- Estructura por capas (Clean Architecture) con dominio **stdlib-only**.
- **Frontera ADR-010 blindada:** tres contratos de `import-linter` — capas, dominio sin
  frameworks/NumPy, y application sin adaptadores. Es la corrección clave sobre el molde
  de Veredicto: Cauce es simulación estocástica, no reglas, así que el Monte Carlo va a
  `infrastructure/`, no al dominio.
- Contrato central `TrayectoriaDeRiqueza` modelado como camino realizado inmutable.
- `metricas.py` implementado con lógica pura real (prob. de agotamiento, percentiles) para
  demostrar la frontera generar/evaluar en el smoke test.

## Decisiones del SAD revisadas en esta sesión (review "vista de halcón")

- **ADR-010** (nuevo): generación numérica en infraestructura; dominio solo evalúa.
- **ADR-007** (rellena hueco): proceso de retornos explícito (block bootstrap por defecto).
- **ADR-011** (nuevo): pensión de sobrevivencia fuera del MVP; `PuertoMortalidad`
  extensible a estado-de-hogar.
- **ADR-003** corregido con la nomenclatura real de tablas (NCG N°306): vejez
  `RV-M-2020`/`CB-H-2020`; factores de mejoramiento `AA_{x,t}` obligatorios.

## Pendientes

- [ ] Descargar **Anexo N°1 de la NCG 306** (valores numéricos de las tablas) — Fase 1.
- [ ] Implementar `PuertoSimulador` con NumPy vectorizado (Fase 1).
- [ ] Property-test de reproducibilidad real (perfil, mortalidad, semilla) — Fase 1.
