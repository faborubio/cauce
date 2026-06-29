"""SendaDePlaneo (glide path) — mezcla de riesgo por edad **y riqueza**. FASE 2.

Tesis central del paper de origen (SAD §1.1): la trayectoria de riesgo de un fondo
generacional debería depender de la edad *y* de la riqueza acumulada, no solo de la
edad. Stub de fase 2 — se implementa en la fase 4 sobre el mismo núcleo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SendaDePlaneo:
    """Glide path de un fondo generacional. Placeholder de fase 2 (SAD §13)."""

    nombre: str
