"""Tests del SimuladorAcumulacion (Fase 4): determinismo, horizonte y crecimiento."""

from decimal import Decimal

import pytest

from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos_acumulacion import SupuestosAcumulacion
from cauce.infrastructure.simulacion.acumulacion import SimuladorAcumulacion


def _perfil(semilla: int = 42, sensibilidad: float = 0.5) -> PerfilAcumulacion:
    senda = SendaDePlaneo("g", 25, 65, 0.9, 0.2, sensibilidad)
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
        semilla=semilla,
    )


def test_determinismo_misma_semilla() -> None:
    sim = SimuladorAcumulacion()
    a = sim.generar(_perfil(semilla=7), 200)
    b = sim.generar(_perfil(semilla=7), 200)
    assert [t.saldo_final.uf for t in a] == [t.saldo_final.uf for t in b]


def test_semillas_distintas_difieren() -> None:
    sim = SimuladorAcumulacion()
    a = sim.generar(_perfil(semilla=1), 200)
    b = sim.generar(_perfil(semilla=2), 200)
    assert [t.saldo_final.uf for t in a] != [t.saldo_final.uf for t in b]


def test_trayectorias_cubren_el_horizonte_y_crecen() -> None:
    trays = SimuladorAcumulacion().generar(_perfil(), 300)
    t0 = trays[0]
    assert t0.edad_inicial == Edad(25)
    assert t0.edad_final == Edad(65)
    assert len(t0.puntos) == 41  # de 25 a 65 inclusive
    finales = sorted(float(t.saldo_final.uf) for t in trays)
    mediana = finales[len(finales) // 2]
    assert mediana > 50.0  # cotización + retorno esperado positivo hacen crecer el saldo


def test_n_trayectorias_invalido() -> None:
    with pytest.raises(ValueError):
        SimuladorAcumulacion().generar(_perfil(), 0)
