"""Tasas reguladas para calibrar los supuestos por defecto (ADR-014).

Valores públicos de la **Superintendencia de Pensiones (SP)**. Son **promedios de mercado**,
no ofertas personales del SCOMP: anclan la *magnitud* de la mesada al período, pero la cifra
exacta de cada persona la entrega su AFP/SCOMP (ver disclaimer, ADR-013).

Cada tasa es **un solo número** que se actualiza a mano; al actualizar, cambiar también la
fecha en la constante ``_FUENTE`` correspondiente:

- **TITRP** (retiro programado): actualización cuatrimestral (~3 veces al año).
- **RV media Vejez** (renta vitalicia): serie mensual.
"""

from __future__ import annotations

from decimal import Decimal

# Tasa de Interés Técnica del Retiro Programado (TITRP) → `Supuestos.tasa_descuento`.
# Fuente: SP — https://www.spensiones.cl/apps/tasas/tasdescto.php
TASA_DESCUENTO_RP = Decimal("0.0331")
TASA_DESCUENTO_RP_FUENTE = "SP TITRP, vigente enero 2026 (tasdescto.php)"

# Tasa de interés media de las Rentas Vitalicias contratadas, pensión de Vejez,
# total del mercado → `Supuestos.tasa_rv`.
# Fuente: SP (origen CMF) — https://www.spensiones.cl/apps/tasas/tasasRentasVitalicias.php
TASA_RV_VEJEZ = Decimal("0.0284")
TASA_RV_VEJEZ_FUENTE = "SP/CMF RV media Vejez, mayo 2026 (tasasRentasVitalicias.php)"
