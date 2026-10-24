[← Volver al README](../README.md)

# Web publicada (Render)

La web está en **<https://mundial-2026-j5o8.onrender.com/>**. Se publica en [Render](https://render.com), un servicio que ejecuta aplicaciones de Python. GitHub Pages no sirve, porque solo publica archivos fijos y no puede ejecutar Python.

La antigua versión en JavaScript estaba en GitHub Pages (repositorio público `mundial-2026-web`). Ahora esa dirección solo redirige a Render y conserva la sección: por ejemplo, `…/mundial-2026-web/#goleadores` lleva a `…onrender.com/#goleadores`. Así los enlaces viejos siguen funcionando. Desde el paso 59, la raíz de Render es la página de inicio con todos los Mundiales, así que esos enlaces viejos llevan a ella (y `#goleadores`, a los máximos goleadores de la historia). El Mundial 2026 está en `/2026/`.

**Cómo está configurado** (`render.yaml`, que Render llama *Blueprint*):

- **Instalación:** Render instala `requirements.txt` y arranca la web con **gunicorn** (`gunicorn app:app`). gunicorn es un servidor preparado para producción; `flask run` es solo para desarrollar.
- **Versión de Python:** la de `.python-version`. GitHub Actions usa ese mismo archivo.
- **Publicación automática:** con `autoDeployTrigger: checksPass`, Render publica cada vez que algo llega a `main`, pero **solo si las pruebas de GitHub Actions han pasado**.
- **Clave de la sesión:** `CLAVE_SECRETA` la inventa Render al azar y la guarda como secreto. Además, en Render la cookie de la sesión solo viaja por HTTPS.
- **Plan gratuito:** si nadie visita la web durante un rato (unos 15 minutos), Render la «duerme», y la siguiente visita tarda hasta un minuto en cargar.

**Cómo se creó el servicio** (ya está hecho; solo habría que repetirlo para crearlo de nuevo):

1. Entra en <https://dashboard.render.com> con tu cuenta de GitHub.
2. Pulsa **New** → **Blueprint** y conecta el repositorio `mundial-2026`. Como es privado, Render te pedirá permiso para leerlo.
3. Render lee `render.yaml` y muestra el servicio `mundial-2026`. Pulsa **Deploy Blueprint**.
4. Espera a que ponga **Live**. La dirección está debajo del nombre del servicio. Render añade al nombre unas letras al azar (`-j5o8`), porque `mundial-2026.onrender.com` ya lo usaba otra persona.

Para comprobar la web publicada con las mismas pruebas:

```bash
venv/bin/python pruebas/probar_web.py https://mundial-2026-j5o8.onrender.com
```

Para probar en tu ordenador con el mismo servidor que Render: `PORT=8000 venv/bin/gunicorn app:app` y abrir <http://127.0.0.1:8000>.
