"""Caso de uso CompararModalidades (MVP) — orquesta los puertos del dominio.

Sin NumPy ni adaptadores concretos (blindado por import-linter): pide la simulación al
`PuertoSimulador`, agrega con el comparador puro, arma el `RastroSimulacion` (que **siempre**
lleva el disclaimer de no-asesoría, C-21/ADR-009) y lo persiste para reproducir (ADR-004).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.rastro import RastroSimulacion
from cauce.domain.ports.puerto_simulador import PuertoSimulador
from cauce.domain.ports.repositorio_simulaciones import RepositorioSimulaciones
from cauce.domain.services.comparador_modalidades import MetricasModalidad, comparar_modalidades


@dataclass(frozen=True, slots=True)
class ResultadoComparacion:
    """Salida del caso de uso: métricas por modalidad + rastro auditable (con disclaimer)."""

    metricas_por_modalidad: Mapping[Modalidad, MetricasModalidad]
    simulacion_id: str
    rastro: RastroSimulacion


class CompararModalidades:
    """Compara las modalidades del perfil y persiste el rastro reproducible."""

    def __init__(
        self,
        simulador: PuertoSimulador,
        repositorio: RepositorioSimulaciones,
    ) -> None:
        self._simulador = simulador
        self._repositorio = repositorio

    def ejecutar(
        self,
        perfil: PerfilPrevisional,
        n_trayectorias: int = 10_000,
    ) -> ResultadoComparacion:
        resultados = self._simulador.comparar_modalidades(
            perfil, list(perfil.modalidades_a_comparar), n_trayectorias
        )
        metricas = comparar_modalidades(resultados)
        rastro = RastroSimulacion(
            perfil_id=perfil.id,
            perfil_version=perfil.version,
            tabla_mortalidad=perfil.tabla_mortalidad,
            semilla=perfil.semilla,
            n_trayectorias=n_trayectorias,
            riesgo_dominante={mod: m.riesgo_dominante for mod, m in metricas.items()},
        )
        simulacion_id = self._repositorio.guardar(rastro)
        return ResultadoComparacion(metricas, simulacion_id, rastro)
