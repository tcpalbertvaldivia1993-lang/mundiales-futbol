"""Descarga los Mundiales de 1930 a 2022 de la base de datos de Joshua C. Fjelstul y los guarda
en español, un archivo por Mundial: data/historicos/1930.json, data/historicos/1934.json...

La web no ejecuta este script: solo lee los JSON que deja. Hay que volver a ejecutarlo
únicamente si cambian las traducciones o la versión de la base de datos:

    venv/bin/python herramientas/importar_historicos.py

Fuente: The Fjelstul World Cup Database v1.2.0, © 2023 Joshua C. Fjelstul, Ph.D.,
https://www.github.com/jfjelstul/worldcup, con licencia CC BY-SA 4.0
(https://creativecommons.org/licenses/by-sa/4.0/legalcode). Los cambios que hacemos
están en data/fuentes.md.
"""

import csv
import io
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

# Un commit concreto de la base de datos: así siempre se descargan los mismos datos
COMMIT = "35a8667f518b07469182ae16d35574dd0e7a00fb"
URL = f"https://raw.githubusercontent.com/jfjelstul/worldcup/{COMMIT}/data-csv/{{}}.csv"

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "historicos"
TRADUCCIONES = json.loads((Path(__file__).parent / "traducciones.json").read_text(encoding="utf-8"))


def descargar(tabla):
    """Una tabla de la base de datos (matches, goals...) como lista de diccionarios.
    Solo los Mundiales masculinos: la base también tiene los femeninos."""
    with urllib.request.urlopen(URL.format(tabla), timeout=60) as respuesta:
        texto = respuesta.read().decode("utf-8")
    return [fila for fila in csv.DictReader(io.StringIO(texto)) if "Men's" in fila["tournament_name"]]


def traducir(tipo, nombre):
    """Las selecciones y las rondas tienen que estar todas en traducciones.json: si falta una,
    el script se para en vez de dejar un nombre en inglés. Las ciudades que no están se dejan
    igual (São Paulo, Guadalajara...)."""
    if tipo == "ciudades":
        return TRADUCCIONES["ciudades"].get(nombre, nombre)
    if nombre not in TRADUCCIONES[tipo]:
        raise KeyError(f"Falta la traducción de «{nombre}» en traducciones.json ({tipo})")
    return TRADUCCIONES[tipo][nombre]


def nombre_del_grupo(grupo):
    """"Group A" -> "A", "Group 1" -> "1". La liguilla final de 1950 no tiene nombre: ""."""
    return "" if grupo == "not applicable" else grupo.removeprefix("Group ")


def convertir_partido(p):
    """Un partido con la misma forma que los de 2026, más las marcas propias de los antiguos."""
    partido = {
        "fecha": p["match_date"],
        "estadio": p["stadium_name"],
        "local": traducir("selecciones", p["home_team_name"]),
        "golesLocal": int(p["home_team_score"]),
        "visitante": traducir("selecciones", p["away_team_name"]),
        "golesVisitante": int(p["away_team_score"]),
    }
    if p["extra_time"] == "1":
        partido["prorroga"] = True
    if p["penalty_shootout"] == "1":
        partido["penaltis"] = [int(p["home_team_score_penalties"]), int(p["away_team_score_penalties"])]
    if p["replayed"] == "1":
        partido["repetido"] = True     # acabó en empate y se volvió a jugar otro día
    if p["replay"] == "1":
        partido["repeticion"] = True   # es el partido que se volvió a jugar
    return partido


def convertir_gol(g, partidos_por_id):
    """Un gol con la misma forma que los de goles.json de 2026."""
    p = partidos_por_id[g["match_id"]]
    minuto = g["minute_regulation"]
    if g["minute_stoppage"] != "0":
        minuto += "+" + g["minute_stoppage"]   # "45+2": tiempo añadido
    # Los jugadores conocidos por un solo nombre (Pelé) no tienen nombre de pila en la base
    jugador = g["family_name"] if g["given_name"] == "not applicable" else f"{g['given_name']} {g['family_name']}"
    gol = {
        "fecha": p["match_date"],
        "local": traducir("selecciones", p["home_team_name"]),
        "visitante": traducir("selecciones", p["away_team_name"]),
        "jugador": jugador,
        "seleccion": traducir("selecciones", g["player_team_name"]),  # la del jugador, también en propia puerta
        "minuto": minuto,
    }
    if g["own_goal"] == "1":
        gol["tipo"] = "propia"
    elif g["penalty"] == "1":
        gol["tipo"] = "penalti"
    return gol


