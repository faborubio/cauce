"""Dominio puro de Cauce — **stdlib-only** (ADR-010).

Regla dura (blindada por import-linter, ver pyproject ``[tool.importlinter]``):
este paquete y sus submódulos **no** pueden importar NumPy, SciPy, Pydantic,
SQLAlchemy ni ningún framework, ni las capas ``application``/``infrastructure``/
``interfaces``. La generación numérica de trayectorias vive en ``infrastructure``;
aquí solo se *define* y se *evalúa*.
"""
