"""La web del Mundial 2026 con Flask.

Para arrancarla, desde la carpeta del proyecto:
    venv/bin/flask --app app run --debug
y abrir http://127.0.0.1:5000

Lo que antes hacía JavaScript en el navegador (filtrar, buscar, elegir ronda...)
ahora lo hace Python en el servidor: cada elección es un parámetro de la dirección,
por ejemplo /2026/?pais=México#sedes, y Flask devuelve la página ya preparada.

Cada Mundial tiene sus páginas bajo su año: /2026/, /2026/partido/12... (por ahora, solo el de 2026).
"""

import hashlib
import os
import re
from functools import cache
from pathlib import Path

from flask import Flask, Response, abort, g, has_request_context, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape

import mundial
import textos

app = Flask(__name__)
# La sesión (donde se guarda cómo va el quiz) se firma con esta clave.
# En un servidor de verdad hay que poner otra en la variable de entorno CLAVE_SECRETA.
app.secret_key = os.environ.get("CLAVE_SECRETA", "solo-para-desarrollo")
# En Render (que define la variable RENDER) la web va por HTTPS: la cookie de la sesión solo viaja
# cifrada. En tu ordenador (http://127.0.0.1) no se activa, porque si no la cookie no se guardaría.
app.config["SESSION_COOKIE_SECURE"] = "RENDER" in os.environ
# La cookie no viaja cuando otra web envía un formulario a esta (p. ej. a /quiz/responder)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Jinja quita el salto de línea y la sangría que dejan las etiquetas {% ... %}: la página pesa menos
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# ===== Un Mundial por año: /2026/, /1986/partido/12... =====
# Las rutas de cada Mundial empiezan por <int:anio>. ("anio" y no "año": Flask solo acepta letras
# sin tilde ni eñe en el nombre de un parámetro.)
MUNDIALES = mundial.cargar_todos()  # los datos se leen una sola vez, al arrancar: {1930: {...}, ...}
ULTIMO = max(MUNDIALES)
H = mundial.cargar_historia(MUNDIALES)  # lo de la página de inicio
HISTORIAL = mundial.historial(MUNDIALES)  # cada selección en todos los Mundiales: {"Brasil": {...}, ...}


app.jinja_env.globals["ultimo_mundial"] = MUNDIALES[ULTIMO]  # para base.html en la 404


def datos():
    """Los datos del Mundial de la página que se está pidiendo (el de su año), o los del último."""
    return MUNDIALES[g.get("anio", ULTIMO)]


@app.url_value_preprocessor
def sacar_el_anio(endpoint, valores):
    """Antes de cada ruta: quita el año de los parámetros y lo guarda en g (lo que dura la petición).
    Así las funciones de las rutas no tienen que recibirlo. Si ese año no tiene Mundial, 404."""
    if valores and "anio" in valores:
        g.anio = valores.pop("anio")
        if g.anio not in MUNDIALES:
            abort(404)


@app.url_defaults
def poner_el_anio(endpoint, valores):
    """En cada url_for() de una ruta que necesita año y no lo lleva, pone el de la página actual
    (o el último, en las páginas que no son de ningún Mundial, como la 404). Así url_for("partido",
    numero=12) da /2026/partido/12 sin tener que escribir el año en cada enlace."""
    if "anio" not in valores and app.url_map.is_endpoint_expecting(endpoint, "anio"):
        valores["anio"] = g.get("anio", ULTIMO)

# ===== Caché de los archivos de static/ =====
# El navegador guarda styles.css un año sin volver a pedirlo. Para que vea los cambios, la dirección
# lleva una "huella" del contenido (styles.css?v=3f9a1c...): si el archivo cambia, cambia la huella,
# la dirección es otra y el navegador lo descarga de nuevo.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 365 * 24 * 60 * 60  # un año, en segundos


