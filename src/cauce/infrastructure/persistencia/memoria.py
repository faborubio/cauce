"""Repositorios en memoria — adaptadores ligeros para el MVP local.

La persistencia real (SQLAlchemy + PostgreSQL) es deuda declarada del MVP (§11); estos
adaptadores implementan los puertos para correr la REST/el MCP sin base de datos.
"""

from __future__ import annotations

from cauce.domain.entities.rastro import RastroSimulacion


class RepositorioSimulacionesMemoria:
    """Implementa ``RepositorioSimulaciones`` con un dict en memoria del proceso."""

    def __init__(self) -> None:
        self._almacen: dict[str, RastroSimulacion] = {}
        self._contador = 0

    def guardar(self, rastro: RastroSimulacion) -> str:
        self._contador += 1
        simulacion_id = f"sim-{self._contador:06d}"
        self._almacen[simulacion_id] = rastro
        return simulacion_id

    def obtener(self, simulacion_id: str) -> RastroSimulacion:
        if simulacion_id not in self._almacen:
            raise KeyError(f"Simulación no encontrada: {simulacion_id}")
        return self._almacen[simulacion_id]
