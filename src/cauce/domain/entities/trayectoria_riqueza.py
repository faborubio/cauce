"""TrayectoriaDeRiqueza — el CONTRATO compartido entre acumulación y des-acumulación.

Es el estado central del modelo (SAD §1.1): la evolución de (saldo, edad) en el
tiempo. Lo que produce el módulo de acumulación es exactamente lo que consume el de
des-acumulación; por eso esto es **un proyecto y no dos pegados**.

Frontera de ADR-010: esta entidad representa **una trayectoria realizada** (un camino
del Monte Carlo) como estructura pura. El ``PuertoSimulador`` (infraestructura, NumPy)
*genera* el conjunto de trayectorias de forma vectorizada; el dominio las *evalúa*.
Una trayectoria es inmutable: representa un hecho ya simulado.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.saldo import SaldoPrevisional


@dataclass(frozen=True, slots=True)
class PuntoTrayectoria:
    """Un punto (edad, saldo) en una trayectoria realizada."""

    edad: Edad
    saldo: SaldoPrevisional


@dataclass(frozen=True, slots=True)
class TrayectoriaDeRiqueza:
    """Camino realizado de (saldo, edad). Contrato único entre ambos módulos.

    Invariante: los puntos vienen ordenados por edad creciente y no vacíos.
    """

    puntos: Sequence[PuntoTrayectoria]

    def __post_init__(self) -> None:
        if not self.puntos:
            raise ValueError("Una TrayectoriaDeRiqueza no puede estar vacía.")
        edades = [p.edad for p in self.puntos]
        if edades != sorted(edades):
            raise ValueError("Los puntos deben venir ordenados por edad creciente.")

    @property
    def edad_inicial(self) -> Edad:
        return self.puntos[0].edad

    @property
    def edad_final(self) -> Edad:
        return self.puntos[-1].edad

    @property
    def saldo_inicial(self) -> SaldoPrevisional:
        return self.puntos[0].saldo

    @property
    def saldo_final(self) -> SaldoPrevisional:
        return self.puntos[-1].saldo

    def se_agoto(self) -> bool:
        """True si el saldo llegó a cero en algún punto (longevidad materializada)."""
        return any(p.saldo.esta_agotado() for p in self.puntos)
