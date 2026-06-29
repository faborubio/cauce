"""PuertoSimulador — genera la TrayectoriaDeRiqueza por Monte Carlo.

**Frontera de ADR-010.** El dominio declara *qué* necesita (un conjunto de trayectorias
para un perfil y una modalidad); la implementación vive en
``infrastructure/simulacion`` y usa NumPy vectorizado para cumplir el SLA de < 3 s
(SAD §10). El dominio nunca ve NumPy: recibe trayectorias ya construidas.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.trayectoria_riqueza import TrayectoriaDeRiqueza


class PuertoSimulador(Protocol):
    """Genera trayectorias de riqueza por Monte Carlo determinista (semilla del perfil)."""

    def generar(
        self,
        perfil: PerfilPrevisional,
        modalidad: Modalidad,
        n_trayectorias: int,
    ) -> Sequence[TrayectoriaDeRiqueza]:
        """Devuelve ``n_trayectorias`` caminos realizados de (saldo, edad)."""
        ...
