"""RepositorioPerfiles — persistencia del PerfilPrevisional versionado e inmutable."""

from __future__ import annotations

from typing import Protocol

from cauce.domain.entities.perfil_previsional import PerfilPrevisional


class RepositorioPerfiles(Protocol):
    """Guarda y recupera perfiles por (id, version). Los perfiles nunca se mutan."""

    def guardar(self, perfil: PerfilPrevisional) -> None:
        """Persiste una versión de perfil. Falla si (id, version) ya existe."""
        ...

    def obtener(self, perfil_id: str, version: int) -> PerfilPrevisional:
        """Recupera una versión concreta del perfil. Lanza si no existe."""
        ...
