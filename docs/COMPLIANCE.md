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

## Sobrevivencia (ADR-011)

El MVP modela **mortalidad de una sola vida** y declara la pensión de sobrevivencia
fuera de alcance — omisión *visible*, no oculta, para no inflar una validez actuarial que
no se sostiene a medias.

## Pendiente

- [ ] Revisión legal del encuadre **antes de publicar** (riesgo Alto, SAD §11).
