# CASES.md — Casos de prueba y escenarios de referencia

> Escenarios canónicos que ilustran qué hace Cauce y sirven de fixtures de validación.
> Se llenan en Fase 2 con datos sintéticos (no personas reales).

## Plantilla de caso

```
### Caso: <nombre>
- Perfil: edad, saldo (UF), género, supuestos (retorno/volatilidad/inflación/tasa)
- Tabla de mortalidad: <id_version>
- Semilla: <int>
- Modalidades comparadas: [...]
- Resultado esperado (cualitativo): qué riesgo domina cada modalidad
```

## Casos planificados (Fase 2)

1. **Saldo bajo, larga longevidad** → el retiro programado expone riesgo de agotamiento;
   la renta vitalicia lo neutraliza a costa de herencia.
2. **Secuencia de retornos adversa al inicio** → penaliza al retiro programado y a la
   renta temporal diferida (ADR-007).
3. **Comparación por género** → distinta tabla (`RV-M-2020` vs `CB-H-2020`) cambia la
   mesada vitalicia.
