"""Abre la web en un navegador automático (Playwright + Chromium) y comprueba cada sección.

Uso, desde la carpeta del proyecto:
    venv/bin/python pruebas/probar_web.py                 # arranca la web de Flask y la prueba
    venv/bin/python pruebas/probar_web.py <dirección>     # prueba una web ya publicada

Por defecto usa el Chromium que descarga Playwright. Con la variable de entorno CANAL_NAVEGADOR=chrome
usa el Google Chrome instalado en el sistema (lo hace GitHub Actions, que ya lo trae instalado).
"""

import logging
import os
import sys
import threading
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # para poder importar app.py
fallos = []
axe = Axe()  # axe-core: revisa la accesibilidad de una página (contraste, etiquetas, títulos...)


def nueva_pagina(navegador, **opciones):
    """Una página nueva, con el navegador en español (locale="es-ES").

    Desde el paso 65 la web sale en el idioma del navegador. El Chrome de GitHub está en inglés,
    y sin esto la web salía en inglés y las pruebas no encontraban los textos en español.
    """
    return navegador.new_page(locale="es-ES", **opciones)


def comprobar(descripcion, condicion):
    print(("  ✅ " if condicion else "  ❌ ") + descripcion)
    if not condicion:
        fallos.append(descripcion)


def arrancar_servidor():
    """La web de Flask, en un hilo y en un puerto libre (como "flask run", pero dentro de las pruebas)."""
    from app import app

    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # sin una línea por cada petición
    servidor = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor, f"http://127.0.0.1:{servidor.server_port}/"


def pulsar(pagina, selector):
    """Pulsa un enlace o botón y espera a que Flask devuelva la página nueva."""
    pagina.locator(selector).first.click()
    pagina.wait_for_load_state("load")


def revisar_accesibilidad(pagina, donde):
    """Pasa axe-core por la página tal como está ahora mismo.

    axe solo revisa lo que se ve: por eso se llama en varios momentos (con un detalle abierto,
    con el quiz respondido...). Si encuentra algo, muestra la regla, qué elemento y un enlace
    que explica cómo arreglarlo.
    """
    # preload: False -> axe no descarga el CSS por su cuenta: la Content-Security-Policy de la web
    # (connect-src) no se lo permite, y saldría un error en la consola que no es de la web
    problemas = axe.run(pagina, options={"resultTypes": ["violations"], "preload": False}).response["violations"]
    comprobar(f"accesibilidad: {donde}", not problemas)
    for problema in problemas:
        print(f"      · {problema['id']} ({problema['impact']}): {problema['help']}")
        print(f"        {problema['helpUrl']}")
        for elemento in problema["nodes"][:3]:
            print(f"        en {', '.join(elemento['target'])}")


def probar_accesibilidad(pagina):
    print("Accesibilidad (axe-core)")
    revisar_accesibilidad(pagina, "la portada, arriba del todo")
    pulsar(pagina, ".enlace-jugador >> text=Kylian Mbappé")
    revisar_accesibilidad(pagina, "con los partidos de un goleador abiertos")
    pulsar(pagina, ".opcion")
    revisar_accesibilidad(pagina, "con una pregunta del quiz respondida")
    pagina.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pagina.wait_for_timeout(300)
    revisar_accesibilidad(pagina, "abajo del todo, con el botón ↑ visible")


# Dónde está el foco y cómo se ve (lo calcula el navegador, en JavaScript)
FOCO = """() => {
  const e = document.activeElement, estilo = getComputedStyle(e), caja = e.getBoundingClientRect();
  const linea = e.getClientRects()[0] || caja;  // la primera línea del elemento
  const cabecera = document.querySelector('.cabecera').getBoundingClientRect().bottom;
  e.dataset.alcanzado = '1';  // para saber después a cuáles se ha llegado
  return {
    elemento: e === document.body ? null : (e.innerText || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 30),
    borde: estilo.outlineStyle === 'solid' && parseFloat(estilo.outlineWidth) >= 2,
    // Tapado por la cabecera (lo de la cabecera no cuenta, ni "Saltar al contenido", que va encima a propósito),
    // o por cualquier otra cosa: lo que se ve en el centro del elemento tiene que ser el propio elemento.
    // Se mira la primera línea: si un enlace ocupa dos, el centro de su caja cae entre las líneas
    tapado: (!e.closest('.cabecera') && !e.matches('.saltar') && caja.top < cabecera - 1)
            || (caja.top >= 0 && caja.bottom <= innerHeight &&
                !e.contains(document.elementFromPoint(linea.left + linea.width / 2, linea.top + linea.height / 2))),
    en_pantalla: caja.bottom > 0 && caja.top < innerHeight,
  };
}"""


