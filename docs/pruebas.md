[← Volver al README](../README.md)

# Pruebas

Hay dos tipos de pruebas: unas rápidas, con **pytest**, y otras en un navegador de verdad.

## Pruebas con pytest (menos de un segundo)

- `pruebas/test_mundial.py`: prueban la lógica de `mundial.py`, sin web. Por ejemplo, que el grupo A queda México 9, Sudáfrica 4…; que el juego limpio pone a Ghana delante de Ecuador; que la línea del tiempo acaba con el resultado en los 104 partidos; o que un gol en propia puerta cuenta para el rival. También comprueban cada respuesta del quiz contra los datos: si el quiz dijera que el campeón es Argentina, la prueba fallaría y diría qué pregunta está mal.
- `pruebas/test_app.py`: prueban las rutas de `app.py` con el cliente de pruebas de Flask, que pide las páginas sin abrir ningún navegador. Por ejemplo, el filtro de estadios, que parámetros raros no rompen la página, que lo escrito en el buscador no se ejecuta como HTML, o que el quiz no deja responder dos veces. También que cada Mundial tiene su página, que 1934 no muestra grupos y 1950 no muestra eliminatorias, y que las direcciones de antes del paso 58 redirigen.
- `pruebas/test_historicos.py`: prueban los datos de 1930 a 2022. Partidos, goles y campeón de cada Mundial tienen que coincidir con cifras conocidas, apuntadas antes de importar los datos; los goles, con los marcadores; y las clasificaciones, con sus partidos. Con un *fixture* con `params`, cada prueba se repite para los 22 Mundiales.

```bash
venv/bin/python -m pytest        # resumen: un punto por prueba que pasa
venv/bin/python -m pytest -v     # el nombre de cada prueba
venv/bin/python -m pytest -k quiz   # solo las que tienen "quiz" en el nombre
```

Si una prueba falla, pytest muestra la línea del `assert` y qué valor salió en lugar del esperado. La configuración (dónde están las pruebas) está en `pyproject.toml`.

## Cobertura: qué código prueban las pruebas

Con **pytest-cov**, cada vez que se ejecuta pytest sale al final una tabla con qué parte de `app.py` y `mundial.py` han ejecutado las pruebas:

```
Name         Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------
app.py          61      0     16      0   100%
mundial.py     163      0     58      0   100%
```

- **Stmts / Miss:** cuántas líneas de código hay y cuántas no ha ejecutado ninguna prueba.
- **Branch / BrPart:** cuántos caminos hay (cada `if` tiene dos, sí y no) y cuántos `if` se han probado solo por uno de ellos.
- **Missing:** lo que falta por probar. `265` es una línea, y `65->67` un salto de la línea 65 a la 67 que no ha ocurrido nunca.

Ahora está todo al 100 %. Para llegar hasta ahí se añadieron dos pruebas: una que comprueba que `cargar()` avisa si los goles no cuadran, y otra que pide una ronda y una selección concretas.

GitHub Actions y el hook `pre-push` ejecutan pytest con `--cov-fail-under=100`, así que **fallan si queda algo sin probar**. Al ejecutar solo algunas pruebas (`-k quiz`), la cobertura baja, pero en tu ordenador no falla. Un 100 % no garantiza que no haya errores: solo que cada línea se ha ejecutado al menos una vez en alguna prueba.

```bash
venv/bin/python -m pytest --cov-fail-under=100   # lo mismo que hacen Actions y el hook
venv/bin/python -m pytest --no-cov               # sin medir la cobertura
```

## Pruebas en el navegador (unos 30 segundos)

