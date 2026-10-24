# Fuentes de los datos

Datos comprobados el 19 de octubre de 2026.

- **Estadios y aforos** (`estadios.json`): [2026 FIFA World Cup, Wikipedia](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup), sección "Venues". Los aforos son los que publica la FIFA para el torneo y pueden no coincidir con el aforo habitual del estadio.
- **Grupos** (`grupos.json`): misma página de Wikipedia, sección "Group stage". El sorteo se hizo el 5 de diciembre de 2025 en Washington D. C. Los grupos se contrastaron con [N+](https://www.nmas.com.mx/deportes/grupos-mundial-2026-como-quedo-sorteo-lista-completa-12-a-l-equipos/) y [NTN24](https://www.ntn24.com/noticias-deportes/asi-quedaron-los-grupos-del-mundial-sin-italia-y-sin-bolivia-tras-confirmarse-las-ultimas-seis-selecciones-clasificadas-614988), que incluyen a los clasificados por repesca, como Chequia en el grupo A.
- **Formato** (dieciseisavos, 8 mejores terceros): Wikipedia, sección "Format".
- **Partidos de la fase de grupos** (`partidos-grupos.json`): las páginas de Wikipedia de cada grupo, de [Group A](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A) a [Group L](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_L).
  - Contrastados con las tablas de clasificación de [Wikipedia](https://en.wikipedia.org/wiki/Template:2026_FIFA_World_Cup_group_tables): las 48 filas coinciden en ganados, empatados, perdidos y goles.
  - Contrastados también con prensa, por muestreo:
    - Sudáfrica 1-0 Corea del Sur: [El Gráfico](https://elgrafico.com.ar/articulo/mundial-2026/100923/historico-sudafrica-sorprendio-a-corea-del-sur-y-paso-la-fase-de-grupos-por-primera-vez).
    - Nueva Zelanda 1-5 Bélgica: [Semanario Universidad](https://semanariouniversidad.com/deportes/belgica-y-egipto-clasifican-nueva-zelanda-fuera/).
    - Ecuador 2-1 Alemania: [El Comercio](https://www.elcomercio.com/deportes/futbol/tabla-posiciones-mejores-terceros-mundial/).
  - El desempate por juego limpio entre Ghana y Ecuador (`juegoLimpio`) sale de la nota de la tabla de terceros de Wikipedia. No lo he encontrado en otra fuente.
- **Partidos por estadio** (sección de sedes): no son un dato nuevo. Se calculan juntando `partidos-grupos.json` y `resultados.json`.
  - El total es 104.
  - Se contrastaron con prensa varios recuentos: Houston 7 y Guadalajara 4 ([beIN Sports](https://prod.beinsports.com/es-us/football/copa-mundial-de-la-fifa-2026/articles/todos-los-estadios-de-la-copa-mundial-de-la-fifa-2026-sedes-capacidad-y-partidos-de-la-copa-del-mundo-2026-05-13)), y Atlanta 8 y Monterrey 4 ([Los Tiempos](https://www.lostiempos.com/deportes/futbol-int/20260510/todos-estadios-del-mundial-2026-sedes-capacidad-datos-clave)).
- **Goleadores** (`goleadores.json`): la [página de datos de goleadores de Wikipedia](https://en.wikipedia.org/wiki/Module:Goalscorers/data/2026_FIFA_World_Cup), que cita las estadísticas de jugadores de la FIFA.
  - 178 jugadores marcaron 294 goles, y hubo 14 goles en propia puerta. En total son 308, los mismos que suman los marcadores de los 104 partidos.
  - Comprobado selección por selección: los goles de sus jugadores, más los goles en propia puerta a su favor, coinciden con sus goles en los partidos en las 48 selecciones.
  - La tabla final de máximos goleadores se contrastó con [Noticias Caracol](https://www.noticiascaracol.com/golcaracol/como-quedo-la-tabla-de-goleadores-del-mundial-2026-luego-de-que-messi-pasara-en-blanco-en-la-final-rg10): Mbappé 10, Messi 8, Haaland 7, Bellingham 7, Kane 6 y Dembélé 6.
- **Goles de cada partido** (`goles.json`): los goleadores y minutos de las fichas de los partidos en Wikipedia. Son las páginas de cada grupo, [round of 32](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_round_of_32), [knockout stage](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage) y [final](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_final).
  - Son 308 goles, sin ningún error en las comprobaciones: en los 104 partidos, los goles coinciden con el marcador; en los 178 jugadores, con `goleadores.json`; y los 14 goles en propia puerta también coinciden.
  - Los goles de la semifinal Inglaterra-Argentina (Gordon, Enzo Fernández y Lautaro Martínez) y de la final (Ferran Torres, en la prórroga) se contrastaron con prensa. El minuto exacto puede variar un minuto según la fuente.
- **Resultados de eliminatorias** (`resultados.json`): cuadro de [2026 FIFA World Cup knockout stage, Wikipedia](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage), sección "Bracket". Contrastados con:
  - Final, España 1-0 Argentina en la prórroga: [Cubanet](https://www.cubanet.org/espana-se-corona-campeona-del-mundial-2026-tras-vencer-a-argentina/) y [RCN Radio](https://newsroom.rcnradio.com/actualidad/quien-gano-el-mundial-2026-final-argentina-espana).
  - Semifinal Inglaterra 1-2 Argentina: [La Nación](https://www.lanacion.com.ar/deportes/canchallena/argentina-vencio-2-1-a-inglaterra-por-el-mundial-2026-nid15072026/).
  - Semifinal Francia 0-2 España y tercer puesto Francia 4-6 Inglaterra: [CNN en Español](https://cnnespanol.cnn.com/category/francia/).

## Mundiales de 1930 a 2022 (`historicos/`)

Los 22 Mundiales anteriores salen de **The Fjelstul World Cup Database v1.2.0**, © 2023 Joshua C. Fjelstul, Ph.D., <https://www.github.com/jfjelstul/worldcup>, con licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Se usa la versión de GitHub (commit `35a8667`), no la de WorldCups.ai, que tiene otra licencia.

Por esa licencia, **los archivos de `historicos/` también tienen licencia CC BY-SA 4.0**: se pueden usar y cambiar citando la fuente y manteniendo la misma licencia.

Los crea `herramientas/importar_historicos.py`. Cambios hechos a la base de datos:

- Solo los Mundiales masculinos, y solo partidos, goles, clasificaciones de grupo, estadios y datos de cada Mundial.
- Selecciones, rondas y algunas ciudades traducidas al español (`herramientas/traducciones.json`), con los mismos nombres que los datos de 2026 (por ejemplo, «Arabia Saudí»). Los estadios conservan su nombre.
- La forma de los datos es la de los JSON de 2026: un archivo por Mundial, con grupos, rondas y goles.
- Los grupos se unen a su clasificación por las selecciones que los jugaron. Así, la segunda fase de 1982 se llama A, B, C y D, como en las clasificaciones de la base, y no 1, 2, 3 y 4, como en sus partidos.
- Marcas añadidas: `desempate` en los partidos de desempate de grupo de 1954 y 1958, que no cuentan en la clasificación. `repetido` y `repeticion` salen de la base.

Comprobaciones (`pruebas/test_historicos.py`):

- Partidos, goles y campeón de cada Mundial coinciden con las cifras conocidas, apuntadas antes de importar. Por ejemplo, 18 partidos y 70 goles en 1930, y 64 partidos y 172 goles en 2022.
- En todos los partidos, los goles coinciden con el marcador, y en todos los grupos, la clasificación coincide con sus partidos.
- Los 5 desempates de 1954 y 1958 son los históricos.
