"""PerfilAcumulacion — insumos de la etapa de acumulación, versionado e inmutable.

Análogo al ``PerfilPrevisional`` de des-acumulación (SAD §5.2): fija persona-en-formación,
cotización, glide path y supuestos; reproducir = fijar ``(perfil, semilla)`` (ADR-006/008).
Produce una ``TrayectoriaDeRiqueza`` que termina en el saldo a la jubilación — exactamente
el insumo del comparador de modalidades (ADR-001, SAD §6.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos_acumulacion import SupuestosAcumulacion


@dataclass(frozen=True, slots=True)
class PerfilAcumulacion:
    """Afiliado en formación + cotización + glide path + supuestos. Inmutable y versionado."""

    id: str
    version: int
    genero: Genero
    edad_inicial: Edad
    edad_jubilacion: Edad
    saldo_inicial: SaldoPrevisional
    cotizacion_anual: SaldoPrevisional  # aporte anual en UF
    senda: SendaDePlaneo
    supuestos: SupuestosAcumulacion
    semilla: int

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("La versión del perfil debe ser >= 1.")
        if self.edad_inicial >= self.edad_jubilacion:
            raise ValueError("edad_inicial debe ser menor que edad_jubilacion.")
        if (
            self.senda.edad_inicial != self.edad_inicial.anios
            or self.senda.edad_jubilacion != self.edad_jubilacion.anios
        ):
            raise ValueError("El glide path debe cubrir el mismo tramo de edades del perfil.")

    @property
    def horizonte(self) -> int:
        """Años de acumulación (de edad_inicial a edad_jubilacion)."""
        return self.edad_jubilacion.anios - self.edad_inicial.anios