@app.template_global()
def estatico(archivo):
    """La dirección de un archivo de static/ con su huella: /static/styles.css?v=3f9a1c2b7d

    Se calcula en cada página (tarda microsegundos): así, si cambias styles.css con la web
    arrancada, la huella cambia enseguida y tu navegador no se queda con el CSS viejo.
    """
    huella = hashlib.sha256((Path(app.static_folder) / archivo).read_bytes()).hexdigest()[:10]
    return url_for("static", filename=archivo, v=huella)


def goles_del_partido(p):
    """Solo los goles de ese partido (ya agrupados al arrancar), en vez de los 308 del Mundial."""
    return datos()["goles_por_partido"].get(mundial.clave_partido(p), [])


# ===== Líneas del tiempo =====
# No vienen dentro de la página: cada una es un enlace (?linea=linea-grupo-12) y Flask solo pinta
# la que se ha pedido. Un mismo partido sale en su estadio, en su grupo y en resultados: el "lugar"
# hace que se abra justo donde se ha pulsado.

@app.template_global()
def id_linea(p, lugar):
    """ "linea-grupo-12": el lugar ("sede", "grupo" o "resultado") y el número del partido."""
    return f"linea-{lugar}-{datos()['numero_de_partido'][mundial.clave_partido(p)]}"


@app.template_global()
def linea_abierta_en(partidos, lugar):
    """¿Hay que abrir el desplegable de estos partidos? Sí, si dentro está la línea del tiempo abierta
    (?linea=...) o la que se acaba de cerrar (?vista=...): así, al cerrarla, no se cierra todo."""
    ids = {id_linea(p, lugar) for p in partidos}
    return request.args.get("linea") in ids or request.args.get("vista") in ids


# ===== Idiomas: español, portugués e inglés =====
# Como el tema: se elige con unos botones (un formulario a /idioma) y se guarda en la sesión.
# Si no se ha elegido ninguno, el del navegador (la cabecera Accept-Language), o español.
app.jinja_env.globals["idiomas"] = textos.IDIOMAS


@app.template_global()
def idioma_elegido():
    """ "es", "pt" o "en". Fuera de una petición (en algunas pruebas), español."""
    if not has_request_context():
        return "es"
    return session.get("idioma") or request.accept_languages.best_match(list(textos.IDIOMAS), default="es")


@app.template_global()
def t(texto, **datos):
    """El texto en el idioma elegido: t("Campeones") -> "Champions". Ver textos.py."""
    return textos.traducir(texto, idioma_elegido(), **datos)


@app.template_filter()
def nombre(texto):
    """El nombre de una selección o una ronda en el idioma elegido: "Brasil" -> "Brazil"."""
    return textos.nombre(texto, idioma_elegido())


def con_puntos(numero):
    """1068 -> "1.068" (en inglés, "1,068")."""
    return f"{numero:,}" if idioma_elegido() == "en" else mundial.con_puntos(numero)


def con_coma(numero):
    """2.986 -> "2,99" (en inglés, "2.99")."""
    return f"{numero:.2f}" if idioma_elegido() == "en" else mundial.con_coma(numero)


def volver_a(si_no):
    """La página desde la que se envió el formulario (el campo "volver"), para regresar a ella.

    Solo direcciones de esta web ("/2026/?pais=México"): si alguien pusiera "https://otra-web.com"
    o "//otra-web.com", la web llevaría allí a quien pulsó el botón. En ese caso, a si_no.
    """
    volver = request.form.get("volver", "")
    if volver.startswith("/") and not volver.startswith("//") and "\\" not in volver:
        return volver
    return si_no


@app.post("/idioma")
def elegir_idioma():
    idioma = request.form.get("idioma")
    if idioma in textos.IDIOMAS:
        session["idioma"] = idioma
    return redirect(volver_a(url_for("raiz")) + "#idioma")


# Funciones de mundial.py que usan las plantillas
app.jinja_env.filters.update(con_signo=mundial.con_signo, con_puntos=con_puntos, con_coma=con_coma,
                             texto_partido=lambda p: textos.texto_partido(p, idioma_elegido()))
