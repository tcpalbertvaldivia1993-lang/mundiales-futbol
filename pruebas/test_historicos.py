"""Pruebas de los Mundiales de 1930 a 2022 (data/historicos/), que crea herramientas/importar_historicos.py
con la base de datos de Fjelstul. Comprueban los datos con cifras conocidas y que cada parte cuadra con las demás."""

import json
from collections import Counter
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent.parent / "data" / "historicos"
TRADUCCIONES = json.loads((CARPETA.parent.parent / "herramientas" / "traducciones.json").read_text(encoding="utf-8"))

# Cifras conocidas de cada Mundial, apuntadas antes de importar los datos: partidos, goles y campeón.
# Cuentan los partidos que se volvieron a jugar (1934 y 1938) y no el que no se jugó (Austria, 1938).
CONOCIDOS = {
    1930: (18, 70, "Uruguay"), 1934: (17, 70, "Italia"), 1938: (18, 84, "Italia"),
    1950: (22, 88, "Uruguay"), 1954: (26, 140, "Alemania Federal"), 1958: (35, 126, "Brasil"),
    1962: (32, 89, "Brasil"), 1966: (32, 89, "Inglaterra"), 1970: (32, 95, "Brasil"),
    1974: (38, 97, "Alemania Federal"), 1978: (38, 102, "Argentina"), 1982: (52, 146, "Italia"),
    1986: (52, 132, "Argentina"), 1990: (52, 115, "Alemania Federal"), 1994: (52, 141, "Brasil"),
    1998: (64, 171, "Francia"), 2002: (64, 161, "Brasil"), 2006: (64, 147, "Italia"),
    2010: (64, 145, "España"), 2014: (64, 171, "Alemania"), 2018: (64, 169, "Francia"),
    2022: (64, 172, "Argentina"),
}


def leer(año):
    return json.loads((CARPETA / f"{año}.json").read_text(encoding="utf-8"))


def partidos_de(mundial):
    return [p for g in mundial["grupos"] for p in g["partidos"]] + [p for r in mundial["rondas"] for p in r["partidos"]]


@pytest.fixture(scope="module", params=sorted(CONOCIDOS))
def mundial(request):
    """Cada prueba que lo usa se ejecuta una vez por Mundial."""
    return leer(request.param)


def test_estan_los_22_mundiales_de_1930_a_2022():
    # Entre 1938 y 1950 no hubo Mundial, por la Segunda Guerra Mundial
    assert sorted(int(a.stem) for a in CARPETA.glob("*.json")) == sorted(CONOCIDOS)


def test_partidos_goles_y_campeon_conocidos(mundial):
    partidos, goles, campeon = CONOCIDOS[mundial["año"]]
    assert len(partidos_de(mundial)) == partidos
    assert sum(p["golesLocal"] + p["golesVisitante"] for p in partidos_de(mundial)) == goles
    assert mundial["campeon"] == campeon


def test_los_goles_de_cada_partido_cuadran_con_el_marcador(mundial):
    goles = Counter((g["fecha"], g["local"], g["visitante"]) for g in mundial["goles"])
    for p in partidos_de(mundial):
        assert goles[(p["fecha"], p["local"], p["visitante"])] == p["golesLocal"] + p["golesVisitante"], p


def test_la_clasificacion_de_cada_grupo_cuadra_con_sus_partidos(mundial):
    for g in mundial["grupos"]:
        partidos = [p for p in g["partidos"] if not p.get("desempate")]  # el desempate no cuenta en la tabla
        jugados = Counter(p[lado] for p in partidos for lado in ("local", "visitante"))
        assert {f["nombre"]: f["pj"] for f in g["clasificacion"]} == dict(jugados), (g["fase"], g["grupo"])
        for f in g["clasificacion"]:
            assert f["g"] + f["e"] + f["p"] == f["pj"]
        # Los goles a favor de todos son los goles que se marcaron en el grupo
        assert sum(f["gf"] for f in g["clasificacion"]) == sum(p["golesLocal"] + p["golesVisitante"] for p in partidos)


def test_los_desempates_de_1954_y_1958():
    desempates = {año: [f"{p['local']}-{p['visitante']}" for g in leer(año)["grupos"] for p in g["partidos"] if p.get("desempate")]
                  for año in CONOCIDOS}
    assert {año: d for año, d in desempates.items() if d} == {
        1954: ["Alemania Federal-Turquía", "Suiza-Italia"],
        1958: ["Irlanda del Norte-Checoslovaquia", "Gales-Hungría", "Unión Soviética-Inglaterra"],
    }


def test_cada_repeticion_viene_despues_de_un_empate(mundial):
    partidos = partidos_de(mundial)
    for r in [p for p in partidos if p.get("repeticion")]:
        (empate,) = [p for p in partidos if p.get("repetido") and {p["local"], p["visitante"]} == {r["local"], r["visitante"]}]
        assert empate["golesLocal"] == empate["golesVisitante"] and empate["fecha"] < r["fecha"]


def test_los_partidos_de_cada_ronda_van_por_fecha(mundial):
    for r in mundial["rondas"]:
        fechas = [p["fecha"] for p in r["partidos"]]
        assert fechas == sorted(fechas), r["ronda"]


def test_todo_esta_en_espanol(mundial):
    """Ninguna selección ni ronda se ha quedado en inglés."""
    selecciones = set(TRADUCCIONES["selecciones"].values())
    rondas = set(TRADUCCIONES["rondas"].values())
    assert set(mundial["sedes"]) | {mundial["campeon"]} <= selecciones
    for p in partidos_de(mundial):
        assert {p["local"], p["visitante"]} <= selecciones
    assert {g["seleccion"] for g in mundial["goles"]} <= selecciones
    assert {g["fase"] for g in mundial["grupos"]} | {r["ronda"] for r in mundial["rondas"]} <= rondas
    assert {e["pais"] for e in mundial["estadios"]} <= selecciones


def test_casos_especiales():
    # 1950 no tuvo final: Uruguay ganó la liguilla final por delante de Brasil
    m = leer(1950)
    (liguilla,) = [g for g in m["grupos"] if g["fase"] == "Liguilla final"]
    assert [f["nombre"] for f in liguilla["clasificacion"]][:2] == ["Uruguay", "Brasil"]
    assert "Final" not in [r["ronda"] for r in m["rondas"]]
    # 1982: la segunda fase de grupos se llamó A, B, C y D
    assert [g["grupo"] for g in leer(1982)["grupos"] if g["fase"] == "Segunda fase de grupos"] == ["A", "B", "C", "D"]
    # 2002 tuvo dos sedes
    assert leer(2002)["sedes"] == ["Corea del Sur", "Japón"]
    # Hasta 1990, ganar daba 2 puntos: Argentina ganó sus 3 partidos de 1930 y sumó 6
    (argentina,) = [f for g in leer(1930)["grupos"] for f in g["clasificacion"] if f["nombre"] == "Argentina"]
    assert (argentina["g"], argentina["puntos"]) == (3, 6)
    # Los jugadores con un solo nombre: Pelé, y no "not applicable Pelé"
    assert any(g["jugador"] == "Pelé" for g in leer(1970)["goles"])
