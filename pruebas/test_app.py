"""Pruebas de las rutas de app.py con el cliente de pruebas de Flask.

El cliente pide las páginas como lo haría un navegador, pero sin abrir ninguno
ni arrancar un servidor: por eso estas pruebas tardan menos de un segundo.
"""

import re

import pytest

import mundial
from app import abreviaturas, app, estatico, fecha


@pytest.fixture
def cliente():
    """Un cliente nuevo en cada prueba: así cada una empieza con la sesión (el quiz) vacía."""
    app.config["TESTING"] = True
    return app.test_client()


def html(respuesta):
    return respuesta.get_data(as_text=True)


def test_la_portada_carga(cliente):
    respuesta = cliente.get("/2026/")
    assert respuesta.status_code == 200
    assert "Copa Mundial 2026" in html(respuesta)


@pytest.mark.parametrize("pais, estadios", [(None, 16), ("Estados Unidos", 11), ("México", 3), ("Canadá", 2)])
def test_filtro_de_estadios(cliente, pais, estadios):
    respuesta = cliente.get("/2026/", query_string={"pais": pais} if pais else {})
    assert f"Mostrando {estadios} de 16 estadios" in html(respuesta)


def test_parametros_que_no_existen_no_rompen_la_pagina(cliente):
    respuesta = cliente.get("/2026/?pais=Narnia&ronda=99&seleccion=Atlantis&jugador=Nadie")
    assert respuesta.status_code == 200
    pagina = html(respuesta)
    assert "Mostrando 16 de 16 estadios" in pagina      # país desconocido: todos
    assert "Ferran Torres <abbr title=\"minuto 106\"" in pagina  # ronda fuera de rango: la final
    assert "Campeona del mundo" in pagina               # selección desconocida: la campeona


def test_se_respetan_la_ronda_y_la_seleccion_elegidas(cliente):
    pagina = html(cliente.get("/2026/?ronda=3&seleccion=Panamá"))
    assert 'aria-current="true">Semifinales</a>' in pagina  # la ronda 3 está marcada
    assert '<option value="Panamá" selected>Panamá</option>' in pagina     # el camino es el de Panamá
    assert "No marcó ningún gol." in pagina


def test_el_buscador_no_distingue_tildes(cliente):
    pagina = html(cliente.get("/2026/?buscar=mexico"))
    assert pagina.count('class="tarjeta grupo"') == 1
    assert "encontrada" in pagina


def test_lo_que_se_escribe_en_el_buscador_no_se_ejecuta_como_html(cliente):
    # Jinja2 "escapa" el texto: < y > se convierten en &lt; y &gt;
    pagina = html(cliente.get("/2026/?buscar=<script>alert(1)</script>"))
    assert "<script>alert(1)</script>" not in pagina
    assert "&lt;script&gt;" in pagina


def test_los_enlaces_conservan_lo_elegido(cliente):
    pagina = html(cliente.get("/2026/?pais=México"))
    # El enlace a la ronda de semifinales sigue llevando el filtro de México
    assert "/2026/?pais=M%C3%A9xico&amp;ronda=3#resultados" in pagina


def test_fuentes(cliente):
    respuesta = cliente.get("/fuentes")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "text/plain"
    assert "Wikipedia" in html(respuesta)


# ===== Abreviaturas (se ve la corta, el lector de pantalla lee la larga) =====

def solo_lector(texto):
    return f'<span class="solo-lector">{texto}</span>'


def test_las_abreviaturas_de_los_goles_se_leen_enteras():
    html = abreviaturas("Harry Kane 30' (pen.) · Declan Rice 49' (p.p.)")
    assert solo_lector("(de penalti)") in html
    assert solo_lector("(en propia puerta)") in html
    assert '<abbr title="(de penalti)" aria-hidden="true">(pen.)</abbr>' in html  # en pantalla, igual que antes


@pytest.mark.parametrize("texto, larga", [("A 1-0 B (prór.)", "(tras la prórroga)"),
                                          ("A 0-0 B (pen. 4-3)", "(penaltis 4-3)")])
def test_prorroga_y_penaltis(texto, larga):
    assert solo_lector(larga) in abreviaturas(texto)


@pytest.mark.parametrize("minuto, se_lee", [("48'", "minuto 48"), ("106'", "minuto 106"),
                                            ("90+1'", "minuto 90 más 1"), ("45+12'", "minuto 45 más 12")])
def test_los_minutos_se_leen_enteros(minuto, se_lee):
    assert solo_lector(se_lee) in abreviaturas(f"Bukayo Saka {minuto}")


def test_un_apostrofo_que_no_es_un_minuto_no_cambia():
    assert abreviaturas("N'Golo Kanté") == "N&#39;Golo Kanté"


def test_las_abreviaturas_no_dejan_pasar_html():
    html = abreviaturas("<b>Kane</b> 30' (pen.)")
    assert "<b>" not in html and "&lt;b&gt;Kane&lt;/b&gt;" in html


def test_un_texto_sin_abreviaturas_no_cambia():
    assert abreviaturas("México 2-0 Sudáfrica") == "México 2-0 Sudáfrica"


def test_la_fecha_se_lee_con_el_mes_entero():
    assert fecha("2026-07-19") == '19 <abbr title="de julio" aria-hidden="true">jul</abbr>' + solo_lector("de julio")


