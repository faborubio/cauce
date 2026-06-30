"""SimuladorMonteCarlo — genera la TrayectoriaDeRiqueza por Monte Carlo (ADR-010).

Aquí vive el cómputo numérico vectorizado (NumPy), **fuera del dominio**. Para cada
trayectoria se sortea una **edad de muerte** desde la curva de mortalidad (riesgo de
longevidad) y una **senda de retornos** desde el proceso de mercado; luego se des-acumula
el saldo año a año. El dominio recibe trayectorias ya construidas y las *evalúa*.

Determinismo (C-16): toda la aleatoriedad nace de ``perfil.semilla`` vía ``SeedSequence``,
con corrientes independientes para mortalidad y retornos.

Regla de retiro (Fase 1, **simplificación declarada**): mesada real constante =
``saldo_inicial / e_x`` (esperanza de vida curtate). El recálculo anual del retiro
programado es el caso **C-07**, de Fase 2.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import numpy as np
from numpy.typing import NDArray

from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.trayectoria_riqueza import PuntoTrayectoria, TrayectoriaDeRiqueza
from cauce.domain.ports.puerto_mortalidad import PuertoMortalidad
from cauce.domain.value_objects.edad import EDAD_MAXIMA, Edad
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico


class SimuladorMonteCarlo:
    """Implementa ``PuertoSimulador`` con NumPy vectorizado."""

    def __init__(
        self,
        mortalidad: PuertoMortalidad,
        retornos: GeneradorRetornosParametrico,
    ) -> None:
        self._mortalidad = mortalidad
        self._retornos = retornos

    def generar(
        self,
        perfil: PerfilPrevisional,
        modalidad: Modalidad,
        n_trayectorias: int,
    ) -> Sequence[TrayectoriaDeRiqueza]:
        if modalidad is not Modalidad.RETIRO_PROGRAMADO:
            raise NotImplementedError(
                f"Fase 1 simula solo RETIRO_PROGRAMADO; {modalidad.name} llega en Fase 2."
            )
        if n_trayectorias < 1:
            raise ValueError("n_trayectorias >= 1.")

        persona = perfil.persona
        x0 = persona.edad.anios
        edades_muerte, probs, e_x = self._distribucion_muerte(perfil)
        horizonte = min(EDAD_MAXIMA, int(edades_muerte[-1])) - x0

        # Corrientes deterministas e independientes desde la semilla del perfil (C-16).
        hijos = np.random.SeedSequence(perfil.semilla).spawn(2)
        rng_mort = np.random.default_rng(hijos[0])
        semilla_ret = int(hijos[1].generate_state(1)[0])

        muertes = rng_mort.choice(edades_muerte, size=n_trayectorias, p=probs)
        retornos = self._retornos.matriz_retornos(
            perfil.supuestos, horizonte, n_trayectorias, semilla_ret
        )

        saldo0 = float(persona.saldo.uf)
        mesada = saldo0 / max(e_x, 1.0)  # simplificación Fase 1 (C-07)
        saldos = self._desacumular(saldo0, mesada, retornos, horizonte)

        return self._a_trayectorias(saldos, muertes.astype(int), x0)

    def _distribucion_muerte(
        self, perfil: PerfilPrevisional
    ) -> tuple[NDArray[np.int_], NDArray[np.float64], float]:
        """Distribución de la edad de muerte y esperanza de vida desde la curva S(x)."""
        surv = self._mortalidad.probabilidades_supervivencia(
            perfil.persona, perfil.tabla_mortalidad
        )
        x0 = perfil.persona.edad.anios
        x_max = max(e.anios for e in surv)
        edades = list(range(x0, x_max + 1))
        s = np.array([surv[Edad(x)] for x in edades], dtype=np.float64)
        # d(x) = S(x) - S(x+1); en x_max todos mueren (q=1), S(x_max+1)=0.
        s_siguiente = np.append(s[1:], 0.0)
        d = s - s_siguiente
        total = d.sum()
        if total <= 0:
            raise ValueError("Distribución de mortalidad degenerada.")
        probs = d / total
        e_x = float(s[1:].sum())  # Σ_{x>x0} S(x), esperanza de vida curtate
        return np.array(edades, dtype=np.int_), probs, e_x

    @staticmethod
    def _desacumular(
        saldo0: float,
        mesada: float,
        retornos: NDArray[np.float64],
        horizonte: int,
    ) -> NDArray[np.float64]:
        """Recursión vectorizada del saldo; piso en cero = agotamiento (riesgo longevidad)."""
        n = retornos.shape[0]
        saldos = np.empty((n, horizonte + 1), dtype=np.float64)
        saldos[:, 0] = saldo0
        for k in range(horizonte):
            nuevo = saldos[:, k] * (1.0 + retornos[:, k]) - mesada
            saldos[:, k + 1] = np.maximum(nuevo, 0.0)
        return saldos

    @staticmethod
    def _a_trayectorias(
        saldos: NDArray[np.float64],
        muertes: NDArray[np.int_],
        x0: int,
    ) -> tuple[TrayectoriaDeRiqueza, ...]:
        """Convierte la matriz NumPy en trayectorias del dominio (frontera C-18)."""
        trayectorias: list[TrayectoriaDeRiqueza] = []
        for i in range(saldos.shape[0]):
            anios_vividos = int(muertes[i]) - x0
            puntos = tuple(
                PuntoTrayectoria(
                    Edad(x0 + k),
                    SaldoPrevisional(Decimal(f"{saldos[i, k]:.6f}")),
                )
                for k in range(anios_vividos + 1)
            )
            trayectorias.append(TrayectoriaDeRiqueza(puntos))
        return tuple(trayectorias)
