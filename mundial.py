"""La lógica de la web de los Mundiales, en Python puro (sin nada de Flask).

Lee los JSON de data/ y calcula todo lo que muestra la web: clasificaciones,
mejores terceros, el camino de cada selección, goleadores, líneas del tiempo...
Así se puede probar sin arrancar la web, y app.py solo se ocupa de las páginas.
"""

import json
import unicodedata
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parent / "data"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]
MINIMO_GOLES = 3  # en la vista corta de goleadores solo salen los que marcaron 3 o más
MARCAS = {"penalti": " (pen.)", "propia": " (p.p.)"}


# ===== Utilidades =====

def leer_json(nombre):
    with open(CARPETA_DATOS / nombre, encoding="utf-8") as archivo:
        return json.load(archivo)


def normalizar(texto):
    """Quita tildes y pasa a minúsculas: "México" -> "mexico"."""
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def formatear_fecha(fecha):
    """"2026-07-19" -> "19 jul"."""
    _, mes, dia = fecha.split("-")
    return f"{int(dia)} {MESES[int(mes) - 1]}"


def con_signo(numero):
    """3 -> "+3", 0 -> "0", -2 -> "-2"."""
    return f"+{numero}" if numero > 0 else str(numero)


def con_puntos(numero):
    """80824 -> "80.824", como se escriben los miles en español."""
    return f"{numero:,}".replace(",", ".")


def con_coma(numero):
    """2.9861 -> "2,99": dos decimales, con coma, como en español."""
    return f"{numero:.2f}".replace(".", ",")


def clave_partido(p):
    """Lo que identifica un partido (o el partido de un gol): fecha, local y visitante."""
    return p["fecha"], p["local"], p["visitante"]


def mismo_partido(gol, partido):
    return clave_partido(gol) == clave_partido(partido)


# ===== Partidos =====

# Las marcas de los partidos especiales de los Mundiales antiguos
NOTAS_PARTIDO = {
    "repetido": " (se volvió a jugar)",   # acabó en empate y se jugó otra vez (1934 y 1938)
    "repeticion": " (repetición)",        # el partido que se jugó otra vez
    "desempate": " (desempate)",          # dos empatados de un grupo jugaron otra vez (1954 y 1958)
}


def texto_partido(p):
    """"México 2-0 Sudáfrica", con "(pen. 4-3)" o "(prór.)" si hizo falta, y la marca de los
    partidos especiales: "Italia 1-1 España (prór.) (se volvió a jugar)"."""
    texto = f"{p['local']} {p['golesLocal']}-{p['golesVisitante']} {p['visitante']}"
    if p.get("penaltis"):
        texto += f" (pen. {p['penaltis'][0]}-{p['penaltis'][1]})"
    elif p.get("prorroga"):
        texto += " (prór.)"
    return texto + "".join(nota for clave, nota in NOTAS_PARTIDO.items() if p.get(clave))


def pareja_de(partidos, p):
    """El otro partido de un empate que se volvió a jugar: su repetición, o el empate del que es
    repetición. None si no es ninguno de los dos."""
    if p.get("repetido"):
        buscar = "repeticion"
    elif p.get("repeticion"):
        buscar = "repetido"
    else:
        return None
    return next(o for o in partidos if o.get(buscar) and {o["local"], o["visitante"]} == {p["local"], p["visitante"]})


def ganador_de(p):
    """El ganador sale de los goles y, si hubo empate, de los penaltis.
    Un partido que se volvió a jugar (1934 y 1938) no tuvo ganador: None."""
    if p.get("repetido"):
        return None
    if p.get("penaltis"):
        return p["local"] if p["penaltis"][0] > p["penaltis"][1] else p["visitante"]
    return p["local"] if p["golesLocal"] > p["golesVisitante"] else p["visitante"]


