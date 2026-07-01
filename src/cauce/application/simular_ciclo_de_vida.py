"""Caso de uso SimularCicloDeVida (Fase 4) — el ciclo completo: de la cotización a la mesada.

Une las dos mitades sobre el mismo núcleo (ADR-001, SAD §6.2): proyecta la acumulación,
toma tres saldos representativos a la jubilación (p10/p50/p90) y **compara las modalidades
para cada uno**, entregando un **rango de pensiones** según cómo le vaya al ahorro. Es el
"momento wow" del portafolio y no reescribe ni la acumulación ni la des-acumulación.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from cauce.application.comparar_modalidades import CompararModalidades, ResultadoComparacion
from cauce.application.proyectar_acumulacion import ProyectarAcumulacion
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.entities.rastro import DISCLAIMER_NO_ASESORIA
from cauce.domain.services.metricas_acumulacion import MetricasAcumulacion
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos


@dataclass(frozen=True, slots=True)
class PensionPorPercentil:
    """La pensión que produciría un saldo dado (un percentil de la acumulación)."""

    percentil: str  # "p10" | "p50" | "p90"
    saldo_uf: Decimal
    comparacion: ResultadoComparacion


@dataclass(frozen=True, slots=True)
class ResultadoCicloDeVida:
    """Acumulación (distribución del saldo) + pensión por percentil + disclaimer."""

    acumulacion: MetricasAcumulacion
    pensiones: Sequence[PensionPorPercentil]
    disclaimer: str


class SimularCicloDeVida:
    """Proyecta la acumulación y compara modalidades sobre p10/p50/p90 del saldo final."""

    def __init__(
        self, proyectar: ProyectarAcumulacion, comparar: CompararModalidades
    ) -> None:
        self._proyectar = proyectar
        self._comparar = comparar

    def ejecutar(
        self,
        perfil_acumulacion: PerfilAcumulacion,
        supuestos_desacumulacion: Supuestos,
        tabla_mortalidad: str,
        modalidades: Sequence[Modalidad],
        n_acumulacion: int = 10_000,
        n_desacumulacion: int = 5_000,
        semilla_desacumulacion: int = 42,
    ) -> ResultadoCicloDeVida:
        acum = self._proyectar.ejecutar(perfil_acumulacion, n_acumulacion)
        met = acum.metricas

        pensiones: list[PensionPorPercentil] = []
        for etiqueta, saldo in (
            ("p10", met.saldo_p10_uf),
            ("p50", met.saldo_p50_uf),
            ("p90", met.saldo_p90_uf),
        ):
            persona = Persona(
                perfil_acumulacion.edad_jubilacion,
                SaldoPrevisional(saldo),
                perfil_acumulacion.genero,
            )
            perfil = PerfilPrevisional(
                id=f"ciclo-{etiqueta}",
                version=1,
                persona=persona,
                supuestos=supuestos_desacumulacion,
                modalidades_a_comparar=list(modalidades),
                tabla_mortalidad=tabla_mortalidad,
                semilla=semilla_desacumulacion,
            )
            comparacion = self._comparar.ejecutar(perfil, n_desacumulacion)
            pensiones.append(PensionPorPercentil(etiqueta, saldo, comparacion))

        return ResultadoCicloDeVida(met, tuple(pensiones), DISCLAIMER_NO_ASESORIA)
