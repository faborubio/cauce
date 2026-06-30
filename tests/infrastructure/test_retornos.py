"""Tests del proceso de retornos paramétrico (ADR-007), incl. vol=0 determinista (C-13)."""

from decimal import Decimal

from cauce.domain.value_objects.supuestos import Supuestos
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico


def _supuestos(retorno: str, vol: str) -> Supuestos:
    return Supuestos(Decimal(retorno), Decimal(vol), Decimal("0.03"), Decimal("0.03"))


def test_c13_volatilidad_cero_es_determinista() -> None:
    gen = GeneradorRetornosParametrico()
    m = gen.matriz_retornos(_supuestos("0.04", "0"), anios=10, n_trayectorias=5, semilla=7)
    assert m.shape == (5, 10)
    assert (m == 0.04).all()


def test_reproducibilidad_misma_semilla() -> None:
    gen = GeneradorRetornosParametrico()
    s = _supuestos("0.04", "0.12")
    a = gen.matriz_retornos(s, 20, 100, 99)
    b = gen.matriz_retornos(s, 20, 100, 99)
    assert (a == b).all()


def test_distinta_semilla_cambia() -> None:
    gen = GeneradorRetornosParametrico()
    s = _supuestos("0.04", "0.12")
    assert not (gen.matriz_retornos(s, 20, 100, 1) == gen.matriz_retornos(s, 20, 100, 2)).all()


def test_piso_retorno_real() -> None:
    gen = GeneradorRetornosParametrico()
    m = gen.matriz_retornos(_supuestos("0.0", "2.0"), 50, 200, 3)  # vol enorme
    assert (m >= -0.99).all()
