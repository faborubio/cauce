"""SimuladorAcumulacion — genera la TrayectoriaDeRiqueza de la acumulación (ADR-010/015).

Cómputo numérico vectorizado (NumPy), **fuera del dominio**. Año a año, para cada
trayectoria: la ``SendaDePlaneo`` fija la fracción riesgosa según edad **y riqueza**; esa
fracción define la media y desviación del retorno de ese año (mezcla activo riesgoso/seguro);
se aporta la cotización y se capitaliza. Termina en el saldo a la jubilación — el insumo del
comparador de modalidades (ADR-001, SAD §6.2).

Determinismo (C-16): toda la aleatoriedad nace de ``perfil.semilla`` vía ``SeedSequence``.

La lógica de la fracción riesgosa **replica** ``SendaDePlaneo.fraccion_riesgosa`` de forma
vectorizada; el dominio conserva la implementación pura de referencia (frontera ADR-010).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import numpy as np
from numpy.typing import NDArray

from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.trayectoria_riqueza import PuntoTrayectoria, TrayectoriaDeRiqueza
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.infrastructure.retornos.parametrico import PISO_RETORNO_REAL


class SimuladorAcumulacion:
    """Implementa ``PuertoSimuladorAcumulacion`` con NumPy vectorizado."""

    def generar(
        self,
        perfil: PerfilAcumulacion,
        n_trayectorias: int,
    ) -> Sequence[TrayectoriaDeRiqueza]:
        if n_trayectorias < 1:
            raise ValueError("n_trayectorias >= 1.")

        senda = perfil.senda
        sup = perfil.supuestos
        x0 = perfil.edad_inicial.anios
        horizonte = perfil.horizonte
        mu_riesgoso = float(sup.retorno_riesgoso)
        sigma_riesgoso = float(sup.volatilidad_riesgosa)
        mu_seguro = float(sup.retorno_seguro)
        cotizacion = float(perfil.cotizacion_anual.uf)
        saldo0 = float(perfil.saldo_inicial.uf)

        w_base = np.array(
            [senda.fraccion_base(x0 + k) for k in range(horizonte)], dtype=np.float64
        )
        referencia = self._referencia(saldo0, cotizacion, w_base, mu_riesgoso, mu_seguro)

        rng = np.random.default_rng(np.random.SeedSequence(perfil.semilla))
        saldos = np.empty((n_trayectorias, horizonte + 1), dtype=np.float64)
        saldos[:, 0] = saldo0
        sens = senda.sensibilidad_riqueza
        for k in range(horizonte):
            s = saldos[:, k]
            if sens == 0.0 or referencia[k] <= 0.0:
                w = np.full(n_trayectorias, min(max(w_base[k], 0.0), 1.0))
            else:
                ajuste = sens * (1.0 - s / referencia[k])
                w = np.clip(w_base[k] + ajuste, 0.0, 1.0)
            mu = w * mu_riesgoso + (1.0 - w) * mu_seguro
            sigma = w * sigma_riesgoso
            retorno = np.maximum(rng.normal(size=n_trayectorias) * sigma + mu, PISO_RETORNO_REAL)
            saldos[:, k + 1] = np.maximum((s + cotizacion) * (1.0 + retorno), 0.0)

        return self._a_trayectorias(saldos, x0)

    @staticmethod
    def _referencia(
        saldo0: float,
        cotizacion: float,
        w_base: NDArray[np.float64],
        mu_riesgoso: float,
        mu_seguro: float,
    ) -> NDArray[np.float64]:
        """Riqueza 'on-track' por edad: acumulación determinista con el backbone por edad."""
        horizonte = w_base.shape[0]
        ref = np.empty(horizonte + 1, dtype=np.float64)
        ref[0] = saldo0
        for k in range(horizonte):
            mu = w_base[k] * mu_riesgoso + (1.0 - w_base[k]) * mu_seguro
            ref[k + 1] = (ref[k] + cotizacion) * (1.0 + mu)
        return ref

    @staticmethod
    def _a_trayectorias(
        saldos: NDArray[np.float64], x0: int
    ) -> tuple[TrayectoriaDeRiqueza, ...]:
        """Convierte la matriz NumPy en trayectorias del dominio (frontera C-18)."""
        n, columnas = saldos.shape
        trayectorias: list[TrayectoriaDeRiqueza] = []
        for i in range(n):
            puntos = tuple(
                PuntoTrayectoria(
                    Edad(x0 + k),
                    SaldoPrevisional(Decimal(f"{saldos[i, k]:.6f}")),
                )
                for k in range(columnas)
            )
            trayectorias.append(TrayectoriaDeRiqueza(puntos))
        return tuple(trayectorias)