def juntar_partidos(datos_grupos, resultados):
    """Los 104 partidos en una sola lista, ordenados por fecha y con su ronda."""
    todos = []
    for g in datos_grupos["grupos"]:
        for p in g["partidos"]:
            todos.append({**p, "ronda": f"Grupo {g['grupo']}", "fase": "Fase de grupos", "eliminatoria": False})
    for r in resultados["rondas"]:
        for p in r["partidos"]:
            todos.append({**p, "ronda": r["ronda"], "eliminatoria": True})
    return sorted(todos, key=lambda p: p["fecha"])  # sorted no cambia el orden de los empates


# ===== Goles de un partido =====

def anotadores_de(goles, p, equipo):
    """Los goleadores de un equipo en un partido: "Kylian Mbappé 48', 66' · Harry Kane 30' (pen.)"."""
    por_jugador = {}  # los diccionarios guardan el orden en que se añaden
    for g in goles:
        if not mismo_partido(g, p):
            continue
        # un gol en propia puerta cuenta para el rival del jugador que lo marca
        a_favor = g["seleccion"] != equipo if g.get("tipo") == "propia" else g["seleccion"] == equipo
        if a_favor:
            por_jugador.setdefault(g["jugador"], []).append(f"{g['minuto']}'{MARCAS.get(g.get('tipo'), '')}")
    return " · ".join(f"{jugador} {', '.join(minutos)}" for jugador, minutos in por_jugador.items())


def leer_minuto(minuto):
    """"45+2" -> (45, 2), para ordenar los goles y colocarlos en la barra."""
    base, _, extra = minuto.partition("+")
    return int(base), int(extra or 0)


# Los tramos de la gráfica de goles por minuto: (nombre, primer minuto, último minuto).
# Los goles del tiempo añadido ("45+2", "90+5") cuentan en el tramo de su minuto base (45 o 90)
TRAMOS = [("1-15", 1, 15), ("16-30", 16, 30), ("31-45+", 31, 45), ("46-60", 46, 60),
          ("61-75", 61, 75), ("76-90+", 76, 90), ("91-120", 91, 120)]  # 91-120: la prórroga


def goles_por_tramo(goles):
    """Cuántos goles hubo en cada tramo de 15 minutos: [{"tramo": "1-15", "goles": 37}, ...]."""
    cuenta = {nombre: 0 for nombre, _, _ in TRAMOS}
    for g in goles:
        minuto = leer_minuto(g["minuto"])[0]
        nombre = next(n for n, primero, ultimo in TRAMOS if primero <= minuto <= ultimo)
        cuenta[nombre] += 1
    return [{"tramo": nombre, "goles": cuenta[nombre]} for nombre, _, _ in TRAMOS]


def goles_por_ronda(partidos):
    """Goles por partido en cada ronda, en el orden en que se jugaron:
    [{"ronda": "Fase de grupos", "partidos": 72, "goles": 215, "media": 2.986...}, ...]."""
    rondas = {}
    for p in partidos:
        nombre = p["ronda"] if p["eliminatoria"] else p["fase"]  # los grupos de una fase, juntos
        fila = rondas.setdefault(nombre, {"ronda": nombre, "partidos": 0, "goles": 0})
        fila["partidos"] += 1
        fila["goles"] += p["golesLocal"] + p["golesVisitante"]
    return [{**fila, "media": fila["goles"] / fila["partidos"]} for fila in rondas.values()]


def records(partidos):
    """Los récords del Mundial. Si dos partidos empatan en un récord, salen los dos."""
    def goles(p):
        return p["golesLocal"] + p["golesVisitante"]

    def diferencia(p):
        return abs(p["golesLocal"] - p["golesVisitante"])

    mayor_diferencia = max(diferencia(p) for p in partidos)
    mas_goles = max(goles(p) for p in partidos)
    return {
        "mayor_goleada": {"diferencia": mayor_diferencia,
                          "partidos": [p for p in partidos if diferencia(p) == mayor_diferencia]},
        "mas_goles": {"goles": mas_goles, "partidos": [p for p in partidos if goles(p) == mas_goles]},
        "penaltis": [p for p in partidos if p.get("penaltis")],
        # Los de penaltis también tuvieron prórroga: aquí solo los que se decidieron en ella
        "prorroga": [p for p in partidos if p.get("prorroga") and not p.get("penaltis")],
        "sin_goles": [p for p in partidos if goles(p) == 0],
    }


