"""Pruebas de la lógica de mundial.py, sin navegador ni Flask.

Ejecutarlas, desde la carpeta del proyecto:
    venv/bin/python -m pytest
pytest busca las funciones que empiezan por test_ y comprueba cada assert.
"""

import pytest

import mundial


@pytest.fixture(scope="module")
def m():
    """Los datos del Mundial, cargados una sola vez para todas las pruebas de este archivo."""
    return mundial.cargar()


def partido(local, goles_local, visitante, goles_visitante, **extra):
    """Un partido inventado para las pruebas, con la misma forma que los de los JSON."""
    return {"fecha": "2026-06-11", "local": local, "golesLocal": goles_local,
            "visitante": visitante, "golesVisitante": goles_visitante, **extra}


# ===== Utilidades =====

def test_normalizar_quita_tildes_y_mayusculas():
    assert mundial.normalizar("México") == "mexico"
    assert mundial.normalizar("Haití") == "haiti"
    assert mundial.normalizar("ESPAÑA") == "espana"


def test_formatear_fecha():
    assert mundial.formatear_fecha("2026-07-19") == "19 jul"
    assert mundial.formatear_fecha("2026-06-01") == "1 jun"


# parametrize: la misma prueba con varios datos, cada uno cuenta como una prueba aparte
@pytest.mark.parametrize("numero, texto", [(3, "+3"), (0, "0"), (-2, "-2")])
def test_con_signo(numero, texto):
    assert mundial.con_signo(numero) == texto


def test_con_puntos_separa_los_miles():
    assert mundial.con_puntos(80824) == "80.824"
    assert mundial.con_puntos(500) == "500"


@pytest.mark.parametrize("minuto, resultado", [("9", (9, 0)), ("45+2", (45, 2)), ("90+8", (90, 8)), ("106", (106, 0))])
def test_leer_minuto(minuto, resultado):
    assert mundial.leer_minuto(minuto) == resultado


def test_los_minutos_del_descuento_van_antes_que_el_minuto_siguiente():
    minutos = ["46", "45+1", "45", "90+8", "90+6"]
    assert sorted(minutos, key=mundial.leer_minuto) == ["45", "45+1", "46", "90+6", "90+8"]


# ===== Partidos =====

def test_texto_partido():
    assert mundial.texto_partido(partido("México", 2, "Sudáfrica", 0)) == "México 2-0 Sudáfrica"
    assert mundial.texto_partido(partido("A", 1, "B", 0, prorroga=True)) == "A 1-0 B (prór.)"
    assert mundial.texto_partido(partido("A", 0, "B", 0, prorroga=True, penaltis=[4, 3])) == "A 0-0 B (pen. 4-3)"
    assert mundial.texto_partido(partido("A", 1, "B", 1, prorroga=True, repetido=True)) == "A 1-1 B (prór.) (se volvió a jugar)"
    assert mundial.texto_partido(partido("A", 1, "B", 0, repeticion=True)) == "A 1-0 B (repetición)"
    assert mundial.texto_partido(partido("A", 4, "B", 1, desempate=True)) == "A 4-1 B (desempate)"


def test_pareja_de_un_partido_repetido():
    empate = partido("A", 1, "B", 1, repetido=True)
    otro_empate = partido("C", 0, "D", 0, repetido=True)
    repeticion = {**partido("B", 2, "A", 1, repeticion=True), "fecha": "2026-06-13"}
    partidos = [empate, otro_empate, repeticion, partido("A", 3, "C", 0)]
    assert mundial.pareja_de(partidos, empate) is repeticion
    assert mundial.pareja_de(partidos, repeticion) is empate    # aunque jueguen de local y visitante al revés
    assert mundial.pareja_de(partidos, partidos[-1]) is None


def test_ganador_por_goles_y_por_penaltis():
    assert mundial.ganador_de(partido("A", 2, "B", 1)) == "A"
    assert mundial.ganador_de(partido("A", 0, "B", 1)) == "B"
    assert mundial.ganador_de(partido("A", 1, "B", 1, penaltis=[2, 4])) == "B"


def test_hay_104_partidos_ordenados_por_fecha(m):
    fechas = [p["fecha"] for p in m["todos_los_partidos"]]
    assert len(fechas) == 104
    assert fechas == sorted(fechas)


