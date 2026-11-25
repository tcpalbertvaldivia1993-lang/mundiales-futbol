---
name: ver
description: Abre una página de la web en español, portugués e inglés, en móvil y escritorio y en tema claro y oscuro, hace capturas y revisa el scroll, la consola y los enlaces. Usar para ver cómo queda un cambio.
argument-hint: "<página, por ejemplo /seleccion/Alemania#goleada>"
---

Página que hay que ver: `$ARGUMENTS`

Si no se ha dado ninguna, usa las páginas que toca el cambio actual (`git diff` y la rama); si no hay cambios, pregunta cuál. Con `#seccion` se captura solo esa sección: úsalo siempre que el cambio esté en una, porque las capturas se cortan a 3000 px de alto.

1. Crea una carpeta temporal **fuera del repositorio** para las capturas (la de la sesión, si la hay).
2. `venv/bin/python .claude/skills/ver/ver.py '<página>' <carpeta>`
   Arranca la web y la cierra al terminar. Si hay varias páginas, lánzalo una vez por cada una, con su carpeta.
3. Mira con Read, como mínimo, `es-movil-oscuro.png`, `es-escritorio-claro.png`, `pt-movil-claro.png` y `en-movil-oscuro.png`. Mira también las demás si algo parece raro.
4. Cuenta lo que se ve: textos cortados o sin traducir, cosas que se salen o se solapan, poco contraste. Añade cada ❌ del script y la ruta completa de la carpeta.

Elige también un caso raro si el cambio lo tiene (una selección sin victorias, 1934 sin grupos, 1950 sin final). Un ❌ de «no existe la sección» puede ser lo correcto en esos casos: dilo. Esto no sustituye a `/probar`.
