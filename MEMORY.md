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

## 2026-06-29 — Fase 2 (en curso): comparador de modalidades

- **Decisión de modelado (usuario):** el RP usa **recálculo anual realista** (C-07),
  `mesada_t=saldo_t/ä(edad_t)`, reusando el tarificador. El riesgo de longevidad del RP es
  **erosión de la pensión**, no cero duro.
- Contrato compartido `TrayectoriaDeRiqueza` se mantuvo limpio: el ingreso y la herencia
  viven en `ResultadoTrayectoria` (propio de des-acumulación), no en el contrato que Fase 4
  reusa.
- **Resultado clave validado:** RP y RV parten con la **misma mesada** (`saldo/ä(x0)`);
  divergen por erosión (RP ~0.50) vs fijeza (RV 1.0) y por herencia (RP ~887 UF vs RV 0).
  Atribución de riesgo derivada de métricas (C-25), no hardcodeada.
- Números aleatorios comunes entre modalidades (C-24) para comparación justa.
- Renombre: `MetricasModalidad` ahora es el de la comparación; el de trayectorias-saldo de
  Fase 1 pasó a `MetricasTrayectorias`.
- **Caso de uso + REST:** `CompararModalidades` (application, solo puertos) + `interfaces/rest`
  (FastAPI, composition root). `POST /comparar` devuelve la comparación + disclaimer (C-21),
  probado con servidor real. Repo de simulaciones en memoria (Postgres = deuda §11).
- **Cierre de bordes (decisiones del usuario):** se implementó fidelidad RV — `margen_rv`
  (C-27, 0=valor justo) y `tasa_rv` distinta de la técnica del RP (C-28); RP y RV ya no parten
  iguales. Cerrados además C-06/C-08/C-11/C-14/C-17/C-18. **Diferidas** (declarado): mixtas
  (C-10/C-29) y bootstrap/crash (C-15/C-12). Declaradas en COMPLIANCE: C-05, C-31, C-30, C-23, C-20.
- **Fase 2 CERRADA.** 47 tests. MVP = comparar RP vs RV por HTTP con disclaimer.

## 2026-06-30 — Fases 2.5, 3 y 4 (una sesión)

- **Giro de propósito (usuario):** el objetivo real es que su **familia** se oriente y llegue
  informada a la AFP. Eso reordenó el trabajo: primero accesibilidad (web), luego lo demás.
- **Fase 2.5 — Orientación familiar** (`053fdf1`):
  - **Web de cero instalación** sobre la REST (ADR-012): HTML estático servido por la misma
    FastAPI, traduce a lenguaje humano, saldo en UF o pesos. Cliente delgado, sin lógica.
  - **Disclaimer en la fuente** (ADR-013): reforzado en `RastroSimulacion` con el encuadre
    paramétrico; REST/MCP/Web lo heredan idéntico.
  - **Calibración SP/CMF** (ADR-014): `tasa_descuento`=TITRP 3,31% (ene-2026), `tasa_rv`=RV
    media Vejez 2,84% (may-2026), con fuente citada. Son promedios de mercado, no oferta SCOMP.
  - **Bug atrapado por smoke test:** `erosion_mediana` es la *fracción que queda* (1.0=fija),
    no "cuánto baja"; el texto de la web estaba invertido. Lección: verificar contra el dominio.
- **Fase 3 — Capa MCP** (`f344136`): `interfaces/mcp/server.py` (FastMCP stdio), hermano de la
  REST. Tools `comparar_modalidades` + `simular_escenario`. **C-22 estructural:** regla de
  no-recomendar + redirigir en las `instructions` del servidor y en `no_recomendacion` de cada
  salida. `simular_escenario` no expone la longevidad como knob "+N años" (vive en la mortalidad
  ya simulada): honestidad. Diferidas: explicar/metricas/evaluar_senda.
- **Fase 4 — Acumulación / ciclo de vida** (ADR-015):
  - **Decisiones del usuario:** glide path por **edad + riqueza** (tesis del paper; baseline
    solo-edad con `sensibilidad_riqueza=0`) y continuidad por **saldo representativo + percentiles**.
  - `SendaDePlaneo` pura (backbone lineal por edad + ajuste por distancia a riqueza de referencia:
    adelantado→menos riesgo). `SimuladorAcumulacion` (NumPy, determinista) mezcla activo
    riesgoso/seguro según la fracción del glide.
  - `SimularCicloDeVida`: p10/p50/p90 del saldo a la jubilación → comparar modalidades → **rango
    de pensiones**. Expuesto por REST `/ciclo-vida` y MCP `proyectar_ciclo_vida`.
  - El glide es **paramétrico/determinista**, no `cvxpy`: el riesgo de no-determinismo de §11 no
    aplica. **67 tests verdes.** Fases 1–4 = proyecto completo y demostrable.

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