# ===== Clasificaciones =====

def test_clasificacion_de_un_grupo_inventado():
    partidos = [partido("A", 2, "B", 0), partido("C", 1, "A", 1), partido("B", 3, "C", 0)]
    tabla = mundial.calcular_clasificacion("X", ["A", "B", "C"], partidos, juego_limpio={})
    assert [(f["nombre"], f["pts"], f["dg"]) for f in tabla] == [("A", 4, 2), ("B", 3, 1), ("C", 1, -3)]
    a = tabla[0]
    assert (a["pj"], a["g"], a["e"], a["p"], a["gf"], a["gc"]) == (2, 1, 1, 0, 3, 1)


def test_el_juego_limpio_desempata_cuando_todo_lo_demas_es_igual():
    filas = [{"nombre": "Ecuador", "pts": 4, "dg": 0, "gf": 2}, {"nombre": "Ghana", "pts": 4, "dg": 0, "gf": 2}]
    ordenadas = mundial.ordenar_filas(filas, {"Ghana": -3, "Ecuador": -5})
    assert [f["nombre"] for f in ordenadas] == ["Ghana", "Ecuador"]


def test_grupo_a(m):
    tabla = m["clasificaciones"]["A"]
    assert [(f["nombre"], f["pts"]) for f in tabla] == [("México", 9), ("Sudáfrica", 4), ("Corea del Sur", 3), ("Chequia", 1)]


def test_mejores_terceros(m):
    terceros = [f["nombre"] for f in m["terceros"]]
    assert len(terceros) == 12
    assert terceros.index("Ghana") < terceros.index("Ecuador")  # desempate por juego limpio
    assert "Senegal" in terceros[:8] and "Irán" not in terceros[:8]


def test_las_32_clasificadas_son_las_que_jugaron_dieciseisavos(m):
    dieciseisavos = m["rondas"][0]["partidos"]
    jugaron = {equipo for p in dieciseisavos for equipo in (p["local"], p["visitante"])}
    assert m["clasificadas"] == jugaron
    assert len(jugaron) == 32


# ===== Buscador =====

@pytest.mark.parametrize("texto, grupos", [("mexico", ["A"]), ("  MÉXICO ", ["A"]), ("zzz", []), ("ia", None)])
def test_buscar_grupos(m, texto, grupos):
    encontrados = [g["grupo"] for g in mundial.buscar_grupos(m["grupos"], texto)]
    if grupos is None:
        assert len(encontrados) > 1  # "ia" está en varias: Arabia Saudí, Argelia, Bosnia...
    else:
        assert encontrados == grupos


def test_buscar_sin_texto_devuelve_los_12_grupos(m):
    assert len(mundial.buscar_grupos(m["grupos"], "")) == 12


# ===== Camino de una selección =====

@pytest.mark.parametrize("seleccion, hasta_donde, partidos", [
    ("España", "🏆 Campeona del mundo", 8),
    ("Argentina", "🥈 Subcampeona", 8),
    ("Inglaterra", "🥉 Tercer puesto", 8),
    ("Francia", "Cuarto puesto", 8),
    ("México", "Eliminada en octavos de final", 5),
    ("Haití", "Eliminada en la fase de grupos", 3),
])
def test_hasta_donde_llego(m, seleccion, hasta_donde, partidos):
    camino = mundial.camino(m, seleccion)
    assert camino["hasta_donde"] == hasta_donde
    assert len(camino["partidos"]) == partidos


def test_camino_de_mexico(m):
    camino = mundial.camino(m, "México")
    assert (camino["grupo"], camino["puesto"]) == ("A", 1)
    assert [p["resultado"] for p in camino["partidos"]] == ["V", "V", "V", "V", "D"]


def test_una_tanda_de_penaltis_cuenta_como_victoria_o_derrota(m):
    camino = mundial.camino(m, "Suiza")  # octavos: Suiza 0-0 Colombia, 4-3 en penaltis
    octavos = next(p for p in camino["partidos"] if p["ronda"] == "Octavos de final")
    assert octavos["resultado"] == "V"


def test_panama_no_marco_ningun_gol(m):
    assert mundial.camino(m, "Panamá")["goleadores"] == []


# ===== Goleadores =====

