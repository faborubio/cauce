"""Supuestos — parámetros económicos de una simulación.

Son **supuestos/escenarios explícitos, no pronósticos** (SAD §3.3). Tasas anuales en
fracción (0.04 = 4 %). Distinguimos la **tasa de interés técnica del retiro programado**
(``tasa_descuento``) de la **tasa de la compañía para la renta vitalicia** (``tasa_rv``),
porque en la realidad difieren (C-28); y un **margen comercial** de la RV (``margen_rv``,
0 = valor actuarial justo) para no mostrar la RV más generosa que la real (C-27).
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
    tasa_descuento: Decimal  # interés técnico del retiro programado
    tasa_rv: Decimal = Decimal("0.03")  # tasa de la compañía para la renta vitalicia (C-28)
    margen_rv: Decimal = Decimal("0")  # carga comercial de la RV, 0..1 (C-27)

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("retorno_esperado", self.retorno_esperado),
            ("volatilidad", self.volatilidad),
            ("inflacion", self.inflacion),
            ("tasa_descuento", self.tasa_descuento),
            ("tasa_rv", self.tasa_rv),
            ("margen_rv", self.margen_rv),
        ):
            if not isinstance(valor, Decimal):
                raise TypeError(f"'{nombre}' debe ser Decimal (tasa anual en fracción).")
        if self.volatilidad < 0:
            raise ValueError(f"La volatilidad no puede ser negativa: {self.volatilidad}.")
        for nombre, tasa in (("tasa_descuento", self.tasa_descuento), ("tasa_rv", self.tasa_rv)):
            if tasa <= -1:
                raise ValueError(f"'{nombre}' inválida (<= -100%): {tasa}.")
        if not 0 <= self.margen_rv < 1:
            raise ValueError(f"El margen de la RV debe estar en [0, 1): {self.margen_rv}.")