app.jinja_env.globals.update(ganador_de=mundial.ganador_de, minimo_goles=mundial.MINIMO_GOLES,
                             anotadores_de=lambda p, equipo: mundial.anotadores_de(goles_del_partido(p), p, equipo),
                             linea_del_tiempo=lambda p: mundial.linea_del_tiempo(goles_del_partido(p), p),
                             hay_goles=lambda p: bool(goles_del_partido(p)))


# ===== Abreviaturas, para los lectores de pantalla =====
# En pantalla se ve la forma corta ("19 jul", "(pen.)") y el lector de pantalla lee la larga.
# Esto es solo cómo se muestra: mundial.py sigue devolviendo el texto corto.

# Las abreviaturas de los tres idiomas están en textos.py. Una expresión regular las encuentra todas,
# y también las tandas de penaltis ("(pen. 4-3)", "(pens 4-3)") y los minutos ("48'", "90+1'").
# El \b obliga a que el minuto empiece en un número suelto
PATRON_ABREVIATURAS = re.compile(
    "|".join(re.escape(corta) for cortas in textos.ABREVIATURAS.values() for corta in cortas)
    + r"|\((?:pen\.|pên\.|pens) (\d+)-(\d+)\)|\b\d+(?:\+\d+)?'")


def leer_entera(encontrada, idioma):
    """La forma larga de una abreviatura: "(pen. 4-3)" -> "(penaltis 4-3)", "90+1'" -> "minuto 90 más 1".

    Si en ese idioma no existe, se busca en español: lo que aún no está traducido sale con sus abreviaturas
    en español, y tienen que seguir leyéndose bien.
    """
    corta = encontrada.group()
    for lengua in (idioma, "es"):
        if corta in textos.ABREVIATURAS[lengua]:
            return textos.ABREVIATURAS[lengua][corta]
    if encontrada.group(1):  # una tanda de penaltis: los dos números
        return textos.TANDA[idioma][1].format(encontrada.group(1), encontrada.group(2))
    minuto, _, anadido = corta.removesuffix("'").partition("+")  # "90+1'" -> "90", "+", "1"
    solo, con_anadido = textos.MINUTO[idioma]
    return con_anadido.format(minuto, anadido) if anadido else solo.format(minuto)


# @cache guarda el resultado de cada llamada: la página pide miles de veces los mismos minutos
# ("45'", "90+1'"...) y las mismas abreviaturas, y así solo se calculan la primera vez.
# Se puede porque el resultado (Markup) es un texto que no cambia, y la caché no crece sin fin
# porque los textos salen de los datos, que son siempre los mismos (no de lo que escribe quien visita).
@app.template_global()
@cache
def abreviatura(corta, larga, clase=""):
    """Se ve "PJ" y el lector de pantalla lee "Partidos jugados" (el title la muestra al pasar el ratón).

    El <abbr> lleva aria-hidden para que el lector no lea también la forma corta, y el texto largo
    va en un <span class="solo-lector">, que no se ve. Markup.format() escapa los textos, así que
    se pueden usar aunque vengan de los datos.
    """
    con_clase = Markup(' class="{}"').format(clase) if clase else ""
    return Markup('<abbr{} title="{}" aria-hidden="true">{}</abbr><span class="solo-lector">{}</span>').format(
        con_clase, larga, corta, larga)


@app.template_filter()
def abreviaturas(texto):
    """Cambia las abreviaturas de un texto ("Harry Kane 30' (pen.)") por su forma accesible, en el idioma elegido."""
    return abreviaturas_en(texto, idioma_elegido())


