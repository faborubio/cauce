"""Fixtures compartidos de infraestructura."""

from decimal import Decimal
from pathlib import Path

import pytest

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos

DIR_MORTALIDAD = Path(__file__).resolve().parents[2] / "data" / "mortalidad"


@pytest.fixture
def dir_mortalidad() -> Path:
    return DIR_MORTALIDAD


def construir_perfil(
    *,
    edad: int = 65,
    saldo: str = "3000",
    genero: Genero = Genero.MASCULINO,
    retorno: str = "0.03",
    volatilidad: str = "0.10",
    semilla: int = 42,
) -> PerfilPrevisional:
    return PerfilPrevisional(
        id="test",
        version=1,
        persona=Persona(Edad(edad), SaldoPrevisional(Decimal(saldo)), genero),
        supuestos=Supuestos(
            retorno_esperado=Decimal(retorno),
            volatilidad=Decimal(volatilidad),
            inflacion=Decimal("0.03"),
            tasa_descuento=Decimal("0.03"),
        ),
        modalidades_a_comparar=[Modalidad.RETIRO_PROGRAMADO],
        tabla_mortalidad="2020",
        semilla=semilla,
    )
