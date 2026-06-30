# AUDIT.md — Auditoría por fase

> Cada fase cierra con una **Vista de halcón** (revisión crítica) y un **sign-off**
> antes de avanzar. Formato heredado de Veredicto (SAD §12).

---

## Fase 0 — Scaffolding

**Entregable:** capas, docs vivos, esqueleto de dominio, Docker + Postgres, fronteras
blindadas por `import-linter`.

### Checklist

- [x] Estructura por capas (`domain`/`application`/`infrastructure`/`interfaces`).
- [x] `domain/` stdlib-only; numérico confinado a `infrastructure/` (ADR-010).
- [x] Contratos `import-linter` (capas + dominio puro + application sin adaptadores).
- [x] Value objects, entidades (`TrayectoriaDeRiqueza`) y puertos (`Protocol`).
- [x] Toolchain: `uv`, `ruff`, `mypy --strict`, `pytest`.
- [x] Docker Compose con PostgreSQL 16.
- [x] Docs §12 creados.
- [x] Tablas reguladas 2020 (RV/CB/B/MI) extraídas y validadas a `data/mortalidad/`.
- [x] **Sign-off** — toolchain en verde, commit `a772c5d` (2026-06-29).

### Vista de halcón (respondida en el sign-off)

- **¿El `import-linter` falla si alguien mete `import numpy` en `domain/`?** ✅ Verificado
  en vivo: se inyectó `import numpy` en `domain/services/metricas.py` y el contrato
  "Dominio puro" rompió (`cauce.domain is not allowed to import numpy`). El blindaje de
  ADR-010 no es decorativo.
- **¿`mypy --strict` pasa sin `Any` ocultos en el dominio?** ✅ 36 archivos, 0 issues.
- **¿El contrato `TrayectoriaDeRiqueza` es suficiente para enchufar acumulación sin tocar
  des-acumulación?** ⏳ Diseñado para ello (frontera generar/evaluar); la prueba real es
  la Fase 4 — anotado como caso C-19 en `CASES.md`.
- **Riesgo abierto detectado:** la fórmula de proyección `q_x → q_{x,t}` vía `AA_{x,t}`
  aún no está implementada (vive en la nota técnica del Anexo N°10). Pasa a Fase 1; caso
  C-01 en `CASES.md`.

**Estado: Fase 0 CERRADA.** Lista para Fase 1.

---

## Fase 1 — Núcleo de simulación

**Entregable:** simulador Monte Carlo (NumPy, en `infrastructure/`) que produce
`TrayectoriaDeRiqueza` con riesgo de longevidad; mortalidad regulada detrás de puerto con
proyección dinámica; proceso de retornos paramétrico; property-test de reproducibilidad.

**Demostrable:** "Simulo la trayectoria de saldo de una persona de 65 con riesgo de
longevidad y veo la probabilidad de que agote su saldo antes de morir."

### Checklist

- [x] **C-01 resuelto:** fórmula oficial de proyección `q_{x,año} = q_{x,2020}·∏(1−AA_{x,t})`
  extraída del Anexo N°10 (vía render del PDF) y **verificada contra el ejemplo oficial**
  (`q_{65,2022}` CB-H-2020 = 0.008526031, match exacto).
- [x] `AdaptadorMortalidad` (implementa `PuertoMortalidad`): selección por (sexo, uso),
  curva de supervivencia de cohorte. Resuelve C-02 (rango), C-03 (selección).
- [x] `GeneradorRetornosParametrico` (implementa `PuertoRetornos`); control vol=0 (C-13).
- [x] `SimuladorMonteCarlo` (implementa `PuertoSimulador`): NumPy vectorizado, sorteo de
  edad de muerte + senda de retornos + des-acumulación. Resuelve C-04, C-16, C-18.
- [x] 15 tests nuevos (mortalidad, retornos, simulador); 24 en total, verdes.
- [x] **SLA:** 10k trayectorias + métricas en ~1.0 s (objetivo < 3 s, §10).
- [x] Toolchain en verde (ruff, mypy --strict 40 archivos, import-linter 3/3, pytest 24).

### Vista de halcón

- **¿La mortalidad proyectada es la regulada, no una aproximación?** ✅ Verificada al
  noveno decimal contra el oráculo oficial. La fórmula es **producto acumulado**, no la de
  potencia (riesgo evitado: muchas implementaciones la confunden).
- **¿El riesgo de longevidad emerge?** ✅ Con retorno bajo el agotamiento sube a ~66%; con
  retorno alto cae a ~0%. La mecánica del producto funciona.
- **¿Reproducibilidad bit-a-bit?** ✅ Misma `(perfil, semilla)` → trayectorias idénticas
  (corrientes independientes vía `SeedSequence`).
- **Deuda declarada:** regla de retiro = mesada real constante `saldo/e_x` (simplificación
  Fase 1); el recálculo anual del RP es **C-07**, Fase 2. El tarificador y la comparación
  de las 4 modalidades son Fase 2.

**Estado: Fase 1 CERRADA.** Lista para Fase 2 (MVP des-acumulación).

## Fase 2 — MVP Des-acumulación *(en curso)*

**Entregable:** comparador de las modalidades del SCOMP; tarificador paramétrico; riesgo de
secuencia; atribución de riesgo; REST mínima con disclaimers.

### Avance

- [x] **Tarificador** por funciones de conmutación (`PuertoTarificador`): `ä_x`, mesada de
  RV. Control cerrado **C-09** verificado (cálculo a mano + propiedad VP·mesada=saldo).
- [x] **Retiro programado con recálculo anual** `mesada_t = saldo_t/ä(edad_t)` (**C-07**),
  reusando el tarificador. La mesada se erosiona (mediana ~0.50) y deja herencia.
- [x] **Renta vitalicia** inmediata: mesada fija de por vida, sin herencia.
- [x] **Comparación con números aleatorios comunes** (**C-24**): un solo sorteo evaluado
  bajo cada modalidad.
- [x] **Métricas + atribución de riesgo dominante** derivada de las métricas (**C-25**,
  **C-26**): herencia esperada/p50, erosión de la pensión, riesgo dominante.
- [x] 10 tests nuevos (34 en total); verde (ruff, mypy 42 archivos, import-linter 3/3).
- [ ] Caso de uso `CompararModalidades` (application) + disclaimer en salida (C-21).
- [ ] REST mínima (`interfaces/rest`).
- [ ] Modalidades mixtas RT+RV diferida / RV+RP (C-10, C-29).

### Vista de halcón (parcial)

- **¿La comparación es justa?** ✅ Números comunes (C-24): RP y RV se evalúan sobre el
  mismo sorteo, sin ruido Monte Carlo entre ellas.
- **¿El resultado es actuarialmente honesto?** ✅ RP y RV parten con la **misma mesada**
  (ambas `saldo/ä(x0)`); divergen por erosión vs. fijeza y por herencia. Refleja el
  trade-off real del SCOMP.
- **Deuda declarada abierta:** margen comercial de la RV (**C-27**) y tasa distinta por
  modalidad (**C-28**) no modelados — hoy RP y RV usan la misma tasa técnica.
## Fase 3 — Capa MCP *(pendiente)*
## Fase 4 — Acumulación *(pendiente)*