@cache  # una caché por texto y por idioma: "48'" se lee "minuto 48" o "minute 48"
def abreviaturas_en(texto, idioma):
    # Las marcas de los goles salen de mundial.py en español: aquí se cambian por las del idioma
    for espanol, traducida in textos.MARCAS_GOL.get(idioma, {}).items():
        texto = texto.replace(espanol, traducida)
    trozos = []
    fin_anterior = 0
    for encontrada in PATRON_ABREVIATURAS.finditer(texto):
        trozos.append(escape(texto[fin_anterior:encontrada.start()]))  # el texto de en medio, escapado
        trozos.append(abreviatura(encontrada.group(), leer_entera(encontrada, idioma)))
        fin_anterior = encontrada.end()
    trozos.append(escape(texto[fin_anterior:]))
    return Markup("").join(trozos)


@app.template_filter()
def fecha(texto):
    """"2026-07-19": se ve "19 jul" y el lector de pantalla lee "19 de julio".
    En portugués, "19 jul" ("19 de julho"); en inglés, el mes delante: "Jul 19" ("July 19")."""
    idioma = idioma_elegido()
    dia = int(texto[8:10])
    cortos, largos = textos.MESES[idioma]
    mes = int(texto[5:7]) - 1
    if idioma == "en":
        return Markup("{} {}").format(abreviatura(cortos[mes], largos[mes]), dia)
    return Markup("{} {}").format(dia, abreviatura(cortos[mes], "de " + largos[mes]))


@app.template_global()
def enlace(_seccion=None, **cambios):
    """La dirección de la página actual con algunos parámetros cambiados (None quita uno).

    Así cada enlace conserva lo demás que estaba elegido: si se filtran los estadios por
    México y luego se elige otra ronda, el filtro de estadios sigue puesto.
    """
    parametros = request.args.to_dict()
    for clave, valor in cambios.items():
        if valor is None:
            parametros.pop(clave, None)
        else:
            parametros[clave] = valor
    return url_for("inicio", **parametros, _anchor=_seccion)


def estado_quiz():
    """Cómo va el quiz de quien visita la web. Se guarda en su sesión (una cookie firmada).

    Si aún no ha empezado, devuelve uno nuevo pero no lo guarda: así, quien solo mira la web
    no recibe ninguna cookie. Se guarda (y se crea la cookie) al responder la primera pregunta.
    """
    return session.get("quiz") or {"indice": 0, "aciertos": 0, "respondida": None}


@app.route("/<int:anio>/")
def inicio():
    M = datos()
    # Lo que se ha elegido en la página llega como parámetros de la dirección
    pais = request.args.get("pais")
    if pais not in M["paises"]:
        pais = None  # todos
    buscar = request.args.get("buscar", "").strip()
    ronda = request.args.get("ronda", type=int)
    if ronda is None or not 0 <= ronda < len(M["rondas"]):
        ronda = len(M["rondas"]) - 1  # por defecto, la final (en 1950, sin eliminatorias: -1, no se usa)
    seleccion = request.args.get("seleccion")
    if seleccion not in M["selecciones"]:
        seleccion = M["campeon"]
    ver_todos = request.args.get("todos") == "1"

    return render_template(
        "index.html",
        m=M,
        pais=pais,
        estadios=[e for e in M["estadios"] if pais in (None, e["pais"])],
        buscar=buscar,
        grupos_visibles=mundial.buscar_grupos(M["grupos"], buscar, traducir=nombre),
        busqueda=mundial.normalizar(buscar),
        normalizar=mundial.normalizar,
        ronda=ronda,
        camino=mundial.camino(M, seleccion),
        ver_todos=ver_todos,
        goleadores=[g for g in M["goleadores"] if ver_todos or g["goles"] >= mundial.MINIMO_GOLES],
        jugador_abierto=request.args.get("jugador"),
        partidos_del_goleador=lambda g: mundial.partidos_del_goleador(
            M["goles"], M["todos_los_partidos"], g["jugador"], g["seleccion"]),
        quiz=estado_quiz(),
    )


# ===== Quiz =====
# Cada botón del quiz envía un formulario (POST). Flask actualiza la sesión y vuelve a la
# página con una redirección, para que al recargar no se envíe otra vez la respuesta.

def volver_al_quiz():
    return redirect(url_for("inicio", **request.args, _anchor="quiz"))