def probar_teclado(navegador, direccion, ancho):
    """Recorre la portada solo con la tecla Tab, como quien no usa ratón."""
    # Con "menos animaciones" la página salta sin desplazamiento suave: así se mide dónde acaba cada cosa
    pagina = nueva_pagina(navegador, viewport={"width": ancho, "height": 800}, reduced_motion="reduce", color_scheme="dark")
    pagina.goto(direccion)
    # Las fuentes de Google llegan un poco después que la página. Al llegar, los títulos cambian de alto
    # y todo se recoloca: si pasa a mitad del recorrido, alguna medida sale mal. Se espera a que estén
    pagina.evaluate("document.fonts.ready.then(() => true)")

    pagina.keyboard.press("Tab")
    foco = pagina.evaluate(FOCO)
    comprobar("el primer Tab llega a 'Saltar al contenido' y se ve",
              foco["elemento"] == "Saltar al contenido" and foco["en_pantalla"])
    pagina.keyboard.press("Enter")
    pagina.keyboard.press("Tab")
    comprobar("tras pulsarlo, el siguiente Tab ya va al contenido (no al menú)",
              pagina.evaluate("document.querySelector('main').contains(document.activeElement)"))

    # Todo lo que se ve y se puede usar: enlaces, botones, campos y desplegables
    pagina.evaluate("window.scrollTo(0, 0)")
    usables = pagina.evaluate("""[...document.querySelectorAll('a[href], button:not([disabled]), input, select, summary')]
                                   .filter(e => e.checkVisibility({visibilityProperty: true})).length""")
    pagina.evaluate("document.activeElement.blur()")
    recorrido = []
    for tecla in ("Tab", "Shift+Tab"):  # hacia delante y hacia atrás (al volver, la cabecera puede tapar)
        for _ in range(usables + 5):
            pagina.keyboard.press(tecla)
            foco = pagina.evaluate(FOCO)
            if foco["elemento"] is None:
                break  # se ha llegado al final (o al principio) de la página
            recorrido.append(foco)
    # Al terminar se está otra vez arriba del todo, donde el botón ↑ está oculto: ese no cuenta
    sin_alcanzar = pagina.evaluate("""[...document.querySelectorAll('a[href], button:not([disabled]), input, select, summary')]
        .filter(e => e.checkVisibility({visibilityProperty: true}) && !e.dataset.alcanzado).map(e => e.innerText.trim())""")
    comprobar(f"con Tab se llega a todo lo que se puede usar ({usables} enlaces, botones y campos)", not sin_alcanzar)
    for elemento in sin_alcanzar[:5]:
        print(f"        sin alcanzar: {elemento}")
    comprobar("todos muestran el borde dorado al tener el foco", all(f["borde"] for f in recorrido))
    tapados = [f["elemento"] for f in recorrido if f["tapado"] or not f["en_pantalla"]]
    comprobar("la cabecera no tapa ninguno y todos quedan en pantalla", not tapados)
    for elemento in tapados[:5]:
        print(f"        tapado o fuera: {elemento}")

    # Usar la web con el teclado: Enter en un filtro
    pagina.focus("#sedes .filtro >> text=México")
    with pagina.expect_navigation():  # espera a que llegue la página nueva
        pagina.keyboard.press("Enter")
    comprobar("Enter en el filtro México lo aplica", pagina.locator("#sedes .tarjeta").count() == 3)
    pagina.close()


def probar_lector_pantalla(pagina, direccion):
    """Lo que oiría un lector de pantalla (NVDA, Orca...).

    El lector no lee el HTML tal cual, sino el "árbol de accesibilidad" que construye el navegador:
    cada cosa con su papel (tabla, enlace, botón...) y su nombre. get_by_role() y aria_snapshot()
    de Playwright buscan en ese árbol, así que comprueban lo que se oye, no lo que se ve.
    """
    print("Lector de pantalla")
    pagina.context.clear_cookies()  # el quiz vuelve a empezar (su estado está en la cookie de la sesión)
    pagina.goto(direccion + "?jugador=Kylian Mbappé|Francia&ronda=4")
    comprobar("cada tabla tiene nombre ('Clasificación del grupo A'...)",
              pagina.locator("table:not(:has(caption))").count() == 0
              and pagina.get_by_role("table", name="Clasificación del grupo A").count() == 1
              and pagina.get_by_role("table", name="Goleadores del Mundial").count() == 1)
    comprobar("las abreviaturas se leen enteras ('PJ' → 'Partidos jugados')",
              pagina.get_by_role("columnheader", name="Partidos jugados").count() == 12
              and pagina.get_by_role("columnheader", name="PJ", exact=True).count() == 0)
    comprobar("se oye qué selecciones se clasificaron (no solo la barra verde)",
              pagina.get_by_role("rowheader", name="México (clasificada)").count() == 1
              and pagina.get_by_role("rowheader", name="Chequia", exact=True).count() == 1)
    camino = pagina.locator("ol.camino").aria_snapshot()
    comprobar("en el camino se oye 'Victoria', no solo 'V'", camino.count("Victoria") == 7 and "Empate" in camino)
    comprobar("las abreviaturas se leen enteras ('19 jul' → '19 de julio', '(prór.)', '1.º', 'EE. UU.')",
              "19 de julio" in camino and "(tras la prórroga)" in camino and "(prór.)" not in camino
              and pagina.get_by_text("Primera del grupo H").count() == 1
              and pagina.get_by_role("navigation", name="Filtrar estadios por país")
                        .get_by_role("link", name="Estados Unidos", exact=True).count() == 1)
    detalle = pagina.locator("tr.detalle-goleador").aria_snapshot()
    comprobar("y también en los goles: '(pen.)' → '(de penalti)'", "(de penalti)" in detalle and "(pen.)" not in detalle)
    comprobar("los minutos se leen como minutos: '90+6'' → 'minuto 90 más 6'",
              "minuto 90 más 6" in detalle and "90+6'" not in detalle)
    comprobar("la gráfica de goles por minuto se oye como una imagen con nombre, y tiene su tabla",
              pagina.get_by_role("img", name="Goles por minuto").count() == 1
              and pagina.get_by_role("table", name="Goles por minuto", include_hidden=True).count() == 1)
    comprobar("la Bota de Oro se oye como tal, no como 'zapatilla deportiva'",
              pagina.get_by_role("link", name="Bota de Oro: Kylian Mbappé").count() == 1)
    pulsar(pagina, "#resultados .abrir-linea")  # abre la primera línea del tiempo de resultados
    contenido = pagina.locator("main").aria_snapshot()
    comprobar("el balón ⚽ no se lee: es decoración", "⚽" not in contenido)
    comprobar("en la línea del tiempo se oye para quién fue cada gol",
              "gol para Inglaterra" in pagina.locator("#resultados .cronologia").first.aria_snapshot())
    pulsar(pagina, ".opcion >> nth=1")  # una respuesta que no es la buena
    comprobar("en el quiz se oye cuál era la buena y cuál elegiste",
              pagina.get_by_role("button", name="48 (correcta)").count() == 1
              and pagina.get_by_role("button", name="40 (tu respuesta, incorrecta)").count() == 1)


