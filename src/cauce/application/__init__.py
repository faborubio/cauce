"""Casos de uso de Cauce — orquestan los puertos del dominio.

Reglas (blindadas por import-linter): esta capa importa ``cauce.domain`` y trabaja
contra **puertos**, nunca contra adaptadores concretos de ``infrastructure`` ni contra
NumPy. La inyección del adaptador real ocurre en el composition root (``interfaces``).

Casos de uso planificados (SAD §5.1, §13):
- ``CompararModalidades``     (MVP, Fase 2)
- ``ExplicarComparacion``     (Fase 2)
- ``SimularEscenario``        (Fase 3)
- ``EvaluarSendaDePlaneo``    (Fase 4)
- ``GestionarPerfil``
"""
