[← Volver al README](../README.md)

# Velocidad

Antes de cambiar nada, se midió dónde se iba el tiempo:
- **La compresión ya la hace Render:** la página viaja comprimida con Brotli (`content-encoding: br`), y pasa de 532 KB a 38 KB. No hace falta añadirla en Flask.
- **Flask tardaba 92 ms en preparar la página.** Con `cProfile` se vio por qué:
  - Para cada partido, `anotadores_de` y `linea_del_tiempo` recorrían los 308 goles del Mundial: unas 168 000 comparaciones por página.
  - Las abreviaturas accesibles se volvían a construir miles de veces, siempre las mismas («45'», «(pen.)»…).
- **El CSS no se guardaba en caché:** el navegador lo volvía a pedir en cada visita (`Cache-Control: no-cache`).

Qué se cambió:
- **`cargar()` agrupa los goles por partido** una sola vez, al arrancar (`goles_por_partido`), y `app.py` pasa a cada función solo los de ese partido. Las funciones de `mundial.py` no cambian. Una prueba comprueba que, en los 104 partidos, sale exactamente lo mismo que con los 308 goles.
- **`@cache`** (de `functools`) en `abreviatura()` y en el filtro `abreviaturas`: cada resultado se calcula una sola vez y después se reutiliza.
- **Caché del CSS con huella.** La dirección del CSS lleva una huella de su contenido (`styles.css?v=fe975c40d6`, función `estatico()`) y Flask le pone `max-age` de un año (`SEND_FILE_MAX_AGE_DEFAULT`). El navegador ya no vuelve a pedirlo. Si el CSS cambia, la huella también, y se descarga el nuevo.
- **`trim_blocks` y `lstrip_blocks`:** Jinja quita los saltos de línea que dejan las etiquetas `{% %}`. Ahorra un 6 %. Antes de dejarlo se compararon el texto y capturas de la página entera, y salieron idénticos píxel a píxel.

| | Antes | Después |
|---|---|---|
| Flask prepara la página | 92 ms | 33 ms |
| Primer byte (en tu ordenador) | 106 ms | 32 ms |
| Página lista, en un móvil lento simulado (CPU ×4) | 407 ms | 335 ms |
| Segunda visita: peticiones | la página y el CSS | solo la página |

## Líneas del tiempo solo al pedirlas

Las 162 líneas del tiempo venían enteras dentro de la página, en `<details>`, aunque nadie las abriera, y eran el 61 % del HTML. Cada partido salía dos veces, en su estadio y en su grupo. Ahora funcionan como el detalle de los goleadores:
- «Línea del tiempo» es un enlace a `?linea=linea-sede-12`, y Flask solo pinta esa. Al pulsarlo otra vez, se cierra.
- El número es el del partido (su puesto por fecha) y el lugar es `sede`, `grupo` o `resultado`. Así se abre justo donde se ha pulsado, no en los tres sitios.
- Si está dentro de un desplegable («5 partidos», «Ver partidos»), Flask lo pinta abierto. Al cerrar la línea, el enlace lleva `?vista=...` para que ese desplegable no se cierre también.

| | Paso 38 | Ahora |
|---|---|---|
| La portada pesa (sin comprimir) | 503 KB | 225 KB |
| Flask prepara la página | 33 ms | 23 ms |

## Con los 23 Mundiales (pasos 57 a 63)

La web carga todos los Mundiales al arrancar, una sola vez (`cargar_todos()` en `mundial.py`):

| | Medida |
|---|---|
| Arrancar la web (leer y preparar los 23 Mundiales) | 0,22 s |
| Memoria | unos 41 MB |
| Página de inicio | 27 KB, unos 7 ms |
| Mundial 2026 (`/2026/`) | 245 KB, unos 30 ms |
| Un Mundial de 64 partidos (`/2022/`) | 152 KB, unos 20 ms |

La página de 2026 pesa 20 KB más que en el paso 38 por los récords y la gráfica de goles por ronda.

Cuidado al medir en este ordenador: la misma página sale a veces en 30 ms y a veces en 60 ms, sin cambiar nada. En el paso 63 pareció que la web se había vuelto el doble de lenta; al repetir la medida alternando la versión de antes y la de ahora, las dos daban 30 o 60 ms por igual. `cProfile`, que cuenta el trabajo y no el reloj, dio un 8 % más, por las secciones nuevas. Por eso conviene medir varias veces y comparar siempre en las mismas condiciones.
