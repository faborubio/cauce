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
from cauce.domain.entities.resultado_trayectoria import ResultadoTrayectoria
from cauce.domain.entities.trayectoria_riqueza import PuntoTrayectoria, TrayectoriaDeRiqueza
from cauce.domain.ports.puerto_mortalidad import PuertoMortalidad
from cauce.domain.value_objects.edad import EDAD_MAXIMA, Edad
from cauce.domain.value_objects.mesada import Mesada
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.tarificacion.conmutacion import MESES_ANIO, TarificadorConmutacion


def _mesada(uf_anual: float) -> Mesada:
    return Mesada(Decimal(f"{uf_anual / MESES_ANIO:.6f}"))


def _saldo(uf: float) -> SaldoPrevisional:
    return SaldoPrevisional(Decimal(f"{max(uf, 0.0):.6f}"))


class SimuladorMonteCarlo:
    """Implementa ``PuertoSimulador`` con NumPy vectorizado."""

    def __init__(
        self,
        mortalidad: PuertoMortalidad,
        retornos: GeneradorRetornosParametrico,
        tarificador: TarificadorConmutacion | None = None,
    ) -> None:
        self._mortalidad = mortalidad
        self._retornos = retornos
        self._tarificador = tarificador or TarificadorConmutacion()

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

    def comparar_modalidades(
        self,
        perfil: PerfilPrevisional,
        modalidades: Sequence[Modalidad],
        n_trayectorias: int,
    ) -> dict[Modalidad, tuple[ResultadoTrayectoria, ...]]:
        """Evalúa cada modalidad sobre el **mismo** sorteo (números comunes, C-24)."""
        if n_trayectorias < 1:
            raise ValueError("n_trayectorias >= 1.")
        persona = perfil.persona
        supuestos = perfil.supuestos
        x0 = persona.edad.anios
        surv = self._mortalidad.probabilidades_supervivencia(persona, perfil.tabla_mortalidad)
        # RP usa la tasa de interés técnica; la RV su propia tasa (C-28).
        factores_rp = self._tarificador.factores_por_edad(surv, float(supuestos.tasa_descuento))
        a_x0_rv = self._tarificador.factor_anualidad(surv, float(supuestos.tasa_rv))

        edades_muerte, probs, _ = self._distribucion_muerte(perfil)
        horizonte = min(EDAD_MAXIMA, int(edades_muerte[-1])) - x0
        f_arr = np.array([factores_rp[x0 + k] for k in range(horizonte + 1)], dtype=np.float64)

        # Sorteo común a todas las modalidades (C-24).
        hijos = np.random.SeedSequence(perfil.semilla).spawn(2)
        muertes = np.random.default_rng(hijos[0]).choice(
            edades_muerte, size=n_trayectorias, p=probs
        ).astype(int)
        anios_muerte = muertes - x0
        retornos = self._retornos.matriz_retornos(
            perfil.supuestos, horizonte, n_trayectorias, int(hijos[1].generate_state(1)[0])
        )

        saldo0 = float(persona.saldo.uf)
        salida: dict[Modalidad, tuple[ResultadoTrayectoria, ...]] = {}
        for modalidad in modalidades:
            if modalidad is Modalidad.RETIRO_PROGRAMADO:
                salida[modalidad] = self._evaluar_rp(saldo0, f_arr, retornos, anios_muerte)
            elif modalidad is Modalidad.RV_INMEDIATA:
                saldo_efectivo = saldo0 * (1.0 - float(supuestos.margen_rv))
                salida[modalidad] = self._evaluar_rv(saldo_efectivo, a_x0_rv, n_trayectorias)
            else:
                raise NotImplementedError(
                    f"{modalidad.name} (mixta) llega en un incremento posterior (C-10/C-29)."
                )
        return salida

    @staticmethod
    def _evaluar_rv(
        saldo_efectivo: float, a_x0: float, n: int
    ) -> tuple[ResultadoTrayectoria, ...]:
        """Renta vitalicia: mesada fija de por vida, sin herencia, sin riesgo de longevidad.

        ``saldo_efectivo`` ya viene neto del margen comercial de la compañía (C-27).
        """
        mesada = _mesada(saldo_efectivo / a_x0)
        cero = _saldo(0.0)
        r = ResultadoTrayectoria(mesada_inicial=mesada, mesada_final=mesada, herencia=cero)
        return tuple(r for _ in range(n))

    def _evaluar_rp(
        self,
        saldo0: float,
        f_arr: NDArray[np.float64],
        retornos: NDArray[np.float64],
        anios_muerte: NDArray[np.int_],
    ) -> tuple[ResultadoTrayectoria, ...]:
        """Retiro programado: mesada_t = saldo_t / ä(edad_t) cada año (C-07)."""
        n, horizonte = retornos.shape
        saldos = np.empty((n, horizonte + 1), dtype=np.float64)
        mesadas = np.empty((n, horizonte), dtype=np.float64)
        saldos[:, 0] = saldo0
        for k in range(horizonte):
            m_k = saldos[:, k] / f_arr[k]
            mesadas[:, k] = m_k
            saldos[:, k + 1] = np.maximum((saldos[:, k] - m_k) * (1.0 + retornos[:, k]), 0.0)

        mesada_inicial = _mesada(saldo0 / float(f_arr[0]))
        resultados: list[ResultadoTrayectoria] = []
        for i in range(n):
            d = int(anios_muerte[i])
            herencia = _saldo(float(saldos[i, d]))
            mesada_final = mesada_inicial if d == 0 else _mesada(float(mesadas[i, d - 1]))
            resultados.append(
                ResultadoTrayectoria(
                    mesada_inicial=mesada_inicial,
                    mesada_final=mesada_final,
                    herencia=herencia,
                )
            )
        return tuple(resultados)

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