def test_puestos_compartidos_en_los_empates():
    goleadores = [{"goles": 10}, {"goles": 8}, {"goles": 7}, {"goles": 7}, {"goles": 6}]
    assert [mundial.puesto_de(goleadores, g["goles"]) for g in goleadores] == [1, 2, 3, 3, 5]


def test_bota_de_oro(m):
    primero = m["goleadores"][0]
    assert (primero["jugador"], primero["goles"], primero["puesto"]) == ("Kylian Mbappé", 10, 1)


def test_los_goles_de_los_jugadores_cuadran_con_los_marcadores(m):
    resumen = m["resumen_goles"]
    assert resumen["goles"] == 308
    assert sum(g["goles"] for g in m["goleadores"]) + resumen["en_propia"] == 308
    assert resumen["media"] == "2,96"


def test_si_los_goles_no_cuadran_cargar_avisa(monkeypatch):
    """Si a goleadores.json le sobra un gol, cargar() debe fallar en vez de mostrar datos mal."""
    leer_de_verdad = mundial.leer_json

    def leer_con_un_gol_de_mas(nombre):
        datos = leer_de_verdad(nombre)
        if nombre == "goleadores.json":
            datos["goleadores"][0]["goles"] += 1
        return datos

    # monkeypatch cambia mundial.leer_json solo durante esta prueba
    monkeypatch.setattr(mundial, "leer_json", leer_con_un_gol_de_mas)
    with pytest.raises(ValueError, match="no cuadran"):
        mundial.cargar()


def test_partidos_de_mbappe(m):
    partidos = mundial.partidos_del_goleador(m["goles"], m["todos_los_partidos"], "Kylian Mbappé", "Francia")
    assert len(partidos) == 6
    assert sum(len(d["minutos"]) for d in partidos) == 10
    assert any("(pen.)" in minuto for d in partidos for minuto in d["minutos"])


# ===== Goles por minuto =====

def test_goles_por_tramo_de_15_minutos(m):
    tramos = {f["tramo"]: f["goles"] for f in m["goles_por_tramo"]}
    assert list(tramos) == ["1-15", "16-30", "31-45+", "46-60", "61-75", "76-90+", "91-120"]
    assert sum(tramos.values()) == 308                    # todos los goles, ninguno fuera de un tramo
    assert tramos["76-90+"] == 81                          # el último cuarto de hora es el de más goles


@pytest.mark.parametrize("minuto, tramo", [("1", "1-15"), ("15", "1-15"), ("16", "16-30"), ("45+3", "31-45+"),
                                           ("46", "46-60"), ("90+8", "76-90+"), ("91", "91-120"), ("120", "91-120")])
def test_cada_minuto_cae_en_su_tramo(minuto, tramo):
    tramos = mundial.goles_por_tramo([{"minuto": minuto}])
    assert [f["tramo"] for f in tramos if f["goles"] == 1] == [tramo]


# ===== Goles por ronda =====

def test_goles_por_ronda(m):
    rondas = {f["ronda"]: f for f in m["goles_por_ronda"]}
    assert list(rondas) == ["Fase de grupos", "Dieciseisavos de final", "Octavos de final",
                            "Cuartos de final", "Semifinales", "Tercer puesto", "Final"]  # en el orden en que se jugaron
    assert sum(f["partidos"] for f in rondas.values()) == 104
    assert sum(f["goles"] for f in rondas.values()) == 308
    assert rondas["Fase de grupos"]["partidos"] == 72 and rondas["Fase de grupos"]["goles"] == 215
    assert rondas["Tercer puesto"]["partidos"] == 1 and rondas["Final"]["partidos"] == 1  # lo dice la nota de la web


def test_goles_por_ronda_con_partidos_inventados():
    partidos = [partido("A", 2, "B", 1, ronda="Grupo A", fase="Fase de grupos", eliminatoria=False),
                partido("C", 0, "D", 0, ronda="Grupo B", fase="Fase de grupos", eliminatoria=False),
                partido("A", 1, "C", 1, ronda="Final", eliminatoria=True)]
    assert mundial.goles_por_ronda(partidos) == [
        {"ronda": "Fase de grupos", "partidos": 2, "goles": 3, "media": 1.5},  # los grupos A y B, juntos
        {"ronda": "Final", "partidos": 1, "goles": 2, "media": 2.0},
    ]


