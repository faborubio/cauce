"""Supuestos — parámetros económicos de una simulación.

Son **supuestos/escenarios explícitos, no pronósticos** (SAD §3.3): retorno e
inflación esperados, volatilidad para el Monte Carlo y la tasa de descuento (tipo
"tasa de interés técnica") usada por el tarificador. Tasas anuales, en fracción
(0.04 = 4 %).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Supuestos:
    """Supuestos económicos anuales de una simulación. Inmutables."""

    retorno_esperado: Decimal
    volatilidad: Decimal
    inflacion: Decimal
    tasa_descuento: Decimal

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("retorno_esperado", self.retorno_esperado),
            ("volatilidad", self.volatilidad),
            ("inflacion", self.inflacion),
            ("tasa_descuento", self.tasa_descuento),
        ):
            if not isinstance(valor, Decimal):
                raise TypeError(f"'{nombre}' debe ser Decimal (tasa anual en fracción).")
        if self.volatilidad < 0:
            raise ValueError(f"La volatilidad no puede ser negativa: {self.volatilidad}.")
        if self.tasa_descuento <= -1:
            raise ValueError(f"Tasa de descuento inválida: {self.tasa_descuento}.")
