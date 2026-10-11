"""QA funcional del Dashboard (§2): señales, enjambre, mapa CARTO y ventana del inspector.

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_dashboard.py [http://127.0.0.1:5050]
Guarda capturas `dashboard-pop-*.png` y termina con código 1 si alguna comprobación falla.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
OUT = Path(__file__).parent
results = []


def check(name, condition, detail=''):
    results.append((bool(condition), name, detail))


def open_dashboard(browser, market, theme='claro', width=1440, height=900):
    ctx = browser.new_context(viewport={'width': width, 'height': height})
    ctx.add_init_script(f"try{{localStorage.setItem('atlas.theme','{theme}');localStorage.setItem('atlas.sidebar','expandida');}}catch(e){{}}")
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    mock_side_effects(page)
    page.goto(f'{BASE}/#dashboard')
    page.wait_for_selector('.dash-grid')
    if page.evaluate('State.targetId') != market:
        page.click('#marketBtn')
        page.click(f'.market-menu__item[data-market="{market}"]')
        page.wait_for_selector('.dash-grid')
    page.wait_for_selector('[data-dash-pin]', timeout=20000)
    page.wait_for_timeout(1500)
    return ctx, page, errors


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--explicitly-allowed-ports=5050,5060,5061,5070,8001"])

    # ---------------- mercado 2: tiene movimiento, 6 señales y nuevos
    ctx, page, errors = open_dashboard(browser, 2)
    signals = page.locator('.dash-signal')
    check('3 señales por defecto', signals.count() == 3, str(signals.count()))
    toggle = page.locator('[data-dash-signals]')
    check('enlace «Ver las 6 señales»', toggle.inner_text().strip() == 'Ver las 6 señales', toggle.inner_text())
    toggle.click()
    check('al ampliar se ven 6', page.locator('.dash-signal').count() == 6)
    check('el enlace pasa a «Ver menos»', page.locator('[data-dash-signals]').inner_text().strip() == 'Ver menos')
    check('recuento atención/lectura', 'requieren atención' in page.locator('.dash-signals__count').inner_text(), page.locator('.dash-signals__count').inner_text())
    first_level = page.locator('.dash-signal__level').first.inner_text().strip().upper()
    check('las de atención van primero', first_level == 'ATENCIÓN', first_level)
    page.locator('[data-dash-signals]').click()
    check('«Ver menos» vuelve a 3', page.locator('.dash-signal').count() == 3)

    move = page.locator('.dash-move').inner_text()
    check('movimiento ADR con signo', move.startswith('+') or move.startswith('−'), move)
    check('pie de movimiento ▲▼', '▲' in page.locator('.dash-card--move .dash-foot').first.inner_text())
    check('11 hoteles fuera del centro', page.locator('.dash-outlier').count() == 11, str(page.locator('.dash-outlier').count()))
    check('3 tramos en la curva', page.locator('.dash-curve__row').count() >= 1, str(page.locator('.dash-curve__row').count()))

    # enjambre: tooltip al pasar el cursor
    dot = page.locator('.dash-swarm__dot').nth(5)
    dot.hover()
    tip = page.locator('#dashSwarmTip')
    expect(tip).to_be_visible()
    check('tooltip del enjambre con nombre y precio', '€' in tip.inner_text(), tip.inner_text())
    page.locator('.dash-card--count').hover()
    expect(tip).to_be_hidden()
    check('el tooltip se oculta al salir', True)

    # mapa: pins sin position inline en la raíz del marcador
    roots = page.locator('.maplibregl-marker')
    check('hay marcadores', roots.count() > 10, str(roots.count()))
    inner_ok = page.locator('.maplibregl-marker > .map-pin').count() == roots.count()
    check('cada marcador envuelve su contenido en .map-pin', inner_ok)
    pin_pos = page.eval_on_selector('.map-pin', 'el => getComputedStyle(el).position')
    check('.map-pin con position:relative', pin_pos == 'relative', pin_pos)

    # ventana del inspector
    pin = page.locator('[data-dash-pin]').nth(3)
    pin.dispatch_event('click')
    pop = page.locator('#dashPop')
    expect(pop).to_be_visible()
    check('ventana con role=dialog', pop.get_attribute('role') == 'dialog')
    check('kicker «Inspector de tarifa · puesto N de M»', 'puesto' in page.locator('.dash-pop__kicker').first.inner_text().lower())
    check('punto seleccionado ×1.45', 'is-selected' in (pin.get_attribute('class') or ''))
    expect(page.locator('#dashPopChart svg')).to_be_visible(timeout=10000)
    check('gráfica por extracción cargada', page.locator('#dashPopChart .dash-pop__pt').count() >= 1)
    frame_box = page.locator('#dashMapFrame').bounding_box()
    pop_box = pop.bounding_box()
    check('la ventana cabe en el mapa', pop_box['x'] >= frame_box['x'] and pop_box['x'] + pop_box['width'] <= frame_box['x'] + frame_box['width'] + 1
          and pop_box['y'] >= frame_box['y'] - 1, f'{pop_box} dentro de {frame_box}')
    check('línea discontinua y anillo', page.locator('#dashPopLine').count() == 1 and page.locator('#dashPopRing').count() == 1)
    legend = page.locator('.dash-pop__legend').inner_text()
    check('el inspector identifica la última extracción', 'Última extracción' in legend, legend)
    point = page.locator('#dashPopChart .dash-pop__pt').first
    point.hover()
    readout = page.locator('.dash-pop__readout').inner_text()
    check('lectura por fecha de estancia y tarifa', 'última' in readout and '€' in readout, readout)
    page.screenshot(path=str(OUT / 'dashboard-pop-dates-1440.png'))

    # sigue al punto al mover el mapa
    before = pop.bounding_box()
    ring_before = page.locator('#dashPopRing').bounding_box()
    page.locator('.maplibregl-ctrl-zoom-in').click()  # acercar mueve el punto en pantalla
    page.wait_for_timeout(900)
    ring_after = page.locator('#dashPopRing').bounding_box()
    check('el anillo sigue al punto al mover el mapa', abs(ring_after['x'] - ring_before['x']) > 20, f"{ring_before['x']} → {ring_after['x']}")

    page.keyboard.press('Escape')
    expect(page.locator('#dashPop')).to_have_count(0)
    check('Esc cierra la ventana', True)
    check('se quita la selección del punto', page.locator('[data-dash-pin].is-selected').count() == 0)

    # tema oscuro: setStyle a dark-matter sin recargar marcadores
    markers_before = page.locator('.maplibregl-marker').count()
    page.click('#themeBtn')
    page.wait_for_timeout(1500)
    check('los marcadores siguen tras cambiar de tema', page.locator('.maplibregl-marker').count() == markers_before)
    canvas_filter = page.eval_on_selector('.maplibregl-canvas', 'el => getComputedStyle(el).filter')
    check('sin filtro CSS en el mapa oscuro', canvas_filter in ('none', ''), canvas_filter)
    page.screenshot(path=str(OUT / 'dashboard-map-oscuro-1440.png'))
    page.click('#themeBtn')

    # «Ver hotel» desde una señal abre la hoja con el hotel buscado
    open_btn = page.locator('.dash-signal__open').first
    name = open_btn.get_attribute('data-dash-hotel')
    open_btn.click()
    expect(page.locator('#hotelSearch')).to_have_value(name)
    check('«Ver hotel» abre la hoja con el hotel buscado', True, name)
    check('sin errores de consola (mercado 2)', not errors, '; '.join(errors[:3]))
    ctx.close()

    # ---------------- mercado 1: sin movimiento comparable
    ctx, page, errors = open_dashboard(browser, 1)
    check('mercado 1 · movimiento sin comparativa', page.locator('.dash-move').inner_text().strip() == '—')
    check('mercado 1 · sin enlace de ampliar con ≤3 señales', page.locator('[data-dash-signals]').count() == (1 if page.locator('.dash-signal').count() > 3 else 0))
    page.locator('[data-dash-pin]').first.dispatch_event('click')
    expect(page.locator('#dashPop')).to_be_visible()
    page.locator('[data-dash-close]').click()
    expect(page.locator('#dashPop')).to_have_count(0)
    check('× cierra la ventana', True)
    check('sin errores de consola (mercado 1)', not errors, '; '.join(errors[:3]))
    ctx.close()

    # ---------------- 1366: la ventana pasa a una columna si no cabe
    ctx, page, errors = open_dashboard(browser, 2, width=1366, height=768)
    page.locator('[data-dash-pin]').nth(2).dispatch_event('click')
    expect(page.locator('#dashPop')).to_be_visible()
    page.wait_for_timeout(500)
    box = page.locator('#dashPop').bounding_box()
    frame_box = page.locator('#dashMapFrame').bounding_box()
    check('1366 · la ventana no se sale del mapa', box['x'] + box['width'] <= frame_box['x'] + frame_box['width'] + 1, f'{box} / {frame_box}')
    page.screenshot(path=str(OUT / 'dashboard-pop-1366.png'))
    check('sin errores de consola (1366)', not errors, '; '.join(errors[:3]))
    ctx.close()
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
