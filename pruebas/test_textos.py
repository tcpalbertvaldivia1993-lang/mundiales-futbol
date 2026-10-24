"""Pruebas de los idiomas: las traducciones de textos.py y los nombres de data/nombres.json."""

import re
import string
from pathlib import Path

import pytest

import mundial
import textos

PLANTILLAS = Path(__file__).resolve().parent.parent / "templates"


def llaves(texto):
    """Los datos entre llaves de un texto: "Los {n} Mundiales" -> {"n"}."""
    return {campo for _, campo, _, _ in string.Formatter().parse(texto) if campo}


def test_traducir():
    assert textos.traducir("Campeones", "es") == "Campeones"
    assert textos.traducir("Campeones", "pt") == "Campeões"
    assert textos.traducir("Los {n} Mundiales", "en", n=23) == "The 23 World Cups"
    assert textos.traducir("Un texto sin traducir", "en") == "Un texto sin traducir"   # sale en español


def test_nombre():
    assert textos.nombre("Brasil", "en") == "Brazil"
    assert textos.nombre("Octavos de final", "pt") == "Oitavas de final"
    assert textos.nombre("Brasil", "es") == "Brasil"
    assert textos.nombre("Kylian Mbappé", "en") == "Kylian Mbappé"       # los jugadores no se traducen
    assert textos.nombre(1950, "en") == 1950                              # ni los años


def test_cada_texto_tiene_sus_dos_traducciones():
    for texto, traducciones in textos.TEXTOS.items():
        assert set(traducciones) == {"pt", "en"}, texto
        for traduccion in traducciones.values():
            assert llaves(traduccion) == llaves(texto), texto              # los mismos datos entre llaves


def test_los_textos_de_las_plantillas_estan_traducidos():
    """Cada t("...") escrito en una plantilla tiene que estar en textos.py: si no, saldría en español.
    También los dos de t("{n} partido" if n == 1 else "{n} partidos")."""
    sin_traducir = set()
    # Con comillas dobles o simples: t("...") o t('...')
    patron = r'\bt\(\s*["\']([^"\']+)["\'](?:\s+if\s+[^"\']*?\s+else\s+["\']([^"\']+)["\'])?'
    for plantilla in PLANTILLAS.rglob("*.html"):
        for encontrados in re.findall(patron, plantilla.read_text(encoding="utf-8")):
            for texto in encontrados:
                if texto and texto not in textos.TEXTOS:
                    sin_traducir.add(f"{plantilla.name}: {texto}")
    assert not sin_traducir


@pytest.mark.parametrize("texto", [
    # Los que llegan a t() desde una variable, y que la prueba de arriba no ve
    "1.º", "2.º", "3.º", "4.º", "Primera", "Segunda", "Tercera", "Cuarta",   # el puesto en el camino
    "V", "E", "D", "Victoria", "Empate", "Derrota",                          # el resultado en el camino
    "se decidió en los penaltis", "se decidieron en los penaltis", "terminó 0-0", "terminaron 0-0",
    "se decidió en la prórroga, sin llegar a los penaltis", "se decidieron en la prórroga, sin llegar a los penaltis",
    "Inicio", "Sedes", "Formato", "Resultados", "Camino", "Quiz",             # el menú de cada Mundial
    "Automático", "Claro", "Oscuro",                                         # los botones del tema
    "la ronda", "Ronda", "Goles por partido en cada ronda",                  # la gráfica de rondas
    "Primera selección", "Segunda selección", "correcta", "incorrecta",      # el cara a cara y el quiz
])
def test_los_textos_que_llegan_desde_una_variable_estan_traducidos(texto):
    assert texto in textos.TEXTOS


@pytest.fixture(scope="module")
def todos():
    return mundial.cargar_todos()


def test_todas_las_selecciones_y_rondas_tienen_nombre_en_los_tres_idiomas(todos):
    nombres = set(mundial.SUCESORAS.values())
    for m in todos.values():
        nombres |= set(m["selecciones"]) | set(m["paises"]) | {e["pais"] for e in m["estadios"]}
        nombres |= {r["ronda"] for r in m["goles_por_ronda"]}
    assert nombres - set(textos.NOMBRES) == set()
    for traducciones in textos.NOMBRES.values():
        assert set(traducciones) == {"pt", "en"}


def test_los_grupos_en_cada_idioma():
    assert textos.nombre("Grupo A", "en") == "Group A"
    assert textos.nombre("Grupo B (segunda fase)", "en") == "Group B (second stage)"
    assert textos.nombre("Grupo 3", "pt") == "Grupo 3"


def test_hasta_donde_llego_en_cada_idioma():
    """Cada texto de mundial.NIVELES (hasta dónde llegó una selección) tiene su traducción."""
    for nivel in mundial.NIVELES:
        assert nivel in textos.TEXTOS, nivel


def partido(**extra):
    return {"local": "Italia", "golesLocal": 1, "golesVisitante": 1, "visitante": "España", **extra}


@pytest.mark.parametrize("extra, es, en, pt", [
    ({}, "Italia 1-1 España", "Italy 1-1 Spain", "Itália 1-1 Espanha"),
    ({"prorroga": True}, "Italia 1-1 España (prór.)", "Italy 1-1 Spain (a.e.t.)", "Itália 1-1 Espanha (prorr.)"),
    ({"prorroga": True, "penaltis": [4, 3]}, "Italia 1-1 España (pen. 4-3)", "Italy 1-1 Spain (pens 4-3)",
     "Itália 1-1 Espanha (pên. 4-3)"),
    ({"prorroga": True, "repetido": True}, "Italia 1-1 España (prór.) (se volvió a jugar)",
     "Italy 1-1 Spain (a.e.t.) (replayed)", "Itália 1-1 Espanha (prorr.) (jogo repetido)"),
])
def test_el_texto_de_un_partido_en_cada_idioma(extra, es, en, pt):
    p = partido(**extra)
    assert (textos.texto_partido(p, "es"), textos.texto_partido(p, "en"), textos.texto_partido(p, "pt")) == (es, en, pt)


def test_cada_idioma_tiene_sus_abreviaturas():
    for diccionario in (textos.ABREVIATURAS, textos.TANDA, textos.MINUTO, textos.PRORROGA):
        assert set(diccionario) == set(textos.IDIOMAS)
    for idioma, marca in textos.PRORROGA.items():
        assert marca in textos.ABREVIATURAS[idioma]           # la marca de la prórroga tiene su forma larga


def test_el_quiz_en_cada_idioma():
    for p in mundial.leer_json("quiz.json"):
        for idioma in ("pt", "en"):
            traducida = p[idioma]
            assert set(traducida) == {"pregunta", "opciones", "explicacion"}, p["pregunta"]
            assert len(traducida["opciones"]) == len(set(traducida["opciones"])) == 4, (idioma, p["pregunta"])
            # Si la respuesta buena es un nombre de los datos ("España"), en ese idioma es su traducción ("Spain")
            correcta = p["opciones"][p["correcta"]]
            if correcta in textos.NOMBRES:
                assert traducida["opciones"][p["correcta"]] == textos.nombre(correcta, idioma), (idioma, p["pregunta"])