def test_con_coma():
    assert mundial.con_coma(2.9861) == "2,99"
    assert mundial.con_coma(10) == "10,00"


# ===== Récords =====

def test_records(m):
    rec = m["records"]
    assert rec["mayor_goleada"]["diferencia"] == 6
    assert [mundial.texto_partido(p) for p in rec["mayor_goleada"]["partidos"]] == [
        "Alemania 7-1 Curazao", "Canadá 6-0 Catar"]          # empatadas: salen las dos, por fecha
    assert rec["mas_goles"]["goles"] == 10
    assert [mundial.texto_partido(p) for p in rec["mas_goles"]["partidos"]] == ["Francia 4-6 Inglaterra"]
    assert len(rec["penaltis"]) == 4
    assert len(rec["prorroga"]) == 5                         # sin contar los 4 que llegaron a los penaltis
    assert len(rec["sin_goles"]) == 8


def test_records_con_partidos_inventados():
    rec = mundial.records([partido("A", 3, "B", 0), partido("C", 2, "D", 2, prorroga=True),
                           partido("E", 0, "F", 0, prorroga=True, penaltis=[4, 3])])
    assert rec["mayor_goleada"] == {"diferencia": 3, "partidos": [partido("A", 3, "B", 0)]}
    assert rec["mas_goles"]["goles"] == 4                     # el 2-2
    assert [p["local"] for p in rec["prorroga"]] == ["C"]     # el de penaltis no cuenta aquí
    assert [p["local"] for p in rec["penaltis"]] == ["E"]
    assert [p["local"] for p in rec["sin_goles"]] == ["E"]


# ===== Quiz =====

def test_las_respuestas_del_quiz_cuadran_con_los_datos(m):
    """Cada respuesta correcta del quiz, sacada de los datos: si un día cambian, esta prueba avisa."""
    partidos = m["todos_los_partidos"]
    assert partidos[-1]["ronda"] == "Final"
    tramo_con_mas_goles = max(m["goles_por_tramo"], key=lambda f: f["goles"])["tramo"]
    (mas_goles,) = m["records"]["mas_goles"]["partidos"]       # uno solo: si hubiera empate, la pregunta no valdría
    (bota_de_oro,) = [g for g in m["goleadores"] if g["puesto"] == 1]
    esperadas = {
        "¿Cuántas selecciones jugaron el Mundial 2026?": str(len(m["selecciones"])),
        "¿Cuántos partidos se jugaron en total?": str(len(partidos)),
        "¿Qué estadio acogió el partido inaugural?": partidos[0]["estadio"],
        "¿Qué ronda nueva apareció con el formato de 48 equipos?": m["rondas"][0]["ronda"],
        "¿En qué estadio se jugó la final?": partidos[-1]["estadio"],
        "¿Quién ganó el Mundial 2026?": m["campeon"],
        "¿Quién ganó la Bota de Oro?": bota_de_oro["jugador"],
        "¿Qué partido tuvo más goles?": mundial.texto_partido(mas_goles),
        "¿En qué tramo de minutos se marcaron más goles?": tramo_con_mas_goles,
        "¿Cuántos partidos se decidieron en los penaltis?": str(len(m["records"]["penaltis"])),
    }
    assert [p["pregunta"] for p in m["preguntas"]] == list(esperadas)  # ninguna pregunta sin comprobar
    for p in m["preguntas"]:
        assert p["opciones"][p["correcta"]] == esperadas[p["pregunta"]], p["pregunta"]


def test_cada_pregunta_del_quiz_tiene_4_opciones_distintas(m):
    for p in m["preguntas"]:
        assert len(set(p["opciones"])) == 4, p["pregunta"]


# ===== Todos los Mundiales =====

@pytest.fixture(scope="module")
def todos():
    """Los 23 Mundiales, cargados una sola vez para todas las pruebas de este archivo."""
    return mundial.cargar_todos()


@pytest.fixture(scope="module")
def h(todos):
    return mundial.cargar_historia(todos)


def test_historia_cifras(h):
    assert [f["año"] for f in h["mundiales"]][:3] == [1930, 1934, 1938]
    assert h["mundiales"][-1]["año"] == 2026
    assert len(h["mundiales"]) == 23
    assert h["partidos"] == 1068 and h["goles"] == 3028    # 964 y 2.720 de 1930 a 2022, más 104 y 308 de 2026