def probar(pagina):
    print("Estadios")
    comprobar("hay 16 tarjetas de estadio", pagina.locator("#sedes .tarjeta").count() == 16)
    pulsar(pagina, "#sedes .filtro >> text=México")
    comprobar("el filtro México deja 3 estadios", pagina.locator("#sedes .tarjeta").count() == 3)
    comprobar("la dirección lleva ?pais=México", "pais=M%C3%A9xico" in pagina.url)
    pulsar(pagina, "#resultados .filtro >> text=Semifinales")
    comprobar("al elegir una ronda se mantiene el filtro de México",
              pagina.locator("#sedes .tarjeta").count() == 3 and pagina.locator(".partido").count() == 2)
    pulsar(pagina, "#sedes .filtro >> text=Todos")
    azteca = pagina.locator("#sedes .tarjeta", has_text="Estadio Azteca")
    comprobar("el Azteca tiene 5 partidos", "5 partidos" in azteca.locator("summary").inner_text())

    print("Líneas del tiempo")
    comprobar("la portada no trae ninguna línea del tiempo dentro, solo los enlaces para abrirlas",
              pagina.locator(".cronologia").count() == 0 and pagina.locator(".abrir-linea").count() > 100)
    azteca.locator("summary").click()
    pulsar(pagina, "#sedes .tarjeta:has-text('Estadio Azteca') .abrir-linea")
    azteca = pagina.locator("#sedes .tarjeta", has_text="Estadio Azteca")  # la página es otra: se busca de nuevo
    comprobar("al pulsar una, Flask la pinta y su desplegable ('5 partidos') sigue abierto",
              "linea=linea-sede-" in pagina.url and azteca.locator(".cronologia").count() == 1
              and azteca.locator("details").get_attribute("open") is not None)
    comprobar("solo se abre esa (el mismo partido en su grupo sigue cerrado)", pagina.locator(".cronologia").count() == 1)
    comprobar("el enlace dice que está abierta (aria-expanded)",
              azteca.locator(".abrir-linea").first.get_attribute("aria-expanded") == "true")
    pulsar(pagina, "#sedes .abrir-linea[aria-expanded=true]")
    comprobar("al pulsarla otra vez se cierra, y el desplegable '5 partidos' sigue abierto",
              pagina.locator(".cronologia").count() == 0 and "linea=" not in pagina.url
              and "vista=linea-sede-" in pagina.url and azteca.locator("details").get_attribute("open") is not None)

    print("Grupos")
    comprobar("hay 12 grupos", pagina.locator(".grupo").count() == 12)
    comprobar("hay 32 filas de clasificadas", pagina.locator(".grupo tr.clasificada").count() == 32)
    pagina.fill("#buscador", "mexico")
    pulsar(pagina, ".buscador >> text=Buscar")
    comprobar("buscar 'mexico' (sin tilde) deja 1 grupo", pagina.locator(".grupo").count() == 1)
    comprobar("la fila de México queda resaltada", pagina.locator("tr.encontrada", has_text="México").count() == 1)
    pulsar(pagina, ".buscador >> text=Quitar")
    comprobar("'Quitar' vuelve a mostrar los 12 grupos", pagina.locator(".grupo").count() == 12)
    terceros = pagina.locator("#tabla-terceros tbody tr")
    comprobar("la tabla de terceros tiene 12 filas, 8 clasificadas",
              terceros.count() == 12 and pagina.locator("#tabla-terceros tr.clasificada").count() == 8)
    comprobar("Ghana va por delante de Ecuador (juego limpio)",
              "Ghana" in terceros.nth(2).inner_text() and "Ecuador" in terceros.nth(3).inner_text())

    print("Resultados")
    # Entre comillas, el texto tiene que ser exacto: sin ellas, "Final" también encontraría "Dieciseisavos de final"
    pulsar(pagina, '#resultados .filtro >> text="Final"')
    comprobar("hay 6 enlaces de ronda", pagina.locator("#resultados .filtro").count() == 6)
    comprobar("el titular dice que España es campeona", "España" in pagina.inner_text(".campeon"))
    final = pagina.locator(".partido")
    comprobar("la final muestra el gol de Ferran Torres",
              final.count() == 1 and "Ferran Torres 106'" in final.inner_text())
    pulsar(pagina, "#resultados .filtro >> text=Dieciseisavos de final")
    comprobar("dieciseisavos tiene 16 partidos", pagina.locator(".partido").count() == 16)

    print("Camino de una selección")
    comprobar("el selector tiene las 48 selecciones", pagina.locator("#selector-camino option").count() == 48)
    comprobar("por defecto muestra a España, campeona, con 8 partidos",
              "Campeona" in pagina.inner_text(".camino-final") and pagina.locator("ol.camino li").count() == 8)
    pulsar(pagina, ".grupo .enlace-seleccion >> text=Japón")
    comprobar("pulsar Japón en los grupos abre su camino", pagina.input_value("#selector-camino") == "Japón")
    pagina.select_option("#selector-camino", "Panamá")
    pulsar(pagina, "#camino >> text=Ver camino")
    comprobar("elegir Panamá en el selector muestra 3 partidos y ningún gol",
              pagina.locator("ol.camino li").count() == 3 and "No marcó" in pagina.inner_text("#camino"))
    pulsar(pagina, "#camino >> text=Volver a grupos")
    comprobar("'Volver a grupos' lleva al grupo de Panamá", pagina.url.endswith("#grupo-L"))

    print("Goleadores")
    comprobar("se ven 28 goleadores con 3 o más goles", pagina.locator("#tabla-goleadores .enlace-jugador").count() == 28)
    pulsar(pagina, ".enlace-jugador >> text=Kylian Mbappé")
    comprobar("al pulsar a Mbappé salen sus 6 partidos", pagina.locator("tr.detalle-goleador li").count() == 6)
    pulsar(pagina, ".enlace-jugador >> text=Kylian Mbappé")
    comprobar("al pulsarlo otra vez se cierra", pagina.locator("tr.detalle-goleador").count() == 0)
    pulsar(pagina, "#ver-goleadores")
    comprobar("'Ver todos' muestra 178 goleadores", pagina.locator("#tabla-goleadores .enlace-jugador").count() == 178)

    print("Quiz")
    for _ in range(10):
        pulsar(pagina, ".opcion")
        pulsar(pagina, "#quiz .boton")  # "Siguiente" o "Ver resultado"
    comprobar("tras 10 respuestas sale el resultado final", "Has acertado" in pagina.inner_text("#quiz"))
    comprobar("el quiz no ha quitado lo elegido antes (todos los goleadores)",
              pagina.locator("#tabla-goleadores .enlace-jugador").count() == 178)
    pulsar(pagina, "#quiz >> text=Reintentar")
    comprobar("'Reintentar' vuelve a la pregunta 1", "Pregunta 1 de 10" in pagina.inner_text("#quiz"))

    print("Volver arriba")
    pagina.evaluate("window.scrollTo(0, 0)")
    pagina.wait_for_timeout(300)
    oculto = pagina.evaluate("getComputedStyle(document.querySelector('.volver-arriba')).visibility")
    pagina.evaluate("window.scrollTo(0, 3000)")
    pagina.wait_for_timeout(300)
    visible = pagina.evaluate("getComputedStyle(document.querySelector('.volver-arriba')).visibility")
    comprobar("arriba del todo el botón está oculto y al bajar aparece", (oculto, visible) == ("hidden", "visible"))

    direccion = pagina.url.split("#")[0].split("?")[0]  # la portada, sin nada elegido
    pagina.goto(direccion)
    probar_accesibilidad(pagina)
    probar_lector_pantalla(pagina, direccion)


