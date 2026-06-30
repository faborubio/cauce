"""Tests de la comparación RP vs RV: números comunes (C-24), herencia (C-26), riesgo (C-25)."""

from pathlib import Path

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.services.comparador_modalidades import comparar_modalidades
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion
from tests.infrastructure.conftest import construir_perfil

MODALIDADES = [Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA]


def _simulador(dir_mortalidad: Path) -> SimuladorMonteCarlo:
    return SimuladorMonteCarlo(
        AdaptadorMortalidad(dir_mortalidad, anio_base=2026),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )


def test_c26_herencia_separa_rp_de_rv(dir_mortalidad: Path) -> None:
    """El retiro programado deja herencia; la renta vitalicia no (C-26)."""
    sim = _simulador(dir_mortalidad)
    res = sim.comparar_modalidades(construir_perfil(), MODALIDADES, 2000)
    m = comparar_modalidades(res)
    assert m[Modalidad.RETIRO_PROGRAMADO].herencia_esperada_uf > 0
    assert m[Modalidad.RV_INMEDIATA].herencia_esperada_uf == 0


def test_c25_atribucion_de_riesgo(dir_mortalidad: Path) -> None:
    """La RV expone irrevocabilidad; el RP, longevidad (derivado de métricas, C-25)."""
    sim = _simulador(dir_mortalidad)
    m = comparar_modalidades(sim.comparar_modalidades(construir_perfil(), MODALIDADES, 2000))
    assert "Irrevocabilidad" in m[Modalidad.RV_INMEDIATA].riesgo_dominante
    assert "Longevidad" in m[Modalidad.RETIRO_PROGRAMADO].riesgo_dominante
    # la RV no se erosiona; el RP sí (mesada decae con la edad)
    assert m[Modalidad.RV_INMEDIATA].erosion_mediana >= 0.99
    assert m[Modalidad.RETIRO_PROGRAMADO].erosion_mediana < 1.0


def test_c24_numeros_comunes_reproducibles(dir_mortalidad: Path) -> None:
    """Misma semilla → misma comparación (sorteo común, C-24 + C-16)."""
    sim = _simulador(dir_mortalidad)
    perfil = construir_perfil(semilla=7)
    a = sim.comparar_modalidades(perfil, MODALIDADES, 500)
    b = sim.comparar_modalidades(perfil, MODALIDADES, 500)
    assert a[Modalidad.RETIRO_PROGRAMADO] == b[Modalidad.RETIRO_PROGRAMADO]


def test_rv_mesada_mayor_pero_sin_herencia(dir_mortalidad: Path) -> None:
    """Trade-off central: la RV parte con mesada >= al RP, pero sin herencia."""
    sim = _simulador(dir_mortalidad)
    m = comparar_modalidades(sim.comparar_modalidades(construir_perfil(), MODALIDADES, 2000))
    rv, rp = m[Modalidad.RV_INMEDIATA], m[Modalidad.RETIRO_PROGRAMADO]
    assert rv.mesada_inicial_uf >= rp.mesada_inicial_uf
    assert rv.herencia_esperada_uf < rp.herencia_esperada_uf