`pruebas/probar_web.py` arranca la web de Flask, la abre en un navegador automático (Chromium, con [Playwright](https://playwright.dev/python/)) y comprueba cada sección. Por ejemplo:
- que el filtro de México deja 3 estadios y se mantiene al elegir una ronda;
- que el buscador encuentra «mexico» sin tilde;
- que la final muestra el gol de Ferran Torres;
- que el quiz llega al resultado;
- que la página de inicio muestra los 23 Mundiales y enlaza al de 2026;
- que 1950, 1934 y 1982 se ven bien en el móvil, que Argentina 1982 cayó en la segunda fase de grupos y que el filtro de Japón de 2002 deja sus 10 estadios;
- que las direcciones de antes del paso 58 (`/partido/103`) llevan a las nuevas.

Lo hace en pantalla de escritorio y de móvil, y avisa si sale algún error en la consola del navegador. También abre una dirección que no existe y comprueba la página 404. Al final abre la web en modo claro y en modo oscuro (`color_scheme`): comprueba que el fondo es el de cada tema y pasa axe en los dos. Ojo: si no se le dice nada, Playwright simula el modo claro, así que las demás pruebas piden el oscuro a propósito.


Además revisa la accesibilidad, el teclado y lo que oiría un lector de pantalla: está explicado en [accesibilidad.md](accesibilidad.md).

La primera vez hay que descargar Chromium:

```bash
venv/bin/python -m playwright install chromium
```

Chromium necesita unas librerías del sistema. Si al ejecutar las pruebas sale un error como `libnspr4.so: cannot open shared object file`, instálalas desde una terminal normal, porque `sudo` pide la contraseña:

```bash
sudo apt-get install -y libnspr4 libnss3 libasound2t64
```

Para ejecutar las pruebas:

```bash
venv/bin/python pruebas/probar_web.py
```

Cada comprobación sale con ✅ o ❌. Al final pone «Todo correcto» o cuántos fallos hay. También se puede probar una web ya publicada: `venv/bin/python pruebas/probar_web.py <dirección>`.


## Pruebas automáticas en GitHub

`.github/workflows/pruebas.yml` hace que GitHub ejecute las mismas pruebas, primero pytest y después el navegador, en cada Pull Request y cada vez que algo llega a `main`. Allí Flask y pytest se instalan solos.

**El navegador en GitHub es otro.** Los servidores de GitHub ya traen Google Chrome instalado, y las pruebas lo usan con la variable `CANAL_NAVEGADOR=chrome` (Playwright lo abre con `channel="chrome"`). En tu ordenador, sin esa variable, se sigue usando el Chromium de Playwright. Al empezar, la prueba dice cuál usa: `Navegador: chromium 156...`.

Por qué: antes se instalaba el Chromium de Playwright con `--with-deps`, que pide a `apt` (el instalador de Ubuntu) las librerías y fuentes del sistema. Un día, con el servidor de paquetes lento, ese paso tardó 8 minutos y medio, cuando lo normal eran 28 segundos (unos 14 de `apt` y 14 de descarga). Guardar Chromium en la caché no lo habría evitado, porque lo lento era `apt`. Con el Chrome de GitHub no hay que instalar nada.

- En la Pull Request aparece una marca ✅ o ❌ junto al commit, y la sección de checks indica si las pruebas han pasado.
- Para ver el detalle, ve a la pestaña **Actions** del repositorio, o pulsa la insignia «Pruebas» de arriba del todo del README.

## Pruebas de la web publicada en Render

`.github/workflows/probar-render.yml` pasa `probar_web.py` contra <https://mundial-2026-j5o8.onrender.com> justo después de cada publicación. Así se comprueba que lo que se ve en internet funciona, y no solo la copia de tu ordenador o de GitHub.

- **Cuándo se lanza:** Render avisa a GitHub cada vez que publica, con un *deployment*. En la portada del repositorio se ven en **Deployments**. Cuando ese aviso pasa a `success`, GitHub lanza este flujo con el evento `deployment_status`.
- **Por qué va en un archivo aparte:** Render solo publica cuando han pasado **todas** las comprobaciones del commit (`checksPass`). Si esta prueba estuviera en `pruebas.yml`, Render la esperaría a ella y ella esperaría a Render, y ninguna de las dos acabaría nunca.
- **Antes de probar**, despierta la web con `curl`, porque en el plan gratis puede estar dormida.
- **Después comprueba que la web sirve de verdad el commit recién publicado.** La dirección `/version` dice qué commit está sirviendo: Render lo guarda en la variable de entorno `RENDER_GIT_COMMIT`, y en tu ordenador sale «desarrollo». El flujo pregunta cada 30 segundos, durante 10 minutos como mucho. Si no coincide, falla con «Render dijo que publicó X, pero la web sigue sirviendo Y». Se añadió en el paso 47 porque, con el paso 45, Render avisó de que había publicado, pero la web siguió con la versión anterior, y solo se notó porque falló una prueba del navegador.
- **Después**, pide la nota de seguridad al Observatory de Mozilla (`pruebas/nota_observatory.py`), y falla si baja de A+.
- **Para lanzarla a mano:** pestaña **Actions** → «Probar la web en Render» → **Run workflow**.
- **Si falla**, sale una ❌ en la pestaña **Actions**, y normalmente GitHub avisa también por correo. La web ya está publicada, así que hay que arreglarlo con otra Pull Request.

## Dependencias al día (Dependabot)

`.github/dependabot.yml` activa **Dependabot**, un robot de GitHub. Cada lunes a las 8:00 (hora de Madrid) mira si hay versiones nuevas de lo que usa el proyecto y, si las hay, abre una Pull Request que cambia el número de versión. Solo propone versiones publicadas hace **más de 3 días** (`cooldown`): si alguien publicara una versión con código malicioso, suele descubrirse y retirarse antes. Por eso, al activarlo, no propuso Playwright 1.64.1, que había salido 7 horas antes. En el registro de Dependabot (pestaña **Actions** → «Dependabot Updates») se lee «Filtered out 1 versions due to cooldown».
- **Paquetes de Python** (`requirements.txt` y `requirements-dev.txt`): van juntos en dos grupos, `web` (Flask y gunicorn) y `pruebas` (pytest, pytest-cov, Playwright y axe). Así llega una Pull Request por grupo, no una por paquete.
- **Acciones de GitHub** (`actions/checkout`, `actions/setup-python`).

En esa Pull Request se lanzan solas las pruebas de GitHub Actions. Si pasan, se puede fusionar como cualquier otra, y Render publicará la versión nueva. Después, en tu ordenador:

```bash
git pull
venv/bin/pip install -r requirements.txt -r requirements-dev.txt
venv/bin/python -m playwright install chromium   # solo si ha cambiado la versión de Playwright
```

Si no lo haces, el hook `pre-push` seguirá probando con las versiones viejas que tienes instaladas.

## Proteger `main`: pruebas antes de cada `git push`

GitHub puede bloquear la fusión de una Pull Request si las pruebas fallan, pero en el plan gratuito solo en repositorios públicos, y este es privado. Por eso la protección está en tu ordenador: `.githooks/pre-push` es un *hook* de Git, un script que Git ejecuta solo antes de cada `git push`.

- Primero ejecuta pytest, que tiene que llegar al 100 % de cobertura. Si falla, el push se cancela al momento, sin abrir el navegador.
- Después ejecuta las pruebas en el navegador.
- Si todo pasa, el push sigue: «✅ Pruebas superadas. Subiendo...».
- Si algo falla, el push se cancela y se muestra qué prueba ha fallado.
- Al borrar una rama (`git push origin --delete ...`) no se ejecutan las pruebas.

Git no activa los hooks de un repositorio por su cuenta, por seguridad. En cada copia del proyecto hay que activarlo una vez:

```bash
git config core.hooksPath .githooks
```

Si algún día necesitas subir algo urgente sin probar: `git push --no-verify`.