def test_titulos_por_pais(h):
    assert [(t["nombre"], t["titulos"]) for t in h["titulos"]] == [
        ("Brasil", 5), ("Alemania", 4), ("Italia", 4), ("Argentina", 3),
        ("España", 2), ("Francia", 2), ("Uruguay", 2), ("Inglaterra", 1)]
    (alemania,) = [t for t in h["titulos"] if t["nombre"] == "Alemania"]
    assert alemania["años"] == [1954, 1974, 1990, 2014]     # tres como Alemania Federal


def test_goleadores_historicos(h):
    primeros = [(g["puesto"], g["jugador"], g["goles"]) for g in h["goleadores"]][:4]
    assert primeros == [(1, "Kylian Mbappé", 22), (2, "Lionel Messi", 21), (3, "Miroslav Klose", 16), (4, "Ronaldo", 15)]
    assert h["goleadores"][0]["años"] == [2018, 2022, 2026]
    assert [g["jugador"] for g in h["goleadores"] if g["puesto"] == 9] == ["Cristiano Ronaldo", "Sándor Kocsis"]  # empatados


def test_goleadores_historicos_con_goles_inventados():
    goles = {1998: [{"jugador": "A", "seleccion": "X"}, {"jugador": "A", "seleccion": "X", "tipo": "propia"}],
             2026: [{"jugador": "Julián Alvarez", "seleccion": "Argentina"}, {"jugador": "B", "seleccion": "Y"}],
             2022: [{"jugador": "Julián Álvarez", "seleccion": "Argentina"}]}
    filas = mundial.goleadores_historicos(goles, cuantos=1)
    # El de propia puerta no cuenta, y "Alvarez" y "Álvarez" son el mismo jugador
    assert filas == [{"jugador": "Julián Álvarez", "seleccion": "Argentina", "goles": 2, "años": [2022, 2026], "puesto": 1}]


# ===== Cada Mundial antiguo =====

def test_cada_mundial_tiene_un_campeon_y_un_subcampeon(todos):
    for año, m in todos.items():
        hasta_donde = [mundial.camino(m, s)["hasta_donde"] for s in m["selecciones"]]
        assert hasta_donde.count("🏆 Campeona del mundo") == 1, año
        assert hasta_donde.count("🥈 Subcampeona") == 1, año
        assert mundial.camino(m, m["campeon"])["hasta_donde"] == "🏆 Campeona del mundo", año


def test_1950_sin_final(todos):
    m = todos[1950]
    assert m["rondas"] == []                                   # ninguna eliminatoria
    assert m["finalistas"] == ["Uruguay", "Brasil"]            # las dos primeras de la liguilla
    assert mundial.camino(m, "Brasil")["hasta_donde"] == "🥈 Subcampeona"
    assert mundial.camino(m, "España")["hasta_donde"] == "Cuarto puesto"
    assert mundial.camino(m, "Uruguay")["grupo"] == "4"        # su grupo de la primera fase, no la liguilla
    assert [r["ronda"] for r in m["goles_por_ronda"]] == ["Fase de grupos", "Liguilla final"]


def test_1934_sin_grupos(todos):
    m = todos[1934]
    assert m["grupos"] == [] and len(m["selecciones"]) == 16   # las selecciones salen de los partidos
    c = mundial.camino(m, "Italia")
    assert (c["grupo"], c["puesto"], c["hasta_donde"]) == (None, None, "🏆 Campeona del mundo")


def test_un_partido_que_se_volvio_a_jugar_no_tiene_ganador(todos):
    m = todos[1934]
    (empate,) = [p for p in m["todos_los_partidos"] if p.get("repetido")]   # Italia 1-1 España
    assert mundial.ganador_de(empate) is None
    partidos = mundial.camino(m, "España")["partidos"]
    assert [p["resultado"] for p in partidos] == ["V", "E", "D"]  # Brasil, Italia (empate), Italia (repetición)


def test_la_segunda_fase_de_grupos(todos):
    m = todos[1982]
    assert mundial.camino(m, "Argentina")["hasta_donde"] == "Eliminada en la segunda fase de grupos"
    assert [g["nombre"] for g in m["grupos"]][-4:] == [f"Grupo {l} (segunda fase)" for l in "ABCD"]
    assert "Segunda fase de grupos" in [r["ronda"] for r in m["goles_por_ronda"]]


