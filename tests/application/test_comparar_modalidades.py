"""Tests del caso de uso CompararModalidades: orquestación + rastro con disclaimer (C-21)."""

from decimal import Decimal
from pathlib import Path

from cauce.application.comparar_modalidades import CompararModalidades
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion

DIR_MORTALIDAD = Path(__file__).resolve().parents[2] / "data" / "mortalidad"
MODALIDADES = [Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA]


def _caso_uso() -> tuple[CompararModalidades, RepositorioSimulacionesMemoria]:
    repo = RepositorioSimulacionesMemoria()
    simulador = SimuladorMonteCarlo(
        AdaptadorMortalidad(DIR_MORTALIDAD, anio_base=2026),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )
    return CompararModalidades(simulador, repo), repo


def _perfil() -> PerfilPrevisional:
    return PerfilPrevisional(
        id="caso",
        version=1,
        persona=Persona(Edad(65), SaldoPrevisional(Decimal("3000")), Genero.MASCULINO),
        supuestos=Supuestos(Decimal("0.03"), Decimal("0.10"), Decimal("0.03"), Decimal("0.03")),
        modalidades_a_comparar=MODALIDADES,
        tabla_mortalidad="2020",
        semilla=42,
    )


def test_ejecuta_y_compara_ambas_modalidades() -> None:
    caso, _ = _caso_uso()
    res = caso.ejecutar(_perfil(), n_trayectorias=1000)
    assert set(res.metricas_por_modalidad) == set(MODALIDADES)
    assert res.simulacion_id.startswith("sim-")


def test_c21_rastro_lleva_disclaimer_y_se_persiste() -> None:
    caso, repo = _caso_uso()
    res = caso.ejecutar(_perfil(), n_trayectorias=500)
    assert "NO constituye asesoría" in res.rastro.disclaimer
    # el rastro es recuperable (reproducibilidad/auditoría, ADR-004)
    recuperado = repo.obtener(res.simulacion_id)
    assert recuperado.semilla == 42
    assert set(recuperado.riesgo_dominante) == set(MODALIDADES)