# El color de fondo de cada tema (--fondo en styles.css), como lo devuelve el navegador
FONDO_DE = {"dark": "rgb(10, 18, 34)", "light": "rgb(244, 246, 250)"}


def probar_temas(navegador, direccion):
    """La web sigue el modo claro u oscuro del sistema (prefers-color-scheme). En los dos tiene
    que verse con sus colores y pasar la revisión de accesibilidad (sobre todo, el contraste)."""
    for tema, nombre in (("light", "claro"), ("dark", "oscuro")):
        print(f"Tema {nombre}")
        pagina = nueva_pagina(navegador, viewport={"width": 1280, "height": 900}, color_scheme=tema)
        pagina.goto(direccion)
        fondo = pagina.evaluate("getComputedStyle(document.body).backgroundColor")
        comprobar(f"con el sistema en modo {nombre}, el fondo es el del tema {nombre} ({fondo})", fondo == FONDO_DE[tema])
        probar_accesibilidad(pagina)
        pagina.close()

    print("Elegir el tema a mano")
    # Todas las variables de color de styles.css, tal como quedan en la página
    colores = """(() => { const estilo = getComputedStyle(document.documentElement);
        return ['--fondo', '--fondo-tarjeta', '--fondo-cabecera', '--foco-luz', '--borde', '--texto',
                '--texto-suave', '--cesped', '--oro', '--rojo'].map(v => estilo.getPropertyValue(v).trim()) })()"""
    pagina = nueva_pagina(navegador, viewport={"width": 1280, "height": 900}, color_scheme="light")
    pagina.goto(direccion)
    claro_del_sistema = pagina.evaluate(colores)
    pulsar(pagina, "#tema >> text=Oscuro")
    fondo = pagina.evaluate("getComputedStyle(document.body).backgroundColor")
    comprobar("con el sistema en claro, el botón 'Oscuro' pone el tema oscuro", fondo == FONDO_DE["dark"])
    comprobar("y queda marcado como pulsado (aria-pressed)",
              pagina.get_attribute("#tema button[value=oscuro]", "aria-pressed") == "true")
    pagina.close()

    pagina = nueva_pagina(navegador, viewport={"width": 1280, "height": 900}, color_scheme="dark")
    pagina.goto(direccion + "?pais=México")
    pulsar(pagina, "#tema >> text=Claro")
    comprobar("con el sistema en oscuro, el botón 'Claro' pone el tema claro y no pierde lo elegido",
              pagina.evaluate("getComputedStyle(document.body).backgroundColor") == FONDO_DE["light"]
              and "pais=M%C3%A9xico" in pagina.url)
    # Los colores del tema claro están dos veces en styles.css: el elegido a mano tiene que ser igual
    comprobar("los colores del 'Claro' elegido a mano son los mismos que los del claro del sistema",
              pagina.evaluate(colores) == claro_del_sistema)
    revisar_accesibilidad(pagina, "con el tema claro elegido a mano")
    pulsar(pagina, "#tema >> text=Automático")
    comprobar("'Automático' vuelve a seguir al sistema (oscuro)",
              pagina.evaluate("getComputedStyle(document.body).backgroundColor") == FONDO_DE["dark"])
    pagina.close()


