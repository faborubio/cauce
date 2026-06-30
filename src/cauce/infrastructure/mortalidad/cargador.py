"""Carga de las tablas reguladas 2020 y proyección dinámica de la mortalidad.

Implementa la fórmula oficial de los **factores de mejoramiento bidimensionales**
(Compendio de Normas del Sistema de Pensiones, Libro III, Título X, Anexo N°10):

    q_{x, anio} = q_{x,2020} * producto_{t=2021..anio} (1 - AA_{x,t})

con ``AA`` constante desde 2036. Verificada contra el ejemplo oficial
(``q_{65,2022}`` CB-H-2020 = 0.008526031). Resuelve el caso borde **C-01**.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ANIO_BASE = 2020  # las tablas 2020 son año base; la proyección arranca en 2021
ANIO_AA_CONSTANTE = 2036  # desde 2036 el factor de mejoramiento se mantiene constante


@dataclass(frozen=True, slots=True)
class TablaMortalidad:
    """Una tabla regulada: ``q_x`` base + matriz de mejoramiento ``AA_{x,t}``."""

    nombre: str
    edad_min: int
    edad_max: int
    _qx: dict[int, float]
    _aa: dict[int, dict[int, float]]  # edad -> {año: AA}

    def qx_base(self, edad: int) -> float:
        """``q_x`` de la tabla 2020 (sin proyectar)."""
        self._validar_edad(edad)
        return self._qx[edad]

    def qx_proyectada(self, edad: int, anio: int) -> float:
        """``q_{x, año}`` aplicando los factores de mejoramiento acumulados (C-01)."""
        self._validar_edad(edad)
        qx = self._qx[edad]
        if anio <= ANIO_BASE:
            return qx
        factores = self._aa[edad]
        producto = 1.0
        for t in range(ANIO_BASE + 1, anio + 1):
            # desde 2036 el factor se mantiene en el valor de 2036
            aa = factores[min(t, ANIO_AA_CONSTANTE)]
            producto *= 1.0 - aa
        return qx * producto

    def _validar_edad(self, edad: int) -> None:
        if not self.edad_min <= edad <= self.edad_max:
            raise ValueError(
                f"Edad {edad} fuera del rango de la tabla {self.nombre} "
                f"[{self.edad_min}, {self.edad_max}] (C-02)."
            )


def cargar_tabla(ruta_csv: Path) -> TablaMortalidad:
    """Lee un CSV de ``data/mortalidad/`` (``edad, qx, aa_2021..aa_2036``)."""
    qx: dict[int, float] = {}
    aa: dict[int, dict[int, float]] = {}
    with ruta_csv.open(encoding="utf-8") as f:
        lector = csv.DictReader(f)
        campos_aa = [c for c in (lector.fieldnames or []) if c.startswith("aa_")]
        anios = [int(c.removeprefix("aa_")) for c in campos_aa]
        for fila in lector:
            edad = int(fila["edad"])
            qx[edad] = float(fila["qx"])
            aa[edad] = {anio: float(fila[c]) for anio, c in zip(anios, campos_aa, strict=True)}
    if not qx:
        raise ValueError(f"Tabla vacía: {ruta_csv}")
    return TablaMortalidad(
        nombre=ruta_csv.stem,
        edad_min=min(qx),
        edad_max=max(qx),
        _qx=qx,
        _aa=aa,
    )
