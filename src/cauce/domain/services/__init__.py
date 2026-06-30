"""Servicios de dominio — lógica pura que **evalúa** trayectorias ya simuladas.

Frontera de ADR-010: estos servicios no *generan* el Monte Carlo (eso es del
``PuertoSimulador`` en infraestructura); reciben los resultados y calculan métricas,
comparan modalidades y atribuyen el riesgo dominante, todo con stdlib.
"""

from cauce.domain.services.comparador_modalidades import (
    MetricasModalidad,
    atribuir_riesgo,
    comparar_modalidades,
)
from cauce.domain.services.metricas import MetricasTrayectorias, calcular_metricas

__all__ = [
    "MetricasModalidad",
    "MetricasTrayectorias",
    "atribuir_riesgo",
    "calcular_metricas",
    "comparar_modalidades",
]