@app.post("/<int:anio>/quiz/responder")
def quiz_responder():
    quiz = estado_quiz()
    preguntas = datos()["preguntas"]  # solo el Mundial 2026 tiene quiz: en los demás, ninguna
    elegida = request.form.get("opcion", type=int)
    if quiz["respondida"] is None and quiz["indice"] < len(preguntas) and elegida is not None:
        quiz["respondida"] = elegida
        if elegida == preguntas[quiz["indice"]]["correcta"]:
            quiz["aciertos"] += 1
        session["quiz"] = quiz  # guardarlo en la sesión: Flask manda la cookie con el cambio
    return volver_al_quiz()


@app.post("/<int:anio>/quiz/siguiente")
def quiz_siguiente():
    quiz = estado_quiz()
    if quiz["respondida"] is not None:
        quiz["indice"] += 1
        quiz["respondida"] = None
        session["quiz"] = quiz
    return volver_al_quiz()


@app.post("/<int:anio>/quiz/reiniciar")
def quiz_reiniciar():
    session.pop("quiz", None)
    return volver_al_quiz()


# ===== Tema claro u oscuro =====
# Por defecto la web sigue el modo del sistema. Si se elige uno a mano, se guarda en la sesión
# (la misma cookie firmada que el quiz) y base.html lo pone en <html data-tema="...">.
TEMAS = {"auto": "Automático", "claro": "Claro", "oscuro": "Oscuro"}
app.jinja_env.globals["temas"] = TEMAS


@app.template_global()
def tema_elegido():
    """ "claro", "oscuro" o "auto" (si no se ha elegido ninguno: el del sistema)."""
    return session.get("tema", "auto")


@app.post("/tema")
def elegir_tema():
    tema = request.form.get("tema")
    if tema in TEMAS and tema != "auto":
        session["tema"] = tema
    else:
        session.pop("tema", None)  # "auto" (o algo que no existe): vuelve a seguir al sistema
    # A la página donde se pulsó. (Antes del paso 65 volvía siempre a un Mundial, también desde la de inicio)
    return redirect(volver_a(url_for("inicio", **request.args)) + "#tema")


# ===== Cabeceras de seguridad =====
# Instrucciones para el navegador de quien visita la web, en todas las respuestas.

# Content-Security-Policy: de dónde puede cargar cosas la página. Si alguien consiguiera colar
# HTML en ella, el navegador no ejecutaría scripts ni cargaría nada de otras webs.
POLITICA_DE_CONTENIDO = "; ".join([
    "default-src 'self'",                      # por defecto, solo de esta misma web
    "script-src 'none'",                       # la web no usa JavaScript: ninguno
    "style-src-elem 'self' https://fonts.googleapis.com",  # styles.css y las fuentes de Google
    # Los style="left: 40%" de la línea del tiempo: solo atributos, nunca bloques <style>
    "style-src-attr 'unsafe-inline'",
    # Para navegadores antiguos que no entienden las dos de arriba
    "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'",
    "font-src https://fonts.gstatic.com",      # los archivos de las fuentes
    "img-src 'self'",                          # el icono de la pestaña
    "form-action 'self'",                      # los formularios solo se envían a esta web
    "base-uri 'none'",
    "object-src 'none'",
    "frame-ancestors 'none'",                  # ninguna web puede meter esta dentro de un <iframe>
])

CABECERAS_DE_SEGURIDAD = {
    "Content-Security-Policy": POLITICA_DE_CONTENIDO,
    "X-Content-Type-Options": "nosniff",         # un .css es CSS: el navegador no "adivina" otro tipo
    "X-Frame-Options": "DENY",                   # lo mismo que frame-ancestors, para navegadores antiguos
    "Referrer-Policy": "strict-origin-when-cross-origin",  # a otras webs solo se les dice el dominio
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",  # la web no los necesita
}


