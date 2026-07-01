"""Explicabilidad de la SendaDePlaneo (glide path) — FASE 4.

Expone el **backbone por edad** de la senda (la fracción riesgosa año a año, sin el ajuste
por riqueza que depende de la trayectoria realizada). Sirve para mostrar y auditar la forma
del glide path; la componente por riqueza se observa en la simulación (ADR-015).
"""

from __future__ import annotations

from cauce.domain.entities.senda_planeo import SendaDePlaneo


def curva_glide_base(senda: SendaDePlaneo) -> tuple[tuple[int, float], ...]:
    """Fracción riesgosa por edad (backbone) de ``edad_inicial`` a ``edad_jubilacion``."""
    return tuple(
        (edad, senda.fraccion_base(edad))
        for edad in range(senda.edad_inicial, senda.edad_jubilacion + 1)
    )
