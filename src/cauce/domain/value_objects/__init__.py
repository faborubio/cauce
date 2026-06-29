"""Value objects del dominio: inmutables, validados, sin identidad propia."""

from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos

__all__ = ["Edad", "Genero", "Mesada", "SaldoPrevisional", "Supuestos"]
