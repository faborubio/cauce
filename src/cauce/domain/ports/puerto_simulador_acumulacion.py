"""PuertoSimuladorAcumulacion — genera las TrayectoriaDeRiqueza de la acumulación.

**Frontera de ADR-010.** El dominio declara *qué* necesita (trayectorias de riqueza de
una persona en formación bajo su glide path); la generación numérica vectorizada vive en
``infrastructure/simulacion`` y usa NumPy. El dominio recibe trayectorias ya construidas.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.trayectoria_riqueza import TrayectoriaDeRiqueza


class PuertoSimuladorAcumulacion(Protocol):
    """Genera trayectorias de acumulación por Monte Carlo determinista (semilla del perfil)."""

    def generar(
        self,
        perfil: PerfilAcumulacion,
        n_trayectorias: int,
    ) -> Sequence[TrayectoriaDeRiqueza]:
        """Devuelve ``n_trayectorias`` caminos de (saldo, edad) hasta la jubilación."""
        ...
