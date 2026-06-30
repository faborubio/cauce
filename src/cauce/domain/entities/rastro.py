"""RastroSimulacion — el snapshot que hace una comparación reproducible y auditable.

Equivalente al "rastro" de Veredicto con peso regulatorio extra (SAD §8, ADR-004/005):
registra el modelo, la tabla de mortalidad as-seen, la semilla y la **atribución de
qué riesgo domina** cada modalidad. Sin él, la comparación no es reconstruible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from cauce.domain.entities.modalidad import Modalidad

# Disclaimer de no-asesoría — obligatorio en cada salida (ADR-009/013, §8).
# Vive en el dominio para que TODOS los adaptadores (REST, MCP, Web) lo hereden idéntico.
# Incluye el encuadre paramétrico: los montos son ilustrativos, no la oferta real (ADR-014).
DISCLAIMER_NO_ASESORIA = (
    "Simulador educativo/ilustrativo. NO constituye asesoría previsional ni "
    "recomendación personalizada. Los montos son ilustrativos: se calculan con supuestos "
    "calibrados a promedios de mercado regulados, no son la oferta real de su AFP o "
    "compañía de seguros. La cifra exacta depende de las ofertas del SCOMP para su caso. "
    "La elección de modalidad es irrevocable y materia de procesos regulados: consulte a "
    "su AFP, a un asesor previsional registrado y al SCOMP antes de decidir."
)


@dataclass(frozen=True, slots=True)
class RastroSimulacion:
    """Linaje completo de una simulación: supuestos, mortalidad, semilla, atribución."""

    perfil_id: str
    perfil_version: int
    tabla_mortalidad: str
    semilla: int
    n_trayectorias: int
    riesgo_dominante: Mapping[Modalidad, str]
    disclaimer: str = DISCLAIMER_NO_ASESORIA
