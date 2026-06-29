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
- [x] Tablas reguladas 2020 (RV/CB/B/MI) extraídas y validadas a `data/mortalidad/`.
- [x] **Sign-off** — toolchain en verde, commit `a772c5d` (2026-06-29).

### Vista de halcón (respondida en el sign-off)

- **¿El `import-linter` falla si alguien mete `import numpy` en `domain/`?** ✅ Verificado
  en vivo: se inyectó `import numpy` en `domain/services/metricas.py` y el contrato
  "Dominio puro" rompió (`cauce.domain is not allowed to import numpy`). El blindaje de
  ADR-010 no es decorativo.
- **¿`mypy --strict` pasa sin `Any` ocultos en el dominio?** ✅ 36 archivos, 0 issues.
- **¿El contrato `TrayectoriaDeRiqueza` es suficiente para enchufar acumulación sin tocar
  des-acumulación?** ⏳ Diseñado para ello (frontera generar/evaluar); la prueba real es
  la Fase 4 — anotado como caso C-19 en `CASES.md`.
- **Riesgo abierto detectado:** la fórmula de proyección `q_x → q_{x,t}` vía `AA_{x,t}`
  aún no está implementada (vive en la nota técnica del Anexo N°10). Pasa a Fase 1; caso
  C-01 en `CASES.md`.

**Estado: Fase 0 CERRADA.** Lista para Fase 1.

---

## Fase 1 — Núcleo de simulación *(pendiente)*
## Fase 2 — MVP Des-acumulación *(pendiente)*
## Fase 3 — Capa MCP *(pendiente)*
## Fase 4 — Acumulación *(pendiente)*