def test_ee_uu_y_el_puesto_del_grupo(cliente):
    pagina = html(cliente.get("/2026/?seleccion=España"))
    assert ">EE. UU.</abbr>" + solo_lector("Estados Unidos") in pagina
    assert ">1.º</abbr>" + solo_lector("Primera") in pagina


# ===== Líneas del tiempo (se pintan solo al pedirlas) =====
# El partido 0 es el primero del Mundial: México - Sudáfrica, en el Estadio Azteca y en el grupo A

def test_la_portada_no_trae_ninguna_linea_del_tiempo(cliente):
    pagina = html(cliente.get("/2026/"))
    assert 'class="cronologia"' not in pagina
    assert 'id="linea-sede-0"' in pagina and 'id="linea-grupo-0"' in pagina  # solo los enlaces
    assert "<details open>" not in pagina


def test_abrir_una_linea_del_tiempo(cliente):
    pagina = html(cliente.get("/2026/?linea=linea-grupo-0"))
    assert pagina.count('class="cronologia"') == 1        # solo esa, no la del Azteca
    assert pagina.count("<details open>") == 1             # el "Ver partidos" del grupo A
    assert 'href="/2026/?vista=linea-grupo-0#linea-grupo-0"' in pagina  # el enlace para cerrarla


def test_al_cerrarla_su_desplegable_sigue_abierto(cliente):
    pagina = html(cliente.get("/2026/?vista=linea-sede-0"))
    assert 'class="cronologia"' not in pagina
    assert pagina.count("<details open>") == 1             # el "5 partidos" del Azteca


def test_una_linea_que_no_existe_no_rompe_la_pagina(cliente):
    respuesta = cliente.get("/2026/?linea=<b>nada</b>&vista=linea-sede-999")
    assert respuesta.status_code == 200
    assert 'class="cronologia"' not in html(respuesta) and "<details open>" not in html(respuesta)


# ===== Caché del CSS =====

def test_el_css_lleva_su_huella_y_se_guarda_un_ano(cliente):
    direccion = re.search(r'href="(/static/styles\.css\?v=[0-9a-f]{10})"', html(cliente.get("/2026/"))).group(1)
    respuesta = cliente.get(direccion)
    assert respuesta.status_code == 200
    assert respuesta.headers["Cache-Control"] == "public, max-age=31536000"


def test_la_web_tiene_icono_para_la_pestana(cliente):
    # Sin icono, el navegador pide /favicon.ico en cada visita y recibe un 404
    direccion = re.search(r'<link rel="icon" href="(/static/favicon\.svg\?v=[0-9a-f]{10})"', html(cliente.get("/2026/"))).group(1)
    respuesta = cliente.get(direccion)
    assert respuesta.status_code == 200 and respuesta.mimetype == "image/svg+xml"


def test_si_el_css_cambia_cambia_la_huella(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "static_folder", str(tmp_path))  # una carpeta static/ de mentira
    huellas = []
    for contenido in ("body { color: red; }", "body { color: blue; }"):
        (tmp_path / "styles.css").write_text(contenido)
        with app.test_request_context():
            huellas.append(estatico("styles.css"))
    assert huellas[0] != huellas[1]


# ===== Cabeceras de seguridad =====

