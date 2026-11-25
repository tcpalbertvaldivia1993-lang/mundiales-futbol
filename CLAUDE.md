# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Flask site about every men's World Cup (1930–2026), fully server-rendered with **no JavaScript at all**. Code, comments, names (including variables: `año`, `partidos`), tests and documentation are in Spanish; comments explain the why. This is the public copy of a private repository: Render deploys from the private one, and the `probar-render.yml` workflow and Dependabot config mentioned in the docs are not here.

## Commands

The virtual environment must be `venv/` (the `pre-push` hook looks for that name). Python 3.14 (`.python-version`).

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt -r requirements-dev.txt
venv/bin/python -m playwright install chromium      # once, for the browser tests
git config core.hooksPath .githooks                 # once, enables the pre-push hook

venv/bin/flask --app app run --debug                # http://127.0.0.1:5000

venv/bin/python -m pytest                           # logic and routes
venv/bin/python -m pytest --cov-fail-under=100      # what GitHub Actions and pre-push require
venv/bin/python -m pytest --no-cov pruebas/test_app.py::test_la_portada_carga   # a single test
venv/bin/python -m pytest --no-cov -k quiz          # tests with "quiz" in their name
venv/bin/python pruebas/probar_web.py               # browser (Playwright + axe); starts Flask itself
CANAL_NAVEGADOR=chrome venv/bin/python pruebas/probar_web.py   # with the system Chrome, as on GitHub
```

- Coverage of `app.py`, `mundial.py` and `textos.py` must be **100% including branches**: every new `if` needs tests for both paths.
- `probar_web.py` is not a pytest file (it is a script using `comprobar(...)`, and cannot be run partially) and needs internet access for Google Fonts. There is no linter.
- Data is read once, when `app` is imported: restart Flask after editing a JSON file (`--debug` only reloads on Python changes).

## Architecture

Three modules: `mundial.py` (pure logic, never imports Flask), `textos.py` (translations) and `app.py` (routes, filters and Jinja globals). Nothing is computed in templates if it can live in `mundial.py`.

**Data → one `m` dictionary per World Cup.** `cargar()` reads the individual 2026 JSON files in `data/`, and `cargar_historico(año)` reads `data/historicos/<año>.json`. Both end in `completar()`, which adds everything common (goals per match, records, charts, numbering…), so templates see the same shape for all of them. Differences: the 2026 standings are computed, while historical ones come in the JSON (with the points system of their era); only 2026 has the quiz, the format section and best third-placed teams. `cargar_historia()` and `historial()` compute what spans several World Cups (home page and `/seleccion/<nombre>`).

- A match is identified by `clave_partido()` (date, home, away), also from its goals. Its number in the URL is its position by date in `todos_los_partidos`, so reordering matches changes URLs.
- An own goal (`tipo: "propia"`) carries the **player's** team and counts for the opponent.
- `completar()` raises `ValueError` at startup if scorers do not add up to the scorelines.
- Odd cases any change must handle: 1934 and 1938 have no groups (and have replayed matches, where `ganador_de()` is `None`), 1950 has no final and no rounds (final round-robin group), 1954/1958 have play-offs that don't count in the table, 1974–1982 have a second group stage.
- `SUCESORAS`/`actual()` merge teams that changed name (Alemania Federal → Alemania); within a single World Cup the name of the era is kept.
- `data/historicos/` is generated: never edit it by hand; change `herramientas/importar_historicos.py` or `herramientas/traducciones.json` and run the script again (it downloads a pinned commit of the Fjelstul database, CC BY-SA 4.0). Data sources are recorded in `data/fuentes.md`, which the site serves at `/fuentes`.

**The year in routes.** World Cup routes start with `/<int:anio>/`, but their functions don't receive `anio`: `url_value_preprocessor` moves it to `g.anio` (404 if there is no such World Cup), `datos()` returns the matching `m`, and `url_defaults` puts it back into every `url_for()`. To link to a different World Cup, pass `anio=` explicitly (`enlace_partido_de`). Old routes without a year redirect (301/308) and must be kept.

**State lives in the URL.** Filters, round, team, expanded player, open timeline (`?linea=`)… are parameters; `enlace(seccion, clave=valor)` builds the current URL with changes and keeps the rest, and the `ocultos` macro does the same in GET forms. An unknown parameter value must never break the page: the default is used. Only the quiz, theme and language use the session, through POST forms + redirect; the cookie must not be created for someone who only browses. To go back to the originating page use `volver_a()`, which prevents open redirects.

**Templates.** `base.html` (menu, footer) → `index.html`, which includes the `secciones/` depending on what `m` has; the same conditions are repeated in the `base.html` menu. Macros are always imported with `{% import "macros.html" as macros with context %}`. Charts are SVG drawn in Jinja, with an accessible summary and table. Link to `static/` with `estatico()` (content hash, one-year cache).

**Languages (es, pt, en).** The Spanish text is the key: `t("Los {n} Mundiales", n=23)` looks it up in `TEXTOS` in `textos.py`; teams, rounds and cities use `| nombre` and live in `data/nombres.json`.

- Every new literal `t("...")` needs `pt` and `en`, with the same `{}` placeholders; if the text reaches `t()` through a variable, also add it to the list in `test_textos.py`, because the automatic test only sees literals.
- Don't name a variable `t` in a template, or `nombre` in `app.py`: they shadow the functions.
- `mundial.py` always returns Spanish. Texts translated later depend on exact matches: `NIVELES` ↔ `hasta_donde_llego()` ↔ `TEXTOS`; `MARCAS` ↔ `textos.MARCAS_GOL`; `NOTAS_PARTIDO` in both modules.
- Logic works with the Spanish names, and translation happens only when rendering. Alphabetical lists are sorted by the translated name.
- Functions with `@cache` (`abreviatura`, `abreviaturas_en`) receive the language or the already translated text as an argument; they must not read `idioma_elegido()` inside or receive text typed by visitors.

## Constraints enforced by tests

- **CSP** (`app.py`): `script-src 'none'`, no `<style>` blocks (`style=` attributes are allowed) and no external resources except Google Fonts.
- **Accessibility:** axe-core, keyboard traversal (nothing hidden under the header, visible focus) and what a screen reader hears. Write short forms with `abreviatura()`, `| abreviaturas` or `| fecha`, and screen-reader-only text with the `solo-lector` class.
- **Light theme:** its colors appear twice in `styles.css` (`@media` and `[data-tema="claro"]`); change both.
- **Quiz:** a new question in `data/quiz.json` includes `pt` and `en`, and its answer is added, in the same order, to `test_las_respuestas_del_quiz_cuadran_con_los_datos`.
- **Historical data:** the figures in `CONOCIDOS` (`test_historicos.py`) were written down before importing; don't adjust them to fit the data.
- In `probar_web.py`, open pages with `nueva_pagina()` (it sets `es-ES`): the site follows the browser language, and GitHub's Chrome is in English.

More detail in `README.md` and `docs/` (testing, accessibility, speed, security, deployment). Some README statements are outdated: the `~/mundial-2026` folder, and that the site "doesn't use" `data/historicos/` yet (it does).
