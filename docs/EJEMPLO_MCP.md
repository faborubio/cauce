# Ejemplo explicado — cómo se usaría el MCP de Cauce

> Documento de demostración para portafolio. Explica, en lenguaje accesible (para
> alguien de 15 o de 60+ años), cómo una persona usaría la capa MCP de la Fase 3.
> Anclado a la salida real del comparador (`CompararModalidades`): campos
> `mesada_inicial_uf`, `herencia_esperada_uf`, `erosion_mediana`, `riesgo_dominante`,
> `disclaimer`, y las modalidades `retiro_programado` / `rv_inmediata`.

## La idea en una frase

Hoy, para usar el motor, alguien tiene que mandar un `curl` con un JSON (eso es para
programadores). **El MCP es el traductor** que permite que una persona normal le escriba
en español a Claude Desktop, como en un chat, y Claude por detrás llama al motor, recibe
los números y se los explica de vuelta en palabras simples.

```
Persona (escribe normal) → Claude Desktop → [MCP de Cauce] → motor (CompararModalidades) → números → Claude los traduce → Persona
```

La persona **nunca ve** UF, JSON, ni percentiles. Solo conversa.

## Los personajes

- **Don Mario, 66 años.** Recién jubilado. Tiene ~3.000 UF en su AFP (unos $117M). La AFP
  le ofreció dos caminos y no entiende ninguno.
- **Sofía, 15 años, su nieta.** Le ayuda con el computador.

## La conversación, paso a paso

### Turno 1 — La pregunta del abuelo

> **Don Mario:** *"Tengo 66 años, soy hombre y junté 3 mil UF en la AFP. Me dan a elegir
> entre 'retiro programado' y 'renta vitalicia' y no sé qué significan. ¿Me puedes mostrar
> la diferencia?"*

**Por detrás:** Claude llama a la herramienta
`comparar_modalidades(edad=66, genero="M", saldo_uf=3000, modalidades=["retiro_programado", "rv_inmediata"])`
— el mismo `CompararModalidades.ejecutar()` que ya usa la REST. El motor corre 10.000
escenarios y devuelve (números ilustrativos):

| modalidad | mesada_inicial_uf | herencia_esperada_uf | erosion_mediana | riesgo_dominante |
|---|---|---|---|---|
| retiro_programado | 14,2 | 1.150 | 0,38 | longevidad |
| rv_inmediata | 13,1 | 0 | 0,00 | inflación/cesión |

**Respuesta de Claude a Don Mario (traducida):**

> **🅰️ Retiro Programado** — *"Usted sigue siendo el dueño de la plata."* Le pagan ~14,2 UF
> al mes al principio, **pero baja con los años** (hacia el final puede valer ~38% menos —
> como una jarra de la que toma todos los meses). **Si fallece, lo que quede es herencia**
> (~1.150 UF). El riesgo principal es **vivir muchos años** (longevidad).
>
> **🅱️ Renta Vitalicia** — *"Le pasa la plata a una compañía y ella le garantiza un sueldo
> de por vida."* Le pagan ~13,1 UF (un poco menos), **nunca baja y nunca se acaba**. Pero
> **ya no es herencia**. El riesgo es otro: que la inflación le reste poder con el tiempo,
> y que cede el control del capital.
>
> En simple: 🅰️ paga un poco más hoy y deja herencia, pero baja; 🅱️ paga un poco menos pero
> es fijo y para siempre.
>
> ⚠️ *Esto es una simulación educativa, **no es un consejo sobre qué elegir**. La decisión
> debe tomarla con su AFP, un asesor previsional registrado o el SCOMP.*

El disclaimer no es opcional: el motor lo manda en el campo `disclaimer` en **cada**
respuesta (C-21). El MCP lo muestra siempre.

### Turno 2 — La pregunta de la nieta ("¿y si...?")

> **Sofía:** *"¿Y qué pasa si mi abuelo vive 5 años más de lo que esperan las tablas?"*

**Por detrás:** Claude llama a `simular_escenario(longevidad=+5años)` (modo simulación, sin
efectos).

> Con la **Renta Vitalicia** 🅱️ *no cambia nada*: esos 5 años extra los cubre la compañía
> —ese es el seguro que está comprando—. Con el **Retiro Programado** 🅰️ esos años salen de
> su misma jarra, así que la mesada de esos últimos años bajaría aún más.

Esto es justo *"le pregunto a Claude qué pasa con mi pensión si vivo 5 años más"* (SAD §13),
lo que un `curl` no hace de forma natural.

### Turno 3 — La pregunta prohibida (caso C-22, el más importante)

> **Don Mario:** *"Ya, ¿y cuál me conviene a mí? Elige tú."*

Aquí está la prueba de fuego. El sistema, por diseño (C-22), responde:

> Le entiendo las ganas de que le diga "este" — pero **no puedo elegir por usted, y sería
> irresponsable hacerlo.** La decisión correcta depende de cosas suyas que esta simulación
> no conoce (su salud, si quiere dejar herencia, otros ingresos, su tranquilidad). Lo que sí
> hice fue **ponerle los números claros** para que llegue informado a su **AFP**, un
> **asesor previsional registrado** o el **SCOMP**. Yo le serví para que llegue entendiendo,
> no perdido.

**Por qué esto da valor al portafolio:** demuestra poner IA al servicio de alguien
vulnerable **sin cruzar la línea regulatoria**. La REST nunca enfrenta esta tentación porque
nadie le conversa. El MCP sí, y la maneja bien.

## Por qué importa para las dos personas

| | Don Mario (66) | Sofía (15) |
|---|---|---|
| **Sin MCP** | Le llega un PDF lleno de jerga; firma lo que le digan. | Vería `"erosion_mediana": 0.38` y no sabría qué es. |
| **Con MCP** | Le habla a Claude como a un nieto; entiende los dos caminos en 2 minutos. | Pregunta "¿y si...?" y aprende cómo funciona una pensión. |
| **Lo que NO pasa** | Nadie le dice "elige esto" — lo mandan al experto humano. | No recibe consejo financiero disfrazado. |

## En una frase

El MCP convierte el motor —que hoy solo entiende JSON— en algo que Don Mario puede usar
hablando, que **explica en vez de solo calcular**, y que **sabe cuándo callar y mandar a la
persona con un experto humano**. Esa última parte es lo más difícil y lo más valioso que
muestra el proyecto.
