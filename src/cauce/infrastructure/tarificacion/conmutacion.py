"""TarificadorConmutacion — tarificación paramétrica de la renta vitalicia (ADR, §11).

Calcula la mesada de una renta vitalicia inmediata por el **valor actuarial de una
anualidad vitalicia anticipada** (annuity-due), usando la curva de supervivencia de
cohorte y la tasa de interés técnica real:

    ä_x = Σ_{k>=0} v^k · S(x0+k)          con v = 1 / (1 + i)
    mesada_anual = saldo / ä_x

Es un **modelo paramétrico declarado**: NO replica ofertas reales de compañías (no
incluye margen comercial; ver C-27). La corrección se verifica contra el cálculo cerrado
(C-09). El piso/PGU (C-31) y el margen (C-27) son casos abiertos.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos

MESES_ANIO = 12


class TarificadorConmutacion:
    """Tarifica la renta vitalicia por conmutación. Implementa ``PuertoTarificador``."""

    def factor_anualidad(
        self,
        supervivencia: Mapping[Edad, float],
        tasa_tecnica: float,
    ) -> float:
        """ä_x: valor presente de 1 UF anual mientras la persona viva (anticipada)."""
        if tasa_tecnica <= -1:
            raise ValueError(f"Tasa técnica inválida: {tasa_tecnica}.")
        v = 1.0 / (1.0 + tasa_tecnica)
        x0 = min(e.anios for e in supervivencia)
        a = 0.0
        for edad, s in supervivencia.items():
            k = edad.anios - x0
            a += (v**k) * s
        if a <= 0:
            raise ValueError("Factor de anualidad no positivo (supervivencia degenerada).")
        return a

    def factores_por_edad(
        self,
        supervivencia: Mapping[Edad, float],
        tasa_tecnica: float,
    ) -> dict[int, float]:
        """ä_x para cada edad de la curva (anualidad condicional a estar vivo a esa edad).

        Reusado por el retiro programado, que recalcula la mesada cada año como
        ``saldo_t / ä_{edad_t}`` (C-07): una sola fuente de verdad del factor actuarial.
        """
        if tasa_tecnica <= -1:
            raise ValueError(f"Tasa técnica inválida: {tasa_tecnica}.")
        v = 1.0 / (1.0 + tasa_tecnica)
        edades = sorted(e.anios for e in supervivencia)
        s = {e: supervivencia[Edad(e)] for e in edades}
        factores: dict[int, float] = {}
        for i, x in enumerate(edades):
            sx = s[x]
            if sx <= 0:
                factores[x] = 1.0
                continue
            a = sum((v ** (y - x)) * s[y] / sx for y in edades[i:])
            factores[x] = a
        return factores

    def tarificar_renta_vitalicia(
        self,
        saldo: SaldoPrevisional,
        supuestos: Supuestos,
        supervivencia: Mapping[Edad, float],
    ) -> Mesada:
        """Mesada **mensual** vitalicia a la tasa de RV, neta del margen comercial (C-09/C-27/C-28).

        Con ``margen_rv`` la compañía retiene una fracción del saldo: la mesada se calcula
        sobre ``saldo * (1 - margen_rv)``. Con margen 0 es el valor actuarial justo.
        """
        a = self.factor_anualidad(supervivencia, float(supuestos.tasa_rv))
        saldo_efectivo = saldo.uf * (Decimal(1) - supuestos.margen_rv)
        mesada_anual = saldo_efectivo / Decimal(str(a))
        mensual = (mesada_anual / MESES_ANIO).quantize(Decimal("0.000001"))
        return Mesada(mensual)
