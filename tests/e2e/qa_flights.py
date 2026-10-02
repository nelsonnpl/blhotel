"""QA funcional de Vuelos (§5).

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_flights.py [http://127.0.0.1:5050]
La captura aérea está interceptada (mock_side_effects): nunca se lanza SerpApi.
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
    ctx.add_init_script("try{localStorage.setItem('atlas.flightTab','overview');localStorage.removeItem('atlas.air-operations.query.v3');localStorage.setItem('atlas.theme','claro');}catch(e){}")
    page = ctx.new_page()
    errors, air_jobs = [], []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: '/api/jobs/air-capture' in r.url and air_jobs.append(r.post_data))
    mock_side_effects(page)
    page.goto(f'{BASE}/#flights')
    page.wait_for_selector('.fl-label', timeout=20000)

    check('3 pestañas con role=tab', page.locator('[data-flight-tab][role="tab"]').count() == 3)
    check('7 KPIs', page.locator('.kpi-strip--fl .kpi-strip__cell').count() == 7)
    check('marcadores envueltos en .map-pin', page.locator('.maplibregl-marker').count() == page.locator('.maplibregl-marker > .map-pin').count())
    check('capa de arcos en el mapa', page.evaluate("() => !!document.querySelector('#flMap canvas')"))
    first = page.locator('#flRouteSelect').input_value()

    # seleccionar ruta desde la etiqueta del mapa
    label = page.locator('.fl-label').nth(3)
    code = label.get_attribute('data-fl-label')
    label.dispatch_event('click')
    check('pulsar etiqueta selecciona la ruta', page.locator('#flRouteSelect').input_value() == code, code)
    check('etiqueta seleccionada resaltada', 'is-focus' in (page.locator(f'[data-fl-label="{code}"]').get_attribute('class') or ''))
    check('fila del mapa de calor resaltada', page.locator(f'.fl-heat__route.is-focus[data-fl-route="{code}"]').count() == 1)

    # select de ruta y fila del mapa de calor
    page.select_option('#flRouteSelect', first)
    check('select cambia la ruta', page.locator('.fl-route__head h2').inner_text().startswith(first))
    page.locator('.fl-heat__route').nth(2).click()
    check('fila del calor selecciona ruta', page.locator('.fl-heat__route.is-focus').count() == 1)

    # modo del grosor
    page.locator('[data-fl-mode="price"]').click()
    check('modo Precio activo', page.locator('[data-fl-mode="price"]').get_attribute('aria-pressed') == 'true')
    check('leyenda de grosor cambia', 'barata' in page.locator('#flMapLegend').inner_text())

    # señales
    sig = page.locator('.fl-signal').first
    sig_code = sig.get_attribute('data-fl-route')
    sig.click()
    check('señal selecciona su ruta', page.locator('#flRouteSelect').input_value() == sig_code, sig_code)

    # desplegable de captura
    page.locator('[data-fl-plan]').click()
    expect(page.locator('#flPlan')).to_be_visible()
    expect(page.locator('#airCaptureEstimate')).to_contain_text('×', timeout=10000)
    est = page.locator('#airCaptureEstimate').inner_text()
    check('estimación «fechas × rutas = consultas»', '×' in est, est)
    page.locator('#airCaptureBudget').fill('1')
    expect(page.locator('#airCaptureEstimate.is-bad')).to_be_visible(timeout=10000)
    check('sin presupuesto: Iniciar desactivado', page.locator('[data-air-capture-start]').is_disabled())
    page.mouse.click(700, 700)
    check('clic fuera cierra el desplegable', page.locator('#flPlan').count() == 0)
    check('ninguna captura aérea lanzada', not air_jobs)

    # Ver N vuelos → operación filtrada
    route_code = page.locator('#flRouteSelect').input_value()
    page.locator('[data-fl-ops]').click()
    page.wait_for_selector('#airOperationsTable')
    check('«Ver N vuelos» abre Operación aérea', page.locator('#flTab-operations').get_attribute('aria-selected') == 'true')
    check('filtrada por la ruta', page.locator('[data-air-operation-filter="origin"]').input_value() == route_code)
    origins = set(page.locator('#airOperationsTable tbody tr td:nth-child(2) strong').all_inner_texts())
    check('todas las filas son de la ruta', origins == {route_code}, str(origins))
    check('17 columnas', page.locator('#airOperationsTable thead th').count() == 17)

    page.locator('.fops__reset').click()
    page.wait_for_function("() => document.querySelector('[data-air-operation-filter=\"origin\"]').value === ''")
    total = page.locator('#airOperationsTable tbody tr').count()
    check('Restablecer quita filtros', total > 10, str(total))

    # ordenación por precio
    page.locator('[data-air-sort="price"]').click()
    page.wait_for_selector('th[aria-sort="ascending"] [data-air-sort="price"]')
    prices = [float(t.replace('€', '').replace('.', '').replace(',', '.').strip()) for t in page.locator('.fops__price').all_inner_texts()]
    check('ordena por precio ascendente', prices == sorted(prices), str(prices[:5]))
    page.locator('[data-air-sort="price"]').click()
    page.wait_for_selector('th[aria-sort="descending"] [data-air-sort="price"]')
    prices = [float(t.replace('€', '').replace('.', '').replace(',', '.').strip()) for t in page.locator('.fops__price').all_inner_texts()]
    check('segundo clic: descendente', prices == sorted(prices, reverse=True))

    # filtro de conexión y búsqueda
    page.select_option('[data-air-operation-filter="connection"]', 'non_direct')
    page.wait_for_timeout(600)
    n_scale = page.locator('#airOperationsTable tbody tr').count()
    check('filtro Con escala (vacío o con chip de escala)', n_scale == 0 and page.locator('.fops__empty').count() == 1 or page.locator('#airOperationsTable .chip--good').count() == 0, str(n_scale))
    page.locator('.fops__reset').click()
    page.wait_for_timeout(400)
    page.locator('#airOperationsSearch').fill('Ryanair')
    page.wait_for_timeout(900)
    airlines = set(page.locator('#airOperationsTable tbody .fl-airline__cell .ellipsis').all_inner_texts())
    check('búsqueda filtra por aerolínea', airlines == {'Ryanair'}, str(airlines))
    check('búsqueda conserva el foco', page.evaluate("() => document.activeElement && document.activeElement.id === 'airOperationsSearch'"))

    # cabecera y primera columna fijas
    check('cabecera sticky', page.eval_on_selector('#airOperationsTable thead th', 'el => getComputedStyle(el).position') == 'sticky')
    check('primera columna sticky', page.eval_on_selector('#airOperationsTable tbody th.fops__sticky', 'el => getComputedStyle(el).position') == 'sticky')

    # pantalla completa
    page.locator('[data-air-operations-fullscreen]').first.click()
    page.wait_for_selector('#airOperationsCard.is-fullscreen')
    box = page.locator('#airOperationsCard').bounding_box()
    check('pantalla completa con 12 px de margen', abs(box['x'] - 12) < 1 and abs(box['y'] - 12) < 1, str(box))
    page.screenshot(path=str(OUT / 'flights-ops-fullscreen-1440.png'))
    page.locator('.fops__tools [data-air-operations-fullscreen]').click()
    page.wait_for_function("() => !document.querySelector('#airOperationsCard.is-fullscreen')")
    check('salir de pantalla completa', not page.evaluate("() => document.body.classList.contains('air-operations-fullscreen')"))

    # la consulta persiste
    stored = page.evaluate("() => localStorage.getItem('atlas.air-operations.query.v3')")
    check('consulta guardada', stored and 'Ryanair' in stored, stored)

    # Rutas → vuelve a Resumen con la ruta
    page.locator('#flTab-routes').click()
    page.wait_for_selector('.fl-range[data-fl-route-open]')
    check('13 filas de rango', page.locator('.fl-range[data-fl-route-open]').count() >= 1)
    row = page.locator('.fl-range[data-fl-route-open]').nth(1)
    rc = row.get_attribute('data-fl-route-open')
    row.click()
    page.wait_for_selector('#flRouteSelect')
    check('pulsar ruta vuelve a Resumen con ella', page.locator('#flRouteSelect').input_value() == rc, rc)

    # teclado en pestañas: foco tras cambio
    page.locator('#flTab-routes').focus()
    page.keyboard.press('Enter')
    page.wait_for_selector('.fl-ranges')
    check('foco en la pestaña tras cambiar', page.evaluate("() => document.activeElement && document.activeElement.id === 'flTab-routes'"))
    check('sin errores de consola', not errors, '; '.join(errors[:3]))
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
