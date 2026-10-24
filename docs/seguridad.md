[← Volver al README](../README.md)

# Seguridad

Con cada respuesta, Flask manda unas **cabeceras de seguridad**: instrucciones para el navegador de quien visita la web. Lo hace la función `cabeceras_de_seguridad()` de `app.py`, con `@app.after_request`, que Flask llama justo antes de enviar cada respuesta. Antes del paso 41 la web no mandaba ninguna.

| Cabecera | Para qué |
|---|---|
| `Content-Security-Policy` | De dónde puede cargar cosas la página: solo de esta web, y de Google para las fuentes. Ningún JavaScript (`script-src 'none'`). Si alguien consiguiera colar HTML en la página, el navegador no ejecutaría su código. |
| `X-Content-Type-Options: nosniff` | El navegador no «adivina» el tipo de un archivo: un `.css` es CSS y nada más. |
| `X-Frame-Options: DENY` y `frame-ancestors 'none'` | Ninguna otra web puede meter esta dentro de un `<iframe>` para engañar a quien la usa. |
| `Referrer-Policy` | Al pulsar un enlace a otra web, solo se le dice el dominio de esta, no la dirección completa. |
| `Permissions-Policy` | La web no puede usar la cámara, el micrófono ni la ubicación. |
| `Strict-Transport-Security` | Solo en Render, que va por HTTPS: el navegador recordará un año que debe usar siempre HTTPS. |

Además, la cookie de la sesión es `SameSite=Lax`: no viaja cuando otra web envía un formulario a esta, por ejemplo a `/quiz/responder`. Y solo existe si hace falta. Antes, `estado_quiz()` usaba `session.setdefault(...)`, que guardaba un quiz vacío en cuanto alguien abría la portada, y Flask mandaba la cookie a todo el mundo. Ahora usa `session.get(...)`, que no guarda nada, y el quiz se guarda al responder.

Dos detalles:
- **Los puntos de la línea del tiempo** se colocan con `style="left: 40%"`. Por eso la política permite estilos en atributos (`style-src-attr 'unsafe-inline'`), pero no bloques `<style>`.
- **axe-core intentaba descargar el CSS por su cuenta**, y la política se lo impedía (con un error en la consola). En vez de abrir la política para la herramienta de pruebas, `probar_web.py` la usa con `preload: False`.

Las pruebas comprueban que todas las respuestas llevan las cabeceras, incluidas la 404 y las redirecciones. En el navegador, se cuela a propósito una imagen con `onload="..."` y se comprueba que su código no se ejecuta.

## Nota del Observatory de Mozilla

El [Observatory](https://developer.mozilla.org/en-US/observatory) es un servicio de Mozilla que visita una web, revisa sus cabeceras de seguridad y le pone nota. La web publicada saca **A+**: 110 puntos (las buenas prácticas suman puntos extra por encima de 100) y 12 de 12 pruebas superadas. La primera vez, justo antes del paso 42, sacó 115. Lo más probable es que los 5 puntos de diferencia fueran por la cookie de la sesión, que estaba bien protegida (`Secure`, `HttpOnly`, `SameSite`): desde el paso 42 la portada ya no manda cookie y no hay nada que puntuar. No se puede confirmar porque la API no da el detalle de cada prueba. `pruebas/nota_observatory.py` pide la nota a su API y termina con error si baja de A+. Si el servicio de Mozilla responde con un error momentáneo (por ejemplo, un 422 porque ya está analizando la misma web), espera 30 segundos y lo reintenta, hasta 3 veces. Lo ejecuta GitHub después de cada publicación, y también se puede usar a mano:

```bash
venv/bin/python pruebas/nota_observatory.py https://mundial-2026-j5o8.onrender.com
```
