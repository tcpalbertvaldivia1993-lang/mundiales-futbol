"""Pide al Observatory de Mozilla la nota de seguridad de la web publicada.

El Observatory visita la web y revisa sus cabeceras de seguridad (Content-Security-Policy,
HTTPS, cookies...). Este script muestra la nota y termina con error si baja de A+.

Uso, desde la carpeta del proyecto:
    venv/bin/python pruebas/nota_observatory.py https://mundial-2026-j5o8.onrender.com

Documentación de la API: https://developer.mozilla.org/en-US/observatory/docs/faq
"""

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

NOTA_MINIMA = "A+"
API = "https://observatory-api.mdn.mozilla.net/api/v2/scan?host={}"
INTENTOS = 3
ESPERA = 30  # segundos entre intentos: el Observatory solo analiza la misma web una vez cada 60 s


def pedir_nota(direccion):
    """El resultado del análisis, como diccionario: grade, score, tests_passed, details_url..."""
    dominio = urlparse(direccion).hostname  # "https://mundial-2026-j5o8.onrender.com/" -> solo el dominio
    peticion = Request(API.format(dominio), method="POST")  # la API pide un POST, sin nada dentro
    with urlopen(peticion, timeout=120) as respuesta:
        return json.load(respuesta)


def pedir_nota_con_reintentos(direccion, intentos=INTENTOS, espera=ESPERA):
    """Como pedir_nota(), pero si Mozilla responde con un error (a veces lo hace un momento, por ejemplo
    si ya está analizando la misma web), espera y lo vuelve a intentar."""
    for intento in range(1, intentos + 1):
        try:
            return pedir_nota(direccion)
        except (HTTPError, URLError) as error:
            print(f"Intento {intento} de {intentos}: el Observatory respondió con un error ({error})")
            if intento == intentos:
                sys.exit("❌ El Observatory no respondió bien: es un problema de su servicio, no de la web")
            time.sleep(espera)


def main():
    if len(sys.argv) != 2:
        sys.exit(f"Uso: {sys.argv[0]} <dirección de la web publicada>")
    resultado = pedir_nota_con_reintentos(sys.argv[1])
    if resultado.get("error"):
        sys.exit(f"❌ El Observatory no pudo analizar la web: {resultado['error']}")

    print(f"Nota: {resultado['grade']} ({resultado['score']} puntos)")
    print(f"Pruebas superadas: {resultado['tests_passed']} de {resultado['tests_quantity']}")
    print(f"Informe completo: {resultado['details_url']}")
    if resultado["grade"] != NOTA_MINIMA:
        sys.exit(f"❌ La nota ha bajado de {NOTA_MINIMA}: mira el informe para ver qué ha cambiado")
    print(f"✅ Nota {NOTA_MINIMA}")


if __name__ == "__main__":
    main()
