"""Servicios de dominio — lógica pura que **evalúa** trayectorias ya simuladas.

Frontera de ADR-010: estos servicios no *generan* el Monte Carlo (eso es del
``PuertoSimulador`` en infraestructura); reciben las trayectorias y calculan métricas,
comparan modalidades y atribuyen el riesgo dominante, todo con stdlib.
"""

from cauce.domain.services.metricas import MetricasModalidad, calcular_metricas

__all__ = ["MetricasModalidad", "calcular_metricas"]
