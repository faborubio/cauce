"""Tests del SimuladorMonteCarlo: reproducibilidad (C-16), longevidad y horizonte (C-04)."""

from pathlib import Path

import pytest

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.services.metricas import calcular_metricas
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from tests.infrastructure.conftest import construir_perfil


def _simulador(dir_mortalidad: Path) -> SimuladorMonteCarlo:
    return SimuladorMonteCarlo(
        AdaptadorMortalidad(dir_mortalidad, anio_base=2026),
        GeneradorRetornosParametrico(),
    )


def test_c16_reproducibilidad(dir_mortalidad: Path) -> None:
    """Misma (perfil, tabla, semilla) → trayectorias idénticas (ADR-006)."""
    sim = _simulador(dir_mortalidad)
    perfil = construir_perfil(semilla=123)
    a = sim.generar(perfil, Modalidad.RETIRO_PROGRAMADO, 300)
    b = sim.generar(perfil, Modalidad.RETIRO_PROGRAMADO, 300)
    assert [t.puntos for t in a] == [t.puntos for t in b]


def test_semilla_distinta_cambia(dir_mortalidad: Path) -> None:
    sim = _simulador(dir_mortalidad)
    a = sim.generar(construir_perfil(semilla=1), Modalidad.RETIRO_PROGRAMADO, 300)
    b = sim.generar(construir_perfil(semilla=2), Modalidad.RETIRO_PROGRAMADO, 300)
    assert [t.puntos for t in a] != [t.puntos for t in b]


def test_riesgo_de_longevidad(dir_mortalidad: Path) -> None:
    """Menor retorno → mayor probabilidad de agotar el saldo antes de morir."""
    sim = _simulador(dir_mortalidad)
    baja = calcular_metricas(
        sim.generar(construir_perfil(retorno="-0.02", volatilidad="0.05"),
                    Modalidad.RETIRO_PROGRAMADO, 2000)
    )
    alta = calcular_metricas(
        sim.generar(construir_perfil(retorno="0.06", volatilidad="0.05"),
                    Modalidad.RETIRO_PROGRAMADO, 2000)
    )
    assert baja.probabilidad_agotamiento > alta.probabilidad_agotamiento


def test_c04_trayectorias_terminan_a_lo_sumo_en_110(dir_mortalidad: Path) -> None:
    sim = _simulador(dir_mortalidad)
    tr = sim.generar(construir_perfil(), Modalidad.RETIRO_PROGRAMADO, 1000)
    assert all(t.edad_inicial.anios == 65 for t in tr)
    assert all(t.edad_final.anios <= 110 for t in tr)
    assert max(t.edad_final.anios for t in tr) > 65  # alguien vive más de un año


def test_modalidad_no_soportada_en_fase1(dir_mortalidad: Path) -> None:
    sim = _simulador(dir_mortalidad)
    with pytest.raises(NotImplementedError, match="Fase 2"):
        sim.generar(construir_perfil(), Modalidad.RV_INMEDIATA, 10)