@app.after_request
def cabeceras_de_seguridad(respuesta):
    """Flask llama a esta función con cada respuesta, justo antes de enviarla."""
    respuesta.headers.update(CABECERAS_DE_SEGURIDAD)
    # La página cambia según el idioma del navegador: así ninguna caché da la de un idioma a quien pidió otro
    respuesta.vary.add("Accept-Language")
    if "RENDER" in os.environ:
        # En Render la web va por HTTPS: el navegador recordará un año que solo debe usar HTTPS
        respuesta.headers["Strict-Transport-Security"] = "max-age=31536000"
    return respuesta


# ===== La página de cada partido =====

@app.template_global()
def enlace_partido(p):
    """La dirección de la página de un partido: /2026/partido/12"""
    return url_for("partido", numero=datos()["numero_de_partido"][mundial.clave_partido(p)])


@app.template_global()
def enlace_partido_de(p, anio):
    """Como enlace_partido(), pero de un partido de cualquier Mundial (en la página de una selección)."""
    return url_for("partido", anio=anio, numero=MUNDIALES[anio]["numero_de_partido"][mundial.clave_partido(p)])


app.jinja_env.globals["actual"] = mundial.actual  # "Alemania Federal" -> "Alemania"


@app.route("/<int:anio>/partido/<int:numero>")
def partido(numero):
    """Un partido con todo: resultado, goleadores y línea del tiempo, con una dirección para compartir.

    <int:numero> hace que Flask solo acepte números enteros (y positivos): /2026/partido/hola da un 404.
    """
    M = datos()
    partidos = M["todos_los_partidos"]
    if numero >= len(partidos):
        abort(404)  # no hay tantos partidos: Flask muestra la página 404
    p = partidos[numero]
    return render_template(
        "partido.html",
        p=p,
        estadio=next(e for e in M["estadios"] if e["nombre"] == p["estadio"]),
        pareja=mundial.pareja_de(partidos, p),  # el otro partido de un empate que se volvió a jugar
        anterior=numero - 1 if numero > 0 else None,
        siguiente=numero + 1 if numero < len(partidos) - 1 else None,
        m=M,
        portada=url_for("inicio"),  # para que el menú lleve a la portada, como en la 404
    )


# ===== Cara a cara entre dos selecciones =====

@app.route("/<int:anio>/cara-a-cara")
def cara_a_cara():
    """Dos selecciones lado a lado: /2026/cara-a-cara?a=España&b=Argentina. Por defecto, los finalistas."""
    M = datos()
    finalistas = M["finalistas"]
    a = request.args.get("a")
    b = request.args.get("b")
    # Si falta una (o no existe), una finalista que no sea la otra: así no sale la misma dos veces
    if a not in M["selecciones"]:
        a = next(f for f in finalistas if f != b)
    if b not in M["selecciones"]:
        b = next(f for f in finalistas if f != a)
    return render_template("cara_a_cara.html", m=M, c=mundial.cara_a_cara(M, a, b), portada=url_for("inicio"))


# ===== La página de inicio: todos los Mundiales =====

@app.route("/")
def raiz():
    """Los 23 Mundiales, los campeones, los máximos goleadores de la historia y una gráfica.

    Hasta el paso 58 aquí estaba el Mundial 2026, y lo que se elegía iba en la dirección
    (/?pais=México). Si llega una dirección así, de un enlace guardado, se lleva a /2026/.
    """
    if request.args:
        return redirect(url_for("inicio", anio=ULTIMO, **request.args), 301)
    return render_template("inicio.html", h=H, ultimo=ULTIMO)


# ===== Cada selección en todos los Mundiales =====

@app.route("/selecciones")
def selecciones():
    """Las 84 selecciones que han jugado algún Mundial, por orden alfabético."""
    # Por orden alfabético en el idioma elegido (Alemania va con la A en español y con la G en inglés: Germany)
    lista = sorted(HISTORIAL.values(), key=lambda h: mundial.normalizar(textos.nombre(h["nombre"], idioma_elegido())))
    return render_template("selecciones.html", lista=lista)


