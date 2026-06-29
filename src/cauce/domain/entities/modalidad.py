"""Modalidad — las modalidades de pensión del SCOMP (des-acumulación, MVP).

Cada modalidad concentra un **riesgo dominante** distinto (SAD §8); la atribución
de ese riesgo es lo que explica la comparación, no solo el monto de la mesada.
"""

from enum import Enum


class Modalidad(Enum):
    """Modalidades de pensión reguladas (SCOMP)."""

    RETIRO_PROGRAMADO = "retiro_programado"
    """Paga la AFP; mantiene propiedad y posible herencia. Riesgo: longevidad."""

    RV_INMEDIATA = "rv_inmediata"
    """Renta vitalicia inmediata; fija de por vida, sin herencia. Riesgo: irrevocabilidad."""

    RT_RV_DIFERIDA = "rt_rv_diferida"
    """Renta temporal + renta vitalicia diferida. Riesgo: mercado en el tramo temporal."""

    RV_INM_CON_RP = "rv_inm_con_rp"
    """Renta vitalicia inmediata combinada con retiro programado. Riesgo: mixto."""
