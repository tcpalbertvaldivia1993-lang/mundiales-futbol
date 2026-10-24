# Mundiales de fútbol, de 1930 a 2026

[![Pruebas](https://github.com/tcpalbertvaldivia1993-lang/mundiales-futbol/actions/workflows/pruebas.yml/badge.svg)](https://github.com/tcpalbertvaldivia1993-lang/mundiales-futbol/actions/workflows/pruebas.yml)

Web sobre todos los Mundiales de fútbol masculinos, de Uruguay 1930 a Norteamérica 2026, hecha con **Python y Flask**. Empezó como una web del Mundial 2026 (por eso la dirección de la web empieza por `mundial-2026`), y desde el paso 57 tiene una página de inicio con todos los Mundiales y una página para cada uno. Es un proyecto de práctica: los datos están en JSON, la lógica en Python y el HTML en plantillas Jinja2. No usa nada de JavaScript.

> Este repositorio es la copia pública del proyecto. Se desarrolló en un repositorio privado, en 69 pasos (cada uno, una rama y una Pull Request); lo aprendido por el camino está en «Lo aprendido» más abajo. Allí siguen también Dependabot y la prueba automática de la web publicada, que no están en esta copia.

**Web publicada:** <https://mundial-2026-j5o8.onrender.com/> (si lleva un rato sin visitas, la primera carga puede tardar casi un minuto).

## Cómo funciona

- `mundial.py` lee los JSON de `data/` (los de 2026, y los de 1930 a 2022 en `data/historicos/`) y calcula todo lo que muestra la web: clasificaciones, mejores terceros, el camino de cada selección, goleadores, líneas del tiempo...
- `app.py` es la aplicación de Flask. Cada vez que alguien abre la página, la prepara con los datos de `mundial.py` y las plantillas de `templates/`.
- Lo que se elige en la página va en la dirección, como parámetros. Por ejemplo, `/2026/?pais=México#sedes` filtra los estadios y `/2026/?seleccion=Japón#camino` muestra el camino de Japón. Por eso los filtros y los botones son enlaces y formularios que piden otra vez la página al servidor.
- El quiz guarda cómo va (pregunta, aciertos) en la **sesión** de Flask, que es una cookie firmada. Cada respuesta se envía con un formulario `POST`. La cookie solo se crea al responder el quiz o al elegir el tema: quien solo mira la web no recibe ninguna. Si se reinicia el quiz y no queda nada más en la sesión, Flask la borra.
- **Página de inicio con todos los Mundiales** (`/`, desde el paso 59): los 23 Mundiales con su sede, campeón, partidos y goles; los títulos de cada selección (los de Alemania Federal cuentan para Alemania, como hace la FIFA); los máximos goleadores de la historia, sumando los datos de Fjelstul y los de 2026; y una gráfica de goles por partido en cada Mundial. Lo calcula `cargar_historia()` en `mundial.py`, al arrancar. Para sumar bien los goles de un jugador escrito de dos formas («Julián Alvarez» en los datos de 2026 y «Julián Álvarez» en los de Fjelstul) está `MISMO_JUGADOR`. La gráfica usa la misma macro que la de rondas, `grafica_goles_por_partido()`, con otros parámetros. La página tiene su propio menú: `base.html` deja cambiarlo con `{% block cabecera %}`.
- **Tres idiomas: español, portugués e inglés** (desde el paso 65). Se elige con unos botones en la página de inicio y en el pie de todas, que funcionan sin JavaScript como los del tema: envían un formulario a `/idioma`, Flask guarda la elección en la sesión y vuelve a la misma página. Si no se ha elegido, se usa el idioma del navegador (`request.accept_languages`). Los textos están en `textos.py`: el texto en español es la llave de su traducción, y en las plantillas se escribe `t("Campeones")`; lo que aún no está traducido sale en español. Los nombres de selecciones y rondas están en `data/nombres.json` y se traducen con el filtro `| nombre`. `<html lang>` cambia con el idioma, para que el lector de pantalla pronuncie bien. Las abreviaturas también cambian, con su forma larga para el lector de pantalla: «(a.e.t.)» se lee «after extra time». Desde el paso 67 están traducidas también las páginas de cada Mundial, con las fechas («Jul 19» en inglés), las ciudades y las marcas de los goles («(o.g.)», «(g.c.)»). Desde el paso 68 está traducida toda la web: también la página de cada partido, el cara a cara, la 404, la 500 y el quiz, cuyas preguntas en portugués e inglés están en `data/quiz.json`.
- **Cada selección en todos los Mundiales** (desde el paso 64): `/selecciones` lista las 84, y `/seleccion/Brasil` muestra los Mundiales que jugó una, hasta dónde llegó en cada uno, sus títulos, sus máximos goleadores y, con `?contra=Argentina`, todos sus partidos contra otra. Lo calcula `historial()` en `mundial.py`, al arrancar. Las selecciones que cambiaron de nombre van con el de hoy, como hace la FIFA (`SUCESORAS`): Alemania Federal está en Alemania, y `/seleccion/Alemania%20Federal` redirige allí. Los partidos decididos en los penaltis cuentan como victoria o derrota, como en el camino de cada Mundial (la FIFA los cuenta como empate).
- **Una página para cada Mundial** (desde el paso 60): `/1930/`, `/1986/`… con las mismas secciones que la de 2026, menos el formato y el quiz. `cargar_historico()` de `mundial.py` da a cada Mundial antiguo la misma forma que el de 2026, y `completar()` calcula lo que es igual en todos (goleadores, récords, gráficas…). En `app.py`, `datos()` devuelve el Mundial de la página que se pide. Los formatos antiguos tienen sus casos: en 1934 y 1938 no hubo grupos, en 1950 no hubo final (el campeón salió de una liguilla final), de 1974 a 1982 hubo una segunda fase de grupos, y un partido que se volvió a jugar no tiene ganador (`ganador_de()` devuelve `None`). Desde el paso 61, `texto_partido()` marca esos partidos especiales: «(se volvió a jugar)», «(repetición)» y «(desempate)», y la página de cada uno lo explica y enlaza a su pareja (`pareja_de()`).
- **Un Mundial por año** (desde el paso 58): las páginas del Mundial 2026 están bajo `/2026/`. Las rutas empiezan por `<int:anio>` (sin eñe: Flask no la acepta en el nombre de un parámetro). `@app.url_value_preprocessor` guarda el año en `g` antes de cada ruta y da 404 si ese año no tiene Mundial, y `@app.url_defaults` lo añade a cada `url_for()`, así que las plantillas no han cambiado. Las direcciones de antes siguen funcionando: `/partido/12` y `/cara-a-cara` redirigen con un 301 (permanente) y los botones del quiz antiguos, con un 308, que vuelve a enviar el formulario. Una dirección antigua con parámetros, como `/?pais=México`, lleva a `/2026/?pais=México`.
- **Cada partido tiene su página:** `/2026/partido/12`, con su ronda, fecha y estadio, los goleadores, la línea del tiempo ya abierta, el camino de cada selección y el partido anterior y el siguiente. El número es el del partido ordenado por fecha: el 0 es el primero (México 2-0 Sudáfrica) y el 103, la final. En la ruta, `<int:numero>` hace que Flask solo acepte números enteros, y para un número que no existe, `abort(404)` muestra la página 404. Desde la portada se llega pulsando cualquier partido de las listas o «Ver partido» en los resultados.
- **Cara a cara:** `/2026/cara-a-cara?a=España&b=Argentina` pone dos selecciones lado a lado: hasta dónde llegó cada una, su grupo, partidos ganados, empatados y perdidos, goles a favor y en contra, y su máximo goleador. Debajo están los partidos que jugaron entre ellas. Los números los calcula `numeros_de()` en `mundial.py`, a partir de `camino()`. Por defecto compara a los dos finalistas, y se llega con «Comparar con otra selección» desde el camino de cualquier selección.
- **Gráfica de goles por minuto** (en «Goleadores»): cuántos de los 308 goles se marcaron en cada tramo de 15 minutos. Los goles del tiempo añadido («45+2», «90+5») cuentan en el tramo de su minuto, y el de 91 a 120 es la prórroga. `goles_por_tramo()` de `mundial.py` cuenta los goles. La macro `grafica_goles_por_tramo()` de `macros.html` dibuja un **SVG**, calculando en Jinja la posición y la altura de cada barra, sin JavaScript. Los colores salen de las variables CSS, así que cambian con el tema. Para quien no ve la gráfica, el SVG tiene un nombre y un resumen («el tramo con más goles es el del 76-90+, con 81»), y debajo hay una tabla con los mismos datos. Al pasar el ratón por una barra, su `<title>` dice cuántos goles son.
- **Gráfica de goles por partido en cada ronda** (en «Goleadores», debajo de la de goles por minuto): la fase de grupos, cada eliminatoria, el tercer puesto y la final. `goles_por_ronda()` de `mundial.py` suma los partidos y los goles de cada ronda (los 12 grupos cuentan juntos) y calcula la media, y el filtro `con_coma` la escribe a la española («2,99»). La macro `grafica_goles_por_ronda()` dibuja las barras **tumbadas**, para que nombres largos como «Dieciseisavos de final» se lean enteros. Destaca el tercer puesto, con 10 goles, pero fue un solo partido, como la final: la nota de encima lo avisa. Tiene, como la otra, nombre, resumen y tabla para quien no ve la gráfica.
- **Récords del Mundial** (al final de «Resultados»): la mayor goleada, el partido con más goles y cuántos partidos se decidieron en los penaltis, en la prórroga o terminaron 0-0, cada uno con el enlace a su partido. `records()` de `mundial.py` los busca entre los 104 partidos: si dos empatan en un récord, salen los dos (la mayor goleada es doble: Alemania 7-1 Curazao y Canadá 6-0 Catar). Las listas largas van plegadas en un `<details>`: se ve cuántos son, y al abrirlo, cuáles.
- **Tema claro y oscuro:** la web sigue el modo del ordenador o del móvil. En `static/styles.css`, los colores son variables (`--fondo`, `--cesped`...), y `@media (prefers-color-scheme: light)` les da otros valores. El verde y el dorado del tema claro son más oscuros, para que se lean bien sobre blanco: su contraste pasa de 4,5, el mínimo para texto. Para verlo, cambia tu sistema a modo claro, o en las DevTools de Chrome: menú ⋮ → *More tools* → *Rendering* → *Emulate CSS media feature prefers-color-scheme*.
- **Elegir el tema a mano:** en el pie hay tres botones, «Automático», «Claro» y «Oscuro». Funcionan sin JavaScript, como el quiz: cada botón envía un formulario a `/tema`, Flask guarda la elección en la sesión y vuelve a la página. `base.html` la pone en `<html data-tema="claro">`, y el CSS usa ese atributo. «Automático» quita la elección y la web vuelve a seguir al sistema. Los colores del tema claro están dos veces en `styles.css`: dentro de la `@media` y en `[data-tema="claro"]`. `probar_web.py` comprueba que las dos copias son iguales.

## Cómo verla

Con el entorno virtual creado (ver «Entorno virtual»):

```bash
cd ~/mundial-2026
venv/bin/flask --app app run --debug
```

Después abre <http://127.0.0.1:5000>. Con `--debug`, Flask recarga la web solo cuando cambias el código y muestra los errores con detalle. Para pararlo, pulsa `Ctrl+C`.

## Entorno virtual

El proyecto usa un entorno virtual en `venv/`. La carpeta no se sube a GitHub (está en `.gitignore`), así que en un ordenador nuevo hay que crearla e instalar lo necesario:

```bash
cd ~/mundial-2026
python3 -m venv venv
venv/bin/pip install -r requirements.txt        # Flask y gunicorn, para la web
venv/bin/pip install -r requirements-dev.txt    # pytest, pytest-cov, Playwright y axe, para las pruebas
```

## Web publicada

La web está en **<https://mundial-2026-j5o8.onrender.com/>**, en [Render](https://render.com). Cada vez que algo llega a `main` y pasan las pruebas, Render la vuelve a publicar sola. Después, GitHub la prueba de nuevo: comprueba que sirve la versión recién publicada (`/version`), pasa las pruebas del navegador y pide la nota de seguridad al Observatory de Mozilla.

Todo el detalle está en [docs/publicacion.md](docs/publicacion.md).

## Pruebas

```bash
venv/bin/python -m pytest                   # la lógica y las rutas, en un par de segundos (100 % de cobertura)
venv/bin/python pruebas/probar_web.py       # la web en un navegador de verdad, en ordenador y móvil
```

GitHub las ejecuta solas en cada Pull Request, y el hook `pre-push` antes de cada `git push` (hay que activarlo una vez con `git config core.hooksPath .githooks`). Todo el detalle está en [docs/pruebas.md](docs/pruebas.md).

## Documentación

| Documento | De qué trata |
|---|---|
| [docs/publicacion.md](docs/publicacion.md) | Cómo se publica la web en Render y qué pasó con la versión antigua de GitHub Pages. |
| [docs/pruebas.md](docs/pruebas.md) | pytest y la cobertura, las pruebas en el navegador, GitHub Actions, las pruebas contra Render, Dependabot y el hook `pre-push`. |
| [docs/accesibilidad.md](docs/accesibilidad.md) | axe-core, la prueba de teclado, lo que oye un lector de pantalla y cómo probarlo tú con NVDA. |
| [docs/velocidad.md](docs/velocidad.md) | Qué se midió y qué se cambió para que la web cargue más rápido. |
| [docs/seguridad.md](docs/seguridad.md) | Las cabeceras de seguridad, la cookie de la sesión y la nota del Observatory de Mozilla. |

## Qué hace cada archivo

| Archivo | Qué practica |
|---|---|
| `app.py` | Flask: rutas (`@app.route`), parámetros de la dirección (`request.args`), formularios `POST`, redirecciones y la sesión. |
| `textos.py` | Los textos de la web en portugués e inglés, con el texto en español como llave, y las funciones `traducir()` y `nombre()`. |
| `templates/selector_idioma.html` | Los botones Español, Português y English. |
| `mundial.py` | La lógica en Python puro: leer JSON, ordenar con `sorted(key=...)`, diccionarios, comprensiones de listas. No sabe nada de Flask. |
| `templates/base.html` | La estructura común: cabecera, menú, pie y botón ↑. Las demás plantillas la heredan (`{% extends %}`). |
| `templates/index.html` | La página: junta las 8 secciones con `{% include %}`. |
| `templates/secciones/` | Una plantilla por sección: portada, sedes, selecciones, formato, resultados, camino, goleadores y quiz. |
| `templates/selecciones.html` y `templates/seleccion.html` | La lista de selecciones (`/selecciones`) y la página de cada una (`/seleccion/Brasil`). |
| `templates/cabecera_historia.html` | El logo y el menú de las páginas de toda la historia (inicio, selecciones), con `{% include %}`. |
| `templates/inicio.html` | La página de inicio (`/`): todos los Mundiales, campeones, goleadores de la historia y la gráfica. Cambia el menú de `base.html` con `{% block cabecera %}`. |
| `templates/partido.html` | La página de cada partido (`/2026/partido/12`). Usa `linea_contenido()` de `macros.html` para la línea del tiempo, que aquí siempre se ve. |
| `templates/404.html` | La página «Fuera de juego» para direcciones que no existen. `app.py` la muestra con `@app.errorhandler(404)` y devuelve el código 404. Hereda el diseño de `base.html` y quita el botón ↑ dejando vacío su bloque. |
| `templates/500.html` | La página «Tarjeta roja» para cuando falla el código de Python (`@app.errorhandler(500)`). No enseña el error: Flask lo guarda en el registro, que en Render está en **Logs**. Con `flask run --debug` no sale: en su lugar aparece el depurador de Flask, con el error. |
| `templates/macros.html` | Trozos de HTML que se repiten: un partido en una lista, sus goleadores, la línea del tiempo. Son como funciones de Jinja2 (`{% macro %}`). |
| `static/styles.css` | El diseño: variables de color en `:root` (con otros valores para el tema claro), `grid`, mobile-first, y el botón ↑ que aparece al bajar solo con CSS. |
| `data/estadios.json` | Los 16 estadios: nombre, ciudad, país y aforo. |
| `data/grupos.json` | Los 12 grupos (A–L) con sus 4 selecciones. |
| `data/partidos-grupos.json` | Los 72 partidos de la fase de grupos. Las tablas no se guardan: las calcula `mundial.py`. |
| `data/resultados.json` | Los 32 partidos de eliminatorias por ronda. El ganador lo calcula `mundial.py` con los goles y los penaltis. |
| `data/goleadores.json` | Los 178 goleadores y los goles en propia puerta. `mundial.py` comprueba al arrancar que suman lo mismo que los marcadores. |
| `data/goles.json` | Los 308 goles uno a uno: partido, jugador, selección, minuto y si fue de penalti o en propia puerta. |
| `data/quiz.json` | Las 10 preguntas del quiz, cada una con su traducción (`pt`, `en`). `correcta` es la posición de la respuesta (empieza en 0). Una prueba comprueba cada respuesta contra los datos: al añadir una pregunta, hay que añadirla también en `test_las_respuestas_del_quiz_cuadran_con_los_datos`. |
| `data/nombres.json` | Los nombres de las 92 selecciones, de las rondas y de las ciudades que cambian en portugués (de Brasil) e inglés. |
| `data/fuentes.md` | De dónde salen los datos. La web lo muestra en `/fuentes`. |
| `data/historicos/` | Los 22 Mundiales de 1930 a 2022, un JSON por Mundial (`1930.json`…), de la base de datos de Fjelstul (licencia CC BY-SA 4.0, ver `data/fuentes.md`). La web todavía no los usa. |
| `herramientas/importar_historicos.py` | Descarga la base de datos de Fjelstul (CSV), la traduce con `herramientas/traducciones.json` y crea `data/historicos/`. Solo hace falta volver a ejecutarlo si cambian las traducciones: `venv/bin/python herramientas/importar_historicos.py`. Si falta la traducción de una selección o ronda, se para en vez de dejarla en inglés. |
| `requirements.txt` | Lo que necesita la web: Flask y gunicorn. |
| `docs/` | Las explicaciones largas: publicación, pruebas, accesibilidad, velocidad y seguridad (ver «Documentación»). |
| `render.yaml` | La configuración de Render (ver [docs/publicacion.md](docs/publicacion.md)). |
| `.python-version` | La versión de Python, para Render y para GitHub Actions. |
| `requirements-dev.txt` | Lo que necesitan las pruebas: pytest, pytest-cov, Playwright y axe. |
| `pyproject.toml` | La configuración de pytest y de la cobertura. |
| `pruebas/test_mundial.py` | Pruebas de la lógica con pytest: `assert`, *fixtures* y `parametrize`. |
| `pruebas/test_app.py` | Pruebas de las rutas con el cliente de pruebas de Flask. |
| `pruebas/test_textos.py` | Pruebas de los idiomas: que cada `t("...")` de las plantillas tiene su traducción, con los mismos datos entre llaves, y que todas las selecciones y rondas tienen nombre en los tres idiomas. |
| `pruebas/test_historicos.py` | Pruebas de los datos de 1930 a 2022: cifras conocidas, goles que cuadran con los marcadores y clasificaciones que cuadran con sus partidos. Un *fixture* con `params` repite cada prueba para los 22 Mundiales. |
| `pruebas/probar_web.py` | Las pruebas en el navegador (ver [docs/pruebas.md](docs/pruebas.md)). |
| `pruebas/nota_observatory.py` | Pide la nota de seguridad de la web publicada al Observatory de Mozilla (ver [docs/seguridad.md](docs/seguridad.md)). Usa `urllib`, de la biblioteca estándar de Python. |
| `.github/workflows/pruebas.yml` | Le dice a GitHub cómo ejecutar las pruebas en cada Pull Request. |
| `.github/workflows/probar-render.yml` | Prueba la web de Render cada vez que Render termina de publicar. (Solo en el repositorio privado, que es el que publica Render.) |
| `.github/dependabot.yml` | Le dice a Dependabot qué revisar cada semana para abrir Pull Requests con versiones nuevas. (Solo en el repositorio privado.) |
| `.githooks/pre-push` | Ejecuta las pruebas antes de cada `git push` y lo cancela si fallan. |

Para cambiar un dato, edita el JSON y reinicia la web: Flask lee los datos al arrancar.

## Lo aprendido en 68 pasos

Cada paso fue una rama, una Pull Request y una fusión en `main`. Así quedó el camino:

| Pasos | Qué se hizo | Qué se aprendió |
|---|---|---|
| 1–17 | La web en HTML, CSS y JavaScript: resultados, grupos, estadios, camino de cada selección, goleadores, líneas del tiempo y botones para moverse. | Separar los datos (JSON) de lo que se muestra, y calcular las tablas en vez de guardarlas. Respetar «menos animaciones» en toda la web. |
| 18–22 | Pruebas en el navegador con Playwright, GitHub Actions, el hook `pre-push` y la publicación en GitHub Pages. | Que las pruebas se ejecuten solas: en GitHub en cada Pull Request y en el ordenador antes de cada `git push`. |
| 23–30 | La web pasa a **Python y Flask**, con pruebas de pytest, publicación en Render, cobertura y páginas 404 y 500. | Rehacer la web en el lenguaje que se conoce: enlaces y formularios en lugar de JavaScript. `mundial.py` no sabe nada de Flask, y eso lo hace fácil de probar. |
| 31–37 | Accesibilidad (axe-core, teclado y lector de pantalla) y tema claro y oscuro. | Una web puede verse bien y sonar mal. El lector de pantalla necesita abreviaturas completas, tablas con nombre y minutos que se lean como minutos. |
| 38–44 | Velocidad, cabeceras de seguridad (nota A+), la cookie solo cuando hace falta y Dependabot. | Medir antes de cambiar, y descartar lo que ahorra poco. Revisar la seguridad con una herramienta externa y vigilarla en cada publicación. |
| 45–50 | Una página para cada partido, la comprobación de `/version`, la documentación en `docs/`, la gráfica de goles en SVG y el cara a cara. | Añadir páginas nuevas reutilizando lo que ya había (`camino()`, las macros). Dibujar una gráfica solo con Jinja y CSS. |
| 51–56 | Este resumen, las notas para retomar el proyecto, la gráfica de goles por partido en cada ronda, los récords del Mundial y el quiz de 10 preguntas comprobadas contra los datos. | Elegir la forma de la gráfica por sus datos (barras tumbadas para nombres largos). Que una prueba vigile que el texto escrito a mano (el quiz) dice lo mismo que los datos. |
| 57–63 | Todos los Mundiales: los datos de 1930 a 2022 (base de datos de Fjelstul, traducida), cada Mundial bajo su año (`/1986/`) con las direcciones antiguas redirigidas, la página de inicio con la historia y una página para cada Mundial, con sus formatos raros. | Importar datos de otros con un script que se para ante lo que no entiende, y comprobarlos con cifras apuntadas antes. Generalizar sin romper lo que había: `url_defaults` para no tocar las plantillas, `completar()` para lo común. |
| 64–68 | La página de cada selección en todos los Mundiales y la web en tres idiomas: español, portugués e inglés. | Traducir con un diccionario propio, con el texto en español como llave, para ir por partes (lo que falta sale en español) y probar que no falta ninguna traducción. No llamar `t` ni `nombre` a una variable: tapa a la función. |

Algunas lecciones que sirven para cualquier proyecto:

- **Comprobar los datos y apuntar de dónde salen** (`data/fuentes.md`). `mundial.py` además comprueba al arrancar que los goleadores suman lo mismo que los marcadores.
- **Que un aviso diga «publicado» no significa que se publicó.** Render avisó una vez de que había publicado y siguió sirviendo la versión anterior. Desde entonces, `/version` dice qué commit está en marcha y GitHub lo comprueba (paso 47).
- **Cuidado con las esperas en círculo.** Render espera a que pasen las pruebas del commit. Si la prueba contra Render fuera una de ellas, cada una esperaría a la otra. Por eso esa prueba va en un flujo aparte.
- **Lo lento a veces está fuera del código.** En GitHub, instalar Chromium con `apt` tardó una vez 8 minutos y medio, y la solución fue usar el Chrome que ya traen sus servidores (paso 40).
- **Pasos pequeños**, cada uno con sus pruebas, para saber siempre qué cambio rompió qué.
- **Mirar el código antes de proponer algo nuevo.** En el paso 52 se apuntaron como ideas la clasificación de cada grupo y los partidos de cada estadio, y los dos ya existían.
- **Apuntar lo que se espera antes de mirar los datos.** Los partidos, goles y campeón de los 22 Mundiales se escribieron en la prueba antes de importar; si se escriben después, se copia lo que dicen los datos, errores incluidos (paso 57).
- **Unir por lo que no cambia.** En la base de Fjelstul, la segunda fase de 1982 se llama «1, 2, 3, 4» en los partidos y «A, B, C, D» en las clasificaciones. Unirlos por las selecciones que juegan, y no por el nombre, lo resolvió (paso 57).
- **Medir dos veces.** En el paso 63 pareció que la web era el doble de lenta. Repitiendo la medida, alternando las dos versiones, salió que el ordenador a veces va a la mitad de velocidad, y las dos versiones por igual.
- **Las pruebas también dependen de dónde se ejecutan.** En el paso 65, la web empezó a salir en el idioma del navegador. En mi ordenador las pruebas pasaban, y en GitHub fallaron, porque su Chrome está en inglés. Ahora cada prueba del navegador dice qué idioma pide.
- **Comprobar que una prueba falla cuando debe.** Una prueba que siempre pasa no vigila nada. En el paso 55 se marcó a propósito una respuesta equivocada en el quiz, para ver que la prueba lo detectaba.

## Licencia

- **El código** tiene licencia [MIT](LICENSE): se puede usar, cambiar y compartir, también en otros proyectos, siempre que se mantenga el aviso de copyright y la licencia.
- **Los datos de 1930 a 2022** (`data/historicos/`) no son míos: salen de la base de datos de Joshua C. Fjelstul y tienen licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Quien los use tiene que citar la fuente y mantener esa licencia (ver `data/fuentes.md`).
- **Los datos de 2026** están recopilados de las fuentes que se citan en `data/fuentes.md`.

## Ideas para seguir

- Escuchar la web con NVDA (ver «Pruébalo tú con NVDA» en [docs/accesibilidad.md](docs/accesibilidad.md)) y arreglar lo que suene raro.
