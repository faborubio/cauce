"""Casos borde de Fase 2: fidelidad RV (C-27/C-28) y robustez/escenarios (C-06,C-11,C-14,C-17)."""

from pathlib import Path

import pytest

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.services.comparador_modalidades import comparar_modalidades
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion
from tests.infrastructure.conftest import construir_perfil

MODS = [Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA]


def _sim(dir_mortalidad: Path) -> SimuladorMonteCarlo:
    return SimuladorMonteCarlo(
        AdaptadorMortalidad(dir_mortalidad, anio_base=2026),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )


def _rv_mesada(sim: SimuladorMonteCarlo, **kw: str) -> float:
    res = sim.comparar_modalidades(construir_perfil(**kw), MODS, 300)
    return float(comparar_modalidades(res)[Modalidad.RV_INMEDIATA].mesada_inicial_uf)


def test_c27_margen_reduce_la_mesada_rv(dir_mortalidad: Path) -> None:
    """A mayor margen comercial, menor mesada de RV (C-27)."""
    sim = _sim(dir_mortalidad)
    sin = _rv_mesada(sim, margen_rv="0")
    con = _rv_mesada(sim, margen_rv="0.05")
    assert con < sin
    assert con == pytest.approx(sin * 0.95, rel=1e-6)  # retiene exactamente esa fracción


def test_c28_tasa_rv_distinta_separa_rp_de_rv(dir_mortalidad: Path) -> None:
    """Con tasa de RV > tasa técnica del RP, RP y RV ya no parten con la misma mesada (C-28)."""
    sim = _sim(dir_mortalidad)
    res = sim.comparar_modalidades(
        construir_perfil(tasa_descuento="0.03", tasa_rv="0.05"), MODS, 300
    )
    m = comparar_modalidades(res)
    rv = m[Modalidad.RV_INMEDIATA].mesada_inicial_uf
    rp = m[Modalidad.RETIRO_PROGRAMADO].mesada_inicial_uf
    assert rv != rp


def test_c06_saldo_minimo_no_revienta(dir_mortalidad: Path) -> None:
    """Saldo ínfimo: la comparación corre sin dividir por cero, con métricas ~0."""
    sim = _sim(dir_mortalidad)
    m = comparar_modalidades(sim.comparar_modalidades(construir_perfil(saldo="1"), MODS, 200))
    assert m[Modalidad.RV_INMEDIATA].mesada_inicial_uf >= 0
    assert m[Modalidad.RETIRO_PROGRAMADO].herencia_esperada_uf >= 0


def test_c17_una_sola_trayectoria(dir_mortalidad: Path) -> None:
    """n=1 no degenera el cálculo de métricas."""
    sim = _sim(dir_mortalidad)
    m = comparar_modalidades(sim.comparar_modalidades(construir_perfil(), MODS, 1))
    assert m[Modalidad.RV_INMEDIATA].n_trayectorias == 1


def test_c11_cola_de_longevidad(dir_mortalidad: Path) -> None:
    """Quien vive mucho agota el RP: existen trayectorias con herencia ~0 y pensión erosionada."""
    sim = _sim(dir_mortalidad)
    rp = sim.comparar_modalidades(construir_perfil(), MODS, 3000)[Modalidad.RETIRO_PROGRAMADO]
    herencias = sorted(float(r.herencia.uf) for r in rp)
    erosiones = sorted(r.erosion for r in rp)
    assert herencias[0] < 100  # la cola larga deja casi nada de herencia
    assert erosiones[0] < 0.3  # y la pensión cae fuerte


def test_c14_retornos_negativos_erosionan_mas_sin_saldo_negativo(dir_mortalidad: Path) -> None:
    """Retorno real negativo: menos herencia que con retorno positivo; nunca saldo negativo."""
    sim = _sim(dir_mortalidad)
    neg = comparar_modalidades(
        sim.comparar_modalidades(construir_perfil(retorno="-0.04"), MODS, 2000)
    )[Modalidad.RETIRO_PROGRAMADO]
    pos = comparar_modalidades(
        sim.comparar_modalidades(construir_perfil(retorno="0.04"), MODS, 2000)
    )[Modalidad.RETIRO_PROGRAMADO]
    assert neg.herencia_esperada_uf < pos.herencia_esperada_uf
    assert neg.herencia_esperada_uf >= 0  # SaldoPrevisional prohíbe negativos
