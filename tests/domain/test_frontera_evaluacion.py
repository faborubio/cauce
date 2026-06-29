"""Smoke de la frontera generar/evaluar (ADR-010).

Un stub *puro* de ``PuertoSimulador`` (sin NumPy) genera trayectorias sintéticas
deterministas; el servicio de dominio las evalúa. Demuestra que el núcleo de evaluación
es testeable sin infraestructura.
"""

from decimal import Decimal

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.trayectoria_riqueza import (
    PuntoTrayectoria,
    TrayectoriaDeRiqueza,
)
from cauce.domain.services.comparador_modalidades import comparar
from cauce.domain.services.metricas import calcular_metricas
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.saldo import SaldoPrevisional


def _trayectoria(saldo_final: int, agota: bool = False) -> TrayectoriaDeRiqueza:
    medio = Decimal("0") if agota else Decimal(saldo_final) / 2
    return TrayectoriaDeRiqueza(
        puntos=(
            PuntoTrayectoria(Edad(65), SaldoPrevisional(Decimal("1000"))),
            PuntoTrayectoria(Edad(80), SaldoPrevisional(medio)),
            PuntoTrayectoria(Edad(95), SaldoPrevisional(Decimal(saldo_final))),
        )
    )


def test_metricas_detectan_agotamiento() -> None:
    trayectorias = [_trayectoria(0, agota=True), _trayectoria(500), _trayectoria(900)]
    m = calcular_metricas(trayectorias)
    assert m.n_trayectorias == 3
    assert m.probabilidad_agotamiento == 1 / 3
    assert m.saldo_final_p10_uf <= m.saldo_final_p90_uf


def test_comparar_evalua_por_modalidad() -> None:
    comp = comparar(
        {
            Modalidad.RETIRO_PROGRAMADO: [_trayectoria(0, agota=True), _trayectoria(300)],
            Modalidad.RV_INMEDIATA: [_trayectoria(200), _trayectoria(200)],
        }
    )
    # El retiro programado expone riesgo de longevidad (agotamiento > 0); la RV no.
    assert comp.metricas_por_modalidad[Modalidad.RETIRO_PROGRAMADO].probabilidad_agotamiento > 0
    assert comp.metricas_por_modalidad[Modalidad.RV_INMEDIATA].probabilidad_agotamiento == 0
