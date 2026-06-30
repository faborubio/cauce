"""Tests del tarificador: control cerrado de la anualidad (C-09)."""

from decimal import Decimal
from pathlib import Path

import pytest

from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion

# Supervivencia de juguete: vive 1 año seguro, 50% un 2º, muere al 3º.
TOY = {Edad(65): 1.0, Edad(66): 0.5, Edad(67): 0.0}


def _supuestos(tasa: str) -> Supuestos:
    return Supuestos(Decimal("0.03"), Decimal("0.10"), Decimal("0.03"), Decimal(tasa))


def test_c09_anualidad_cerrada_tasa_cero() -> None:
    """ä = 1 + 0.5 + 0 = 1.5 con tasa 0 (cálculo a mano)."""
    t = TarificadorConmutacion()
    assert t.factor_anualidad(TOY, 0.0) == pytest.approx(1.5)


def test_c09_anualidad_cerrada_con_descuento() -> None:
    """ä = 1 + 0.5/1.04 con tasa 4%."""
    t = TarificadorConmutacion()
    esperado = 1.0 + 0.5 / 1.04
    assert t.factor_anualidad(TOY, 0.04) == pytest.approx(esperado)


def test_c09_mesada_iguala_vp_del_saldo() -> None:
    """Propiedad actuarial: ä · mesada_anual = saldo (VP de los pagos = saldo)."""
    t = TarificadorConmutacion()
    saldo = SaldoPrevisional(Decimal("1500"))
    m = t.tarificar_renta_vitalicia(saldo, _supuestos("0"), TOY)
    mesada_anual = m.uf * 12
    a = Decimal(str(t.factor_anualidad(TOY, 0.0)))
    assert mesada_anual * a == pytest.approx(saldo.uf, abs=Decimal("0.01"))


def test_mayor_tasa_tecnica_mayor_mesada() -> None:
    t = TarificadorConmutacion()
    saldo = SaldoPrevisional(Decimal("1500"))
    baja = t.tarificar_renta_vitalicia(saldo, _supuestos("0.01"), TOY)
    alta = t.tarificar_renta_vitalicia(saldo, _supuestos("0.08"), TOY)
    assert alta.uf > baja.uf


def test_tasa_invalida() -> None:
    with pytest.raises(ValueError, match="Tasa técnica"):
        TarificadorConmutacion().factor_anualidad(TOY, -1.5)


def test_integracion_con_mortalidad_real(dir_mortalidad: Path) -> None:
    """Mesada plausible para un hombre de 65 con 3000 UF y tasa 3%."""
    ad = AdaptadorMortalidad(dir_mortalidad, anio_base=2026)
    persona = Persona(Edad(65), SaldoPrevisional(Decimal("3000")), Genero.MASCULINO)
    surv = ad.probabilidades_supervivencia(persona, "2020")
    m = TarificadorConmutacion().tarificar_renta_vitalicia(
        persona.saldo, _supuestos("0.03"), surv
    )
    assert isinstance(m, Mesada)
    assert Decimal("8") < m.uf < Decimal("25")  # UF/mes razonable