def test_los_goleadores_de_un_mundial_antiguo(todos):
    m = todos[1958]
    assert (m["goleadores"][0]["jugador"], m["goleadores"][0]["goles"]) == ("Just Fontaine", 13)
    assert m["resumen_goles"]["partidos"] == 35


def test_contar_goleadores():
    goles = [{"jugador": "B", "seleccion": "X"}, {"jugador": "A", "seleccion": "X"},
             {"jugador": "A", "seleccion": "X"}, {"jugador": "C", "seleccion": "Y", "tipo": "propia"}]
    assert mundial.contar_goleadores(goles) == [{"jugador": "A", "seleccion": "X", "goles": 2},
                                                {"jugador": "B", "seleccion": "X", "goles": 1}]


def test_si_los_goles_no_cuadran_no_arranca(m):
    roto = {**m, "goleadores": [dict(g) for g in m["goleadores"]], "en_propia": m["en_propia"] + 1}
    with pytest.raises(ValueError, match="no cuadran"):
        mundial.completar(roto)


# ===== Cada selección en todos los Mundiales =====

@pytest.fixture(scope="module")
def historial(todos):
    return mundial.historial(todos)


def test_historial_de_brasil(historial):
    b = historial["Brasil"]
    assert len(b["participaciones"]) == 23                     # todos los Mundiales
    assert b["titulos"] == [1958, 1962, 1970, 1994, 2002]
    assert b["nombres"] == []
    assert b["partidos"] == b["g"] + b["e"] + b["p"]
    assert (b["goleadores"][0]["jugador"], b["goleadores"][0]["goles"]) == ("Ronaldo", 15)


def test_las_selecciones_que_cambiaron_de_nombre(historial):
    assert historial["Alemania"]["nombres"] == ["Alemania Federal"]
    assert historial["Alemania"]["titulos"] == [1954, 1974, 1990, 2014]
    assert historial["Chequia"]["nombres"] == ["Checoslovaquia", "República Checa"]
    assert historial["Chequia"]["mejor"] == "🥈 Subcampeona"     # como Checoslovaquia, en 1934 y 1962
    assert historial["RD del Congo"]["nombres"] == ["Zaire"]
    assert "Alemania Federal" not in historial and "Unión Soviética" not in historial


def test_historial_cifras_generales(historial, todos):
    assert len(historial) == 84
    assert sum(len(h["titulos"]) for h in historial.values()) == 23   # un campeón por Mundial
    # Las participaciones de todas suman las selecciones de cada Mundial
    assert sum(len(h["participaciones"]) for h in historial.values()) == sum(len(m["selecciones"]) for m in todos.values())


def test_el_mejor_resultado(historial):
    assert historial["Estados Unidos"]["mejor"] == "Eliminada en semifinales"   # 1930, sin tercer puesto
    assert historial["Cabo Verde"]["mejor"] == "Eliminada en dieciseisavos de final"
    assert historial["Indonesia"]["goleadores"] == []          # 1938: perdió 6-0 y no marcó


def test_partidos_entre_dos_selecciones(todos):
    entre = mundial.partidos_entre(todos, "Argentina", "Alemania")
    assert [p["año"] for p in entre] == [1958, 1966, 1986, 1990, 2006, 2010, 2014]
    assert mundial.resumen_de_partidos(entre, {"Alemania", "Alemania Federal"}) == \
        {"partidos": 7, "g": 5, "e": 1, "p": 1, "gf": 12, "gc": 5}


def test_goleadores_historicos_con_menos_de_los_pedidos():
    goles = {2026: [{"jugador": "A", "seleccion": "X"}]}
    assert [f["jugador"] for f in mundial.goleadores_historicos(goles, cuantos=5)] == ["A"]


# ===== Goles de un partido =====

def test_los_goles_agrupados_por_partido_son_los_308(m):
    assert sum(len(goles) for goles in m["goles_por_partido"].values()) == 308
    assert all(mundial.clave_partido(g) == clave for clave, goles in m["goles_por_partido"].items() for g in goles)


