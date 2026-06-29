"""Edad — años cumplidos, en el eje temporal de la TrayectoriaDeRiqueza."""

from __future__ import annotations

from dataclasses import dataclass

EDAD_MINIMA = 0
EDAD_MAXIMA = 120  # horizonte de las tablas de mortalidad reguladas


@dataclass(frozen=True, slots=True, order=True)
class Edad:
    """Edad en años cumplidos. Inmutable y comparable."""

    anios: int

    def __post_init__(self) -> None:
        if not isinstance(self.anios, int):
            raise TypeError("La edad debe ser un entero de años cumplidos.")
        if not EDAD_MINIMA <= self.anios <= EDAD_MAXIMA:
            raise ValueError(
                f"Edad fuera de rango [{EDAD_MINIMA}, {EDAD_MAXIMA}]: {self.anios}."
            )

    def mas(self, anios: int) -> Edad:
        """Devuelve la edad desplazada en ``anios`` (puede ser negativo)."""
        return Edad(self.anios + anios)
