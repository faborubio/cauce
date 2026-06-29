# AUDIT.md — Auditoría por fase

> Cada fase cierra con una **Vista de halcón** (revisión crítica) y un **sign-off**
> antes de avanzar. Formato heredado de Veredicto (SAD §12).

---

## Fase 0 — Scaffolding

**Entregable:** capas, docs vivos, esqueleto de dominio, Docker + Postgres, fronteras
blindadas por `import-linter`.

### Checklist

- [x] Estructura por capas (`domain`/`application`/`infrastructure`/`interfaces`).
- [x] `domain/` stdlib-only; numérico confinado a `infrastructure/` (ADR-010).
- [x] Contratos `import-linter` (capas + dominio puro + application sin adaptadores).
- [x] Value objects, entidades (`TrayectoriaDeRiqueza`) y puertos (`Protocol`).
- [x] Toolchain: `uv`, `ruff`, `mypy --strict`, `pytest`.
- [x] Docker Compose con PostgreSQL 16.
- [x] Docs §12 creados.
- [ ] **Sign-off** (pendiente de verificación verde de todo el toolchain).

### Vista de halcón (a completar en el sign-off)

- ¿El `import-linter` falla si alguien mete `import numpy` en `domain/`? → verificar.
- ¿`mypy --strict` pasa sin `Any` ocultos en el dominio?
- ¿El contrato `TrayectoriaDeRiqueza` es suficiente para que acumulación se enchufe sin
  tocar des-acumulación? (revisar en Fase 4, anotado).

---

## Fase 1 — Núcleo de simulación *(pendiente)*
## Fase 2 — MVP Des-acumulación *(pendiente)*
## Fase 3 — Capa MCP *(pendiente)*
## Fase 4 — Acumulación *(pendiente)*
