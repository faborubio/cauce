"""Métricas de acumulación (puras) — resume la distribución del saldo a la jubilación.

Evalúa trayectorias ya simuladas (frontera ADR-010): sin NumPy, usa ``statistics`` de la
stdlib. El saldo a la jubilación es incierto (depende de la secuencia de retornos), por eso
se reporta como distribución (p10/p50/p90 + esperado), no como un número único.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, quantiles

from cauce.domain.entities.trayectoria_riqueza import TrayectoriaDeRiqueza


@dataclass(frozen=True, slots=True)
class MetricasAcumulacion:
    """Distribución del saldo a la jubilación sobre el sample simulado."""

    n_trayectorias: int
    saldo_p10_uf: Decimal
    saldo_p50_uf: Decimal
    saldo_p90_uf: Decimal
    saldo_esperado_uf: Decimal


def _uf(x: float) -> Decimal:
    return Decimal(f"{max(x, 0.0):.6f}")


def resumir_acumulacion(trayectorias: Sequence[TrayectoriaDeRiqueza]) -> MetricasAcumulacion:
    """Resume la distribución del saldo final (a la jubilación) de las trayectorias."""
    if not trayectorias:
        raise ValueError("Se requiere al menos una trayectoria de acumulación.")
    finales = [float(t.saldo_final.uf) for t in trayectorias]
    if len(finales) == 1:
        p10 = p50 = p90 = finales[0]
    else:
        cortes = quantiles(finales, n=10, method="inclusive")  # 9 cortes (deciles)
        p10, p50, p90 = cortes[0], cortes[4], cortes[8]
    return MetricasAcumulacion(
        n_trayectorias=len(finales),
        saldo_p10_uf=_uf(p10),
        saldo_p50_uf=_uf(p50),
        saldo_p90_uf=_uf(p90),
        saldo_esperado_uf=_uf(mean(finales)),
    )
