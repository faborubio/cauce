"""Infraestructura de Cauce — adaptadores que implementan los puertos del dominio.

Aquí vive **todo lo numérico** (ADR-010): el simulador Monte Carlo vectorizado con
NumPy, el generador de retornos (block bootstrap / paramétrico), el tarificador
paramétrico tipo SCOMP, los adaptadores de mortalidad regulada y la persistencia
SQLAlchemy. El dominio nunca importa este paquete.

Submódulos:
- ``simulacion``   implementación de ``PuertoSimulador`` (NumPy).
- ``mortalidad``   tablas reguladas NCG N°306 (``PuertoMortalidad``).
- ``retornos``     proceso de mercado (``PuertoRetornos``).
- ``tarificacion`` renta vitalicia paramétrica (``PuertoTarificador``).
- ``persistencia`` repositorios SQLAlchemy + PostgreSQL.
"""
