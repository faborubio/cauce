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

## 2026-06-29 — Fase 1: Núcleo de simulación

- **C-01 resuelto con la fuente, no con suposición:** la fórmula de proyección de
  mortalidad estaba como imagen en el compendio (Anexo N°10); se **renderizó el PDF a PNG
  y se leyó la ecuación**. Es **producto acumulado** `q_{x,año}=q_{x,2020}·∏(1−AA_{x,t})`,
  NO la fórmula de potencia que muchos asumen. Verificada al 9º decimal contra el ejemplo
  oficial (`q_{65,2022}`=0.008526031). Lección: cuando el dato es regulatorio y crítico,
  ir a la fuente y validar contra un oráculo.
- Mortalidad, retornos y simulador implementados en `infrastructure/` (NumPy), detrás de
  sus puertos. La frontera ADR-010 se mantuvo (import-linter 3/3, NumPy nunca en dominio).
- Determinismo por `SeedSequence` con corrientes independientes (C-16).
- SLA holgado: 10k trayectorias + métricas en ~1.0 s (objetivo <3 s).
- **Deuda declarada:** regla de retiro simplificada (`saldo/e_x`); recálculo anual del RP
  es C-07 (Fase 2). Tarificador y comparación de 4 modalidades, Fase 2.

## Decisiones del SAD revisadas en esta sesión (review "vista de halcón")

- **ADR-010** (nuevo): generación numérica en infraestructura; dominio solo evalúa.
- **ADR-007** (rellena hueco): proceso de retornos explícito (block bootstrap por defecto).
- **ADR-011** (nuevo): pensión de sobrevivencia fuera del MVP; `PuertoMortalidad`
  extensible a estado-de-hogar.
- **ADR-003** corregido con la nomenclatura real de tablas (NCG N°306): vejez
  `RV-M-2020`/`CB-H-2020`; factores de mejoramiento `AA_{x,t}` obligatorios.

## Pendientes

- [x] ~~Tablas reguladas + `PuertoSimulador` NumPy + property-test de reproducibilidad~~ (Fase 1 ✅).
- [ ] Fase 2: tarificador por funciones de conmutación (C-09), recálculo anual del RP (C-07),
  comparación de las 4 modalidades del SCOMP, REST mínima, disclaimers.
- [ ] Revisar M-2016 (queda como fixture; ya no se usa como tabla real).
