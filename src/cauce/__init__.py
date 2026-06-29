"""Cauce — Motor de Ciclo de Vida Previsional (acumulación + des-acumulación) + capa MCP.

Arquitectura por capas (Clean Architecture, ver SAD §5):

- ``domain``         núcleo puro, **stdlib-only** (sin NumPy/Pydantic/ORM). Define
                     *qué* es una persona previsional, el contrato
                     ``TrayectoriaDeRiqueza`` y *cómo se evalúa* una modalidad.
- ``application``    casos de uso; orquesta puertos del dominio.
- ``infrastructure`` adaptadores: simulador Monte Carlo (NumPy), mortalidad,
                     retornos, tarificación, persistencia. Aquí vive el numérico (ADR-010).
- ``interfaces``     entrega: REST (FastAPI) y MCP (FastMCP).
"""

__version__ = "0.1.0"