@app.route("/seleccion/<nombre>")
def seleccion(nombre):
    """Una selección en todos los Mundiales: /seleccion/Brasil. Con ?contra=Argentina, sus partidos contra otra."""
    if nombre in mundial.SUCESORAS:
        # Alemania Federal está dentro de la página de Alemania
        return redirect(url_for("seleccion", nombre=mundial.actual(nombre), **request.args), 301)
    if nombre not in HISTORIAL:
        abort(404)
    h = HISTORIAL[nombre]
    nombres = {nombre, *h["nombres"]}
    # Las selecciones contra las que ha jugado alguna vez (con su nombre de hoy)
    rivales = sorted({mundial.actual(p[lado]) for m in MUNDIALES.values() for p in m["todos_los_partidos"]
                      if nombres & {p["local"], p["visitante"]} for lado in ("local", "visitante")} - {nombre},
                     # Por orden alfabético en el idioma elegido. (Aquí "nombre" es el de la selección:
                     # el parámetro tapa a la función nombre(), por eso se usa textos.nombre)
                     key=lambda r: mundial.normalizar(textos.nombre(r, idioma_elegido())))
    contra = request.args.get("contra")
    entre = mundial.partidos_entre(MUNDIALES, nombre, contra) if contra in rivales else None
    return render_template("seleccion.html", h=h, rivales=rivales, contra=contra if entre else None, entre=entre,
                           balance=mundial.resumen_de_partidos(entre, nombres) if entre else None)


# ===== Direcciones de antes =====
# Hasta el paso 58 el Mundial 2026 estaba en la raíz: /partido/12, /cara-a-cara. Esas direcciones
# llevan ahora a las nuevas, con los mismos parámetros, para que no se rompa ningún enlace guardado.


@app.route("/partido/<int:numero>")
def partido_antes(numero):
    """301: redirección permanente. El navegador (y Google) recuerdan que la dirección cambió."""
    return redirect(url_for("partido", numero=numero), 301)


@app.route("/cara-a-cara")
def cara_a_cara_antes():
    return redirect(url_for("cara_a_cara", **request.args), 301)


@app.post("/quiz/<accion>")
def quiz_antes(accion):
    """308: como 301, pero el navegador vuelve a enviar el formulario (POST) a la nueva dirección.
    Sirve para una página abierta antes del cambio, que aún tenga los botones del quiz antiguos."""
    if accion not in ("responder", "siguiente", "reiniciar"):
        abort(404)
    return redirect(url_for(f"quiz_{accion}", **request.args), 308)


@app.route("/version")
def version():
    """El commit que está sirviendo la web (texto plano), o "desarrollo" en tu ordenador.

    Render guarda el commit desplegado en la variable de entorno RENDER_GIT_COMMIT. Así se puede
    comprobar que la web publicada es de verdad la última versión (en el paso 45 no lo era).
    """
    return Response(os.environ.get("RENDER_GIT_COMMIT", "desarrollo"), mimetype="text/plain")


@app.route("/fuentes")
def fuentes():
    """De dónde salen los datos (data/fuentes.md, tal cual)."""
    texto = (mundial.CARPETA_DATOS / "fuentes.md").read_text(encoding="utf-8")
    return Response(texto, mimetype="text/plain")


@app.errorhandler(404)
def pagina_no_encontrada(error):
    """Si se abre una dirección que no existe, Flask llama a esta función en vez de mostrar su página de error.

    Devuelve la página y también el código 404, para que el navegador (y Google) sepan que no existe.
    """
    return render_template("404.html", direccion=request.path, portada=url_for("inicio")), 404


@app.errorhandler(500)
def error_del_servidor(error):
    """Si el código de Python lanza una excepción, Flask la anota en el registro (los "Logs" de Render)
    y después llama a esta función. Con "flask run --debug" no se ve: sale el depurador de Flask.
    """
    return render_template("500.html", portada=url_for("inicio")), 500