def test_con_los_goles_agrupados_sale_lo_mismo_que_con_todos(m):
    """La web pasa solo los goles de cada partido (es más rápido): el resultado tiene que ser el mismo."""
    for p in m["todos_los_partidos"]:
        del_partido = m["goles_por_partido"].get(mundial.clave_partido(p), [])
        assert mundial.linea_del_tiempo(del_partido, p) == mundial.linea_del_tiempo(m["goles"], p)
        for equipo in (p["local"], p["visitante"]):
            assert mundial.anotadores_de(del_partido, p, equipo) == mundial.anotadores_de(m["goles"], p, equipo)


def final(m):
    return m["rondas"][-1]["partidos"][0]


def tercer_puesto(m):
    return m["rondas"][-2]["partidos"][0]


def test_anotadores_de_la_final(m):
    assert mundial.anotadores_de(m["goles"], final(m), "España") == "Ferran Torres 106'"
    assert mundial.anotadores_de(m["goles"], final(m), "Argentina") == ""


def test_un_gol_en_propia_puerta_cuenta_para_el_rival(m):
    argentina_cabo_verde = next(p for p in m["rondas"][0]["partidos"] if p["visitante"] == "Cabo Verde")
    assert "Diney 111' (p.p.)" in mundial.anotadores_de(m["goles"], argentina_cabo_verde, "Argentina")


def test_linea_del_tiempo_del_tercer_puesto(m):
    t = mundial.linea_del_tiempo(m["goles"], tercer_puesto(m))
    assert t["duracion"] == 90
    assert t["cortes"] == [50.0]  # el descanso, a mitad de la barra
    assert [f["marcador"] for f in t["filas"]][3] == "0-4"  # 4-0 para Inglaterra al descanso
    assert t["filas"][-1]["marcador"] == "4-6"


def test_linea_del_tiempo_con_prorroga(m):
    t = mundial.linea_del_tiempo(m["goles"], final(m))
    assert t["duracion"] == 120
    assert t["cortes"] == [37.5, 75.0]  # descanso y minuto 90
    assert t["filas"][-1]["marcador"] == "1-0"


def test_sin_goles_no_hay_linea_del_tiempo(m):
    cero_a_cero = next(p for p in m["todos_los_partidos"] if p["golesLocal"] + p["golesVisitante"] == 0)
    assert mundial.linea_del_tiempo(m["goles"], cero_a_cero) is None


def test_la_linea_del_tiempo_acaba_con_el_resultado_en_los_104_partidos(m):
    for p in m["todos_los_partidos"]:
        t = mundial.linea_del_tiempo(m["goles"], p)
        esperado = f"{p['golesLocal']}-{p['golesVisitante']}"
        assert (t["filas"][-1]["marcador"] if t else "0-0") == esperado, mundial.texto_partido(p)



# ===== Cara a cara =====

def test_los_numeros_de_espana(m):
    n = mundial.numeros_de(m, "España")
    assert (n["partidos"], n["ganados"], n["empatados"], n["perdidos"]) == (8, 7, 1, 0)
    assert (n["goles_a_favor"], n["goles_en_contra"]) == (14, 1)
    assert (n["maximos_goleadores"], n["goles_del_maximo"]) == (["Mikel Oyarzabal"], 5)


def test_una_seleccion_sin_goles_no_tiene_maximo_goleador(m):
    n = mundial.numeros_de(m, "Panamá")
    assert (n["goles_a_favor"], n["maximos_goleadores"], n["goles_del_maximo"]) == (0, [], 0)


def test_los_goles_a_favor_cuadran_con_todos_los_partidos(m):
    """Sumando los goles a favor de las 48 selecciones salen los 308 goles del Mundial."""
    assert sum(mundial.numeros_de(m, s)["goles_a_favor"] for s in m["selecciones"]) == 308


def test_cara_a_cara_de_los_finalistas(m):
    c = mundial.cara_a_cara(m, "España", "Argentina")
    assert (c["a"]["seleccion"], c["b"]["seleccion"]) == ("España", "Argentina")
    assert [p["ronda"] for p in c["entre_ellas"]] == ["Final"]


def test_dos_selecciones_que_no_se_enfrentaron(m):
    assert mundial.cara_a_cara(m, "Japón", "Panamá")["entre_ellas"] == []
