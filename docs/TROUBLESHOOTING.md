# TROUBLESHOOTING.md

> Problemas frecuentes y su solución. Se va llenando a medida que aparecen.

## Entorno

**`uv sync` falla por versión de Python.** Cauce requiere 3.12+. Verifica con
`python3 --version`; `uv` puede instalar la versión con `uv python install 3.12`.

**`lint-imports` reporta una violación de frontera.** Significa que alguien importó
hacia arriba o metió un framework en el dominio. Revisa el contrato infringido en la
salida; la regla de oro es: `domain/` no importa NumPy ni capas externas (ADR-010).

## Base de datos

**`docker compose up postgres` no levanta.** Revisa que el puerto 5432 esté libre
(`POSTGRES_PORT` en `.env`) y que el healthcheck pase (`docker compose ps`).

## Simulación (Fase 1+)

**Dos corridas con la misma semilla dan resultados distintos.** Revisa que el
`BitGenerator` de NumPy y las versiones de librerías estén fijados; la reproducibilidad
es **dentro del mismo entorno** (ADR-006).
