"""ResultadoTrayectoria — resumen de des-acumulación de UN camino simulado.

Separa lo que la `TrayectoriaDeRiqueza` (contrato compartido) no debe cargar: el
**ingreso** (mesada) y la **herencia**. Así el contrato de acumulación↔des-acumulación
queda limpio (relevante a C-19), y la comparación de modalidades tiene los tres ejes que
las distinguen: nivel de pensión, erosión de la pensión (riesgo de longevidad) y herencia.
"""

from __future__ import annotations

from dataclasses import dataclass

from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional


@dataclass(frozen=True, slots=True)
class ResultadoTrayectoria:
    """Resultado de una modalidad en un camino: pensión inicial/final + herencia."""

    mesada_inicial: Mesada
    mesada_final: Mesada  # mesada en el año de muerte (RV = inicial; RP suele erosionarse)
    herencia: SaldoPrevisional  # saldo a la muerte (RP > 0; RV = 0)

    @property
    def erosion(self) -> float:
        """mesada_final / mesada_inicial: 1.0 = pensión estable; < 1 = erosionada."""
        if self.mesada_inicial.uf == 0:
            return 1.0
        return float(self.mesada_final.uf / self.mesada_inicial.uf)
