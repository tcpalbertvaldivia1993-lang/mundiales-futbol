[← Volver al README](../README.md)

# Accesibilidad

Que la web se pueda usar sin ratón, con un lector de pantalla o viendo poco. Lo comprueba `pruebas/probar_web.py` (ver [pruebas.md](pruebas.md)) de tres maneras: con axe-core, recorriéndola con el teclado y mirando lo que oiría un lector de pantalla.

## Revisión automática con axe-core

`pruebas/probar_web.py` pasa [axe-core](https://github.com/dequelabs/axe-core) por la página, con el paquete `axe-playwright-python`. axe revisa unas 100 reglas de accesibilidad: contraste suficiente entre texto y fondo, campos con nombre, títulos en orden, idioma de la página, que todo esté dentro de una zona (`header`, `nav`, `main`, `footer`)... Lo hace en varios momentos, porque solo revisa lo que se ve en ese momento: la portada, con un goleador abierto, con el quiz respondido, con el botón ↑ visible, en el móvil y en la 404. También la página de inicio con todos los Mundiales (en español y en inglés), páginas en otros idiomas (un partido en inglés, la 404 en portugués) y los Mundiales de 1950, 1934 y 1982, los más distintos al de 2026. Si encuentra algo, dice la regla, el elemento y un enlace que explica cómo arreglarlo:

```
  ❌ accesibilidad: abajo del todo, con el botón ↑ visible
      · region (moderate): All page content should be contained by landmarks
        https://dequeuniversity.com/rules/axe/4.12/region?application=axeAPI
        en .volver-arriba
```

Así encontró que el botón ↑ estaba suelto en el `<body>`, fuera de cualquier zona. Ahora está dentro del pie. Una herramienta automática no lo encuentra todo: por ejemplo, no sabe si un texto alternativo describe bien una imagen.

## Teclado

Hay quien no puede usar el ratón y se mueve por la web con la tecla Tab (y Mayús+Tab para volver). `probar_web.py` recorre la portada así, en el ordenador, en el móvil y a 760 px de ancho, y comprueba:
- que el primer Tab llega a **«Saltar al contenido»**, un enlace escondido que solo aparece al recibir el foco, y que al pulsarlo se salta el menú;
- que con Tab se llega a todos los enlaces, botones, campos y desplegables que se ven;
- que todos muestran el **borde dorado** al tener el foco, para saber dónde se está;
- que nada tapa ninguno de ellos, tanto hacia delante como hacia atrás: ni la cabecera fija, ni el botón ↑, ni el borde del menú. Para saberlo, mira qué elemento hay en el centro de la primera línea de cada uno (`elementFromPoint`).
- que Enter en un filtro funciona igual que pulsarlo con el ratón.

Lo hace con «menos animaciones» activado (`reduced_motion="reduce"`). Si no, la página aún se estaría desplazando cuando se mide dónde ha quedado cada cosa. Por la misma razón, antes de empezar espera a que lleguen las fuentes de Google (`document.fonts.ready`). Al llegar, los títulos cambian de alto y la página se recoloca. Sin esa espera, la prueba fallaba más o menos 1 de cada 12 veces, siempre con el filtro «Canadá» en el móvil.

Esta prueba encontró varios fallos:
- **La cabecera tapaba elementos.** En el móvil la cabecera medía 108 px, pero `scroll-padding-top` solo dejaba 72 px. Al volver hacia atrás con Mayús+Tab, 19 elementos quedaban medio tapados, y también los títulos al abrir un enlace como `/#camino`.
- **El menú cortaba enlaces.** Cuando no cabía, se deslizaba de lado. Al recorrerlo con Tab, el navegador no siempre lo desplazaba del todo, y enlaces como «Resultados» o «Quiz» quedaban medio cortados por el borde.
- **El botón ↑ tapaba los botones del tema** al llegar al final de la página en el móvil.

Cómo quedó:
- **El menú ya no se desliza:** si los enlaces no caben, bajan a otra fila.
- **En el móvil (menos de 720 px), la cabecera no es fija:** se queda arriba y se va al bajar. Con el menú en dos o tres filas, fija ocuparía casi una quinta parte de la pantalla. Para volver a ella está el botón ↑, que lleva a `#top`, el principio de todo.
- **Desde 720 px, la cabecera es fija.** Se reservan 104 px mientras el menú va en dos filas (hasta 849 px) y 72 px desde 850 px, cuando cabe en una.
- **El pie tiene sitio abajo para el botón ↑.**

## Lector de pantalla

Las personas ciegas usan un lector de pantalla (NVDA, JAWS, VoiceOver, Orca), que lee la página en voz alta. El lector no lee el HTML tal cual, sino el *árbol de accesibilidad* que construye el navegador: cada cosa con su papel (tabla, enlace, botón...) y su nombre. Playwright puede consultar ese árbol (`get_by_role()`, `aria_snapshot()`), y así `probar_web.py` comprueba lo que se **oye**, no lo que se ve.

Al revisar ese árbol salieron varias cosas que solo se entendían mirando la pantalla. Para arreglarlas se usa la clase CSS `solo-lector`, que esconde un texto de la pantalla pero deja que el lector lo lea:

| Antes se oía | Ahora se oye | Cómo |
|---|---|---|
| «tabla» | «tabla Clasificación del grupo A» | `<caption class="solo-lector">` |
| «P J», «D G», «Pts» | «Partidos jugados», «Diferencia de goles», «Puntos» | función `abreviatura()` de `app.py`: se ve «PJ» y se lee la palabra entera |
| «México» (la barra verde no se oye) | «México (clasificada)» | texto `solo-lector` |
| «V», «E» (el `title` no se lee) | «Victoria», «Empate» | `abreviatura()` |
| «zapatilla deportiva Kylian Mbappé» | «Bota de Oro: Kylian Mbappé» | `<span role="img" aria-label="Bota de Oro:">` |
| «balón de fútbol» antes de cada lista de goles | «Goles de Francia: ...» | ⚽ con `aria-hidden="true"` |
| «3' Declan Rice 0-1» (el color del punto no se oye) | «3' Declan Rice, gol para Inglaterra, 0-1» | texto `solo-lector` |
| quiz: «botón 48, no disponible» (el verde no se oye) | «botón 48 (correcta)», «botón 40 (tu respuesta, incorrecta)» | texto `solo-lector` |
| «19 jul», «EE. UU.», «1.º del grupo H» | «19 de julio», «Estados Unidos», «Primera del grupo H» | `abreviatura()` y el filtro `fecha` |
| «(pen.)», «(p.p.)», «(prór.)», «(pen. 4-3)» | «(de penalti)», «(en propia puerta)», «(tras la prórroga)», «(penaltis 4-3)» | filtro `abreviaturas` |
| «48'», «90+1'» | «minuto 48», «minuto 90 más 1» | filtro `abreviaturas` |

Los textos de los partidos («Kylian Mbappé 70' (pen.)») salen de `mundial.py` tal cual, sin HTML, y así los prueba pytest. Al pintar la página, el filtro `abreviaturas` de `app.py` busca las abreviaturas con una expresión regular (`re`) y las cambia por la versión accesible. El resto del texto lo escapa con `escape()`, para que nada de los datos se convierta en HTML.

## Pruébalo tú con NVDA

Las pruebas automáticas no saben si lo que se oye *se entiende*. Eso hay que escucharlo:
1. Instala [NVDA](https://www.nvaccess.org/download/), que es gratis, en Windows y ábrelo. Para callarlo en cualquier momento, pulsa `Ctrl`. Para salir, `Insert+Q`.
2. Abre la web en el navegador y prueba estas teclas:
   - `H` (y `Mayús+H` para volver): salta de título en título. Con `2` salta solo a los de sección.
   - `D`: salta de zona en zona (cabecera, menú, contenido, pie).
   - `T`: salta de tabla en tabla. Dentro de una tabla, `Ctrl+Alt+flechas` se mueve por las celdas y lee la columna, por ejemplo «Puntos 9».
   - `Tab`: va de enlace en enlace y de botón en botón, como la prueba de teclado.
   - `Insert+F7`: abre la lista de todos los enlaces y títulos.
3. Responde una pregunta del quiz, mira el camino de una selección y abre la línea del tiempo de un partido. ¿Se entiende todo sin mirar?
4. Si algo suena raro, apúntalo: es una idea para el siguiente paso.
