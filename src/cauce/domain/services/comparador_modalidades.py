"""ComparadorModalidades — contrasta modalidades y atribuye el riesgo dominante.

Servicio puro (SAD §5.2): recibe, por modalidad, las trayectorias ya generadas, calcula
sus métricas y determina qué riesgo domina (longevidad, mercado, irrevocabilidad). El
esqueleto fija el contrato; la atribución completa se implementa en la Fase 2 (SAD §13).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.trayectoria_riqueza import TrayectoriaDeRiqueza
from cauce.domain.services.metricas import MetricasModalidad, calcular_metricas


@dataclass(frozen=True, slots=True)
class Comparacion:
    """Resultado de comparar modalidades: métricas por modalidad."""

    metricas_por_modalidad: Mapping[Modalidad, MetricasModalidad]


def comparar(
    trayectorias_por_modalidad: Mapping[Modalidad, Sequence[TrayectoriaDeRiqueza]],
) -> Comparacion:
    """Evalúa cada modalidad sobre sus trayectorias. Puro, sin efectos."""
    if not trayectorias_por_modalidad:
        raise ValueError("Debe compararse al menos una modalidad.")
    return Comparacion(
        metricas_por_modalidad={
            modalidad: calcular_metricas(trayectorias)
            for modalidad, trayectorias in trayectorias_por_modalidad.items()
        }
    )
