"""PuertoTarificador — tarificación tipo SCOMP de la renta vitalicia.

Modelo **paramétrico documentado** (no replica ofertas reales de compañías; SAD §11):
calcula la mesada de renta vitalicia a partir del saldo, la tasa de descuento (interés
técnico) y la curva de mortalidad. La corrección se verifica contra el valor presente
actuarial cerrado (SAD §10).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos


class PuertoTarificador(Protocol):
    """Convierte un saldo en mesada de renta vitalicia (anualidad actuarial)."""

    def tarificar_renta_vitalicia(
        self,
        saldo: SaldoPrevisional,
        supuestos: Supuestos,
        supervivencia: Mapping[Edad, float],
    ) -> Mesada:
        """Mesada vitalicia tal que el VP de los pagos iguala el saldo."""
        ...
