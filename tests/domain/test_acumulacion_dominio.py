"""Tests del dominio de acumulación (Fase 4): glide path (ADR-015) y métricas puras."""

from decimal import Decimal

import pytest

from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.entities.trayectoria_riqueza import PuntoTrayectoria, TrayectoriaDeRiqueza
from cauce.domain.services.metricas_acumulacion import resumir_acumulacion
from cauce.domain.services.senda_planeo import curva_glide_base
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.saldo import SaldoPrevisional


def test_glide_base_interpola_por_edad() -> None:
    s = SendaDePlaneo("g", 25, 65, w_joven=0.9, w_final=0.1)
    assert s.fraccion_base(25) == 0.9
    assert s.fraccion_base(65) == 0.1
    assert abs(s.fraccion_base(45) - 0.5) < 1e-9  # punto medio del tramo


def test_glide_riqueza_derriskea_si_adelantado() -> None:
    # La tesis del paper (ADR-015): adelantado -> menos riesgo; atrasado -> más.
    s = SendaDePlaneo("g", 25, 65, w_joven=0.8, w_final=0.2, sensibilidad_riqueza=0.5)
    base = s.fraccion_base(45)
    adelantado = s.fraccion_riesgosa(45, saldo=150.0, referencia=100.0)
    atrasado = s.fraccion_riesgosa(45, saldo=50.0, referencia=100.0)
    assert adelantado < base < atrasado


def test_glide_sin_sensibilidad_es_solo_edad() -> None:
    s = SendaDePlaneo("g", 25, 65, w_joven=0.8, w_final=0.2, sensibilidad_riqueza=0.0)
    assert s.fraccion_riesgosa(45, 999.0, 1.0) == s.fraccion_base(45)


def test_glide_valida_edades_y_pesos() -> None:
    with pytest.raises(ValueError):
        SendaDePlaneo("g", 65, 25, 0.9, 0.2)  # edades invertidas
    with pytest.raises(ValueError):
        SendaDePlaneo("g", 25, 65, 1.5, 0.2)  # w fuera de [0, 1]


def test_curva_base_cubre_el_tramo() -> None:
    curva = curva_glide_base(SendaDePlaneo("g", 25, 30, 0.9, 0.4))
    assert curva[0] == (25, 0.9)
    assert curva[-1] == (30, 0.4)
    assert len(curva) == 6


def test_metricas_percentiles_ordenados() -> None:
    def tray(final: int) -> TrayectoriaDeRiqueza:
        return TrayectoriaDeRiqueza(
            (
                PuntoTrayectoria(Edad(25), SaldoPrevisional(Decimal("10"))),
                PuntoTrayectoria(Edad(26), SaldoPrevisional(Decimal(str(final)))),
            )
        )

    m = resumir_acumulacion([tray(x) for x in range(1, 101)])  # finales 1..100
    assert m.n_trayectorias == 100
    assert m.saldo_p10_uf < m.saldo_p50_uf < m.saldo_p90_uf
