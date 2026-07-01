"""SendaDePlaneo (glide path) — mezcla de riesgo por edad **y riqueza** (ADR-015).

Tesis central del paper de origen (SAD §1.1): la trayectoria de riesgo de un fondo
generacional debería depender de la edad *y* de la riqueza acumulada, no solo de la edad.

- **Componente por edad (backbone):** interpola linealmente la fracción riesgosa desde
  ``w_joven`` (a ``edad_inicial``) hasta ``w_final`` (a ``edad_jubilacion``).
- **Componente por riqueza (la tesis):** ajusta según la distancia a una riqueza de
  referencia ("on-track"). Si va **adelantado** (saldo > referencia) baja el riesgo para
  asegurar la meta; si va **atrasado** lo sube, acotado. Con ``sensibilidad_riqueza = 0``
  la senda es la **clásica solo por edad** (baseline comparable).

Es dominio puro (stdlib): trabaja con la fracción de riesgo (un ratio), no con dinero;
la generación numérica de trayectorias vive en infraestructura (ADR-010).
"""

from __future__ import annotations

from dataclasses import dataclass


def _clamp(x: float, bajo: float, alto: float) -> float:
    return max(bajo, min(alto, x))


@dataclass(frozen=True, slots=True)
class SendaDePlaneo:
    """Glide path de un fondo generacional: fracción riesgosa por (edad, riqueza)."""

    nombre: str
    edad_inicial: int
    edad_jubilacion: int
    w_joven: float  # fracción riesgosa al inicio (p. ej. 0.9)
    w_final: float  # fracción riesgosa a la jubilación (p. ej. 0.2)
    sensibilidad_riqueza: float = 0.0  # 0 = clásica por edad; > 0 = tesis edad+riqueza

    def __post_init__(self) -> None:
        if self.edad_inicial >= self.edad_jubilacion:
            raise ValueError("edad_inicial debe ser menor que edad_jubilacion.")
        for nombre, w in (("w_joven", self.w_joven), ("w_final", self.w_final)):
            if not 0.0 <= w <= 1.0:
                raise ValueError(f"'{nombre}' debe estar en [0, 1]: {w}.")
        if self.sensibilidad_riqueza < 0:
            raise ValueError("sensibilidad_riqueza no puede ser negativa.")

    def fraccion_base(self, edad: int) -> float:
        """Componente por edad: interpolación lineal ``w_joven`` → ``w_final``."""
        if edad <= self.edad_inicial:
            return self.w_joven
        if edad >= self.edad_jubilacion:
            return self.w_final
        avance = (edad - self.edad_inicial) / (self.edad_jubilacion - self.edad_inicial)
        return self.w_joven + (self.w_final - self.w_joven) * avance

    def fraccion_riesgosa(self, edad: int, saldo: float, referencia: float) -> float:
        """Fracción riesgosa final en (edad, riqueza), acotada a [0, 1] (ADR-015).

        ``referencia`` es la riqueza "on-track" a esa edad; si es 0 o la sensibilidad es
        nula, se devuelve solo el backbone por edad.
        """
        base = self.fraccion_base(edad)
        if self.sensibilidad_riqueza == 0.0 or referencia <= 0.0:
            return _clamp(base, 0.0, 1.0)
        # Adelantado (saldo > referencia) -> (1 - saldo/ref) < 0 -> menos riesgo.
        ajuste = self.sensibilidad_riqueza * (1.0 - saldo / referencia)
        return _clamp(base + ajuste, 0.0, 1.0)
