"""Género — relevante para la tabla de mortalidad y la compensación por esperanza de vida.

En Chile la asignación de tabla por sexo es asimétrica (NCG N°306, ver SAD ADR-003):
vejez → ``CB-H-2020`` (hombres) / ``RV-M-2020`` (mujeres). El dominio solo conoce el
eje sexo; *qué tabla* le corresponde es decisión del adaptador de mortalidad.
"""

from enum import Enum


class Genero(Enum):
    """Sexo registral usado para seleccionar la tabla de mortalidad regulada."""

    FEMENINO = "F"
    MASCULINO = "M"
