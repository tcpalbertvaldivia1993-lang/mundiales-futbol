---
name: probar
description: Pasa todas las pruebas del proyecto, pytest con cobertura del 100 % y probar_web.py en el navegador. Usar antes de dar un cambio por hecho o de subirlo.
---

Pasa las dos pruebas en este orden, desde la carpeta del proyecto.

1. Si falta `venv/` o algo de `requirements-dev.txt`, dilo y prepáralo con los comandos de `CLAUDE.md`.
2. `venv/bin/python -m pytest -q --cov-fail-under=100`
   Si falla, para aquí: di qué prueba falla y por qué, o qué líneas o ramas faltan (columna «Missing»: `65->67` es un `if` probado por un solo camino).
3. `venv/bin/python pruebas/probar_web.py` (unos 30 segundos; necesita internet para Google Fonts)
   Cuenta los ✅ y los ❌, y muestra entero cada ❌. Mira también el código de salida: si el script se corta a medias, no ha pasado aunque no haya ningún ❌.
4. Da los dos resultados. Solo están en verde si los dos terminan con código 0, y después de la última edición.

Si algo falla, explica la causa. No arregles nada si solo se ha pedido probar, y nunca cambies una prueba, bajes la cobertura ni uses `--no-verify` para que pase.
