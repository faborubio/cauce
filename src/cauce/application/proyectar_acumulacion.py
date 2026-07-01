"""Caso de uso ProyectarAcumulacion (Fase 4) — orquesta el simulador de acumulación.

Pide las trayectorias al ``PuertoSimuladorAcumulacion`` (sin NumPy ni adaptadores, blindado
por import-linter), las resume con el servicio puro y adjunta el disclaimer de no-asesoría
(C-21/ADR-009/013). Es la mitad "de entrada" del ciclo de vida (ADR-001, SAD §6.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.rastro import DISCLAIMER_NO_ASESORIA
from cauce.domain.ports.puerto_simulador_acumulacion import PuertoSimuladorAcumulacion
from cauce.domain.services.metricas_acumulacion import MetricasAcumulacion, resumir_acumulacion


@dataclass(frozen=True, slots=True)
class ResultadoAcumulacion:
    """Distribución del saldo a la jubilación + disclaimer."""

    metricas: MetricasAcumulacion
    disclaimer: str


class ProyectarAcumulacion:
    """Proyecta la acumulación de un perfil y resume el saldo a la jubilación."""

    def __init__(self, simulador: PuertoSimuladorAcumulacion) -> None:
        self._simulador = simulador

    def ejecutar(
        self, perfil: PerfilAcumulacion, n_trayectorias: int = 10_000
    ) -> ResultadoAcumulacion:
        trayectorias = self._simulador.generar(perfil, n_trayectorias)
        metricas = resumir_acumulacion(trayectorias)
        return ResultadoAcumulacion(metricas, DISCLAIMER_NO_ASESORIA)
