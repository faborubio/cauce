"""RepositorioSimulaciones — persistencia del rastro/snapshot de cada comparación."""

from __future__ import annotations

from typing import Protocol

from cauce.domain.entities.rastro import RastroSimulacion


class RepositorioSimulaciones(Protocol):
    """Persiste el rastro de una simulación para auditoría y reproducción (ADR-004)."""

    def guardar(self, rastro: RastroSimulacion) -> str:
        """Persiste el rastro y devuelve su ``simulacion_id``."""
        ...

    def obtener(self, simulacion_id: str) -> RastroSimulacion:
        """Recupera el rastro de una simulación. Lanza si no existe."""
        ...
