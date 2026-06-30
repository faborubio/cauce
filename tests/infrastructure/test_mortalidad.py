"""Tests del adaptador de mortalidad: proyección AA (C-01), rangos (C-02), selección (C-03)."""

import itertools
from decimal import Decimal
from pathlib import Path

import pytest

from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.mortalidad.cargador import cargar_tabla


def test_c01_proyeccion_contra_ejemplo_oficial(dir_mortalidad: Path) -> None:
    """Oráculo oficial: q_{65,2022} CB-H-2020 = 0.008526031 (Anexo N°10)."""
    tabla = cargar_tabla(dir_mortalidad / "cb_2020_hombres.csv")
    assert tabla.qx_proyectada(65, 2022) == pytest.approx(0.008526031, abs=1e-9)


def test_proyeccion_en_anio_base_es_qx_base(dir_mortalidad: Path) -> None:
    tabla = cargar_tabla(dir_mortalidad / "cb_2020_hombres.csv")
    assert tabla.qx_proyectada(65, 2020) == tabla.qx_base(65)
    # el mejoramiento solo reduce la mortalidad
    assert tabla.qx_proyectada(65, 2030) < tabla.qx_base(65)


def test_aa_constante_desde_2036(dir_mortalidad: Path) -> None:
    tabla = cargar_tabla(dir_mortalidad / "rv_2020_mujeres.csv")
    # más allá de 2036 sigue mejorando (factor constante > 0), nunca sube
    assert tabla.qx_proyectada(70, 2050) < tabla.qx_proyectada(70, 2036)


def test_c02_edad_fuera_de_rango(dir_mortalidad: Path) -> None:
    tabla = cargar_tabla(dir_mortalidad / "rv_2020_mujeres.csv")  # parte en 20
    with pytest.raises(ValueError, match="fuera del rango"):
        tabla.qx_base(18)


def test_c03_supervivencia_decrece_y_mujeres_viven_mas(dir_mortalidad: Path) -> None:
    ad = AdaptadorMortalidad(dir_mortalidad, anio_base=2026)
    h = Persona(Edad(65), SaldoPrevisional(Decimal("1000")), Genero.MASCULINO)
    m = Persona(Edad(65), SaldoPrevisional(Decimal("1000")), Genero.FEMENINO)
    sh = ad.probabilidades_supervivencia(h, "2020")
    sm = ad.probabilidades_supervivencia(m, "2020")
    # S(65)=1 y decrece monótonamente
    assert sh[Edad(65)] == pytest.approx(1.0)
    valores = [sh[Edad(x)] for x in range(65, 111)]
    assert all(a >= b for a, b in itertools.pairwise(valores))
    # selección por sexo: la mujer sobrevive más a los 90 (C-03)
    assert sm[Edad(90)] > sh[Edad(90)]


def test_esperanza_vida_realista(dir_mortalidad: Path) -> None:
    ad = AdaptadorMortalidad(dir_mortalidad, anio_base=2026)
    h = Persona(Edad(65), SaldoPrevisional(Decimal("1000")), Genero.MASCULINO)
    e = ad.esperanza_vida_curtate(h)
    assert 18 < e < 26  # rentista hombre a los 65 en Chile