@pytest.mark.parametrize("pedir", [
    lambda c: c.get("/2026/"),                                  # la portada
    lambda c: c.get("/no-existe"),                         # la página 404
    lambda c: c.get("/fuentes"),                           # el texto de las fuentes
    lambda c: c.post("/tema", data={"tema": "claro"}),     # una redirección después de un formulario
])
def test_todas_las_respuestas_llevan_las_cabeceras_de_seguridad(cliente, pedir):
    cabeceras = pedir(cliente).headers
    assert "script-src 'none'" in cabeceras["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in cabeceras["Content-Security-Policy"]
    assert cabeceras["X-Content-Type-Options"] == "nosniff"
    assert cabeceras["X-Frame-Options"] == "DENY"
    assert cabeceras["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_hsts_solo_en_render(cliente, monkeypatch):
    # En tu ordenador la web va por http://, y ahí no tiene sentido pedir HTTPS
    assert "Strict-Transport-Security" not in cliente.get("/2026/").headers
    monkeypatch.setenv("RENDER", "true")
    assert cliente.get("/2026/").headers["Strict-Transport-Security"] == "max-age=31536000"


def test_la_cookie_de_la_sesion_es_samesite_lax(cliente):
    cookie = cliente.post("/tema", data={"tema": "claro"}).headers["Set-Cookie"]
    assert "SameSite=Lax" in cookie and "HttpOnly" in cookie


# ===== Página 404 =====

def test_una_direccion_que_no_existe_muestra_la_pagina_404(cliente):
    respuesta = cliente.get("/estadios")
    assert respuesta.status_code == 404                  # el código sigue siendo 404, no 200
    pagina = html(respuesta)
    assert "Fuera de juego" in pagina
    assert "<code>/estadios</code>" in pagina            # dice qué dirección no existe
    assert '<a class="boton" href="/2026/">Volver a la portada</a>' in pagina
    assert "volver-arriba" not in pagina                 # la página es corta: sin botón ↑


def test_en_la_404_el_menu_lleva_a_la_portada(cliente):
    pagina = html(cliente.get("/estadios"))
    assert 'href="/2026/#sedes"' in pagina                    # "/2026/#sedes": la sección de la portada
    assert 'href="#sedes"' not in pagina                 # "#sedes" solo no llevaría a ningún sitio


def test_en_la_portada_el_menu_no_recarga_la_pagina(cliente):
    pagina = html(cliente.get("/2026/?pais=México"))
    assert 'href="#sedes"' in pagina                     # solo "#sedes": se mantiene ?pais=México
    assert 'class="volver-arriba"' in pagina


def test_la_direccion_de_la_404_no_se_ejecuta_como_html(cliente):
    pagina = html(cliente.get("/<b>hola</b>"))
    assert "<b>hola</b>" not in pagina
    assert "&lt;b&gt;hola&lt;/b&gt;" in pagina


# ===== Página 500 =====

def test_si_el_codigo_falla_sale_la_pagina_500(cliente, monkeypatch):
    def fallar(*args):
        raise RuntimeError("fallo inventado para la prueba")

    # Se rompe a propósito una función que usa la portada, solo durante esta prueba
    monkeypatch.setattr(mundial, "buscar_grupos", fallar)
    # En modo de pruebas Flask deja pasar las excepciones (para verlas en pytest).
    # Así se comporta como en el servidor de verdad: las convierte en un error 500
    monkeypatch.setitem(app.config, "PROPAGATE_EXCEPTIONS", False)

    respuesta = cliente.get("/2026/")
    assert respuesta.status_code == 500
    pagina = html(respuesta)
    assert "Tarjeta roja" in pagina
    assert "fallo inventado" not in pagina               # el detalle del error no se enseña
    assert 'href="/2026/#sedes"' in pagina                     # el menú lleva a la portada
    assert "volver-arriba" not in pagina


# ===== Elegir el tema =====

def boton_pulsado(pagina):
    """El valor del botón de tema que tiene aria-pressed="true" (los espacios entre medias dan igual)."""
    return re.findall(r'value="(\w+)"\s+aria-pressed="true"', pagina)[0]

def test_por_defecto_el_tema_es_el_del_sistema(cliente):
    pagina = html(cliente.get("/2026/"))
    assert '<html lang="es">' in pagina                           # sin data-tema: lo decide el CSS
    assert '<meta name="color-scheme" content="dark light">' in pagina
    assert boton_pulsado(pagina) == "auto"


@pytest.mark.parametrize("tema, color_scheme", [("claro", "light"), ("oscuro", "dark")])
def test_elegir_un_tema(cliente, tema, color_scheme):
    respuesta = cliente.post("/tema?pais=Canad%C3%A1", data={"tema": tema})
    assert respuesta.headers["Location"] == "/2026/?pais=Canad%C3%A1#tema"  # vuelve a donde estaba
    with cliente.session_transaction() as sesion:
        assert sesion["tema"] == tema
    pagina = html(cliente.get("/2026/"))
    assert f'<html lang="es" data-tema="{tema}">' in pagina
    assert f'<meta name="color-scheme" content="{color_scheme}">' in pagina
    assert boton_pulsado(pagina) == tema


@pytest.mark.parametrize("valor", ["auto", "morado", None])
def test_automatico_o_algo_raro_vuelve_al_tema_del_sistema(cliente, valor):
    cliente.post("/tema", data={"tema": "claro"})
    cliente.post("/tema", data={"tema": valor} if valor else {})
    with cliente.session_transaction() as sesion:
        assert "tema" not in sesion
    assert "data-tema" not in html(cliente.get("/2026/"))


def test_el_tema_tambien_vale_en_la_pagina_404(cliente):
    cliente.post("/tema", data={"tema": "claro"})
    assert 'data-tema="claro"' in html(cliente.get("/no-existe"))


# ===== Quiz =====

def test_responder_bien_suma_un_acierto(cliente):
    respuesta = cliente.post("/2026/quiz/responder", data={"opcion": "2"})  # pregunta 1: 48 selecciones
    assert respuesta.status_code == 302  # redirección de vuelta a la página
    with cliente.session_transaction() as sesion:
        assert sesion["quiz"] == {"indice": 0, "aciertos": 1, "respondida": 2}


def test_no_se_puede_responder_dos_veces_la_misma_pregunta(cliente):
    cliente.post("/2026/quiz/responder", data={"opcion": "2"})
    cliente.post("/2026/quiz/responder", data={"opcion": "2"})
    with cliente.session_transaction() as sesion:
        assert sesion["quiz"]["aciertos"] == 1


def test_no_se_puede_pasar_de_pregunta_sin_responder(cliente):
    cliente.post("/2026/quiz/siguiente")
    with cliente.session_transaction() as sesion:
        assert "quiz" not in sesion                        # no ha cambiado nada: no se guarda nada
    assert "Pregunta 1 de 10" in html(cliente.get("/2026/"))


def test_quiz_completo_con_todo_bien(cliente):
    correctas = [p["correcta"] for p in mundial.leer_json("quiz.json")]
    for opcion in correctas:
        cliente.post("/2026/quiz/responder", data={"opcion": str(opcion)})
        cliente.post("/2026/quiz/siguiente")
    assert "Has acertado 10 de 10" in html(cliente.get("/2026/"))
    cliente.post("/2026/quiz/reiniciar")
    assert "Pregunta 1 de 10" in html(cliente.get("/2026/"))


def test_el_quiz_vuelve_a_la_misma_direccion(cliente):
    respuesta = cliente.post("/2026/quiz/responder?pais=Canad%C3%A1&todos=1", data={"opcion": "0"})
    assert respuesta.headers["Location"] == "/2026/?pais=Canad%C3%A1&todos=1#quiz"


# ===== Un Mundial por año, y las direcciones de antes =====

def test_un_anio_sin_mundial_da_404(cliente):
    assert cliente.get("/2030/").status_code == 404           # todavía no se ha jugado
    assert cliente.get("/1942/partido/0").status_code == 404  # no hubo Mundial (la guerra)


def test_los_enlaces_llevan_el_anio(cliente):
    pagina = html(cliente.get("/2026/"))
    assert 'href="/2026/partido/0"' in pagina
    assert 'action="/2026/quiz/responder"' in pagina
    assert 'href="/partido/' not in pagina                     # ninguno se ha quedado sin año


@pytest.mark.parametrize("antes, ahora, codigo", [
    ("/?pais=M%C3%A9xico&ronda=2", "/2026/?pais=M%C3%A9xico&ronda=2", 301),  # con lo que estaba elegido
    ("/partido/103", "/2026/partido/103", 301),
    ("/cara-a-cara?a=Jap%C3%B3n&b=Panam%C3%A1", "/2026/cara-a-cara?a=Jap%C3%B3n&b=Panam%C3%A1", 301),
])
def test_las_direcciones_de_antes_llevan_a_las_nuevas(cliente, antes, ahora, codigo):
    respuesta = cliente.get(antes)
    assert (respuesta.status_code, respuesta.headers["Location"]) == (codigo, ahora)


def test_el_quiz_de_antes_vuelve_a_enviar_la_respuesta(cliente):
    respuesta = cliente.post("/quiz/responder?todos=1", data={"opcion": "2"})
    assert (respuesta.status_code, respuesta.headers["Location"]) == (308, "/2026/quiz/responder?todos=1")
    # follow_redirects: el cliente sigue la redirección, como haría el navegador, con el mismo POST
    cliente.post("/quiz/responder", data={"opcion": "2"}, follow_redirects=True)
    with cliente.session_transaction() as sesion:
        assert sesion["quiz"]["aciertos"] == 1                 # la respuesta llegó


def test_una_accion_del_quiz_que_no_existe_da_404(cliente):
    assert cliente.post("/quiz/hackear").status_code == 404


# ===== Los Mundiales antiguos =====

@pytest.mark.parametrize("anio", [1930, 1934, 1950, 1982, 2002, 2022])
def test_cada_mundial_tiene_su_pagina(cliente, anio):
    pagina = html(cliente.get(f"/{anio}/"))
    assert f"<h1>Copa Mundial {anio}</h1>" in pagina
    assert f'class="logo">Mundial <span>{anio}</span>' in pagina
    assert 'id="quiz"' not in pagina and 'id="formato"' not in pagina   # solo en 2026


def test_un_mundial_antiguo_por_dentro(cliente):
    pagina = html(cliente.get("/1986/"))
    assert "🏆 Campeón: Argentina" in pagina
    assert '<h3>Grupo F</h3>' in pagina
    assert 'href="/1986/partido/51"' in pagina                 # la final, con su año
    assert 'href="#formato"' not in pagina                     # ni en el menú
    assert "Mejores terceros" not in pagina                    # la tabla de terceros es de 2026


def test_1950_no_tuvo_eliminatorias(cliente):
    pagina = html(cliente.get("/1950/"))
    assert "Este Mundial no tuvo eliminatorias" in pagina
    assert "<h3>Liguilla final</h3>" in pagina
    assert "<strong>Ningún partido</strong> se decidió en los penaltis" in pagina   # y no "0 partidos"


def test_1934_no_tuvo_grupos(cliente):
    pagina = html(cliente.get("/1934/"))
    assert 'id="selecciones"' not in pagina and 'href="#selecciones"' not in pagina
    assert "Volver a grupos" not in pagina                     # en el camino tampoco
    assert "Sin fase de grupos" in html(cliente.get("/1934/cara-a-cara"))


def test_solo_hay_filtro_de_paises_si_hubo_varios(cliente):
    assert 'aria-label="Filtrar estadios por país"' in html(cliente.get("/2002/"))   # Corea del Sur y Japón
    assert 'aria-label="Filtrar estadios por país"' not in html(cliente.get("/1998/"))


def test_el_quiz_de_un_mundial_sin_quiz_no_hace_nada(cliente):
    cliente.post("/1998/quiz/responder", data={"opcion": "0"})
    with cliente.session_transaction() as sesion:
        assert "quiz" not in sesion


def test_la_pagina_de_inicio_enlaza_a_todos(cliente):
    pagina = html(cliente.get("/"))
    assert '<th scope="row"><a href="/1930/">1930</a></th>' in pagina
    assert "llegan pronto" not in pagina


def test_los_partidos_que_se_volvieron_a_jugar(cliente):
    # Italia 1-1 España en cuartos de 1934 (partido 11) se repitió al día siguiente (partido 12)
    assert "Prórroga · Se volvió a jugar" in html(cliente.get("/1934/?ronda=1"))   # en la tarjeta de resultados
    empate, repeticion = html(cliente.get("/1934/partido/11")), html(cliente.get("/1934/partido/12"))
    assert "como entonces no había tanda de penaltis, se volvió a jugar" in empate
    assert '<a href="/1934/partido/12">ver la repetición (Italia 1-0 España (repetición))</a>' in empate
    assert '<a href="/1934/partido/11">ver el primer partido (' in repeticion
    assert "Es la repetición del empate" in repeticion


def test_un_desempate_de_grupo(cliente):
    assert "Gales 2-1 Hungría (desempate)" in html(cliente.get("/1958/"))           # en la lista del grupo
    pagina = html(cliente.get("/1958/partido/25"))
    assert "Partido de desempate: Gales y Hungría empataron en el grupo" in pagina
    assert "Es la repetición" not in pagina


# ===== Cada selección en todos los Mundiales =====

def test_la_lista_de_selecciones(cliente):
    pagina = html(cliente.get("/selecciones"))
    assert "<h1>Las 84 selecciones</h1>" in pagina
    assert '<th scope="row"><a href="/seleccion/Brasil">Brasil</a></th>' in pagina
    assert 'href="/selecciones">Selecciones</a>' in pagina     # en el menú


def test_la_pagina_de_una_seleccion(cliente):
    pagina = html(cliente.get("/seleccion/Alemania"))
    assert "<h1>Alemania</h1>" in pagina
    assert "También jugó como Alemania Federal." in pagina
    assert '<a href="/1974/?seleccion=Alemania+Federal#camino">1974</a>' in pagina
    assert "(como Alemania Federal)" in pagina
    assert '<th scope="row">Miroslav Klose</th>' in pagina


def test_contra_otra_seleccion(cliente):
    pagina = html(cliente.get("/seleccion/Alemania?contra=Argentina"))
    assert "7 partidos contra Argentina" in pagina
    assert "Alemania: 5 ganados, 1 empatado y 1 perdido (12-5 en goles)" in " ".join(pagina.split())  # sin saltos de línea
    assert 'href="/2014/partido/63">Alemania 1-0 Argentina' in pagina   # la final de 2014, con su año
    assert "partidos contra" not in html(cliente.get("/seleccion/Alemania?contra=Narnia"))  # un rival que no existe


@pytest.mark.parametrize("ruta, codigo, destino", [
    ("/seleccion/Alemania%20Federal", 301, "/seleccion/Alemania"),     # va dentro de la de Alemania
    ("/seleccion/Uni%C3%B3n%20Sovi%C3%A9tica?contra=Brasil", 301, "/seleccion/Rusia?contra=Brasil"),
    ("/seleccion/Narnia", 404, None),
])
def test_selecciones_con_otro_nombre_o_que_no_existen(cliente, ruta, codigo, destino):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == codigo and respuesta.headers.get("Location") == destino


def test_enlaces_a_las_selecciones(cliente):
    assert '<a href="/seleccion/Alemania">Alemania Federal</a>' in html(cliente.get("/"))   # campeón de 1954
    assert 'href="/seleccion/RD%20del%20Congo">RD del Congo en todos los Mundiales' in html(cliente.get("/1974/?seleccion=Zaire"))


# ===== Idiomas =====

def test_por_defecto_el_idioma_del_navegador(cliente):
    assert '<html lang="es"' in html(cliente.get("/"))                                    # sin decir nada
    assert '<html lang="en"' in html(cliente.get("/", headers={"Accept-Language": "en-GB,en;q=0.9"}))
    assert '<html lang="pt"' in html(cliente.get("/", headers={"Accept-Language": "pt-BR"}))
    assert '<html lang="es"' in html(cliente.get("/", headers={"Accept-Language": "de"}))  # uno que no hay
    assert "Accept-Language" in cliente.get("/").headers["Vary"]


def test_elegir_un_idioma(cliente):
    respuesta = cliente.post("/idioma", data={"idioma": "en", "volver": "/selecciones?x=1"})
    assert respuesta.headers["Location"] == "/selecciones?x=1#idioma"     # vuelve a donde estaba
    pagina = html(cliente.get("/", headers={"Accept-Language": "pt"}))  # lo elegido manda sobre el navegador
    assert '<html lang="en"' in pagina
    assert "<h1>FIFA World Cup</h1>" in pagina
    assert "<li><strong>1,068</strong> matches</li>" in pagina           # los números, a la inglesa
    assert "<td>South Korea and Japan</td>" in pagina
    assert 'aria-pressed="true">English</button>' in pagina


def test_un_idioma_que_no_existe_no_cambia_nada(cliente):
    cliente.post("/idioma", data={"idioma": "klingon", "volver": "/"})
    with cliente.session_transaction() as sesion:
        assert "idioma" not in sesion


@pytest.mark.parametrize("volver", ["https://otra-web.com/", "//otra-web.com/", "/\\otra-web.com", ""])
def test_los_botones_solo_vuelven_a_esta_web(cliente, volver):
    respuesta = cliente.post("/idioma", data={"idioma": "pt", "volver": volver})
    assert respuesta.headers["Location"] == "/#idioma"


def test_el_tema_vuelve_a_la_pagina_donde_se_eligio(cliente):
    # Antes del paso 65, desde la página de inicio llevaba a /2026/
    assert cliente.post("/tema", data={"tema": "claro", "volver": "/"}).headers["Location"] == "/#tema"


def test_el_selector_de_idioma_esta_en_la_portada_y_en_el_pie(cliente):
    pagina = html(cliente.get("/"))
    assert 'id="idioma-portada"' in pagina and 'id="idioma"' in pagina
    # Cada idioma, con su nombre en ese idioma (lang="pt") para que el lector de pantalla lo pronuncie bien
    assert 'value="pt" lang="pt" aria-pressed="false">Português</button>' in " ".join(pagina.split())
    assert 'id="idioma"' in html(cliente.get("/2026/"))                   # el del pie, en todas las páginas


def test_las_selecciones_en_ingles(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = " ".join(html(cliente.get("/seleccion/Alemania?contra=Argentina")).split())
    assert "<h1>Germany</h1>" in pagina and "Also played as West Germany." in pagina
    assert "74 wins, 17 draws and 25 losses" in pagina
    assert '<option value="Argentina" selected>Argentina</option>' in pagina    # el valor, en español
    assert "<td>🏆 World champion" in pagina
    # La tanda de penaltis de 2006, con su forma larga en inglés para el lector de pantalla
    assert '<abbr title="(penalties 4-2)" aria-hidden="true">(pens 4-2)</abbr>' in pagina
    lista = " ".join(html(cliente.get("/selecciones")).split())
    assert lista.index(">Algeria</a>") < lista.index(">Germany</a>")           # por orden alfabético en inglés
    assert "<h1>The 84 teams</h1>" in lista


def test_un_minuto_se_lee_en_el_idioma_elegido(cliente):
    from app import abreviaturas_en
    assert '<span class="solo-lector">minute 90 plus 1</span>' in abreviaturas_en("Kane 90+1'", "en")
    assert '<span class="solo-lector">minuto 90 mais 1</span>' in abreviaturas_en("Kane 90+1'", "pt")
    # Las marcas de los goles (en español en mundial.py) salen en el idioma elegido
    assert '>(g.c.)</abbr><span class="solo-lector">(gol contra)</span>' in abreviaturas_en("Pepe 10' (p.p.)", "pt")
    assert '>(o.g.)</abbr><span class="solo-lector">(own goal)</span>' in abreviaturas_en("Pepe 10' (p.p.)", "en")
    # Una abreviatura en español que no tiene traducción en ese texto se sigue leyendo bien
    assert '<span class="solo-lector">(tras la prórroga)</span>' in abreviaturas_en("A 1-0 B (prór.)", "pt")


def test_un_mundial_en_ingles(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = " ".join(html(cliente.get("/2026/?seleccion=Japón&ronda=4")).split())
    assert "<h1>2026 World Cup</h1>" in pagina
    assert "🏆 Champion: Spain" in pagina
    assert '<abbr title="July" aria-hidden="true">Jul</abbr><span class="solo-lector">July</span> 19' in pagina  # la final
    assert '<option value="Japón" selected>Japan</option>' in pagina   # se ve en inglés, se envía en español
    assert "Standings of group A" in pagina
    assert "308 goals in 104 matches (2.96 per match), 14 of them own goals." in pagina
    assert '<span role="img" aria-label="Golden Boot:">👟</span>' in pagina
    assert "Ciudad de México" not in pagina and "Mexico City" in pagina


def test_buscar_una_seleccion_por_su_nombre_en_otro_idioma(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = html(cliente.get("/2026/?buscar=germany"))
    assert 'id="grupo-E"' in pagina                                   # el grupo de Alemania
    assert "No hay ninguna" not in pagina and "There is no team" not in pagina


def test_un_mundial_en_portugues(cliente):
    cliente.post("/idioma", data={"idioma": "pt", "volver": "/"})
    pagina = " ".join(html(cliente.get("/1950/")).split())
    assert "<h1>Copa do Mundo de 1950</h1>" in pagina
    assert "<h3>Quadrangular final</h3>" in pagina
    assert "Esta Copa não teve mata-mata" in pagina
    assert "<strong>Nenhum jogo</strong> foi decidido nos pênaltis" in pagina


def test_la_pagina_de_un_partido_en_ingles(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = " ".join(html(cliente.get("/1934/partido/11")).split())
    assert "<h1>Italy 1-1 Spain</h1>" in pagina
    assert "It ended in a draw and, as there were no penalty shoot-outs then, it was replayed on" in pagina
    assert '<a href="/1934/partido/12">see the replay (Italy 1-0 Spain (replay))</a>' in pagina
    assert "Quarter-finals ·" in pagina and "Florence (Italy)" in pagina
    assert "Italy&#39;s path" in pagina and "Next match →" in pagina   # el apóstrofo, escapado en el HTML


def test_el_cara_a_cara_en_portugues(cliente):
    cliente.post("/idioma", data={"idioma": "pt", "volver": "/"})
    pagina = " ".join(html(cliente.get("/2026/cara-a-cara")).split())
    assert "<h1>Frente a frente</h1>" in pagina
    assert '<option value="Argentina" selected>Argentina</option>' in pagina
    assert "<td>🏆 Campeã do mundo</td>" in pagina and "Entre elas" in pagina


def test_la_404_en_ingles(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = html(cliente.get("/no-existe"))
    assert "<h1>Offside</h1>" in pagina and "Back to the home page" in pagina


def test_el_quiz_en_ingles(cliente):
    cliente.post("/idioma", data={"idioma": "en", "volver": "/"})
    pagina = " ".join(html(cliente.get("/2026/")).split())
    assert "Question 1 of 10" in pagina and "How many teams played at the 2026 World Cup?" in pagina
    cliente.post("/2026/quiz/responder", data={"opcion": "2"})      # 48: la buena
    pagina = " ".join(html(cliente.get("/2026/")).split())
    assert "✅ Correct! It is the first World Cup with 48 teams." in pagina
    assert '48<span class="solo-lector"> (your answer, correct)</span>' in pagina


# ===== La página de inicio: todos los Mundiales =====

def test_la_pagina_de_inicio(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200                     # ya no redirige: es la página de inicio
    pagina = html(respuesta)
    assert "<h2>Los 23 Mundiales</h2>" in pagina
    assert '<th scope="row"><a href="/2026/">2026</a></th>' in pagina   # el de 2026 tiene su página
    assert "<td>Corea del Sur y Japón</td>" in pagina
    assert "<td>Estados Unidos, México y Canadá</td>" in pagina
    assert '<th scope="row"><a href="/seleccion/Brasil">Brasil</a></th><td><strong>5</strong></td><td>1958, 1962, 1970, 1994, 2002</td>' in pagina
    assert '<th scope="row">Kylian Mbappé</th>' in pagina
    assert "el Mundial con más goles por partido es «1954», con 5,38" in pagina


def test_la_pagina_de_inicio_tiene_su_propio_menu(cliente):
    pagina = html(cliente.get("/"))
    assert 'href="#campeones">Campeones</a>' in pagina
    assert 'href="#quiz"' not in pagina                     # el menú del Mundial 2026 no sale aquí
    assert 'href="/">Todos los Mundiales</a>' in html(cliente.get("/2026/"))  # y desde 2026 se vuelve


# ===== La cookie de la sesión, solo cuando hace falta =====

@pytest.mark.parametrize("ruta", ["/", "/2026/", "/2026/?pais=México&ronda=2&linea=linea-sede-0", "/no-existe", "/fuentes"])
def test_solo_mirar_la_web_no_crea_ninguna_cookie(cliente, ruta):
    assert "Set-Cookie" not in cliente.get(ruta).headers


@pytest.mark.parametrize("pedir", [lambda c: c.post("/2026/quiz/responder", data={"opcion": "2"}),
                                   lambda c: c.post("/tema", data={"tema": "claro"})])
def test_responder_el_quiz_o_elegir_el_tema_si_crea_la_cookie(cliente, pedir):
    assert pedir(cliente).headers["Set-Cookie"].startswith("session=")


def test_al_reiniciar_el_quiz_sin_tema_elegido_se_borra_la_cookie(cliente):
    cliente.post("/2026/quiz/responder", data={"opcion": "2"})
    cookie = cliente.post("/2026/quiz/reiniciar").headers["Set-Cookie"]
    assert "Max-Age=0" in cookie                          # la sesión quedó vacía: Flask la borra


def test_al_reiniciar_el_quiz_se_mantiene_el_tema(cliente):
    cliente.post("/tema", data={"tema": "oscuro"})
    cliente.post("/2026/quiz/responder", data={"opcion": "2"})
    cliente.post("/2026/quiz/reiniciar")
    with cliente.session_transaction() as sesion:
        assert sesion == {"tema": "oscuro"}


# ===== La página de cada partido =====

def test_la_pagina_de_la_final(cliente):
    respuesta = cliente.get("/2026/partido/103")                # el último partido por fecha
    assert respuesta.status_code == 200
    pagina = html(respuesta)
    assert "<title>España 1-0 Argentina (prór.) · Final · Mundial 2026</title>" in pagina
    assert "<h1>España 1-0 Argentina</h1>" in pagina
    assert "MetLife Stadium · Nueva York / Nueva Jersey (Estados Unidos)" in pagina
    assert pagina.count('class="cronologia"') == 1         # la línea del tiempo, ya abierta
    assert 'href="/2026/?seleccion=Argentina#camino"' in pagina
    assert 'href="/2026/partido/102"' in pagina and 'href="/2026/partido/104"' not in pagina  # no hay siguiente


def test_el_primer_partido_no_tiene_anterior(cliente):
    pagina = html(cliente.get("/2026/partido/0"))
    assert "<h1>México 2-0 Sudáfrica</h1>" in pagina
    assert "Partido anterior" not in pagina and 'href="/2026/partido/1"' in pagina


def test_un_partido_sin_goles(cliente):
    numero = next(i for i, p in enumerate(mundial.cargar()["todos_los_partidos"])
                  if p["golesLocal"] + p["golesVisitante"] == 0)
    pagina = html(cliente.get(f"/2026/partido/{numero}"))
    assert "Sin goles." in pagina and 'class="cronologia"' not in pagina


@pytest.mark.parametrize("ruta", ["/2026/partido/104", "/2026/partido/-1", "/2026/partido/hola"])
def test_un_partido_que_no_existe_da_404(cliente, ruta):
    assert cliente.get(ruta).status_code == 404


def test_la_portada_enlaza_a_las_paginas_de_los_partidos(cliente):
    pagina = html(cliente.get("/2026/"))
    assert 'href="/2026/partido/0">México 2-0 Sudáfrica</a>' in pagina    # en su estadio y en su grupo
    assert 'href="/2026/partido/103">Ver partido' in pagina                # en la tarjeta de la final


# ===== Qué versión sirve la web =====

def test_en_tu_ordenador_la_version_es_desarrollo(cliente, monkeypatch):
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    respuesta = cliente.get("/version")
    assert respuesta.mimetype == "text/plain" and html(respuesta) == "desarrollo"


def test_en_render_la_version_es_el_commit_desplegado(cliente, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "d9b2325aaaa")
    assert html(cliente.get("/version")) == "d9b2325aaaa"
    assert "Set-Cookie" not in cliente.get("/version").headers


# ===== Gráficas de goles =====

def grafica(pagina, id_titulo):
    """Solo el trozo de la página con una gráfica (su <figure>), para no contar las barras de la otra."""
    donde = pagina.index(f'id="{id_titulo}"')
    return pagina[pagina.rindex("<figure", 0, donde):pagina.index("</figure>", donde)]


def test_la_grafica_de_goles_por_minuto(cliente):
    pagina = grafica(html(cliente.get("/2026/")), "grafica-titulo")
    assert '<svg viewBox="0 0 340 200" role="img" aria-labelledby="grafica-titulo grafica-resumen">' in pagina
    assert pagina.count('class="grafica-barra"') == 7       # una barra por tramo
    assert pagina.count('class="grafica-valor"') == 1       # solo la más alta lleva su número
    assert "<title>76-90+: 81 goles</title>" in pagina      # al pasar el ratón
    assert "el tramo con más goles es el del 76-90+, con 81" in pagina
    assert '<th scope="row">91-120 (prórroga)</th><td>8</td>' in pagina  # la tabla con los mismos datos


def test_la_grafica_de_goles_por_ronda(cliente):
    pagina = grafica(html(cliente.get("/2026/")), "grafica-ronda-titulo")
    assert pagina.count('class="grafica-barra"') == 7       # una barra por ronda
    assert pagina.count('class="grafica-valor"') == 1       # la más larga, con su número más marcado
    assert "<title>Final: 1 gol en 1 partido</title>" in pagina            # en singular
    assert "<title>Tercer puesto: 10 goles en 1 partido</title>" in pagina  # al pasar el ratón
    assert "la ronda con más goles por partido es «Tercer puesto», con 10,00" in pagina
    # La tabla con los mismos datos: ronda, partidos, goles y goles por partido
    assert '<th scope="row">Fase de grupos</th><td>72</td><td>215</td><td>2,99</td>' in pagina


# ===== Récords =====

def test_los_records_salen_en_resultados(cliente):
    pagina = html(cliente.get("/2026/"))
    assert "<h3>Récords del Mundial</h3>" in pagina
    assert "<strong>Mayor goleada</strong> (6 goles de diferencia)" in pagina
    assert "<strong>Partido con más goles</strong> (10)" in pagina
    assert "<strong>4 partidos</strong> se decidieron en los penaltis" in pagina
    assert "<strong>8 partidos</strong> terminaron 0-0" in pagina


def test_los_records_son_los_mismos_en_cualquier_ronda(cliente):
    # Son de los 104 partidos: elegir otra ronda no los cambia
    pagina = html(cliente.get("/2026/?ronda=0"))
    assert "<strong>Partido con más goles</strong> (10)" in pagina


# ===== Cara a cara =====

@pytest.mark.parametrize("ruta, a, b", [
    ("/2026/cara-a-cara", "España", "Argentina"),                  # por defecto, los finalistas
    ("/2026/cara-a-cara?a=Argentina", "Argentina", "España"),       # falta b: la otra finalista
    ("/2026/cara-a-cara?b=España", "Argentina", "España"),          # falta a: la otra finalista
    ("/2026/cara-a-cara?a=Narnia&b=Japón", "España", "Japón"),      # una que no existe
    ("/2026/cara-a-cara?a=Japón&b=Panamá", "Japón", "Panamá"),
])
def test_que_selecciones_compara(cliente, ruta, a, b):
    assert f"<title>{a} y {b}, cara a cara · Mundial 2026</title>" in html(cliente.get(ruta))


def test_la_pagina_del_cara_a_cara(cliente):
    pagina = html(cliente.get("/2026/cara-a-cara?a=España&b=Argentina"))
    assert "<td>Mikel Oyarzabal (5)</td>" in pagina and "<td>Lionel Messi (8)</td>" in pagina
    assert 'href="/2026/partido/103"' in pagina                     # la final, el partido entre ellas
    assert '<option value="España" selected>España</option>' in pagina


def test_cara_a_cara_sin_partidos_entre_ellas_ni_goles(cliente):
    pagina = html(cliente.get("/2026/cara-a-cara?a=Japón&b=Panamá"))
    assert "No se enfrentaron en este Mundial." in pagina and "<td>Nadie marcó</td>" in pagina


def test_la_misma_seleccion_dos_veces(cliente):
    pagina = html(cliente.get("/2026/cara-a-cara?a=Ghana&b=Ghana"))
    assert "Has elegido la misma selección dos veces." in pagina and "Entre ellas" not in pagina


def test_el_camino_enlaza_al_cara_a_cara(cliente):
    assert 'href="/2026/cara-a-cara?a=Jap%C3%B3n">Comparar con otra selección' in html(cliente.get("/2026/?seleccion=Japón"))