def probar_seguridad(navegador, direccion):
    """La Content-Security-Policy bloquea de verdad un script colado en la página."""
    pagina = nueva_pagina(navegador, color_scheme="dark")
    avisos = []
    pagina.on("console", lambda m: avisos.append(m.text))  # aquí se esperan avisos: no cuentan como errores
    respuesta = pagina.goto(direccion)
    comprobar("la página llega con su Content-Security-Policy",
              "script-src 'none'" in respuesta.headers.get("content-security-policy", ""))
    # Como si alguien hubiera conseguido colar este HTML: una imagen que, al cargar, ejecuta JavaScript
    pagina.evaluate("""document.body.insertAdjacentHTML('beforeend',
        '<img src="/static/favicon.svg" onload="document.title = \\'hackeado\\'">')""")
    pagina.wait_for_timeout(500)
    comprobar("un script colado en la página no se ejecuta (la CSP lo bloquea)",
              pagina.title() != "hackeado" and any("Content Security Policy" in a for a in avisos))
    pagina.close()


def probar_partido(navegador, direccion, errores):
    """La página de un partido, llegando a ella desde la portada como lo haría quien visita la web."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(f"[{m.type}] {m.text}"))
    pagina.goto(direccion)
    pulsar(pagina, "#resultados >> text=Ver partido")    # la tarjeta de la final (la ronda por defecto)
    comprobar("'Ver partido' lleva a la página de la final (/partido/103)", pagina.url.endswith("/partido/103"))
    comprobar("la página dice el resultado y trae la línea del tiempo abierta",
              pagina.inner_text("h1").upper() == "ESPAÑA 1-0 ARGENTINA" and pagina.locator(".cronologia li").count() == 1)
    comprobar("no hay scroll horizontal en el móvil",
              pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
    revisar_accesibilidad(pagina, "la página de un partido")
    pulsar(pagina, "text=← Partido anterior")
    comprobar("'Partido anterior' lleva al partido 102 (el tercer puesto)",
              pagina.url.endswith("/partido/102") and "TERCER PUESTO" in pagina.inner_text(".antetitulo").upper())
    pulsar(pagina, "text=Camino de Francia")
    comprobar("'Camino de Francia' vuelve a la portada, con el camino de Francia",
              pagina.input_value("#selector-camino") == "Francia")
    pagina.close()


def probar_cara_a_cara(navegador, direccion, errores):
    """Del camino de una selección a compararla con otra."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(f"[{m.type}] {m.text}"))
    pagina.goto(direccion + "?seleccion=Japón#camino")
    pulsar(pagina, "text=Comparar con otra selección")
    comprobar("desde el camino de Japón se llega a compararla (con España, la campeona)",
              pagina.input_value("#seleccion-a") == "Japón" and pagina.input_value("#seleccion-b") == "España")
    pagina.select_option("#seleccion-b", "Panamá")
    pulsar(pagina, "text=Comparar")
    comprobar("al elegir Panamá y pulsar 'Comparar', sale Japón y Panamá",
              "a=Jap%C3%B3n&b=Panam%C3%A1" in pagina.url and "No se enfrentaron" in pagina.inner_text("main"))
    comprobar("no hay scroll horizontal en el móvil",
              pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
    revisar_accesibilidad(pagina, "la página del cara a cara")
    pagina.close()


def probar_404(navegador, direccion, errores):
    """Una dirección que no existe, en pantalla de móvil."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    # El aviso "Failed to load resource ... 404" es justo lo que se espera aquí: no cuenta como error
    pagina.on("console", lambda m: m.type in ("error", "warning") and "404" not in m.text
              and errores.append(f"[{m.type}] {m.text}"))
    pagina.on("pageerror", lambda e: errores.append(f"[excepción] {e}"))

    # Sin guiones ni espacios: el navegador no tiene por dónde partirla si no se lo dice el CSS
    respuesta = pagina.goto(direccion + "estadireccionnoexisteyestanlargaquenocabeenlapantalladeunmovil")
    comprobar("una dirección que no existe responde con el código 404", respuesta.status == 404)
    comprobar("y muestra la página 'Fuera de juego'", "Fuera de juego" in pagina.inner_text("h1"))
    comprobar("la dirección larga no provoca scroll horizontal",
              pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
    revisar_accesibilidad(pagina, "la página 404")
    pulsar(pagina, ".menu >> text=Goleadores")
    comprobar("el menú de la 404 lleva a la sección de la portada",
              pagina.url == direccion + "#goleadores" and pagina.locator("#tabla-goleadores").count() == 1)
    pagina.close()


def probar_inicio(navegador, raiz, errores):
    """La página de inicio, con todos los Mundiales, en el móvil."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(f"[{m.type}] {m.text}"))
    pagina.goto(raiz)
    comprobar("la raíz muestra los 23 Mundiales", pagina.locator("#mundiales tbody tr").count() == 23)
    comprobar("no hay scroll horizontal",
              pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
    comprobar("el menú cabe entero", pagina.evaluate(
        "[...document.querySelectorAll('.menu a')].every(a => a.getBoundingClientRect().right <= innerWidth)"))
    revisar_accesibilidad(pagina, "la página de inicio")
    pulsar(pagina, "#mundiales a >> text=2026")
    comprobar("el enlace 2026 lleva a su Mundial", pagina.url == raiz + "2026/")

    # El idioma: el botón de la portada cambia la página a inglés y vuelve a ella
    pagina.goto(raiz)
    pulsar(pagina, "#idioma-portada button[value=en]")
    comprobar("el botón English pone la página en inglés",
              pagina.url == raiz + "#idioma" and pagina.inner_text("h1").upper() == "FIFA WORLD CUP"
              and pagina.get_attribute("html", "lang") == "en")
    revisar_accesibilidad(pagina, "la página de inicio en inglés")
    pulsar(pagina, "#idioma-portada button[value=es]")
    comprobar("y el botón Español la devuelve al español", pagina.get_attribute("html", "lang") == "es")
    pagina.close()


def probar_mundiales_antiguos(navegador, raiz, errores):
    """Los Mundiales más distintos al de 2026, en el móvil: 1950 (sin final), 1934 (sin grupos),
    1982 (dos fases de grupos) y 2002 (dos países)."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(f"[{m.type}] {m.text}"))
    for anio in (1950, 1934):
        pagina.goto(f"{raiz}{anio}/")
        comprobar(f"{anio}: sin scroll horizontal",
                  pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
        comprobar(f"{anio}: el menú cabe entero", pagina.evaluate(
            "[...document.querySelectorAll('.menu a')].every(a => a.getBoundingClientRect().right <= innerWidth)"))
        revisar_accesibilidad(pagina, f"el Mundial {anio}")
    pulsar(pagina, "#camino .camino a")  # el primer partido del camino del campeón (Italia, 1934)
    comprobar("el partido de 1934 abre su página", "/1934/partido/" in pagina.url)

    # 1982: dos fases de grupos. Argentina cayó en la segunda
    pagina.goto(f"{raiz}1982/?seleccion=Argentina#camino")
    comprobar("1982: la segunda fase de grupos tiene sus 4 grupos",
              pagina.locator("#selecciones h3", has_text="(segunda fase)").count() == 4)
    comprobar("1982: Argentina, eliminada en la segunda fase de grupos",
              pagina.inner_text(".camino-final") == "Eliminada en la segunda fase de grupos")
    revisar_accesibilidad(pagina, "el Mundial 1982")

    # 2002: dos países. El filtro de sedes deja solo los estadios de Japón
    pagina.goto(f"{raiz}2002/#sedes")
    pulsar(pagina, "#sedes .filtro >> text=Japón")
    comprobar("2002: el filtro de Japón deja sus 10 estadios", pagina.locator("#sedes article").count() == 10)
    # En inglés, con el botón del pie: la misma página (con el filtro de Japón) y todo traducido
    pulsar(pagina, "#idioma button[value=en]")
    comprobar("2002 en inglés: «2002 World Cup», con el filtro de Japón aún puesto",
              pagina.inner_text("h1").upper() == "2002 WORLD CUP" and pagina.locator("#sedes article").count() == 10
              and pagina.inner_text("#sedes .filtro.activo") == "Japan")
    revisar_accesibilidad(pagina, "el Mundial 2002 en inglés")
    pagina.close()


def probar_selecciones(navegador, raiz, errores):
    """La lista de selecciones y la página de una, en el móvil."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(f"[{m.type}] {m.text}"))
    pagina.goto(raiz + "selecciones")
    comprobar("la lista tiene las 84 selecciones", pagina.locator("tbody tr").count() == 84)
    revisar_accesibilidad(pagina, "la lista de selecciones")
    pulsar(pagina, "tbody a >> text=Alemania")
    comprobar("Alemania tiene sus 21 Mundiales (con los de Alemania Federal)",
              pagina.locator("#mundiales tbody tr").count() == 21)
    pagina.select_option("#selector-contra", "Argentina")
    pulsar(pagina, "#contra .boton")
    comprobar("contra Argentina salen sus 7 partidos", pagina.locator("#contra .lista-partidos li").count() == 7)
    comprobar("sin scroll horizontal", pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
    comprobar("el menú cabe entero", pagina.evaluate(
        "[...document.querySelectorAll('.menu a')].every(a => a.getBoundingClientRect().right <= innerWidth)"))
    revisar_accesibilidad(pagina, "la página de Alemania")
    # En inglés, con el botón del pie: vuelve a la misma página (con el rival elegido)
    pulsar(pagina, "#idioma button[value=en]")
    comprobar("en inglés, la página de Alemania es la de Germany, con sus 7 partidos contra Argentina",
              pagina.inner_text("h1").upper() == "GERMANY" and "contra=Argentina" in pagina.url
              and pagina.locator("#contra .lista-partidos li").count() == 7)
    revisar_accesibilidad(pagina, "la página de Alemania en inglés")
    pagina.close()


def probar_otros_idiomas(navegador, raiz, errores):
    """Las páginas del paso 68 en otros idiomas, cambiando el idioma con el botón del pie (en el móvil)."""
    pagina = nueva_pagina(navegador, viewport={"width": 375, "height": 800}, color_scheme="dark")
    pagina.on("console", lambda m: m.type in ("error", "warning") and "404" not in m.text
              and errores.append(f"[{m.type}] {m.text}"))
    pagina.goto(raiz + "1934/partido/11")
    pulsar(pagina, "#idioma button[value=en]")
    comprobar("un partido en inglés: «Italy 1-1 Spain», con el aviso de que se repitió",
              pagina.inner_text("h1").upper() == "ITALY 1-1 SPAIN" and "replayed on" in pagina.inner_text(".aviso"))
    revisar_accesibilidad(pagina, "un partido en inglés")
    pagina.goto(raiz + "2026/#quiz")
    pulsar(pagina, "#quiz .opcion >> nth=2")
    comprobar("el quiz en inglés: «Correct!» y su explicación", "Correct! It is the first World Cup" in pagina.inner_text("#quiz"))
    pagina.goto(raiz + "no-existe")
    pulsar(pagina, "#idioma button[value=pt]")
    comprobar("la 404 en portugués: «Impedimento»", pagina.inner_text("h1").upper() == "IMPEDIMENTO")
    revisar_accesibilidad(pagina, "la 404 en portugués")
    pagina.close()


def probar_direcciones(navegador, raiz):
    """Las direcciones de antes del paso 58 (sin el año) llevan a las nuevas."""
    pagina = nueva_pagina(navegador)
    pagina.goto(raiz + "?pais=México")
    comprobar("la raíz lleva al Mundial 2026, con lo elegido", pagina.url == raiz + "2026/?pais=M%C3%A9xico")
    pagina.goto(raiz + "partido/103")
    comprobar("/partido/103 lleva a /2026/partido/103", pagina.url == raiz + "2026/partido/103")
    pagina.close()


def main():
    if len(sys.argv) > 1:
        servidor, raiz = None, sys.argv[1].rstrip("/") + "/"
    else:
        servidor, raiz = arrancar_servidor()
    direccion = raiz + "2026/"  # el Mundial 2026 está en /2026/ desde el paso 58
    print(f"Probando {direccion}")
    errores = []
    with sync_playwright() as p:
        # channel=None: el Chromium de Playwright; channel="chrome": el Chrome del sistema
        navegador = p.chromium.launch(channel=os.environ.get("CANAL_NAVEGADOR"))
        print(f"Navegador: {navegador.browser_type.name} {navegador.version}")

        for nombre, ancho, alto in (("escritorio", 1280, 900), ("móvil", 375, 800)):
            print(f"\n=== Pantalla {nombre} ({ancho}px) ===")
            # Playwright simula el modo claro si no se le dice nada: estas pruebas usan el oscuro, el de siempre
            pagina = nueva_pagina(navegador, viewport={"width": ancho, "height": alto}, color_scheme="dark")
            # Todo lo que saldría en rojo en la consola (F12)
            # Con la dirección que lo provoca: "Failed to load resource" no dice cuál era
            pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(
                f"[{m.type}] {m.text} ({m.location.get('url') or 'sin dirección'})"))
            pagina.on("pageerror", lambda e: errores.append(f"[excepción] {e}"))

            # Abrir un enlace directo a una sección: el título tiene que quedar justo bajo la cabecera.
            # Primero se carga una vez y se espera a las fuentes de Google: si llegan a mitad de la medida,
            # los títulos cambian de alto y la página se recoloca unos píxeles (la prueba fallaba a veces)
            pagina.goto(direccion)
            pagina.evaluate("document.fonts.ready.then(() => true)")
            pagina.goto(direccion + "#camino")
            pagina.wait_for_timeout(1000)
            arriba = pagina.evaluate("document.getElementById('camino').getBoundingClientRect().top")
            # En el móvil la cabecera no es fija: al bajar se va (su borde de abajo queda por encima de la pantalla)
            cabecera = max(0, pagina.evaluate("document.querySelector('.cabecera').getBoundingClientRect().bottom"))
            comprobar(f"un enlace a #camino deja la sección justo bajo la cabecera ({arriba:.0f}px, cabecera {cabecera:.0f}px)",
                      cabecera <= arriba <= cabecera + 40)

            pagina.goto(direccion)
            comprobar("no hay scroll horizontal",
                      pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
            if nombre == "escritorio":
                # El CSS lleva una huella en la dirección (?v=...) y el navegador lo guarda un año
                css = pagina.evaluate("document.querySelector('link[rel=stylesheet][href*=styles]').href")
                cache_control = pagina.request.get(css).headers.get("cache-control", "")
                comprobar(f"el CSS lleva su huella y se guarda un año en caché ({cache_control})",
                          "?v=" in css and "max-age=31536000" in cache_control)
            if nombre == "móvil":
                comprobar("el menú cabe entero: ningún enlace queda cortado por el borde",
                          pagina.evaluate("""[...document.querySelectorAll('.menu a')]
                                             .every(a => a.getBoundingClientRect().right <= innerWidth)"""))
                pagina.click(".menu a[href='#goleadores']")
                pagina.wait_for_timeout(1000)
                comprobar("el enlace 'Goleadores' del menú lleva a su sección", pagina.url.endswith("#goleadores"))
                revisar_accesibilidad(pagina, "la portada en el móvil")
            else:
                probar(pagina)
            pagina.close()

            print("Teclado")
            probar_teclado(navegador, direccion, ancho)

        # Entre 720 y 849px el menú va en dos filas junto al logo: la cabecera es más alta
        print("\n=== Teclado en pantalla mediana (760px) ===")
        probar_teclado(navegador, direccion, 760)

        print("\n=== Página de un partido (móvil) ===")
        probar_partido(navegador, direccion, errores)

        print("\n=== Cara a cara (móvil) ===")
        probar_cara_a_cara(navegador, direccion, errores)

        print("\n=== Página 404 (móvil) ===")
        probar_404(navegador, direccion, errores)

        print("\n=== Temas claro y oscuro ===")
        probar_temas(navegador, direccion)

        print("\n=== Página de inicio (móvil) ===")
        probar_inicio(navegador, raiz, errores)

        print("\n=== Mundiales antiguos (móvil) ===")
        probar_mundiales_antiguos(navegador, raiz, errores)

        print("\n=== Selecciones (móvil) ===")
        probar_selecciones(navegador, raiz, errores)

        print("\n=== Otros idiomas (móvil) ===")
        probar_otros_idiomas(navegador, raiz, errores)

        print("\n=== Direcciones de antes ===")
        probar_direcciones(navegador, raiz)

        print("\n=== Seguridad ===")
        probar_seguridad(navegador, direccion)
        navegador.close()
    if servidor:
        servidor.shutdown()

    print("\n=== Consola del navegador ===")
    for e in errores:
        print("  " + e)
    comprobar("sin errores ni avisos en la consola", not errores)

    print(f"\n{'Todo correcto' if not fallos else f'{len(fallos)} fallo(s)'}")
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()
