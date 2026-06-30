"""GeneradorRetornosParametrico — proceso de mercado paramétrico (ADR-007).

Baseline del proceso de retornos: retornos reales anuales ~ Normal(media, desviacion),
deterministas dada la semilla. Es el comparable explícito; el **block bootstrap** (que
preserva la autocorrelación y modela mejor el riesgo de secuencia) entra como otra
implementación del mismo puerto en Fase 2. Nunca se presenta como pronóstico (SAD §3.3).

Con desviacion = 0 el proceso es determinista (todos los retornos = media): control **C-13**.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from cauce.domain.value_objects.supuestos import Supuestos

PISO_RETORNO_REAL = -0.99  # un retorno real no puede destruir más del 100% del capital


class GeneradorRetornosParametrico:
    """Genera retornos reales anuales con distribución normal. Implementa ``PuertoRetornos``."""

    def matriz_retornos(
        self,
        supuestos: Supuestos,
        anios: int,
        n_trayectorias: int,
        semilla: int,
    ) -> NDArray[np.float64]:
        """Matriz ``n`` por ``anios`` de retornos reales (NumPy; ruta vectorizada interna)."""
        if anios < 0 or n_trayectorias < 1:
            raise ValueError("anios >= 0 y n_trayectorias >= 1.")
        mu = float(supuestos.retorno_esperado)
        sigma = float(supuestos.volatilidad)
        rng = np.random.default_rng(semilla)
        retornos = rng.normal(mu, sigma, size=(n_trayectorias, anios))
        return np.maximum(retornos, PISO_RETORNO_REAL)

    def trayectorias_retorno(
        self,
        supuestos: Supuestos,
        anios: int,
        n_trayectorias: int,
        semilla: int,
    ) -> tuple[tuple[float, ...], ...]:
        """Versión del puerto (tipos stdlib) sobre la matriz vectorizada."""
        m = self.matriz_retornos(supuestos, anios, n_trayectorias, semilla)
        return tuple(tuple(float(x) for x in fila) for fila in m)
