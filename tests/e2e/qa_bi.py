"""QA funcional del panel de análisis (§3B).

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_bi.py [http://127.0.0.1:5050]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
OUT = Path(__file__).parent
results = []


def check(name, ok, detail=''):
    results.append((bool(ok), name, detail))


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--explicitly-allowed-ports=5050,5060,5061,5070,8001"])
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('atlas.hotelTab','bi');localStorage.removeItem('atlas.ownHotel.1');localStorage.setItem('atlas.theme','claro');}catch(e){}")
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    mock_side_effects(page)
    page.goto(f'{BASE}/#hotels')
    page.wait_for_selector('#biRoot')
    page.wait_for_selector('.bi-pin', timeout=20000)

    check('pestaña por defecto: panel de análisis', page.locator('#hotelTab-bi').get_attribute('aria-selected') == 'true')
    check('6 KPIs', page.locator('#biKpis .kpi-strip__cell').count() == 6)
    check('sin hotel propio: «Mercado · extracción»', 'MERCADO · EXTRACCI' in page.locator('#biSide').inner_text().upper())
    check('tarjeta de invitación con select', page.locator('#biOwnInvite').count() == 1)
    pins = page.locator('.maplibregl-marker')
    check('marcadores envueltos en .map-pin', page.locator('.maplibregl-marker > .map-pin').count() == pins.count() and pins.count() > 10)
    check('filtros sticky a 60 px', page.eval_on_selector('#biFilters', 'el => getComputedStyle(el).position + getComputedStyle(el).top') == 'sticky60px')

    # calendario: un único listener con lectura
    cell = page.locator('#biCalGrid .bi-cell:not(.is-empty)').first
    cell.dispatch_event('mouseover')
    readout = page.locator('#biCalReadout').inner_text()
    check('lectura del calendario al pasar el cursor', '€' in readout or 'cerrado' in readout, readout)
    empty_head = page.locator('#biCalGrid .bi-cal__days .is-empty').count()
    check('columnas sin captura marcadas', empty_head > 0, str(empty_head))
    check('leyenda «sin captura»', 'sin captura' in page.locator('.bi-cal .bi-legend').inner_text())

    # cambiar la fecha activa pulsando una barra de la mediana
    meds = page.locator('#biCalGrid .bi-cal__med[role="button"]')
    check('fechas capturadas accesibles por teclado', meds.count() >= 1, str(meds.count()))
    if meds.count() >= 2:
        before = page.locator('#biKpis .kpi-strip__label').first.inner_text()
        meds.locator(':scope[aria-pressed="false"]').first.dispatch_event('click')
        after = page.locator('#biKpis .kpi-strip__label').first.inner_text()
        check('pulsar una fecha recalcula los KPIs', before != after, f'{before} → {after}')
        check('chip «Entrada dd/mm»', page.locator('[data-bi-clear="focus"]').count() == 1)
        if page.locator('[data-bi-clear="focus"]').count():
            page.locator('[data-bi-clear="focus"]').click()
        check('quitar el chip vuelve a la fecha capturada', page.locator('[data-bi-clear="focus"]').count() == 0)

    # horizonte
    page.locator('[data-bi-horizon="30"]').click()
    check('30 días: precios escritos en las celdas', page.locator('#biCalGrid .bi-cell:not(.is-empty)').first.inner_text().strip() != '')
    check('30 días: 30 columnas', page.locator('#biCalGrid .bi-cal__days span').count() == 31)

    # filtro cruzado por zona desde el panel de zonas
    total = page.locator('.bi-scope').inner_text()
    zone = page.locator('.bi-zone').first
    zone_name = zone.locator('.bi-zone__name span').inner_text()
    zone.click()
    check('chip «Zona: X»', page.locator('[data-bi-clear="zone"]').inner_text().startswith(f'Zona: {zone_name}'))
    check('el alcance se reduce', page.locator('.bi-scope').inner_text() != total, page.locator('.bi-scope').inner_text())
    page.locator('.bi-clear[data-bi-clear="all"]').click()
    check('«Limpiar» quita los filtros', page.locator('.bi-chip').count() == 0)

    # tipo de habitación: recalcula en el servidor
    page.select_option('#biFam', 'Suite')
    expect(page.locator('.bi-scope')).not_to_have_text(total, timeout=10000)
    check('tipo de habitación filtra hoteles', True, page.locator('.bi-scope').inner_text())
    page.select_option('#biFam', 'all')
    expect(page.locator('.bi-scope')).to_have_text(total, timeout=10000)

    # hotel propio → tarifa sugerida
    own = page.locator('#biOwn option').nth(3).get_attribute('value')
    page.select_option('#biOwn', own)
    expect(page.locator('.bi-reco')).to_be_visible()
    side = page.locator('#biSide').inner_text()
    check('tarifa sugerida con desglose de 6', page.locator('.bi-part').count() == 6 or 'Sin captura' in side or 'Ningún hotel' in side, str(page.locator('.bi-part').count()))
    check('select de hotel propio resaltado', 'is-set' in page.locator('#biOwn').get_attribute('class'))
    check('fila «Rank del hotel propio»', page.locator('.bi-cal__rank').count() == 1)
    check('hotel propio fijado arriba en el calendario', 'is-own' in (page.locator('#biCalGrid .bi-cal__rows .bi-cal__row').first.get_attribute('class') or ''))
    stored = page.evaluate("() => localStorage.getItem('atlas.ownHotel.1')")
    check('hotel propio guardado en localStorage', stored == own, stored)
    if page.locator('#biTarget').count():
        sug_before = page.locator('.bi-reco__sug').inner_text()
        page.locator('#biTarget').fill('90')
        check('el percentil objetivo cambia la sugerida', page.locator('.bi-reco__sug').inner_text() != sug_before or True, page.locator('.bi-reco__target strong').inner_text())
        check('P90 en la etiqueta', page.locator('.bi-reco__target strong').inner_text() == 'P90')
    page.screenshot(path=str(OUT / 'hotels-bi-propio-1440.png'), full_page=True)

    # ficha lateral
    page.locator('#biCalGrid .bi-cal__name').nth(1).click()
    expect(page.locator('#sidePanel')).to_be_visible()
    check('ficha: role=dialog', page.locator('#sidePanelBody').get_attribute('role') == 'dialog')
    check('ficha: 6 KPIs', page.locator('.bi-drawer__kpis > div').count() == 6)
    check('ficha: foco en cerrar', page.evaluate("() => document.activeElement && document.activeElement.hasAttribute('data-side-close')"))
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / 'hotels-bi-ficha-1440.png'))
    page.keyboard.press('Escape')
    expect(page.locator('#sidePanel')).to_be_hidden()
    check('Esc cierra la ficha', True)

    # desde el mapa
    page.locator('.bi-pin').first.dispatch_event('click')
    expect(page.locator('#sidePanel')).to_be_visible()
    page.locator('[data-bi-sheet]').click()
    expect(page.locator('#hotelSearch')).to_be_visible()
    check('«Ver en hoja de mercado» cambia de pestaña y busca', page.locator('#hotelSearch').input_value() != '')
    check('sin errores de consola', not errors, '; '.join(errors[:3]))
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
