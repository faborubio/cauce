"""SupuestosAcumulacion — parámetros del proceso de mercado durante la acumulación.

La acumulación mezcla dos activos según la fracción de riesgo del glide path (ADR-015):
uno **riesgoso** (mayor retorno esperado y volatilidad) y uno **seguro** (retorno bajo,
volatilidad despreciable). El retorno anual de cada año se sortea con media y desviación
que dependen de esa mezcla. Tasas reales anuales en fracción (0.05 = 5 %); no son pronóstico.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SupuestosAcumulacion:
    """Supuestos del activo riesgoso y del seguro. Inmutables."""

    retorno_riesgoso: Decimal  # retorno real anual esperado del activo riesgoso
    volatilidad_riesgosa: Decimal  # desviación estándar anual del activo riesgoso
    retorno_seguro: Decimal  # retorno real anual del activo seguro (vol. despreciable)

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("retorno_riesgoso", self.retorno_riesgoso),
            ("volatilidad_riesgosa", self.volatilidad_riesgosa),
            ("retorno_seguro", self.retorno_seguro),
        ):
            if not isinstance(valor, Decimal):
                raise TypeError(f"'{nombre}' debe ser Decimal (tasa anual en fracción).")
        if self.volatilidad_riesgosa < 0:
            raise ValueError(
                f"La volatilidad no puede ser negativa: {self.volatilidad_riesgosa}."
            )