def convertir_mundial(torneo, etapas, partidos, clasificaciones, goles, estadios):
    """Todo lo de un Mundial en un diccionario, listo para guardarlo en su JSON."""
    numero_de_etapa = {e["stage_name"]: e["stage_number"] for e in etapas}
    partidos = sorted(partidos, key=lambda p: (p["match_date"], p["match_time"]))
    partidos_por_id = {p["match_id"]: p for p in partidos}

    # Las fases de grupos (puede haber dos) y, dentro de cada una, sus grupos
    fases = {}
    rondas = {}
    for p in partidos:
        ronda = traducir("rondas", p["stage_name"])
        if p["group_stage"] == "1":
            fase = fases.setdefault(ronda, {"fase": ronda, "numero": numero_de_etapa[p["stage_name"]], "grupos": {}})
            grupo = fase["grupos"].setdefault(nombre_del_grupo(p["group_name"]), [])
            grupo.append(convertir_partido(p))
        else:
            rondas.setdefault(ronda, []).append(convertir_partido(p))

    # Las clasificaciones son las de la base de datos, con los puntos y desempates de cada época
    # (hasta 1990, ganar daba 2 puntos). Se buscan por el número de etapa, porque el nombre no
    # siempre coincide con el de los partidos ("first round" frente a "group stage").
    tablas = defaultdict(list)
    for c in sorted(clasificaciones, key=lambda c: int(c["position"])):
        tablas[(c["stage_number"], nombre_del_grupo(c["group_name"]))].append({
            "nombre": traducir("selecciones", c["team_name"]),
            "pj": int(c["played"]), "g": int(c["wins"]), "e": int(c["draws"]), "p": int(c["losses"]),
            "gf": int(c["goals_for"]), "gc": int(c["goals_against"]), "puntos": int(c["points"]),
            "pasa": c["advanced"] == "1",
        })

    # Cada grupo se une a su clasificación por las selecciones que lo jugaron, no por el nombre:
    # en la base, la liguilla de 1950 no tiene nombre en los partidos, y la segunda fase de 1982
    # se llama "1, 2, 3, 4" en los partidos y "A, B, C, D" (como fue) en las clasificaciones.
    grupos = []
    for fase in fases.values():
        for partidos_del_grupo in fase["grupos"].values():
            equipos = {p[lado] for p in partidos_del_grupo for lado in ("local", "visitante")}
            (letra,) = [letra for (numero, letra), tabla in tablas.items()
                        if numero == fase["numero"] and {f["nombre"] for f in tabla} == equipos]
            # En 1954 y 1958, dos selecciones empatadas en el grupo jugaban otra vez entre ellas: ese
            # desempate es el segundo partido entre las mismas y no cuenta en la clasificación
            vistos = set()
            for p in partidos_del_grupo:
                pareja = frozenset((p["local"], p["visitante"]))
                if pareja in vistos:
                    p["desempate"] = True
                vistos.add(pareja)
            grupos.append({"fase": fase["fase"], "grupo": letra, "clasificacion": tablas[(fase["numero"], letra)],
                           "partidos": partidos_del_grupo})
    grupos.sort(key=lambda g: (fases[g["fase"]]["numero"], g["grupo"]))  # 1982: A, B, C, D

    usados = {p["stadium_id"] for p in partidos}
    return {
        "año": int(torneo["year"]),
        # 2002 tuvo dos sedes, y la base llama "Korea" a Corea del Sur
        "sedes": [traducir("selecciones", "South Korea" if s == "Korea" else s) for s in torneo["host_country"].split(", ")],
        "campeon": traducir("selecciones", torneo["winner"]),
        "inicio": torneo["start_date"],
        "fin": torneo["end_date"],
        "selecciones": int(torneo["count_teams"]),
        "estadios": [{"nombre": e["stadium_name"], "ciudad": traducir("ciudades", e["city_name"]),
                      "pais": traducir("selecciones", e["country_name"]), "capacidad": int(e["stadium_capacity"])}
                     for e in estadios if e["stadium_id"] in usados],
        "grupos": grupos,
        "rondas": [{"ronda": r, "partidos": ps} for r, ps in rondas.items()],
        "goles": [convertir_gol(g, partidos_por_id) for g in goles],
    }


def main():
    print("Descargando la base de datos de Fjelstul...")
    torneos = descargar("tournaments")
    etapas, partidos, clasificaciones, goles = (descargar(t) for t in
                                                ("tournament_stages", "matches", "group_standings", "goals"))
    with urllib.request.urlopen(URL.format("stadiums"), timeout=60) as respuesta:
        estadios = list(csv.DictReader(io.StringIO(respuesta.read().decode("utf-8"))))

    def de(filas, torneo):
        return [f for f in filas if f["tournament_id"] == torneo["tournament_id"]]

    SALIDA.mkdir(parents=True, exist_ok=True)
    for t in torneos:
        mundial = convertir_mundial(t, de(etapas, t), de(partidos, t), de(clasificaciones, t), de(goles, t), estadios)
        archivo = SALIDA / f"{mundial['año']}.json"
        archivo.write_text(json.dumps(mundial, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        partidos_jugados = sum(len(g["partidos"]) for g in mundial["grupos"]) + sum(len(r["partidos"]) for r in mundial["rondas"])
        print(f"  {archivo.relative_to(RAIZ)}: {partidos_jugados} partidos, {len(mundial['goles'])} goles")


if __name__ == "__main__":
    main()
