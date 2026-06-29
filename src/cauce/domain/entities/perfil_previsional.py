"""PerfilPrevisional — persona + supuestos, UNIDAD ATÓMICA versionada e inmutable.

Como la ``Politica`` de Veredicto (SAD §5.2): el perfil lleva la semántica y el motor
es estable. Reproducir una comparación = fijar ``(perfil, tabla_mortalidad, semilla)``
(ADR-006, ADR-008).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.supuestos import Supuestos


@dataclass(frozen=True, slots=True)
class PerfilPrevisional:
    """Persona + supuestos + qué comparar + qué tabla + semilla. Inmutable y versionado."""

    id: str
    version: int
    persona: Persona
    supuestos: Supuestos
    modalidades_a_comparar: Sequence[Modalidad]
    tabla_mortalidad: str  # id_version de la tabla regulada (p. ej. "RV-M-2020") o sintética
    semilla: int  # semilla Monte Carlo determinista

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("La versión del perfil debe ser >= 1.")
        if not self.modalidades_a_comparar:
            raise ValueError("Debe indicarse al menos una modalidad a comparar.")
