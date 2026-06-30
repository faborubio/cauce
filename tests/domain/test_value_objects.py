"""Smoke tests de los value objects del dominio (validación e inmutabilidad)."""

from decimal import Decimal

import pytest

from cauce.domain.value_objects import Edad, Genero, Mesada, SaldoPrevisional, Supuestos


def test_edad_valida_y_desplaza() -> None:
    assert Edad(65).mas(5) == Edad(70)


@pytest.mark.parametrize("anios", [-1, 121])
def test_edad_fuera_de_rango(anios: int) -> None:
    with pytest.raises(ValueError):
        Edad(anios)


def test_saldo_no_negativo_y_agotamiento() -> None:
    assert SaldoPrevisional(Decimal("0")).esta_agotado()
    assert not SaldoPrevisional(Decimal("1000")).esta_agotado()
    with pytest.raises(ValueError):
        SaldoPrevisional(Decimal("-1"))


def test_mesada_no_negativa() -> None:
    with pytest.raises(ValueError):
        Mesada(Decimal("-0.01"))


def test_supuestos_validan_volatilidad() -> None:
    with pytest.raises(ValueError):
        Supuestos(
            retorno_esperado=Decimal("0.04"),
            volatilidad=Decimal("-0.1"),
            inflacion=Decimal("0.03"),
            tasa_descuento=Decimal("0.03"),
        )


def test_genero_existe() -> None:
    assert {g.value for g in Genero} == {"F", "M"}


def test_c08_tasas_y_margen_degenerados() -> None:
    base = {
        "retorno_esperado": Decimal("0.04"),
        "volatilidad": Decimal("0.10"),
        "inflacion": Decimal("0.03"),
    }
    with pytest.raises(ValueError):  # tasa <= -100%
        Supuestos(**base, tasa_descuento=Decimal("-1.5"))
    with pytest.raises(ValueError):  # margen fuera de [0, 1)
        Supuestos(**base, tasa_descuento=Decimal("0.03"), margen_rv=Decimal("1.2"))
