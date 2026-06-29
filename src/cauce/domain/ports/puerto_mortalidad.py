"""PuertoMortalidad — probabilidades de supervivencia por edad.

La implementación sirve tablas reguladas versionadas (NCG N°306: ``RV-M-2020``,
``CB-H-2020``, ...) aplicando ``q_x`` proyectado por los factores de mejoramiento
``AA_{x,t}`` (mortalidad dinámica) — ver ADR-003. La firma admite extensión a
**estado-de-hogar** (mortalidad conjunta) para la pensión de sobrevivencia de fase 4
sin reescribir el contrato (ADR-011).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad


class PuertoMortalidad(Protocol):
    """Curva de supervivencia de una persona según la tabla regulada vigente."""

    def probabilidades_supervivencia(
        self,
        persona: Persona,
        tabla_mortalidad: str,
    ) -> Mapping[Edad, float]:
        """Probabilidad de seguir vivo a cada edad futura (1.0 en la edad actual)."""
        ...
