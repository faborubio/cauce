"""Tests del caso de uso SimularCicloDeVida (Fase 4): continuidad acumulación→des-acumulación."""

from decimal import Decimal
from pathlib import Path

from cauce.application.comparar_modalidades import CompararModalidades
from cauce.application.proyectar_acumulacion import ProyectarAcumulacion
from cauce.application.simular_ciclo_de_vida import SimularCicloDeVida
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.domain.value_objects.supuestos_acumulacion import SupuestosAcumulacion
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.acumulacion import SimuladorAcumulacion
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion

DIR = Path(__file__).resolve().parents[2] / "data" / "mortalidad"
MODS = [Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA]
SUP_DESAC = Supuestos(
    Decimal("0.03"), Decimal("0.10"), Decimal("0.03"), Decimal("0.0331"), Decimal("0.0284")
)


def _ciclo() -> SimularCicloDeVida:
    simulador = SimuladorMonteCarlo(
        AdaptadorMortalidad(DIR, anio_base=2026),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )
    comparar = CompararModalidades(simulador, RepositorioSimulacionesMemoria())
    return SimularCicloDeVida(ProyectarAcumulacion(SimuladorAcumulacion()), comparar)


def _perfil() -> PerfilAcumulacion:
    senda = SendaDePlaneo("g", 25, 65, 0.9, 0.2, 0.5)
    return PerfilAcumulacion(
        id="acc",
        version=1,
        genero=Genero.MASCULINO,
        edad_inicial=Edad(25),
        edad_jubilacion=Edad(65),
        saldo_inicial=SaldoPrevisional(Decimal("50")),
        cotizacion_anual=SaldoPrevisional(Decimal("60")),
        senda=senda,
        supuestos=SupuestosAcumulacion(Decimal("0.05"), Decimal("0.16"), Decimal("0.01")),
        semilla=42,
    )


def test_ciclo_produce_tres_percentiles_y_disclaimer() -> None:
    res = _ciclo().ejecutar(
        _perfil(), SUP_DESAC, "2020", MODS, n_acumulacion=1500, n_desacumulacion=400
    )
    assert [p.percentil for p in res.pensiones] == ["p10", "p50", "p90"]
    assert "NO constituye asesoría" in res.disclaimer


def test_mas_saldo_produce_mas_pension() -> None:
    res = _ciclo().ejecutar(
        _perfil(), SUP_DESAC, "2020", MODS, n_acumulacion=1500, n_desacumulacion=400
    )
    saldos = {p.percentil: p.saldo_uf for p in res.pensiones}
    assert saldos["p10"] <= saldos["p50"] <= saldos["p90"]

    def mesada_rp(percentil: str) -> Decimal:
        pension = next(p for p in res.pensiones if p.percentil == percentil)
        return next(
            m.mesada_inicial_uf
            for mod, m in pension.comparacion.metricas_por_modalidad.items()
            if mod == Modalidad.RETIRO_PROGRAMADO
        )

    assert mesada_rp("p10") < mesada_rp("p50") < mesada_rp("p90")
