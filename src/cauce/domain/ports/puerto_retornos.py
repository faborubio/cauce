"""PuertoRetornos — proceso de mercado que alimenta el Monte Carlo (ADR-007).

El riesgo de secuencia de retornos es path-dependiente; por eso el proceso es un
puerto con varias implementaciones: **block bootstrap histórico (por defecto)**,
paramétrico (GBM/normal, baseline) y escenarios deterministas para tests. La elección
es auditable, no un detalle oculto de infraestructura.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from cauce.domain.value_objects.supuestos import Supuestos


class PuertoRetornos(Protocol):
    """Genera trayectorias anuales de retorno real, deterministas dada la semilla."""

    def trayectorias_retorno(
        self,
        supuestos: Supuestos,
        anios: int,
        n_trayectorias: int,
        semilla: int,
    ) -> Sequence[Sequence[float]]:
        """Devuelve una matriz ``n_trayectorias`` por ``anios`` de retornos reales anuales."""
        ...
