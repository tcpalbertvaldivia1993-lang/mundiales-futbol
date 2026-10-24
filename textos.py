"""Los textos de la web en portugués e inglés.

La web está escrita en español, y cada texto en español es la "llave" de su traducción:
en las plantillas, t("Campeones") da "Campeões" en portugués y "Champions" en inglés.
Si un texto no está aquí, sale en español (así nada se rompe mientras se traduce la web por partes).

Los textos pueden llevar datos entre llaves, como en str.format(): t("Los {n} Mundiales", n=23).
Los nombres de selecciones y rondas no están aquí, sino en data/nombres.json.
"""

import json
from pathlib import Path

import mundial

IDIOMAS = {"es": "Español", "pt": "Português", "en": "English"}

TEXTOS = {
    # ----- Comunes: cabecera, menú y pie -----
    "Saltar al contenido": {"pt": "Pular para o conteúdo", "en": "Skip to content"},
    "Secciones": {"pt": "Seções", "en": "Sections"},
    "Mundial": {"pt": "Copa", "en": "World Cup"},
    "Mundiales": {"pt": "Copas", "en": "World Cups"},
    "Mundial {año}": {"pt": "Copa de {año}", "en": "{año} World Cup"},
    "Inicio": {"pt": "Início", "en": "Home"},
    "Campeones": {"pt": "Campeões", "en": "Champions"},
    "Goleadores": {"pt": "Artilheiros", "en": "Top scorers"},
    "Goles": {"pt": "Gols", "en": "Goals"},
    "Selecciones": {"pt": "Seleções", "en": "Teams"},
    "Sedes": {"pt": "Sedes", "en": "Venues"},
    "Formato": {"pt": "Formato", "en": "Format"},
    "Resultados": {"pt": "Resultados", "en": "Results"},
    "Camino": {"pt": "Caminho", "en": "Path"},
    "Quiz": {"pt": "Quiz", "en": "Quiz"},
    "Proyecto de práctica hecho con Python y Flask.": {
        "pt": "Projeto de prática feito com Python e Flask.", "en": "A practice project made with Python and Flask."},
    "Datos verificados: ver": {"pt": "Dados verificados: ver", "en": "Verified data: see"},
    "las fuentes": {"pt": "as fontes", "en": "the sources"},
    "Todos los Mundiales": {"pt": "Todas as Copas", "en": "All World Cups"},
    "Tema": {"pt": "Tema", "en": "Theme"},
    "Automático": {"pt": "Automático", "en": "Automatic"},
    "Claro": {"pt": "Claro", "en": "Light"},
    "Oscuro": {"pt": "Escuro", "en": "Dark"},
    "Idioma": {"pt": "Idioma", "en": "Language"},
    "Volver arriba": {"pt": "Voltar ao topo", "en": "Back to top"},

    # ----- Gráfica de goles por partido (macros.html) -----
    "Gráfica de barras: {que} con más goles por partido es «{cual}», con {media}. Los datos están en la tabla de debajo.": {
        "pt": "Gráfico de barras: {que} com mais gols por jogo é «{cual}», com {media}. Os dados estão na tabela abaixo.",
        "en": "Bar chart: {que} with the most goals per match is “{cual}”, with {media}. The data is in the table below."},
    "Ver los datos en una tabla": {"pt": "Ver os dados em uma tabela", "en": "Show the data in a table"},
    "Partidos": {"pt": "Jogos", "en": "Matches"},
    "Por partido": {"pt": "Por jogo", "en": "Per match"},
    "{n} gol": {"pt": "{n} gol", "en": "{n} goal"},
    "{n} goles": {"pt": "{n} gols", "en": "{n} goals"},
    "{n} partido": {"pt": "{n} jogo", "en": "{n} match"},
    "{n} partidos": {"pt": "{n} jogos", "en": "{n} matches"},
    "{goles} en {partidos}": {"pt": "{goles} em {partidos}", "en": "{goles} in {partidos}"},
    "Goles por partido en cada ronda": {"pt": "Gols por jogo em cada fase", "en": "Goals per match in each round"},
    "la ronda": {"pt": "a fase", "en": "the round"},
    "Ronda": {"pt": "Fase", "en": "Round"},

    # ----- Página de inicio -----
    "Mundiales de fútbol 1930–2026": {"pt": "Copas do Mundo 1930–2026", "en": "FIFA World Cups 1930–2026"},
    "De Uruguay 1930 a Norteamérica 2026": {"pt": "Do Uruguai 1930 à América do Norte 2026",
                                            "en": "From Uruguay 1930 to North America 2026"},
    "Copa Mundial de la FIFA": {"pt": "Copa do Mundo da FIFA", "en": "FIFA World Cup"},
    "Todos los Mundiales, partido a partido y gol a gol.": {
        "pt": "Todas as Copas do Mundo, jogo a jogo e gol a gol.", "en": "Every World Cup, match by match and goal by goal."},
    "partidos": {"pt": "jogos", "en": "matches"},
    "goles": {"pt": "gols", "en": "goals"},
    "campeones": {"pt": "campeões", "en": "champions"},
    "y": {"pt": "e", "en": "and"},
    "Ver el Mundial {año}": {"pt": "Ver a Copa de {año}", "en": "See the {año} World Cup"},
    "Los {n} Mundiales": {"pt": "As {n} Copas do Mundo", "en": "The {n} World Cups"},
    "Entre 1938 y 1950 no hubo Mundial, por la Segunda Guerra Mundial.": {
        "pt": "Entre 1938 e 1950 não houve Copa, por causa da Segunda Guerra Mundial.",
        "en": "There was no World Cup between 1938 and 1950 because of the Second World War."},
    "Los Mundiales, del primero al último": {"pt": "As Copas do Mundo, da primeira à última",
                                             "en": "The World Cups, from first to last"},
    "Año": {"pt": "Ano", "en": "Year"},
    "Sede": {"pt": "Sede", "en": "Host"},
    "Campeón": {"pt": "Campeão", "en": "Champion"},
    "Los títulos de Alemania Federal (1954, 1974 y 1990) cuentan para Alemania, como hace la FIFA.": {
        "pt": "Os títulos da Alemanha Ocidental (1954, 1974 e 1990) contam para a Alemanha, como faz a FIFA.",
        "en": "West Germany's titles (1954, 1974 and 1990) count for Germany, as FIFA does."},
    "Títulos de cada selección": {"pt": "Títulos de cada seleção", "en": "Titles by team"},
    "Selección": {"pt": "Seleção", "en": "Team"},
    "Títulos": {"pt": "Títulos", "en": "Titles"},
    "Años": {"pt": "Anos", "en": "Years"},
    "Máximos goleadores de la historia": {"pt": "Maiores artilheiros da história", "en": "All-time top scorers"},
    "Goles en fases finales de los Mundiales, sin contar los de propia puerta.": {
        "pt": "Gols em Copas do Mundo, sem contar os gols contra.", "en": "Goals at World Cup finals, not counting own goals."},
    "Máximos goleadores de todos los Mundiales": {"pt": "Maiores artilheiros de todas as Copas",
                                                  "en": "Top scorers of all World Cups"},
    "Puesto": {"pt": "Posição", "en": "Rank"},
    "Jugador": {"pt": "Jogador", "en": "Player"},
    "¿En qué Mundial hubo más goles?": {"pt": "Em qual Copa houve mais gols?", "en": "Which World Cup had the most goals?"},
    "Goles por partido en cada Mundial.": {"pt": "Gols por jogo em cada Copa.", "en": "Goals per match at each World Cup."},
    "Goles por partido en cada Mundial": {"pt": "Gols por jogo em cada Copa", "en": "Goals per match at each World Cup"},
    "el Mundial": {"pt": "a Copa", "en": "the World Cup"},

    # ----- Hasta dónde llegó una selección (los textos de mundial.hasta_donde_llego, NIVELES) -----
    "🏆 Campeona del mundo": {"pt": "🏆 Campeã do mundo", "en": "🏆 World champion"},
    "🥈 Subcampeona": {"pt": "🥈 Vice-campeã", "en": "🥈 Runner-up"},
    "🥉 Tercer puesto": {"pt": "🥉 Terceiro lugar", "en": "🥉 Third place"},
    "Eliminada en semifinales": {"pt": "Eliminada nas semifinais", "en": "Lost in the semi-finals"},
    "Cuarto puesto": {"pt": "Quarto lugar", "en": "Fourth place"},
    "Eliminada en la segunda fase de grupos": {"pt": "Eliminada na segunda fase de grupos",
                                               "en": "Out in the second group stage"},
    "Eliminada en cuartos de final": {"pt": "Eliminada nas quartas de final", "en": "Lost in the quarter-finals"},
    "Eliminada en octavos de final": {"pt": "Eliminada nas oitavas de final", "en": "Lost in the round of 16"},
    "Eliminada en dieciseisavos de final": {"pt": "Eliminada nos dezesseis-avos de final", "en": "Lost in the round of 32"},
    "Eliminada en la fase de grupos": {"pt": "Eliminada na fase de grupos", "en": "Out in the group stage"},

    # ----- Las selecciones: la lista y la página de cada una -----
    "Las {n} selecciones": {"pt": "As {n} seleções", "en": "The {n} teams"},
    "Todas las que han jugado algún Mundial, de 1930 a 2026. Las que cambiaron de nombre van con el de hoy, como hace la FIFA: Alemania Federal está en Alemania, y la Unión Soviética, en Rusia.": {
        "pt": "Todas as que jogaram alguma Copa, de 1930 a 2026. As que mudaram de nome aparecem com o nome atual, como faz a FIFA: a Alemanha Ocidental está na Alemanha, e a União Soviética, na Rússia.",
        "en": "Every team that has played a World Cup, from 1930 to 2026. Teams that changed their name appear under today's name, as FIFA does: West Germany is under Germany, and the Soviet Union under Russia."},
    "Selecciones que han jugado algún Mundial": {"pt": "Seleções que jogaram alguma Copa", "en": "Teams that have played a World Cup"},
    "Mejor resultado": {"pt": "Melhor resultado", "en": "Best result"},
    "Mejor resultado: {resultado}": {"pt": "Melhor resultado: {resultado}", "en": "Best result: {resultado}"},
    "{seleccion} en los Mundiales": {"pt": "{seleccion} nas Copas do Mundo", "en": "{seleccion} at the World Cups"},
    "También jugó como {nombres}.": {"pt": "Também jogou como {nombres}.", "en": "Also played as {nombres}."},
    "título": {"pt": "título", "en": "title"},
    "títulos": {"pt": "títulos", "en": "titles"},
    "Sus Mundiales": {"pt": "Suas Copas", "en": "Its World Cups"},
    "{g}, {e} y {p}": {"pt": "{g}, {e} e {p}", "en": "{g}, {e} and {p}"},
    "{n} ganado": {"pt": "{n} vitória", "en": "{n} win"},
    "{n} ganados": {"pt": "{n} vitórias", "en": "{n} wins"},
    "{n} empatado": {"pt": "{n} empate", "en": "{n} draw"},
    "{n} empatados": {"pt": "{n} empates", "en": "{n} draws"},
    "{n} perdido": {"pt": "{n} derrota", "en": "{n} loss"},
    "{n} perdidos": {"pt": "{n} derrotas", "en": "{n} losses"},
    "{balance}; {gf} goles a favor y {gc} en contra.": {"pt": "{balance}; {gf} gols marcados e {gc} sofridos.",
                                                        "en": "{balance}; {gf} goals scored and {gc} conceded."},
    "Los partidos decididos en los penaltis cuentan como victoria o derrota (la FIFA los cuenta como empate).": {
        "pt": "Os jogos decididos nos pênaltis contam como vitória ou derrota (a FIFA os conta como empate).",
        "en": "Matches decided on penalties count as a win or a loss (FIFA counts them as draws)."},
    "{seleccion} en cada Mundial": {"pt": "{seleccion} em cada Copa", "en": "{seleccion} at each World Cup"},
    "Hasta dónde llegó": {"pt": "Até onde chegou", "en": "How far it went"},
    "PJ": {"pt": "J", "en": "P"},
    "Partidos jugados": {"pt": "Jogos disputados", "en": "Played"},
    "G": {"pt": "V", "en": "W"},
    "Ganados": {"pt": "Vitórias", "en": "Won"},
    "E": {"pt": "E", "en": "D"},
    "Empatados": {"pt": "Empates", "en": "Drawn"},
    "P": {"pt": "D", "en": "L"},
    "Perdidos": {"pt": "Derrotas", "en": "Lost"},
    "GF": {"pt": "GP", "en": "GF"},
    "Goles a favor": {"pt": "Gols pró", "en": "Goals for"},
    "GC": {"pt": "GC", "en": "GA"},
    "Goles en contra": {"pt": "Gols contra", "en": "Goals against"},
    "como {nombre}": {"pt": "como {nombre}", "en": "as {nombre}"},
    "Sus máximos goleadores": {"pt": "Seus maiores artilheiros", "en": "Its top scorers"},
    "Máximos goleadores de {seleccion} en los Mundiales": {"pt": "Maiores artilheiros de {seleccion} nas Copas",
                                                           "en": "{seleccion}'s top World Cup scorers"},
    "Contra otra selección": {"pt": "Contra outra seleção", "en": "Against another team"},
    "Elige un rival": {"pt": "Escolha um adversário", "en": "Choose an opponent"},
    "Ver partidos": {"pt": "Ver jogos", "en": "See matches"},
    "{n} partido contra {rival}": {"pt": "{n} jogo contra {rival}", "en": "{n} match against {rival}"},
    "{n} partidos contra {rival}": {"pt": "{n} jogos contra {rival}", "en": "{n} matches against {rival}"},
    "{gf}-{gc} en goles": {"pt": "{gf}-{gc} em gols", "en": "{gf}-{gc} on goals"},

    # ----- Las páginas de cada Mundial (paso 67) -----
    "Ver el camino de {seleccion}": {"pt": "Ver o caminho de {seleccion}", "en": "See {seleccion}'s path"},
    "Goles de": {"pt": "Gols de", "en": "Goals by"},
    "Línea del tiempo": {"pt": "Linha do tempo", "en": "Timeline"},
    "gol para {seleccion}": {"pt": "gol de {seleccion}", "en": "goal for {seleccion}"},
    "Goles por minuto": {"pt": "Gols por minuto", "en": "Goals by minute"},
    "Gráfica de barras: el tramo con más goles es el del {tramo}, con {goles}. Los datos están en la tabla de debajo.": {"pt": "Gráfico de barras: o intervalo com mais gols é o de {tramo}, com {goles}. Os dados estão na tabela abaixo.", "en": "Bar chart: the period with the most goals is {tramo}, with {goles}. The data is in the table below."},
    "Minutos": {"pt": "Minutos", "en": "Minutes"},
    "prórroga": {"pt": "prorrogação", "en": "extra time"},
    "Copa Mundial {año}": {"pt": "Copa do Mundo de {año}", "en": "{año} World Cup"},
    "Tres países, un solo balón.": {"pt": "Três países, uma só bola.", "en": "Three countries, one ball."},
    "selecciones": {"pt": "seleções", "en": "teams"},
    "sedes": {"pt": "sedes", "en": "venues"},
    "países": {"pt": "países", "en": "countries"},
    "Sedes y estadios": {"pt": "Sedes e estádios", "en": "Venues and stadiums"},
    "Filtrar estadios por país": {"pt": "Filtrar estádios por país", "en": "Filter stadiums by country"},
    "Todos": {"pt": "Todos", "en": "All"},
    "EE. UU.": {"pt": "EUA", "en": "USA"},
    "Mostrando {n} de {total} estadios": {"pt": "Mostrando {n} de {total} estádios", "en": "Showing {n} of {total} stadiums"},
    "{n} espectadores": {"pt": "{n} espectadores", "en": "{n} spectators"},
    "Busca una selección": {"pt": "Procure uma seleção", "en": "Search for a team"},
    "Ej.: Argentina, mexico…": {"pt": "Ex.: Argentina, mexico…", "en": "E.g. Argentina, mexico…"},
    "Buscar": {"pt": "Buscar", "en": "Search"},
    "Quitar": {"pt": "Limpar", "en": "Clear"},
    "No hay ninguna selección con ese nombre.": {"pt": "Não há nenhuma seleção com esse nome.", "en": "There is no team with that name."},
    "Las filas con barra verde son las selecciones que pasaron a la ronda siguiente. Pulsa una selección para ver su camino.": {"pt": "As linhas com barra verde são as seleções que passaram para a fase seguinte. Toque em uma seleção para ver o seu caminho.", "en": "Rows with a green bar are the teams that went through to the next round. Tap a team to see its path."},
    "Clasificación de la liguilla final": {"pt": "Classificação do quadrangular final", "en": "Final round standings"},
    "Clasificación del {grupo}": {"pt": "Classificação do {grupo}", "en": "Standings of {grupo}"},
    "DG": {"pt": "SG", "en": "GD"},
    "Diferencia de goles": {"pt": "Saldo de gols", "en": "Goal difference"},
    "Pts": {"pt": "Pts", "en": "Pts"},
    "Puntos": {"pt": "Pontos", "en": "Points"},
    "clasificada": {"pt": "classificada", "en": "qualified"},
    "Mejores terceros": {"pt": "Melhores terceiros", "en": "Best third-placed teams"},
    "De los 12 terceros de grupo pasan los 8 mejores.": {"pt": "Dos 12 terceiros colocados passam os 8 melhores.", "en": "The best 8 of the 12 third-placed teams go through."},
    "Mejores terceros: pasan los 8 primeros": {"pt": "Melhores terceiros: passam os 8 primeiros", "en": "Best third-placed teams: the top 8 go through"},
    "Grupo": {"pt": "Grupo", "en": "Group"},
    "Ghana y Ecuador empataron en puntos, diferencia de goles y goles a favor. La FIFA los desempató por juego limpio (Ghana −3, Ecuador −5), por eso Ghana aparece delante.": {"pt": "Gana e Equador empataram em pontos, saldo de gols e gols pró. A FIFA os desempatou pelo fair play (Gana −3, Equador −5), por isso Gana aparece à frente.", "en": "Ghana and Ecuador were level on points, goal difference and goals scored. FIFA separated them on fair play (Ghana −3, Ecuador −5), so Ghana is ahead."},
    "El formato nuevo": {"pt": "O novo formato", "en": "The new format"},
    "Hasta 2022": {"pt": "Até 2022", "en": "Until 2022"},
    "8 grupos de 4": {"pt": "8 grupos de 4", "en": "8 groups of 4"},
    "Pasan 16 a octavos": {"pt": "16 vão às oitavas", "en": "16 go through to the round of 16"},
    "Desde 2026": {"pt": "Desde 2026", "en": "From 2026"},
    "12 grupos de 4": {"pt": "12 grupos de 4", "en": "12 groups of 4"},
    "Pasan 32 a dieciseisavos": {"pt": "32 vão aos dezesseis-avos", "en": "32 go through to the round of 32"},
    "De cada grupo pasan los <strong>dos primeros</strong> (24 equipos) y se suman los <strong>8 mejores terceros</strong>, con lo que quedan 32. Esos 32 juegan una ronda nueva, los <strong>dieciseisavos de final</strong>, y desde ahí sigue el camino de siempre: octavos, cuartos, semifinales y final. El campeón juega 8 partidos, uno más que antes.": {"pt": "De cada grupo passam os <strong>dois primeiros</strong> (24 seleções) e somam-se os <strong>8 melhores terceiros</strong>, totalizando 32. Essas 32 jogam uma fase nova, os <strong>dezesseis-avos de final</strong>, e a partir daí segue o caminho de sempre: oitavas, quartas, semifinais e final. O campeão joga 8 partidas, uma a mais que antes.", "en": "The <strong>top two</strong> of each group (24 teams) go through, joined by the <strong>8 best third-placed teams</strong>, making 32. Those 32 play a new round, the <strong>round of 32</strong>, and from there it is the usual path: round of 16, quarter-finals, semi-finals and final. The champion plays 8 matches, one more than before."},
    "Campeón: {seleccion}": {"pt": "Campeão: {seleccion}", "en": "Champion: {seleccion}"},
    "Elegir ronda": {"pt": "Escolher fase", "en": "Choose a round"},
    "Goles de {seleccion}:": {"pt": "Gols de {seleccion}:", "en": "Goals for {seleccion}:"},
    "Penaltis {a}-{b}": {"pt": "Pênaltis {a}-{b}", "en": "Penalties {a}-{b}"},
    "Prórroga": {"pt": "Prorrogação", "en": "Extra time"},
    "Se volvió a jugar": {"pt": "Foi repetido", "en": "Replayed"},
    "Repetición": {"pt": "Repetição", "en": "Replay"},
    "Ver partido": {"pt": "Ver jogo", "en": "See match"},
    "Este Mundial no tuvo eliminatorias: el campeón fue el primero de la liguilla final.": {"pt": "Esta Copa não teve mata-mata: o campeão foi o primeiro do quadrangular final.", "en": "This World Cup had no knockout stage: the champion was the winner of the final round."},
    "Ver la liguilla final": {"pt": "Ver o quadrangular final", "en": "See the final round"},
    "Récords del Mundial": {"pt": "Recordes da Copa", "en": "World Cup records"},
    "Mayor goleada": {"pt": "Maior goleada", "en": "Biggest win"},
    "{n} goles de diferencia": {"pt": "{n} gols de diferença", "en": "{n}-goal margin"},
    "Partido con más goles": {"pt": "Jogo com mais gols", "en": "Highest-scoring match"},
    "Ningún partido": {"pt": "Nenhum jogo", "en": "No match"},
    "se decidió en los penaltis": {"pt": "foi decidido nos pênaltis", "en": "was decided on penalties"},
    "se decidieron en los penaltis": {"pt": "foram decididos nos pênaltis", "en": "were decided on penalties"},
    "se decidió en la prórroga, sin llegar a los penaltis": {"pt": "foi decidido na prorrogação, sem chegar aos pênaltis", "en": "was decided in extra time, without penalties"},
    "se decidieron en la prórroga, sin llegar a los penaltis": {"pt": "foram decididos na prorrogação, sem chegar aos pênaltis", "en": "were decided in extra time, without penalties"},
    "terminó 0-0": {"pt": "terminou 0-0", "en": "ended 0-0"},
    "terminaron 0-0": {"pt": "terminaram 0-0", "en": "ended 0-0"},
    "El camino de una selección": {"pt": "O caminho de uma seleção", "en": "A team's path"},
    "Elige una selección": {"pt": "Escolha uma seleção", "en": "Choose a team"},
    "Ver camino": {"pt": "Ver caminho", "en": "See path"},
    "1.º": {"pt": "1º", "en": "1st"},
    "2.º": {"pt": "2º", "en": "2nd"},
    "3.º": {"pt": "3º", "en": "3rd"},
    "4.º": {"pt": "4º", "en": "4th"},
    "Primera": {"pt": "Primeira", "en": "First"},
    "Segunda": {"pt": "Segunda", "en": "Second"},
    "Tercera": {"pt": "Terceira", "en": "Third"},
    "Cuarta": {"pt": "Quarta", "en": "Fourth"},
    "del grupo {grupo}": {"pt": "do grupo {grupo}", "en": "in group {grupo}"},
    "{n} partido jugado": {"pt": "{n} jogo disputado", "en": "{n} match played"},
    "{n} partidos jugados": {"pt": "{n} jogos disputados", "en": "{n} matches played"},
    "Goleadores:": {"pt": "Artilheiros:", "en": "Scorers:"},
    "No marcó ningún gol.": {"pt": "Não marcou nenhum gol.", "en": "Scored no goals."},
    "V": {"pt": "V", "en": "W"},
    "D": {"pt": "D", "en": "L"},
    "Victoria": {"pt": "Vitória", "en": "Win"},
    "Empate": {"pt": "Empate", "en": "Draw"},
    "Derrota": {"pt": "Derrota", "en": "Loss"},
    "← Volver a grupos": {"pt": "← Voltar aos grupos", "en": "← Back to groups"},
    "Comparar con otra selección →": {"pt": "Comparar com outra seleção →", "en": "Compare with another team →"},
    "{seleccion} en todos los Mundiales →": {"pt": "{seleccion} em todas as Copas →", "en": "{seleccion} at every World Cup →"},
    "{goles} goles en {partidos} partidos ({media} por partido), {propia} de ellos en propia puerta.": {"pt": "{goles} gols em {partidos} jogos ({media} por jogo), {propia} deles contra.", "en": "{goles} goals in {partidos} matches ({media} per match), {propia} of them own goals."},
    "{n} jugadores marcaron al menos uno.": {"pt": "{n} jogadores marcaram pelo menos um.", "en": "{n} players scored at least once."},
    "¿En qué minuto se marcaron?": {"pt": "Em que minuto foram marcados?", "en": "When were they scored?"},
    "¿En qué ronda hubo más goles?": {"pt": "Em qual fase houve mais gols?", "en": "Which round had the most goals?"},
    "Goles por partido.": {"pt": "Gols por jogo.", "en": "Goals per match."},
    "El tercer puesto y la final fueron un solo partido cada uno.": {"pt": "A disputa do terceiro lugar e a final foram um único jogo cada.", "en": "The third-place match and the final were one match each."},
    "La final fue un solo partido.": {"pt": "A final foi um único jogo.", "en": "The final was a single match."},
    "Goleadores del Mundial": {"pt": "Artilheiros da Copa", "en": "World Cup scorers"},
    "Bota de Oro:": {"pt": "Chuteira de Ouro:", "en": "Golden Boot:"},
    "goles:": {"pt": "gols:", "en": "goals:"},
    "Ver solo los de {n} o más goles": {"pt": "Ver só os de {n} ou mais gols", "en": "Show only those with {n} or more goals"},
    "Ver los {n} goleadores": {"pt": "Ver os {n} artilheiros", "en": "Show all {n} scorers"},
    # ----- Página de cada partido, cara a cara, 404, 500 y quiz (paso 68) -----
    "Acabó en empate y, como entonces no había tanda de penaltis, se volvió a jugar el {fecha}:": {"pt": "Terminou empatado e, como não havia disputa de pênaltis, foi repetido em {fecha}:", "en": "It ended in a draw and, as there were no penalty shoot-outs then, it was replayed on {fecha}:"},
    "ver la repetición": {"pt": "ver a repetição", "en": "see the replay"},
    "Es la repetición del empate del {fecha}:": {"pt": "É a repetição do empate de {fecha}:", "en": "It is the replay of the draw on {fecha}:"},
    "ver el primer partido": {"pt": "ver o primeiro jogo", "en": "see the first match"},
    "Partido de desempate: {a} y {b} empataron en el grupo y jugaron otra vez para decidir cuál pasaba de ronda. No cuenta en la clasificación del grupo.": {"pt": "Jogo de desempate: {a} e {b} empataram no grupo e jogaram de novo para decidir quem passava de fase. Não conta na classificação do grupo.", "en": "Play-off: {a} and {b} finished level in the group and played again to decide who went through. It does not count in the group standings."},
    "Sin goles.": {"pt": "Sem gols.", "en": "No goals."},
    "El camino de cada selección": {"pt": "O caminho de cada seleção", "en": "Each team's path"},
    "Camino de {seleccion}": {"pt": "Caminho de {seleccion}", "en": "{seleccion}'s path"},
    "Otros partidos": {"pt": "Outros jogos", "en": "Other matches"},
    "← Partido anterior": {"pt": "← Jogo anterior", "en": "← Previous match"},
    "Partido siguiente →": {"pt": "Próximo jogo →", "en": "Next match →"},
    "{a} y {b}, cara a cara": {"pt": "{a} e {b}, frente a frente", "en": "{a} and {b}, head to head"},
    "Cara a cara": {"pt": "Frente a frente", "en": "Head to head"},
    "Primera selección": {"pt": "Primeira seleção", "en": "First team"},
    "Segunda selección": {"pt": "Segunda seleção", "en": "Second team"},
    "Comparar": {"pt": "Comparar", "en": "Compare"},
    "Has elegido la misma selección dos veces.": {"pt": "Você escolheu a mesma seleção duas vezes.", "en": "You chose the same team twice."},
    "Sin fase de grupos": {"pt": "Sem fase de grupos", "en": "No group stage"},
    "Máximo goleador": {"pt": "Artilheiro", "en": "Top scorer"},
    "Nadie marcó": {"pt": "Ninguém marcou", "en": "Nobody scored"},
    "Entre ellas": {"pt": "Entre elas", "en": "Against each other"},
    "No se enfrentaron en este Mundial.": {"pt": "Não se enfrentaram nesta Copa.", "en": "They did not meet at this World Cup."},
    "Página no encontrada": {"pt": "Página não encontrada", "en": "Page not found"},
    "Error 404": {"pt": "Erro 404", "en": "Error 404"},
    "Fuera de juego": {"pt": "Impedimento", "en": "Offside"},
    "No hay ninguna página en": {"pt": "Não há nenhuma página em", "en": "There is no page at"},
    "Volver a la portada": {"pt": "Voltar ao início", "en": "Back to the home page"},
    "Error del servidor": {"pt": "Erro do servidor", "en": "Server error"},
    "Error 500": {"pt": "Erro 500", "en": "Error 500"},
    "Tarjeta roja": {"pt": "Cartão vermelho", "en": "Red card"},
    "Algo ha fallado en el servidor. No es culpa tuya: prueba otra vez en un momento.": {"pt": "Algo falhou no servidor. Não é culpa sua: tente de novo daqui a pouco.", "en": "Something went wrong on the server. It is not your fault: try again in a moment."},
    "Datos curiosos": {"pt": "Curiosidades", "en": "Fun facts"},
    "Resultado final": {"pt": "Resultado final", "en": "Final score"},
    "Has acertado {n} de {total}": {"pt": "Você acertou {n} de {total}", "en": "You got {n} out of {total}"},
    "🏆 ¡Pleno! Eres un experto del Mundial.": {"pt": "🏆 Gabaritou! Você é especialista em Copa.", "en": "🏆 Perfect score! You are a World Cup expert."},
    "¿Lo intentas otra vez?": {"pt": "Quer tentar de novo?", "en": "Want to try again?"},
    "Reintentar": {"pt": "Tentar de novo", "en": "Try again"},
    "Pregunta {n} de {total}": {"pt": "Pergunta {n} de {total}", "en": "Question {n} of {total}"},
    "tu respuesta, ": {"pt": "sua resposta, ", "en": "your answer, "},
    "correcta": {"pt": "correta", "en": "correct"},
    "incorrecta": {"pt": "incorreta", "en": "wrong"},
    "¡Correcto!": {"pt": "Correto!", "en": "Correct!"},
    "No era esa.": {"pt": "Não era essa.", "en": "That wasn't it."},
    "Siguiente": {"pt": "Próxima", "en": "Next"},
    "Ver resultado": {"pt": "Ver resultado", "en": "See score"},
}

