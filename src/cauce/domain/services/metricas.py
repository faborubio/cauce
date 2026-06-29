"""Métricas de pensión — evaluación pura de un conjunto de trayectorias (stdlib).

Calcula, sobre las trayectorias que generó el ``PuertoSimulador``, las métricas que
explican una modalidad: probabilidad de agotamiento (riesgo de longevidad), saldo/
herencia esperada y sus percentiles. Sin NumPy: usa ``statistics`` de la stdlib, lo
que es suficiente para la *evaluación* (el cómputo masivo es la generación, en infra).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean

from cauce.domain.entities.trayectoria_riqueza import TrayectoriaDeRiqueza


@dataclass(frozen=True, slots=True)
class MetricasModalidad:
    """Resumen de riesgo/resultado de una modalidad sobre el sample simulado."""

    n_trayectorias: int
    probabilidad_agotamiento: float
    saldo_final_esperado_uf: Decimal
    saldo_final_p10_uf: Decimal
    saldo_final_p90_uf: Decimal


def _percentil(valores_ordenados: Sequence[Decimal], fraccion: float) -> Decimal:
    """Percentil por interpolación lineal del rango más cercano (stdlib puro)."""
    if not valores_ordenados:
        raise ValueError("No hay valores para calcular el percentil.")
    if len(valores_ordenados) == 1:
        return valores_ordenados[0]
    pos = fraccion * (len(valores_ordenados) - 1)
    bajo = int(pos)
    alto = min(bajo + 1, len(valores_ordenados) - 1)
    peso = Decimal(str(pos - bajo))
    return valores_ordenados[bajo] + (valores_ordenados[alto] - valores_ordenados[bajo]) * peso


def calcular_metricas(trayectorias: Sequence[TrayectoriaDeRiqueza]) -> MetricasModalidad:
    """Evalúa el conjunto de trayectorias realizadas de una modalidad."""
    if not trayectorias:
        raise ValueError("Se requiere al menos una trayectoria para calcular métricas.")

    n = len(trayectorias)
    n_agotadas = sum(1 for t in trayectorias if t.se_agoto())
    saldos_finales = sorted(t.saldo_final.uf for t in trayectorias)

    return MetricasModalidad(
        n_trayectorias=n,
        probabilidad_agotamiento=n_agotadas / n,
        saldo_final_esperado_uf=Decimal(str(mean(saldos_finales))),
        saldo_final_p10_uf=_percentil(saldos_finales, 0.10),
        saldo_final_p90_uf=_percentil(saldos_finales, 0.90),
    )

