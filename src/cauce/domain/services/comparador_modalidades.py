"""ComparadorModalidades — contrasta modalidades y atribuye el riesgo dominante (puro).

Recibe, por modalidad, los `ResultadoTrayectoria` ya simulados (frontera ADR-010) y los
agrega en métricas comparables en sus tres ejes: **pensión** (nivel), **erosión** de la
pensión (riesgo de longevidad, C-25) y **herencia** (C-26). La atribución del riesgo
dominante se **deriva de las métricas**, no se etiqueta a mano.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, median

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.resultado_trayectoria import ResultadoTrayectoria

UMBRAL_EROSION = 0.85  # bajo este nivel, la pensión se considera materialmente erosionada
UMBRAL_ESTABLE = 0.99  # sobre este nivel, la pensión se considera estable


@dataclass(frozen=True, slots=True)
class MetricasModalidad:
    """Resumen comparable de una modalidad sobre el sample simulado."""

    n_trayectorias: int
    mesada_inicial_uf: Decimal
    herencia_esperada_uf: Decimal
    herencia_p50_uf: Decimal
    erosion_mediana: float  # mesada_final/inicial mediana: 1.0 estable, < 1 erosionada
    riesgo_dominante: str


def atribuir_riesgo(herencia_esperada: Decimal, erosion_mediana: float) -> str:
    """Deriva el riesgo dominante de las métricas (C-25), no de una etiqueta fija."""
    if herencia_esperada == 0 and erosion_mediana >= UMBRAL_ESTABLE:
        return (
            "Irrevocabilidad: pensión fija de por vida, sin herencia; "
            "traspasa el riesgo de longevidad a la aseguradora."
        )
    if erosion_mediana < UMBRAL_EROSION:
        return (
            "Longevidad: la pensión se erosiona si vive muchos años; "
            "mantiene propiedad del saldo y deja herencia."
        )
    return "Mixto: comparte riesgo de mercado y longevidad, con herencia parcial."


def _metricas(resultados: Sequence[ResultadoTrayectoria]) -> MetricasModalidad:
    if not resultados:
        raise ValueError("Se requiere al menos una trayectoria.")
    herencias = [r.herencia.uf for r in resultados]
    erosiones = [r.erosion for r in resultados]
    herencia_esperada = Decimal(str(mean(herencias)))
    erosion_med = median(erosiones)
    return MetricasModalidad(
        n_trayectorias=len(resultados),
        mesada_inicial_uf=resultados[0].mesada_inicial.uf,
        herencia_esperada_uf=herencia_esperada,
        herencia_p50_uf=Decimal(str(median(herencias))),
        erosion_mediana=erosion_med,
        riesgo_dominante=atribuir_riesgo(herencia_esperada, erosion_med),
    )


def comparar_modalidades(
    resultados_por_modalidad: Mapping[Modalidad, Sequence[ResultadoTrayectoria]],
) -> dict[Modalidad, MetricasModalidad]:
    """Agrega cada modalidad en sus métricas comparables. Puro, sin efectos."""
    if not resultados_por_modalidad:
        raise ValueError("Debe compararse al menos una modalidad.")
    return {
        modalidad: _metricas(resultados)
        for modalidad, resultados in resultados_por_modalidad.items()
    }
