"""Mesada — monto mensual de pensión, en UF."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True, order=True)
class Mesada:
    """Monto mensual de pensión en UF. No negativo."""

    uf: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.uf, Decimal):
            raise TypeError("La mesada debe expresarse como Decimal en UF.")
        if self.uf < 0:
            raise ValueError(f"La mesada no puede ser negativa: {self.uf} UF.")