def linea_del_tiempo(goles, p):
    """Lo que necesita la plantilla para dibujar la línea del tiempo, o None si fue 0-0."""
    del_partido = [g for g in goles if mismo_partido(g, p)]
    if not del_partido:
        return None
    del_partido.sort(key=lambda g: leer_minuto(g["minuto"]))

    duracion = 120 if p.get("prorroga") else 90

    def posicion(minuto):
        return round(min(minuto, duracion) / duracion * 100, 2)

    filas, goles_local, goles_visitante = [], 0, 0
    for g in del_partido:
        para_local = g["seleccion"] != p["local"] if g.get("tipo") == "propia" else g["seleccion"] == p["local"]
        if para_local:
            goles_local += 1
        else:
            goles_visitante += 1
        filas.append({
            "minuto": g["minuto"],
            "jugador": g["jugador"] + MARCAS.get(g.get("tipo"), ""),
            "para_local": para_local,
            "posicion": posicion(leer_minuto(g["minuto"])[0]),
            "marcador": f"{goles_local}-{goles_visitante}",
        })

    # Rayas en el descanso y, si hubo prórroga, en el minuto 90
    cortes = [posicion(m) for m in ([45, 90] if duracion == 120 else [45])]
    return {"duracion": duracion, "cortes": cortes, "filas": filas}


# ===== Grupos =====

