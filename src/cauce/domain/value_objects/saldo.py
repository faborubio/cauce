"""SaldoPrevisional — saldo acumulado, expresado en UF (Unidad de Fomento).

Se usa ``Decimal`` (stdlib) y no ``float`` para el dinero del dominio: evita el
ruido de coma flotante en las firmas puras. La simulación Monte Carlo, que sí es
masivamente numérica, opera sobre vectores NumPy en ``infrastructure`` (ADR-010);
este value object es el saldo *como concepto de negocio*, no la matriz simulada.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True, order=True)
class SaldoPrevisional:
    """Saldo en UF. No negativo (un saldo previsional no se endeuda)."""

    uf: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.uf, Decimal):
            raise TypeError("El saldo debe expresarse como Decimal en UF.")
        if self.uf < 0:
            raise ValueError(f"El saldo previsional no puede ser negativo: {self.uf} UF.")

    def esta_agotado(self) -> bool:
        """True si el saldo llegó a cero (riesgo de longevidad materializado)."""
        return self.uf == 0
