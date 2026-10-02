"""QA funcional de Reputación (§4).

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_reputation.py [http://127.0.0.1:5050]
POST /api/hotel-reviews/captures está interceptado: nunca se lanza Jev, Google ni Booking.
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
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('atlas.theme','claro');}catch(e){}")
    page = ctx.new_page()
    errors, captures = [], []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: '/api/hotel-reviews/captures' in r.url and r.method == 'POST' and captures.append(r.post_data))
    mock_side_effects(page)
    page.goto(f'{BASE}/#reputation')
    page.wait_for_selector('.rep-table tbody tr')

    rows = page.locator('[data-reputation-row]')
    total = rows.count()
    check('5 KPIs', page.locator('.rep-kpis .kpi-strip__cell').count() == 5)
    check('cabecera: Configurar y Capturar inventario', page.locator('[data-rep-config]').count() == 1 and page.locator('[data-review-capture-all]').count() == 1)
    check('8 columnas', page.locator('.rep-table thead th').count() == 8)
    check('sin controles de captura a la vista', page.locator('[data-review-capture-controls]').count() == 0)

    # pestañas
    page.locator('[data-rep-tab="maps"]').click()
    shown = page.locator('[data-reputation-row]:not([hidden])').count()
    expected = int(page.locator('[data-rep-tab="maps"] span').inner_text())
    check('Maps por revisar filtra', shown == expected and shown < total, f'{shown}/{expected}')
    check('ningún «verificado» en Maps por revisar', page.locator('[data-reputation-row]:not([hidden]) .rep-chip--ok').count() == 0)
    page.locator('[data-rep-tab="none"]').click()
    check('Sin captura filtra', page.locator('[data-reputation-row]:not([hidden])').count() == int(page.locator('[data-rep-tab="none"] span').inner_text()))
    page.locator('[data-rep-tab="all"]').click()

    # búsqueda
    page.locator('#reviewCatalogSearch').fill('servatur')
    n = page.locator('[data-reputation-row]:not([hidden])').count()
    check('búsqueda sin acentos', 0 < n < total, str(n))
    check('pie «N de M hoteles»', page.locator('#reviewCatalogCount').inner_text().startswith(f'{n} de'))
    page.locator('#reviewCatalogSearch').fill('zzzz')
    check('estado vacío', page.locator('#repEmpty').is_visible())
    page.locator('#reviewCatalogSearch').fill('')

    # selección
    check('sin selección no hay barra', page.locator('.rep-selbar').count() == 0)
    page.locator('[data-review-select]').nth(0).check()
    expect(page.locator('.rep-selbar')).to_be_visible()
    check('fila seleccionada resaltada', 'is-selected' in page.locator('[data-reputation-row]').nth(0).get_attribute('class'))
    check('Comparar desactivado con 1', page.locator('.rep-selbar [data-review-compare]').is_disabled())
    page.locator('[data-review-select]').nth(1).check()
    check('«2 seleccionados»', '2 seleccionados' in page.locator('.rep-selbar').inner_text())
    sb = page.locator('.rep-selbar').bounding_box()
    centre = 236 + (1440 - 236) / 2
    check('barra centrada en el área de contenido', abs(sb['x'] + sb['width'] / 2 - centre) < 2, str(sb))
    page.locator('.rep-selbar [data-review-compare]').click()
    expect(page.locator('#sidePanel')).to_be_visible()
    expect(page.locator('.rep-compare table')).to_be_visible(timeout=10000)
    check('comparación en panel lateral', page.locator('.rep-compare tbody tr').count() == 2)
    page.keyboard.press('Escape')
    expect(page.locator('#sidePanel')).to_be_hidden()
    page.locator('[data-rep-clear]').click()
    check('× quita la selección', page.locator('.rep-selbar').count() == 0 and page.locator('[data-review-select]:checked').count() == 0)

    # casilla de cabecera
    page.locator('[data-rep-tab="maps"]').click()
    page.locator('#reviewSelectAll').check()
    sel = page.locator('[data-review-select]:checked').count()
    check('cabecera selecciona solo las visibles', sel == page.locator('[data-reputation-row]:not([hidden])').count(), str(sel))
    page.locator('[data-rep-clear]').click()
    page.locator('[data-rep-tab="all"]').click()

    # configuración
    page.locator('[data-rep-config]').click()
    expect(page.locator('#sidePanelBody.side-panel--rep')).to_be_visible()
    w = page.locator('#sidePanelBody').bounding_box()['width']
    check('panel de 460 px', abs(w - 460) < 1, str(w))
    check('foco en cerrar', page.evaluate("() => document.activeElement && document.activeElement.hasAttribute('data-side-close')"))
    check('3 fuentes como botones', page.locator('[data-rep-src]').count() == 3)
    page.locator('[data-rep-unbounded]').click()
    check('«Hasta agotar» desactiva Máx. reseñas', page.locator('#repCfgMax').is_disabled())
    page.locator('[data-rep-src="google_hotels"]').click()
    page.locator('[data-rep-src="google_maps"]').click()
    check('fuente conmutada', page.locator('[data-rep-src="google_maps"]').get_attribute('aria-pressed') == 'true')
    page.locator('#repCfgUnit').fill('0.002')
    page.locator('#repCfgBudget').fill('5')
    est = page.locator('#repCfgEstimate').inner_text()
    check('estimación «para N hoteles · US$»', 'Estimación para' in est and 'US$' in est, est)
    page.locator('.rep-cfg__foot [data-side-close]').click()
    page.locator('[data-rep-config]').click()
    check('Cancelar descarta', page.locator('[data-rep-src="google_maps"]').get_attribute('aria-pressed') == 'false')
    page.locator('[data-rep-src="google_hotels"]').click()
    page.locator('[data-rep-config-save]').click()
    expect(page.locator('#sidePanel')).to_be_hidden()
    page.locator('[data-rep-config]').click()
    check('Guardar conserva', page.locator('[data-rep-src="google_hotels"]').get_attribute('aria-pressed') == 'false')
    page.screenshot(path=str(OUT / 'reputation-config-1440.png'))
    page.keyboard.press('Escape')

    # captura: solo Booking (sin gasto) → POST interceptado
    page.locator('[data-review-select]').nth(0).check()
    page.locator('.rep-selbar [data-review-capture-selected]').click()
    page.wait_for_timeout(800)
    check('Capturar reseñas envía la selección (interceptado)', len(captures) == 1 and '"booking"' in (captures[0] or ''), str(captures))

    # ficha
    page.locator('[data-review-open]').first.click()
    page.wait_for_selector('.review-profile-head')
    check('ficha sin controles en línea y con «Configurar captura»', page.locator('[data-review-capture-controls]').count() == 0 and page.locator('[data-rep-config]').count() == 1)
    check('sin errores de consola', not errors, '; '.join(errors[:3]))
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