def calcular_clasificacion(letra, selecciones, partidos, juego_limpio):
    """La tabla no se guarda en el JSON: se calcula a partir de los resultados."""
    filas = {nombre: {"nombre": nombre, "grupo": letra, "pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0}
             for nombre in selecciones}

    for partido in partidos:
        local, visitante = filas[partido["local"]], filas[partido["visitante"]]
        local["pj"] += 1
        visitante["pj"] += 1
        local["gf"] += partido["golesLocal"]
        local["gc"] += partido["golesVisitante"]
        visitante["gf"] += partido["golesVisitante"]
        visitante["gc"] += partido["golesLocal"]

        if partido["golesLocal"] > partido["golesVisitante"]:
            local["g"] += 1
            visitante["p"] += 1
        elif partido["golesLocal"] < partido["golesVisitante"]:
            visitante["g"] += 1
            local["p"] += 1
        else:
            local["e"] += 1
            visitante["e"] += 1

    for f in filas.values():
        f["dg"] = f["gf"] - f["gc"]
        f["pts"] = 3 * f["g"] + f["e"]
    return ordenar_filas(filas.values(), juego_limpio)


def ordenar_filas(filas, juego_limpio):
    """Puntos, diferencia de goles, goles a favor y, si siguen empatados, juego limpio."""
    return sorted(filas, key=lambda f: (-f["pts"], -f["dg"], -f["gf"], -juego_limpio.get(f["nombre"], 0)))


def buscar_grupos(grupos, texto, traducir=lambda s: s):
    """Los grupos con alguna selección que contenga el texto (sin mirar tildes ni mayúsculas).
    traducir: el nombre en el idioma de la web, para encontrar también "Germany" o "Alemanha"."""
    busqueda = normalizar(texto.strip())
    return [g for g in grupos
            if any(busqueda in normalizar(s) or busqueda in normalizar(traducir(s)) for s in g["selecciones"])]


# ===== Camino de una selección =====

def hasta_donde_llego(seleccion, partidos, puesto_final=None):
    """Hasta dónde llegó, según su último partido. puesto_final: su puesto en la liguilla final
    (en 1950 no hubo final: el campeón fue el primero de una liguilla de cuatro)."""
    ultimo = partidos[-1]
    if not ultimo["eliminatoria"]:
        if ultimo["fase"] == "Liguilla final":
            return ["🏆 Campeona del mundo", "🥈 Subcampeona", "🥉 Tercer puesto", "Cuarto puesto"][puesto_final - 1]
        return f"Eliminada en la {ultimo['fase'].lower()}"  # "Eliminada en la segunda fase de grupos"

    gano = ganador_de(ultimo) == seleccion
    if ultimo["ronda"] == "Final":
        return "🏆 Campeona del mundo" if gano else "🥈 Subcampeona"
    if ultimo["ronda"] == "Tercer puesto":
        return "🥉 Tercer puesto" if gano else "Cuarto puesto"
    return f"Eliminada en {ultimo['ronda'].lower()}"  # "Eliminada en octavos de final"


def resultado_para(seleccion, p):
    """Desde el punto de vista de la selección: V (victoria), E (empate) o D (derrota)."""
    if p["eliminatoria"] and not p.get("repetido"):
        # En eliminatorias siempre hay ganador, aunque sea por penaltis (salvo si se volvió a jugar)
        return "V" if ganador_de(p) == seleccion else "D"
    a_favor, en_contra = ((p["golesLocal"], p["golesVisitante"]) if p["local"] == seleccion
                          else (p["golesVisitante"], p["golesLocal"]))
    if a_favor > en_contra:
        return "V"
    if a_favor < en_contra:
        return "D"
    return "E"


# ===== Goleadores =====

def puesto_de(goleadores, goles):
    """Puesto compartido en los empates: 10, 8, 7, 7, 6 -> 1, 2, 3, 3, 5."""
    return sum(1 for g in goleadores if g["goles"] > goles) + 1


def partidos_del_goleador(goles, todos_los_partidos, jugador, seleccion):
    """Los partidos en los que marcó un jugador, con los minutos de sus goles."""
    por_partido = {}
    for g in goles:
        if g["jugador"] != jugador or g["seleccion"] != seleccion or g.get("tipo") == "propia":
            continue
        clave = (g["fecha"], g["local"], g["visitante"])
        if clave not in por_partido:
            partido = next(p for p in todos_los_partidos if mismo_partido(g, p))
            por_partido[clave] = {"partido": partido, "minutos": []}
        marca = " (pen.)" if g.get("tipo") == "penalti" else ""
        por_partido[clave]["minutos"].append(f"{g['minuto']}'{marca}")
    return list(por_partido.values())


# ===== Todo junto =====

def contar_goleadores(goles):
    """Los goleadores de un Mundial a partir de sus goles, de más a menos goles (sin los de propia puerta)."""
    cuenta = {}
    for g in goles:
        if g.get("tipo") != "propia":
            clave = (g["jugador"], g["seleccion"])
            cuenta[clave] = cuenta.get(clave, 0) + 1
    filas = [{"jugador": j, "seleccion": s, "goles": n} for (j, s), n in cuenta.items()]
    return sorted(filas, key=lambda f: (-f["goles"], normalizar(f["jugador"])))


def completar(m):
    """Lo que se calcula igual en todos los Mundiales, a partir de sus partidos, grupos y goles."""
    partidos = m["todos_los_partidos"]
    m["partidos_por_estadio"] = {}
    for p in partidos:
        m["partidos_por_estadio"].setdefault(p["estadio"], []).append(p)

    # Los goles agrupados por partido, para no tener que recorrer todos cada vez que se pinta uno
    m["goles_por_partido"] = {}
    for g in m["goles"]:
        m["goles_por_partido"].setdefault(clave_partido(g), []).append(g)

    for i, g in enumerate(m["goleadores"]):
        g["puesto"] = puesto_de(m["goleadores"], g["goles"])
        g["clave"] = f"{g['jugador']}|{g['seleccion']}"
        g["ancla"] = f"goleador-{i}"  # para volver a su fila al abrir o cerrar su detalle

    # Los goles de los marcadores tienen que ser los de los jugadores más los marcados en propia puerta
    goles_partidos = sum(p["golesLocal"] + p["golesVisitante"] for p in partidos)
    if sum(g["goles"] for g in m["goleadores"]) + m["en_propia"] != goles_partidos:
        raise ValueError(f"{m['año']}: los goles de los goleadores no cuadran con los marcadores")

    # Salen de los partidos y no de los grupos: en 1934 y 1938 no hubo grupos, todo fue eliminatoria
    m["selecciones"] = sorted({p[lado] for p in partidos for lado in ("local", "visitante")}, key=normalizar)
    m["goles_por_tramo"] = goles_por_tramo(m["goles"])
    m["goles_por_ronda"] = goles_por_ronda(partidos)
    m["records"] = records(partidos)
    # Un número para cada partido (su puesto por fecha), para darle una dirección: /2026/partido/12
    m["numero_de_partido"] = {clave_partido(p): i for i, p in enumerate(partidos)}
    m["resumen_goles"] = {
        "goles": goles_partidos,
        "partidos": len(partidos),
        "media": con_coma(goles_partidos / len(partidos)),
        "en_propia": m["en_propia"],
    }
    # Las dos selecciones de la final (o, en 1950, las dos primeras de la liguilla final): el cara a cara
    # las compara si no se elige otra
    if m["rondas"] and m["rondas"][-1]["ronda"] == "Final":
        final = m["rondas"][-1]["partidos"][-1]
        m["finalistas"] = [final["local"], final["visitante"]]
    else:
        m["finalistas"] = [f["nombre"] for f in m["clasificaciones"][m["grupos"][-1]["grupo"]][:2]]
    return m


def cargar():
    """El Mundial 2026: lee sus JSON y calcula todo lo que no depende de lo que elija quien visita la web."""
    grupos = leer_json("grupos.json")
    datos_grupos = leer_json("partidos-grupos.json")
    resultados = leer_json("resultados.json")
    datos_goleadores = leer_json("goleadores.json")

    juego_limpio = datos_grupos["juegoLimpio"]
    partidos_por_grupo = {g["grupo"]: g["partidos"] for g in datos_grupos["grupos"]}
    clasificaciones = {g["grupo"]: calcular_clasificacion(g["grupo"], g["selecciones"],
                                                         partidos_por_grupo[g["grupo"]], juego_limpio)
                       for g in grupos}
    terceros = ordenar_filas([filas[2] for filas in clasificaciones.values()], juego_limpio)
    clasificadas = {f["nombre"] for filas in clasificaciones.values() for f in filas[:2]}
    clasificadas |= {f["nombre"] for f in terceros[:8]}
    for filas in clasificaciones.values():
        for f in filas:
            f["pasa"] = f["nombre"] in clasificadas  # la barra verde de la tabla

    return completar({
        "año": 2026,
        "estadios": leer_json("estadios.json"),
        "paises": ["Estados Unidos", "México", "Canadá"],
        "grupos": [{**g, "nombre": f"Grupo {g['grupo']}"} for g in grupos],
        "clasificaciones": clasificaciones,
        "terceros": terceros,
        "clasificadas": clasificadas,
        "partidos_por_grupo": partidos_por_grupo,
        "todos_los_partidos": juntar_partidos(datos_grupos, resultados),
        "rondas": resultados["rondas"],
        "campeon": resultados["campeon"],
        "goleadores": datos_goleadores["goleadores"],
        "en_propia": sum(g["goles"] for g in datos_goleadores["enPropiaPuerta"]),
        "goles": leer_json("goles.json"),
        "preguntas": leer_json("quiz.json"),
    })


def cargar_historico(año):
    """Un Mundial de 1930 a 2022 (data/historicos/), con la misma forma que el de 2026.

    Las clasificaciones vienen ya hechas en el JSON (con los puntos de su época), y los grupos
    pueden ser de dos fases: la segunda fase de grupos (1974-1982) o la liguilla final (1950).
    """
    h = leer_json(f"historicos/{año}.json")
    grupos, clasificaciones, partidos_por_grupo, todos = [], {}, {}, []
    for g in h["grupos"]:
        if g["fase"] == "Liguilla final":
            clave, nombre = "final", "Liguilla final"
        elif g["fase"] == "Segunda fase de grupos":
            clave, nombre = g["grupo"], f"Grupo {g['grupo']} (segunda fase)"
        else:
            clave, nombre = g["grupo"], f"Grupo {g['grupo']}"
        filas = [{**f, "grupo": clave, "pts": f["puntos"], "dg": f["gf"] - f["gc"]} for f in g["clasificacion"]]
        partidos = [{**p, "ronda": nombre, "fase": g["fase"], "eliminatoria": False} for p in g["partidos"]]
        grupos.append({"grupo": clave, "nombre": nombre, "selecciones": [f["nombre"] for f in filas]})
        clasificaciones[clave] = filas
        partidos_por_grupo[clave] = partidos
        todos += partidos
    rondas = [{"ronda": r["ronda"], "partidos": [{**p, "ronda": r["ronda"], "eliminatoria": True} for p in r["partidos"]]}
              for r in h["rondas"]]
    todos += [p for r in rondas for p in r["partidos"]]

    return completar({
        "año": año,
        "estadios": h["estadios"],
        "paises": h["sedes"],
        "grupos": grupos,
        "clasificaciones": clasificaciones,
        "terceros": [],
        "partidos_por_grupo": partidos_por_grupo,
        "todos_los_partidos": sorted(todos, key=lambda p: p["fecha"]),
        "rondas": rondas,
        "campeon": h["campeon"],
        "goleadores": contar_goleadores(h["goles"]),
        "en_propia": sum(1 for g in h["goles"] if g.get("tipo") == "propia"),
        "goles": h["goles"],
        "preguntas": [],
    })


# ===== Todos los Mundiales (la página de inicio) =====

# Selecciones que hoy juegan con otro nombre. Como hace la FIFA, la de ahora hereda el historial
# de la anterior: por ejemplo, los títulos de Alemania Federal (1954, 1974 y 1990) cuentan para Alemania
SUCESORAS = {
    "Alemania Federal": "Alemania",
    "Unión Soviética": "Rusia",
    "Yugoslavia": "Serbia",
    "Serbia y Montenegro": "Serbia",
    "Checoslovaquia": "Chequia",
    "República Checa": "Chequia",
    "Zaire": "RD del Congo",
    "Indias Orientales Neerlandesas": "Indonesia",
}


def actual(nombre):
    """El nombre de hoy de una selección: "Alemania Federal" -> "Alemania", "Brasil" -> "Brasil"."""
    return SUCESORAS.get(nombre, nombre)
# El mismo jugador, escrito de dos formas: con tilde en la base de Fjelstul y sin ella en los datos de 2026
MISMO_JUGADOR = {"Julián Alvarez": "Julián Álvarez"}


def resumen_de(año, sedes, campeon, partidos):
    """Una fila de la lista de Mundiales: año, sedes, campeón, partidos, goles y media."""
    goles = sum(p["golesLocal"] + p["golesVisitante"] for p in partidos)
    return {"año": año, "sedes": sedes, "campeon": campeon, "partidos": len(partidos),
            "goles": goles, "media": goles / len(partidos)}


def titulos_por_pais(mundiales):
    """[{"nombre": "Brasil", "titulos": 5, "años": [1958, ...]}, ...], de más a menos títulos."""
    años = {}
    for m in mundiales:
        años.setdefault(actual(m["campeon"]), []).append(m["año"])
    filas = [{"nombre": n, "titulos": len(a), "años": a} for n, a in años.items()]
    return sorted(filas, key=lambda f: (-f["titulos"], normalizar(f["nombre"])))


def goleadores_historicos(goles_por_año, cuantos=10):
    """Los máximos goleadores de todos los Mundiales (sin los goles en propia puerta), con los años
    en que marcaron. Salen los `cuantos` primeros y los que empatan con el último."""
    filas = {}
    for año, goles in goles_por_año.items():
        for g in goles:
            if g.get("tipo") == "propia":
                continue
            jugador = MISMO_JUGADOR.get(g["jugador"], g["jugador"])
            fila = filas.setdefault((jugador, g["seleccion"]), {"jugador": jugador, "seleccion": g["seleccion"],
                                                                 "goles": 0, "años": []})
            fila["goles"] += 1
            if año not in fila["años"]:
                fila["años"].append(año)
    todos = sorted(filas.values(), key=lambda f: (-f["goles"], normalizar(f["jugador"])))
    minimo = todos[min(cuantos, len(todos)) - 1]["goles"]  # si hay menos de `cuantos`, salen todos
    elegidos = [f for f in todos if f["goles"] >= minimo]
    for f in elegidos:
        f["puesto"] = puesto_de(elegidos, f["goles"])
        f["años"].sort()
    return elegidos


def años_historicos():
    """Los años de data/historicos/: [1930, 1934, ..., 2022]."""
    return sorted(int(a.stem) for a in (CARPETA_DATOS / "historicos").glob("*.json"))


def cargar_todos():
    """Todos los Mundiales, por año: {1930: {...}, ..., 2026: {...}}."""
    return {año: cargar_historico(año) for año in años_historicos()} | {2026: cargar()}


def cargar_historia(mundiales):
    """Lo que muestra la página de inicio, a partir de todos los Mundiales ({año: mundial})."""
    filas = [resumen_de(año, m["paises"], m["campeon"], m["todos_los_partidos"]) for año, m in sorted(mundiales.items())]
    return {
        "mundiales": filas,
        "partidos": sum(f["partidos"] for f in filas),
        "goles": sum(f["goles"] for f in filas),
        "titulos": titulos_por_pais(filas),
        "goleadores": goleadores_historicos({año: m["goles"] for año, m in mundiales.items()}),
    }


# ===== Cada selección en todos los Mundiales =====

# De mejor a peor: para saber cuál fue su mejor Mundial. En 1930 no hubo tercer puesto,
# y las dos eliminadas en semifinales quedan entre el tercero y el cuarto
NIVELES = ["🏆 Campeona del mundo", "🥈 Subcampeona", "🥉 Tercer puesto", "Eliminada en semifinales",
           "Cuarto puesto", "Eliminada en la segunda fase de grupos", "Eliminada en cuartos de final",
           "Eliminada en octavos de final", "Eliminada en dieciseisavos de final", "Eliminada en la fase de grupos"]


def resumen_de_partidos(partidos, nombres):
    """Ganados, empatados, perdidos y goles de una selección (con cualquiera de sus nombres)."""
    fila = {"partidos": len(partidos), "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0}
    for p in partidos:
        nombre = p["local"] if p["local"] in nombres else p["visitante"]
        fila[{"V": "g", "E": "e", "D": "p"}[resultado_para(nombre, p)]] += 1
        fila["gf"] += p["golesLocal"] if p["local"] == nombre else p["golesVisitante"]
        fila["gc"] += p["golesVisitante"] if p["local"] == nombre else p["golesLocal"]
    return fila


def historial(mundiales):
    """Cada selección (con su nombre de hoy) en todos los Mundiales: {"Brasil": {...}, ...}."""
    selecciones = {}
    for año, m in sorted(mundiales.items()):
        for nombre in m["selecciones"]:
            c = camino(m, nombre)
            h = selecciones.setdefault(actual(nombre), {"nombre": actual(nombre), "participaciones": [], "goles": {}})
            h["participaciones"].append({"año": año, "como": nombre, "hasta_donde": c["hasta_donde"],
                                         **resumen_de_partidos(c["partidos"], {nombre})})
        for g in m["goles"]:
            if g.get("tipo") != "propia":
                selecciones[actual(g["seleccion"])]["goles"].setdefault(año, []).append(g)

    for h in selecciones.values():
        ps = h["participaciones"]
        h["titulos"] = [p["año"] for p in ps if p["hasta_donde"] == "🏆 Campeona del mundo"]
        h["mejor"] = min((p["hasta_donde"] for p in ps), key=NIVELES.index)
        h["nombres"] = sorted({p["como"] for p in ps} - {h["nombre"]})   # los otros nombres con los que jugó
        for clave in ("partidos", "g", "e", "p", "gf", "gc"):
            h[clave] = sum(p[clave] for p in ps)
        # Sus máximos goleadores de todos los Mundiales (los 5 primeros y los empatados con el quinto)
        goles = h.pop("goles")
        h["goleadores"] = goleadores_historicos(goles, cuantos=5) if goles else []
    return selecciones


def partidos_entre(mundiales, a, b):
    """Todos los partidos entre dos selecciones (con sus nombres de hoy) en todos los Mundiales,
    cada uno con su año, del más antiguo al más reciente."""
    return [{**p, "año": año} for año, m in sorted(mundiales.items()) for p in m["todos_los_partidos"]
            if {actual(p["local"]), actual(p["visitante"])} == {a, b}]


def camino(mundial, seleccion):
    """Todo lo que muestra la sección "El camino de una selección"."""
    partidos = [p for p in mundial["todos_los_partidos"] if seleccion in (p["local"], p["visitante"])]
    def puesto_en(grupo):
        return [f["nombre"] for f in mundial["clasificaciones"][grupo["grupo"]]].index(seleccion) + 1

    # Su grupo de la primera fase y el último que jugó (la liguilla final de 1950). En 1934 y 1938
    # no hubo grupos: entonces no tiene ninguno (None)
    sus_grupos = [g for g in mundial["grupos"] if seleccion in g["selecciones"]]
    grupo = sus_grupos[0] if sus_grupos else None
    return {
        "seleccion": seleccion,
        "grupo": grupo["grupo"] if grupo else None,
        "nombre_grupo": grupo["nombre"] if grupo else None,
        "puesto": puesto_en(grupo) if grupo else None,
        "hasta_donde": hasta_donde_llego(seleccion, partidos, puesto_en(sus_grupos[-1]) if grupo else None),
        "goleadores": [g for g in mundial["goleadores"] if g["seleccion"] == seleccion],
        "partidos": [{**p, "resultado": resultado_para(seleccion, p)} for p in partidos],
    }


# ===== Cara a cara =====

def numeros_de(mundial, seleccion):
    """Los números de una selección en el Mundial, para compararla con otra."""
    c = camino(mundial, seleccion)
    partidos = c["partidos"]
    goles_a_favor = sum(p["golesLocal"] if p["local"] == seleccion else p["golesVisitante"] for p in partidos)
    goles_en_contra = sum(p["golesVisitante"] if p["local"] == seleccion else p["golesLocal"] for p in partidos)
    # Sus máximos goleadores: puede haber empate (varios con los mismos goles)
    mas_goles = c["goleadores"][0]["goles"] if c["goleadores"] else 0
    return {
        "seleccion": seleccion,
        "hasta_donde": c["hasta_donde"],
        "grupo": c["grupo"],
        "nombre_grupo": c["nombre_grupo"],
        "puesto": c["puesto"],
        "partidos": len(partidos),
        "ganados": sum(p["resultado"] == "V" for p in partidos),
        "empatados": sum(p["resultado"] == "E" for p in partidos),
        "perdidos": sum(p["resultado"] == "D" for p in partidos),
        "goles_a_favor": goles_a_favor,
        "goles_en_contra": goles_en_contra,
        "maximos_goleadores": [g["jugador"] for g in c["goleadores"] if g["goles"] == mas_goles] if mas_goles else [],
        "goles_del_maximo": mas_goles,
    }


def cara_a_cara(mundial, a, b):
    """Los números de dos selecciones, y los partidos que jugaron entre ellas."""
    return {
        "a": numeros_de(mundial, a),
        "b": numeros_de(mundial, b),
        "entre_ellas": [p for p in mundial["todos_los_partidos"] if {p["local"], p["visitante"]} == {a, b}],
    }