# ===== Abreviaturas, en cada idioma =====
# Se ve la forma corta y el lector de pantalla lee la larga (app.py, filtro abreviaturas)
ABREVIATURAS = {
    "es": {"(pen.)": "(de penalti)", "(p.p.)": "(en propia puerta)", "(prór.)": "(tras la prórroga)"},
    "pt": {"(pên.)": "(de pênalti)", "(g.c.)": "(gol contra)", "(prorr.)": "(após a prorrogação)"},
    "en": {"(pen.)": "(penalty)", "(o.g.)": "(own goal)", "(a.e.t.)": "(after extra time)"},
}
# Las marcas de los goles que pone mundial.py (en español): "Kane 30' (pen.)", "Pepe 10' (p.p.)"
MARCAS_GOL = {"pt": {" (pen.)": " (pên.)", " (p.p.)": " (g.c.)"},
              "en": {" (p.p.)": " (o.g.)"}}  # en inglés, "(pen.)" es igual
# Los meses: la forma corta, que se ve, y la larga, que lee el lector de pantalla
MESES = {
    "es": (["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"],
           ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]),
    "pt": (["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
           ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro"]),
    "en": (["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
           ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"]),
}
# La marca de un partido que se decidió en la prórroga
PRORROGA = {"es": "(prór.)", "pt": "(prorr.)", "en": "(a.e.t.)"}
# Una tanda de penaltis: la forma corta y la larga ("(pen. 4-3)" se lee "(penaltis 4-3)")
TANDA = {"es": ("(pen. {}-{})", "(penaltis {}-{})"),
         "pt": ("(pên. {}-{})", "(pênaltis {}-{})"),
         "en": ("(pens {}-{})", "(penalties {}-{})")}
# Un minuto, como lo lee el lector de pantalla: "48'" -> "minuto 48", "90+1'" -> "minuto 90 más 1"
MINUTO = {"es": ("minuto {}", "minuto {} más {}"),
          "pt": ("minuto {}", "minuto {} mais {}"),
          "en": ("minute {}", "minute {} plus {}")}
# Las marcas de los partidos especiales (en español están en mundial.py, NOTAS_PARTIDO)
NOTAS_PARTIDO = {
    "pt": {"repetido": " (jogo repetido)", "repeticion": " (repetição)", "desempate": " (desempate)"},
    "en": {"repetido": " (replayed)", "repeticion": " (replay)", "desempate": " (play-off)"},
}

# Los nombres de selecciones y rondas: {"Brasil": {"pt": "Brasil", "en": "Brazil"}, ...}
_datos = json.loads((Path(__file__).resolve().parent / "data" / "nombres.json").read_text(encoding="utf-8"))
NOMBRES = _datos["selecciones"] | _datos["rondas"] | _datos["ciudades"]


def traducir(texto, idioma, **datos):
    """El texto en ese idioma, con los datos puestos: traducir("Los {n} Mundiales", "en", n=23) -> "The 23 World Cups"."""
    if idioma != "es":
        texto = TEXTOS.get(texto, {}).get(idioma, texto)
    return texto.format(**datos) if datos else texto


# Los grupos: "Grupo A" y "Grupo A (segunda fase)"
GRUPO = {"pt": ("Grupo {}", " (segunda fase)"), "en": ("Group {}", " (second stage)")}


def nombre(texto, idioma):
    """El nombre de una selección, una ronda o un grupo en ese idioma: nombre("Brasil", "en") -> "Brazil",
    nombre("Grupo A (segunda fase)", "en") -> "Group A (second stage)".
    Lo que no está en data/nombres.json (jugadores, estadios, años) se queda igual."""
    if idioma == "es":
        return texto
    if texto in NOMBRES:
        return NOMBRES[texto][idioma]
    if isinstance(texto, str) and texto.startswith("Grupo "):
        letra, segunda, _ = texto.removeprefix("Grupo ").partition(" (segunda fase)")
        return GRUPO[idioma][0].format(letra) + (GRUPO[idioma][1] if segunda else "")
    return texto


def texto_partido(p, idioma):
    """ "Italia 1-1 España (prór.)" en el idioma elegido: "Italy 1-1 Spain (a.e.t.)".
    En español es el de mundial.texto_partido(), que es el original."""
    if idioma == "es":
        return mundial.texto_partido(p)
    texto = f"{nombre(p['local'], idioma)} {p['golesLocal']}-{p['golesVisitante']} {nombre(p['visitante'], idioma)}"
    if p.get("penaltis"):
        texto += " " + TANDA[idioma][0].format(*p["penaltis"])
    elif p.get("prorroga"):
        texto += " " + PRORROGA[idioma]
    return texto + "".join(nota for clave, nota in NOTAS_PARTIDO[idioma].items() if p.get(clave))
