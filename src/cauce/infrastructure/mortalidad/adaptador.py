"""AdaptadorMortalidad — implementa ``PuertoMortalidad`` con las tablas reguladas 2020.

Selecciona la tabla por **(sexo, uso)** según la asimetría regulatoria (C-03):
vejez → ``CB-2020`` (hombres) / ``RV-2020`` (mujeres). Construye la curva de
**supervivencia de cohorte**: a medida que la persona envejece, el año de cálculo
avanza, así que cada ``q_x`` se proyecta a su año calendario (C-01).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import EDAD_MAXIMA, Edad
from cauce.domain.value_objects.genero import Genero
from cauce.infrastructure.mortalidad.cargador import TablaMortalidad, cargar_tabla

# Mapeo (uso, sexo) -> archivo de tabla 2020. Vejez es el uso del MVP (ADR-011).
# CB-2020-HOMBRES sirve vejez Y sobrevivencia masculina (misma tabla, asimetría).
_TABLAS: dict[tuple[str, Genero], str] = {
    ("vejez", Genero.MASCULINO): "cb_2020_hombres",
    ("vejez", Genero.FEMENINO): "rv_2020_mujeres",
    ("sobrevivencia", Genero.MASCULINO): "cb_2020_hombres",
    ("sobrevivencia", Genero.FEMENINO): "b_2020_mujeres",
    ("invalidez", Genero.MASCULINO): "mi_2020_hombres",
    ("invalidez", Genero.FEMENINO): "mi_2020_mujeres",
}


class AdaptadorMortalidad:
    """Sirve curvas de supervivencia desde las tablas reguladas 2020 versionadas."""

    def __init__(self, directorio: Path, anio_base: int = 2026, uso: str = "vejez") -> None:
        self._dir = directorio
        self._anio_base = anio_base
        self._uso = uso
        self._cache: dict[str, TablaMortalidad] = {}

    def _tabla_para(self, genero: Genero) -> TablaMortalidad:
        clave = (self._uso, genero)
        if clave not in _TABLAS:
            raise ValueError(f"Uso '{self._uso}' no soportado para {genero} (C-03).")
        nombre = _TABLAS[clave]
        if nombre not in self._cache:
            self._cache[nombre] = cargar_tabla(self._dir / f"{nombre}.csv")
        return self._cache[nombre]

    def probabilidades_supervivencia(
        self,
        persona: Persona,
        tabla_mortalidad: str,
    ) -> Mapping[Edad, float]:
        """S(x) = P(vivo a la edad x | vivo a la edad actual), proyección de cohorte.

        ``tabla_mortalidad`` es la añada (p. ej. ``"2020"``); la tabla concreta se
        elige por sexo y uso. Devuelve S desde la edad actual hasta la máxima.
        """
        tabla = self._tabla_para(persona.genero)
        x0 = persona.edad.anios
        if x0 < tabla.edad_min:
            raise ValueError(
                f"Edad {x0} bajo el rango de la tabla {tabla.nombre} (C-02); "
                "el MVP es vejez (edades de jubilación)."
            )
        supervivencia: dict[Edad, float] = {Edad(x0): 1.0}
        s = 1.0
        for x in range(x0, min(tabla.edad_max, EDAD_MAXIMA)):
            anio = self._anio_base + (x - x0)
            qx = tabla.qx_proyectada(x, anio)
            s *= 1.0 - qx
            supervivencia[Edad(x + 1)] = s
        return supervivencia

    def esperanza_vida_curtate(self, persona: Persona) -> float:
        """e_x ≈ Σ_{x>x0} S(x): años esperados de vida restante (entero)."""
        surv = self.probabilidades_supervivencia(persona, "2020")
        x0 = persona.edad.anios
        return sum(p for e, p in surv.items() if e.anios > x0)
