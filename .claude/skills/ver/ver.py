"""Capturas de una página en los tres idiomas, en móvil y escritorio y en los dos temas. Lo usa /ver.

    venv/bin/python .claude/skills/ver/ver.py '/seleccion/Alemania#goleada' <carpeta>

Con #seccion captura solo esa sección. Termina con código 1 si algo está mal.
"""

import sys
from pathlib import Path
from urllib.parse import urldefrag

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pruebas"))
from probar_web import arrancar_servidor, comprobar, fallos  # noqa: E402  (el mismo servidor que las pruebas)

IDIOMAS = {"es": "es-ES", "pt": "pt-BR", "en": "en-GB"}
PANTALLAS = {"movil": (375, 800), "escritorio": (1200, 900)}
TEMAS = {"claro": "light", "oscuro": "dark"}
ALTO_MAXIMO = 3000  # una captura más alta no se lee


def recuadro(pagina, seccion):
    """Qué parte de la página se captura: la sección pedida o, si no la hay, la página entera."""
    if seccion and pagina.locator(f'[id="{seccion}"]').count():
        r = pagina.locator(f'[id="{seccion}"]').bounding_box()
    else:
        ancho, alto = pagina.evaluate("[innerWidth, document.documentElement.scrollHeight]")
        r = {"x": 0, "y": 0, "width": ancho, "height": alto}
    return {**r, "height": min(r["height"], ALTO_MAXIMO)}, r["height"] > ALTO_MAXIMO


def revisar_enlaces(pagina, raiz):
    """Los enlaces de la página a la propia web, cada uno una vez."""
    destinos = pagina.evaluate("[...document.querySelectorAll('a[href]')].map(a => a.href)")
    propios = sorted({urldefrag(d).url for d in destinos if d.startswith(raiz)})
    rotos = [d for d in propios if not pagina.request.get(d).ok]
    comprobar(f"los {len(propios)} enlaces a la propia web funcionan", not rotos)
    for d in rotos:
        print(f"      · {d}")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    ruta, seccion = urldefrag(sys.argv[1].lstrip("/"))
    carpeta = Path(sys.argv[2])
    carpeta.mkdir(parents=True, exist_ok=True)
    servidor, raiz = arrancar_servidor()
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for idioma, locale in IDIOMAS.items():
            print(f"=== {idioma} ===")
            for pantalla, (ancho, alto) in PANTALLAS.items():
                for tema, esquema in TEMAS.items():
                    nombre, errores = f"{idioma}-{pantalla}-{tema}", []
                    pagina = navegador.new_page(locale=locale, viewport={"width": ancho, "height": alto}, color_scheme=esquema)
                    pagina.on("console", lambda m: m.type in ("error", "warning") and errores.append(m.text))
                    respuesta = pagina.goto(raiz + ruta)
                    comprobar(f"{nombre}: responde {respuesta.status}", respuesta.ok)
                    if seccion:
                        comprobar(f"{nombre}: existe la sección #{seccion}" if pagina.locator(f'[id="{seccion}"]').count()
                                  else f"{nombre}: no existe la sección #{seccion} (se captura la página)",
                                  pagina.locator(f'[id="{seccion}"]').count() == 1)
                    comprobar(f"{nombre}: sin scroll horizontal",
                              pagina.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                    recorte, cortada = recuadro(pagina, seccion)
                    pagina.screenshot(path=carpeta / f"{nombre}.png", full_page=True, clip=recorte)
                    if cortada:
                        print(f"  ⚠️ {nombre}: captura cortada a {ALTO_MAXIMO} px (pide una #seccion)")
                    if nombre.startswith("es-movil-claro"):
                        revisar_enlaces(pagina, raiz)  # son los mismos en todos los idiomas y tamaños
                    comprobar(f"{nombre}: sin errores en la consola", not errores)
                    for e in errores:
                        print(f"      · {e}")
                    pagina.close()
        navegador.close()
    servidor.shutdown()
    print(f"\nCapturas en {carpeta.resolve()}\n{'Todo correcto' if not fallos else f'{len(fallos)} fallo(s)'}")
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()
