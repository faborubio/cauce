"""Entidades del dominio: tienen identidad y/o son el estado central del modelo."""

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.entities.rastro import RastroSimulacion
from cauce.domain.entities.trayectoria_riqueza import PuntoTrayectoria, TrayectoriaDeRiqueza

__all__ = [
    "Modalidad",
    "PerfilPrevisional",
    "Persona",
    "PuntoTrayectoria",
    "RastroSimulacion",
    "TrayectoriaDeRiqueza",
]
