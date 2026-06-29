"""Persona — el afiliado: edad, saldo, género, beneficiarios.

Nota de alcance (ADR-011): el MVP modela **mortalidad de una sola vida**. Los
``beneficiarios`` se registran pero la **pensión de sobrevivencia queda fuera del
MVP**; entran en fase 4 sin reescribir este contrato.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional


@dataclass(frozen=True, slots=True)
class Beneficiario:
    """Beneficiario de pensión de sobrevivencia. Reservado para fase 4 (ADR-011)."""

    edad: Edad
    genero: Genero


@dataclass(frozen=True, slots=True)
class Persona:
    """Afiliado al sistema de pensiones."""

    edad: Edad
    saldo: SaldoPrevisional
    genero: Genero
    beneficiarios: Sequence[Beneficiario] = field(default_factory=tuple)
