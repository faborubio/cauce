# CASES.md — Casos borde (backlog vivo)

> Catálogo de escenarios espinosos que el motor **debe** resolver bien. Se anotan apenas
> se detectan y se responden a medida que avanzamos; cada caso cierra con su **Respuesta**
> y, cuando aplica, el test que lo fija. Es documentación viva: si un caso revela una
> decisión de arquitectura, sube a un ADR del SAD.
>
> **Estado:** 🔲 abierto · 🟡 en análisis · ✅ resuelto
> Datos sintéticos siempre (nunca personas reales). Toda salida lleva disclaimer (ADR-009).

---

## A. Mortalidad y longevidad

### C-01 · Proyección `q_x → q_{x,t}` con factores de mejoramiento ✅ (Fase 1)
- **Escenario:** las tablas 2020 traen `q_x` base + matriz `AA_{x,t}` (2021–2036, constante desde 2036). La mortalidad usada debe ser la *proyectada* al año, no la base.
- **Por qué es borde:** usar `q_x` base subestima la longevidad (objetivo de calidad #3). La fórmula exacta vive en la **nota técnica del Anexo N°10**, no la inventamos.
- **Respuesta:** ✅ Fórmula oficial (Anexo N°10): `q_{x,año} = q_{x,2020} · ∏_{t=2021}^{año} (1 − AA_{x,t})` — **producto acumulado** (no potencia), `AA` constante desde 2036, factores por sexo. Implementada en `cargador.py::qx_proyectada` y **verificada al 9º decimal** contra el ejemplo oficial (`q_{65,2022}` = 0.008526031). Test: `test_mortalidad.py`.

### C-02 · Edad fuera del rango de la tabla ✅ (Fase 1)
- **Escenario:** `RV-2020-MUJERES` parte en edad 20; alguien con edad < 20, o cualquier persona que cruce los 110 (`q_x(110)=1`).
- **Por qué es borde:** ¿extrapolar, truncar o lanzar error? Una extrapolación silenciosa corrompe la validez.
- **Respuesta:** ✅ Borde joven → **error explícito** (`ValueError`, nunca extrapola). Borde alto → `q_x(110)=1` trunca la trayectoria a los 110 (ver C-04). Test: `test_mortalidad.py::test_c02_edad_fuera_de_rango`.

### C-03 · Selección de tabla por (sexo, uso) ✅ (Fase 1)
- **Escenario:** vejez → `CB-2020-HOMBRES` (H) / `RV-2020-MUJERES` (M); sobrevivencia → `B-2020-MUJERES` / `CB-2020-HOMBRES` (misma del hombre). Invalidez (`MI`) está fuera del MVP.
- **Por qué es borde:** asimetría regulatoria real; pedir invalidez en el MVP no debe romper ni inventar.
- **Respuesta:** ✅ Mapeo `(uso, sexo) → tabla` explícito en `adaptador.py::_TABLAS`; uso no soportado → `ValueError`. Verificado que la mujer sobrevive más (S(90) M > H). Test: `test_mortalidad.py::test_c03_...`.

### C-04 · Horizonte forzado por `q_x(110)=1` ✅ (Fase 1)
- **Escenario:** toda persona muere a más tardar a los 110; las trayectorias tienen largo variable según la edad de muerte simulada.
- **Por qué es borde:** la `TrayectoriaDeRiqueza` debe representar caminos de distinta longitud; las métricas agregan sobre muestras no alineadas.
- **Respuesta:** ✅ Se sortea la edad de muerte por trayectoria y cada `TrayectoriaDeRiqueza` se trunca ahí (largos 1–46 en el demo, todas terminan ≤110). Test: `test_simulador.py::test_c04_...`.

### C-05 · Sexo registral binario / dato faltante 🟡 (Fase 1)
- **Escenario:** las tablas solo son F/M; el `Genero` del dominio es binario.
- **Por qué es borde:** el insumo regulatorio es el sexo registral; no hay tabla para otra categoría.
- **Respuesta:** 🟡 **Decisión declarada:** se exige sexo registral F/M (insumo de la tabla regulada); no hay tabla para otra categoría. Registrado en COMPLIANCE; sin default silencioso.

---

## B. Des-acumulación y modalidades

### C-06 · Saldo cero o casi nulo al jubilar ✅ (Fase 2)
- **Escenario:** persona llega a la jubilación con saldo ínfimo.
- **Por qué es borde:** la mesada de RV → ~0; el retiro programado se agota de inmediato; divisiones por cero en el tarificador.
- **Respuesta:** ✅ Sin división por cero (ä>0); saldo ínfimo → métricas ~0 sin reventar. La REST exige `saldo_uf>0`. Test: `test_bordes_fase2.py::test_c06_...`.

### C-07 · Retiro programado: recálculo anual de la mesada ✅ (Fase 2)
- **Escenario:** en Chile el RP **recalcula la mesada cada año** según saldo y expectativa de vida; la mesada decae con la edad.
- **Por qué es borde:** modelarlo bien es la esencia del riesgo de longevidad del RP; simplificarlo de más invalida la comparación contra la RV.
- **Respuesta:** ✅ El RP recalcula `mesada_t = saldo_t / ä(edad_t)` cada año (reusa el tarificador). La mesada decae con la edad; nunca cero duro, deja herencia. En el demo erosiona a ~0.50 mediana. `montecarlo.py::_evaluar_rp`.

### C-08 · Tasa de descuento / interés técnico degenerada ✅ (Fase 2)
- **Escenario:** `tasa_descuento` negativa, ~0, o ≥ retorno esperado.
- **Por qué es borde:** el valor presente de la anualidad explota o se vuelve absurdo.
- **Respuesta:** ✅ `Supuestos` valida `tasa<= -100%` y `margen_rv∈[0,1)`; el tarificador rechaza tasa inválida. Tests: `test_value_objects.py::test_c08_...`.

### C-09 · Renta vitalicia: VP de la anualidad = saldo (control de corrección) ✅ (Fase 2)
- **Escenario:** tarificar una RV cuyo valor presente actuarial debe igualar el saldo.
- **Por qué es borde:** es el **caso de control** del objetivo de calidad #5 — verificar contra el cálculo cerrado por funciones de conmutación (`ä_x`).
- **Respuesta:** ✅ Tarificador por conmutación `ä_x=Σ v^k·S(x0+k)`; mesada=saldo/ä. Verificado contra cálculo a mano (ä juguete=1.5; VP·mesada=saldo). Tests: `test_tarificador.py`.

### C-10 · Modalidades mixtas (RT+RV diferida, RV inm.+RP) 🟡 (Fase 2)
- **Escenario:** el saldo se reparte entre tramos (temporal/diferido, vitalicio/programado).
- **Por qué es borde:** empalmar tramos sin discontinuidades ni doble conteo del saldo.
- **Respuesta:** 🟡 **Diferido post-MVP (decisión del usuario):** las modalidades mixtas (partición del saldo + empalme de tramos) quedan fuera del MVP; hoy lanzan `NotImplementedError` honesto. El valor del MVP es RP vs RV puras.

### C-11 · Cola de longevidad (vivir mucho más que la EV) ✅ (Fase 2)
- **Escenario:** la persona supera con creces su esperanza de vida.
- **Por qué es borde:** es **el** caso que separa las modalidades — RP agotado y sin pensión vs RV que sigue pagando. Núcleo del valor del producto.
- **Respuesta:** ✅ Las trayectorias de la cola larga dejan herencia ~0 y pensión erosionada (<0.3). Verificado sobre el sample. Test: `test_bordes_fase2.py::test_c11_...`.

---

## C. Riesgo de secuencia y retornos

### C-12 · Crash de mercado en el año 1 del retiro 🟡 (Fase 2)
- **Escenario:** secuencia de retornos adversa justo al inicio de la des-acumulación.
- **Por qué es borde:** penaliza fuerte al RP y a la renta temporal diferida; es el riesgo de secuencia hecho carne (ADR-007).
- **Respuesta:** 🟡 El proceso paramétrico ya modela riesgo de secuencia (path-dependiente); la inyección precisa de un crash en el año 1 llega con el modo escenarios / bootstrap (C-15, Fase 3).

### C-13 · Volatilidad cero → determinístico (control numérico) ✅ (Fase 1)
- **Escenario:** `volatilidad = 0`.
- **Por qué es borde:** el Monte Carlo debe colapsar al cálculo determinístico cerrado; **caso de control** del simulador.
- **Respuesta:** ✅ Con `volatilidad=0` el generador devuelve todos los retornos = media exacta (la des-acumulación queda determinística salvo la edad de muerte). Test: `test_retornos.py::test_c13_...`.

### C-14 · Retorno real persistentemente negativo ✅ (Fase 2)
- **Escenario:** inflación > retorno por períodos largos.
- **Por qué es borde:** erosión real del saldo; no debe producir saldos negativos (el VO `SaldoPrevisional` lo prohíbe) sino agotamiento.
- **Respuesta:** ✅ Retorno real negativo → menos herencia que con positivo; saldo nunca negativo (`SaldoPrevisional` lo prohíbe, piso en cero). Test: `test_bordes_fase2.py::test_c14_...`.

### C-15 · Block bootstrap vs paramétrico (mismo perfil) 🔲 (Fase 2)
- **Escenario:** correr el mismo perfil con los dos procesos de retorno (ADR-007).
- **Por qué es borde:** cuantifica cuánto subestima el iid/paramétrico al riesgo de secuencia.
- **Respuesta:** _pendiente — segunda implementación de `PuertoRetornos` (block bootstrap); enriquecimiento de Fase 3._

---

## D. Numéricos y determinismo

### C-16 · Reproducibilidad: misma (perfil, tabla, semilla) → idéntico ✅ (Fase 1)
- **Escenario:** repetir la simulación con los mismos insumos.
- **Por qué es borde:** base de auditoría (ADR-006). **Property-test** central de la Fase 1.
- **Respuesta:** ✅ Toda la aleatoriedad nace de `perfil.semilla` vía `np.random.SeedSequence` con corrientes independientes (mortalidad / retornos). Misma semilla → trayectorias idénticas; semilla distinta → cambian. Tests: `test_simulador.py::test_c16_...`, `test_semilla_distinta_cambia`.

### C-17 · `n_trayectorias` extremo (1 y muy grande) ✅ (Fase 1/2)
- **Escenario:** una sola trayectoria (percentiles degenerados) vs 10k+ (SLA < 3 s, §10).
- **Por qué es borde:** robustez de las métricas y cumplimiento del SLA con NumPy vectorizado.
- **Respuesta:** ✅ SLA 10k+métricas ~1s; `n=1` no degenera el cálculo (percentiles robustos). Tests: `test_bordes_fase2.py::test_c17_...`.

### C-18 · Frontera `Decimal` (dominio) ↔ `float64` (infra) ✅ (Fase 1)
- **Escenario:** el dominio usa `Decimal` (UF); el simulador NumPy usa `float64`.
- **Por qué es borde:** redondeo al cruzar la frontera generar/evaluar (ADR-010); evitar ruido espurio o pérdida de determinismo.
- **Respuesta:** ✅ Conversión única en la frontera (`Decimal(f"{v:.6f}")`, 6 decimales UF), determinista. Suficiente para las métricas del MVP.

---

## E. Contrato y arquitectura

### C-19 · `TrayectoriaDeRiqueza` enchufa acumulación → des-acumulación 🔲 (Fase 4)
- **Escenario:** una sola simulación de los 25 a la mesada, sobre el mismo contrato.
- **Por qué es borde:** es la **prueba de fuego** de ADR-001/010 — si el contrato está bien, acumulación se enchufa sin tocar des-acumulación.
- **A decidir:** confirmar que el saldo final de acumulación es exactamente el insumo del comparador, sin adaptadores.
- **Respuesta:** _pendiente — se valida recién en Fase 4; anotado en el sign-off de Fase 0._

### C-20 · `PerfilPrevisional` inmutable y versionado 🟡 (Fase 2)
- **Escenario:** editar un perfil crea v2; reproducir una simulación vieja con v1 mientras existe v2.
- **Por qué es borde:** reproducibilidad histórica (ADR-008); el motor estable + perfil versionado.
- **Respuesta:** 🟡 La entidad ya es **inmutable** (`frozen`) y **versionada** (`id`, `version`), y el rastro persiste `(perfil_id, version, semilla)`. La persistencia del perfil con enforcement de unicidad `(id, version)` va con la persistencia real (Postgres = deuda §11); el MVP arma el perfil ad-hoc.

---

## F. Regulatorio y honestidad

### C-21 · Ninguna salida sin disclaimer ✅ (Fase 2)
- **Escenario:** intentar emitir una comparación sin el disclaimer de no-asesoría.
- **Por qué es borde:** ADR-009 gobierna todo; debe ser estructuralmente imposible omitirlo.
- **Respuesta:** ✅ El caso de uso siempre arma un `RastroSimulacion`, que lleva el `DISCLAIMER_NO_ASESORIA` por defecto; la REST lo incluye en cada respuesta. Tests: `test_comparar_modalidades.py::test_c21_...`, `test_rest.py::test_c21_...`. Falta replicar en MCP (Fase 3).

### C-22 · Usuario pide recomendación vía MCP 🔲 (Fase 3)
- **Escenario:** "¿cuál me conviene contratar?".
- **Por qué es borde:** la capa MCP es read-only + simulación; recomendar roza asesoría regulada.
- **A decidir:** redirigir a AFP / asesor registrado / SCOMP, mostrar escenarios, nunca elegir.
- **Respuesta:** _pendiente._

### C-23 · Sobrevivencia pedida en el MVP 🟡 (Fase 2)
- **Escenario:** perfil con beneficiarios esperando pensión de sobrevivencia.
- **Por qué es borde:** fuera del MVP (ADR-011); no debe inventar mortalidad conjunta a medias.
- **Respuesta:** 🟡 **Declarado:** el MVP modela **vejez, una sola vida**. `Persona` acepta `beneficiarios` pero el comparador los **ignora** (no simula sobrevivencia); la REST solo expone vejez. Registrado en COMPLIANCE (ADR-011).

---

## G. Tarificación y comparación (Fase 2)

### C-24 · Números aleatorios comunes entre modalidades ✅ (Fase 2)
- **Escenario:** comparar las 4 modalidades del SCOMP para un mismo perfil.
- **Por qué es borde:** si cada modalidad usa un sorteo Monte Carlo independiente, el **ruido** del muestreo contamina la comparación y dos modalidades casi iguales pueden parecer distintas. Hay que evaluarlas sobre las **mismas trayectorias** de mortalidad y retornos (common random numbers).
- **Respuesta:** ✅ Un solo sorteo (mortalidad + retornos) desde `perfil.semilla`, evaluado bajo cada modalidad. Misma semilla → comparación idéntica. Test: `test_comparacion.py::test_c24_...`.

### C-25 · Atribución objetiva del riesgo dominante ✅ (Fase 2)
- **Escenario:** cada salida debe decir *qué riesgo asume* el pensionado en cada modalidad (longevidad / mercado / irrevocabilidad / cero herencia).
- **Por qué es borde:** es el corazón de la explicabilidad (objetivo #4); no puede ser una etiqueta hardcodeada, debe derivarse de las métricas (p. ej. prob. agotamiento alta ⇒ riesgo de longevidad).
- **Respuesta:** ✅ `atribuir_riesgo` deriva el riesgo de las métricas (herencia≈0 + erosión≈1 → irrevocabilidad; erosión<0.85 → longevidad). No es etiqueta fija. Test: `test_comparacion.py::test_c25_...`.

### C-26 · Herencia como métrica diferenciadora ✅ (Fase 2)
- **Escenario:** el retiro programado deja **herencia** (saldo a la muerte); la renta vitalicia no.
- **Por qué es borde:** es uno de los ejes que separan las modalidades; comparar solo por mesada esconde este trade-off.
- **Respuesta:** ✅ Herencia = saldo a la muerte por trayectoria; RP>0 (~887 UF demo), RV=0. Esperada + p50. Test: `test_comparacion.py::test_c26_...`.

### C-27 · Carga / margen de la compañía en la renta vitalicia ✅ (Fase 2)
- **Escenario:** la RV real se tarifica con un **margen** sobre el valor actuarial justo; nuestro tarificador es paramétrico.
- **Por qué es borde:** sin margen, la RV parece más generosa que la real; con un margen inventado, parece dato real. Riesgo de "tarificación simplificada de más" (§11).
- **Respuesta:** ✅ `margen_rv` (0..1, default 0=valor justo): la RV se tarifica sobre `saldo·(1−margen)`. Declarado que NO replica ofertas reales, pero el margen es explícito y auditable. Test: `test_bordes_fase2.py::test_c27_...`.

### C-28 · Tasa de interés técnica del RP vs tasa de la RV ✅ (Fase 2)
- **Escenario:** el retiro programado usa una **tasa de interés técnica** regulada (vector de tasas); la RV usa la tasa de la compañía.
- **Por qué es borde:** usar una sola tasa para ambos sesga la comparación.
- **Respuesta:** ✅ `tasa_descuento` = interés técnico del RP; `tasa_rv` = tasa de la compañía. Con tasas distintas, RP y RV ya no parten con la misma mesada. Test: `test_bordes_fase2.py::test_c28_...`.

### C-29 · Renta temporal + RV diferida: partición y discontinuidad 🟡 (Fase 2)
- **Escenario:** el saldo se parte entre un tramo temporal (mesada alta) y una RV diferida (mesada menor luego).
- **Por qué es borde:** discontinuidad de la mesada al pasar de un tramo a otro; el saldo no se puede contar dos veces.
- **Respuesta:** 🟡 Diferido junto a C-10 (mixtas) post-MVP; declarado.

### C-30 · Reportar dominancia sin recomendar ✅ (Fase 2/3)
- **Escenario:** una modalidad resulta mejor en *todas* las métricas (más mesada y más herencia).
- **Por qué es borde:** mostrar "esta es mejor" roza la recomendación (ADR-009); pero ocultarlo es deshonesto.
- **Respuesta:** ✅ La salida entrega métricas + riesgo dominante + disclaimer; **nunca** un "elige esta". La dominancia es visible en los números, la decisión se redirige (ADR-009). Refinar el lenguaje en MCP (Fase 3).

### C-31 · Pensión mínima / PGU como piso 🟡 (Fase 2)
- **Escenario:** existe un piso regulado (Pensión Garantizada Universal / pensión mínima) bajo el cual no se cae.
- **Por qué es borde:** cambia el riesgo de longevidad efectivo (el agotamiento del RP no deja a la persona en cero real).
- **Respuesta:** 🟡 **Fuera del MVP, declarado:** no se modela el piso PGU/pensión mínima. El agotamiento del RP se muestra como erosión real, sin el piso estatal. Registrado en COMPLIANCE; entra en fase posterior.

---

## Plantilla para casos nuevos

```
### C-NN · <título> 🔲 (Fase X)
- **Escenario:** ...
- **Por qué es borde:** ...
- **A decidir:** ...
- **Respuesta:** _pendiente._
```
