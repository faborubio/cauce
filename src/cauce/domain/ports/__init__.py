"""Puertos del dominio — interfaces (``Protocol``) que la infraestructura implementa.

El dominio define *qué* necesita (generar trayectorias, estimar mortalidad, tarificar,
persistir); la infraestructura provee el *cómo* (NumPy, tablas reguladas, ORM). Esto
mantiene el dominio stdlib-only y testeable con stubs (ADR-010).
"""

from cauce.domain.ports.puerto_mortalidad import PuertoMortalidad
from cauce.domain.ports.puerto_retornos import PuertoRetornos
from cauce.domain.ports.puerto_simulador import PuertoSimulador
from cauce.domain.ports.puerto_tarificador import PuertoTarificador
from cauce.domain.ports.repositorio_perfiles import RepositorioPerfiles
from cauce.domain.ports.repositorio_simulaciones import RepositorioSimulaciones

__all__ = [
    "PuertoMortalidad",
    "PuertoRetornos",
    "PuertoSimulador",
    "PuertoTarificador",
    "RepositorioPerfiles",
    "RepositorioSimulaciones",
]
