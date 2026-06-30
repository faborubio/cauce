# COMPLIANCE.md — Encuadre de no-asesoría

> Registro del **carácter educativo/simulador** del producto y de cómo se materializa
> en el código. Gobernado por **ADR-009** (el ADR que gobierna el resto, SAD §9).

## Principio

Cauce **no constituye asesoría previsional ni recomendación personalizada**. No le dice a
una persona concreta qué modalidad contratar; ilustra escenarios, trade-offs y
sensibilidades. La elección de modalidad es **irrevocable** y materia de procesos
regulados (SCOMP, asesores previsionales registrados, AFP).

## Cómo se materializa en el código

| Mecanismo | Dónde |
|-----------|-------|
| Disclaimer obligatorio en cada salida | `domain/entities/rastro.py` → `DISCLAIMER_NO_ASESORIA` |
| Capa MCP **read-only + simulación** (sin recomendaciones, sin trámites) | `interfaces/mcp/` (Fase 3) |
| Salidas siempre con supuestos + métricas de riesgo | `application/` casos de uso (Fase 2) |
| Acumulación: no permite "elegir" fondo obligatorio | alcance (SAD §3.3) |

## Limitaciones declaradas del MVP (omisiones visibles, no ocultas)

- **Sobrevivencia (ADR-011, C-23):** modela **una sola vida, vejez**. Acepta `beneficiarios`
  pero no simula pensión de sobrevivencia; no infla una validez actuarial que no se sostiene a medias.
- **Sexo registral (C-05):** la selección de tabla regulada exige sexo registral **F/M**; no
  existe tabla para otra categoría. Sin default silencioso (se rechaza el dato faltante).
- **Pensión mínima / PGU (C-31):** no se modela el piso estatal. El agotamiento del retiro
  programado se muestra como **erosión real de la pensión**, sin el piso PGU; entra en fase posterior.
- **Margen comercial de la RV (C-27):** parametrizable (`margen_rv`); con margen 0 es el
  **valor actuarial justo** y se declara que NO replica ofertas reales de compañías.
- **Sin recomendación (C-30, ADR-009):** la salida entrega métricas + riesgo dominante +
  disclaimer; **nunca** un "elige esta modalidad". La dominancia se ve en los números; la
  decisión se redirige a AFP / asesor registrado / SCOMP.

## Pendiente

- [ ] Revisión legal del encuadre **antes de publicar** (riesgo Alto, SAD §11).
