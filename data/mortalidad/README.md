# Tablas de mortalidad reguladas — RV/CB/B/MI 2020

Insumo actuarial canónico de Cauce (ADR-003). **Versionado en git** (datos pequeños y autoritativos).

## Fuente

- Planilla oficial SP: `docs/tablas_mortalidad_historicas.xlsx` (hojas por uso × sexo).
- Norma: tablas **2020** del Compendio de Normas del Sistema de Pensiones, **Libro III, Título X, Cap. IX** (NCG conjunta SP/CMF de 24-feb-2023). Vigencia 2023-07-01 a ~2029.
- ⚠️ No confundir con la **NCG 306 de la CMF (2011)** (reservas de seguros no previsionales, tablas M-2016) — otra norma homónima. M-2016 solo se usa como *fixture de tests*, nunca como tabla de producto.

## Archivos y mapeo (uso × sexo → tabla)

| Archivo | Uso | Sexo | Nota |
|---------|-----|------|------|
| `rv_2020_mujeres.csv` | Vejez | Mujeres | edades 20–110 |
| `cb_2020_hombres.csv` | **Vejez y sobrevivencia** | Hombres | una sola tabla (asimetría regulatoria) |
| `b_2020_mujeres.csv` | Sobrevivencia | Mujeres | |
| `mi_2020_hombres.csv` | Invalidez | Hombres | |
| `mi_2020_mujeres.csv` | Invalidez | Mujeres | |

Selección en `PuertoMortalidad`: **vejez** (MVP) → `rv_2020_mujeres` (F) / `cb_2020_hombres` (M).

## Esquema

`edad, qx, aa_2021, …, aa_2036`

- `qx`: probabilidad base de muerte a la edad (tabla 2020).
- `aa_YYYY`: **factor de mejoramiento** `AA_{x,t}` por año de proyección. **Desde 2036 se mantiene constante** (último valor). El `q_x` proyectado al año `t` se calcula según la nota técnica del Anexo N°10 de la norma (a implementar en `PuertoMortalidad`, Fase 1) — usar solo `q_x` base subestima la longevidad.

## Validación aplicada (extracción 2026-06-29)

- Edades contiguas, sin huecos; `qx ∈ (0,1]`, creciente hacia edades altas, `qx(110)=1`.
- Matriz `AA` completa (16 años, sin celdas vacías).
- `MI` diverge de `CB`/`B` en edades activas (~4–7×), coincide en edad 0 → consistente.
- `CB-2020-HOMBRES` idéntica en hojas Vejez y Sobrevivencia (0 filas distintas).

## Regenerar

Script de extracción en el historial de la sesión; se formalizará como loader en `infrastructure/mortalidad/` (Fase 1).
