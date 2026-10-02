"""QA funcional de Vuelos (§5).

Uso: .venv/bin/python tests/e2e/qa_flights.py [http://127.0.0.1:5060]
La captura aérea está interceptada (mock_side_effects): nunca se lanza SerpApi.

G1-14: los endpoints de pago (capture/estimate, booking-options) están
BLOQUEADOS por diseño (mocks.py deny-by-default). La QA espera
403 {"error": "bloqueado por mocks e2e"} y no aborta: el desplegable del
plan muestra el bloqueo y el inicio queda desactivado (gasto 0).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects  # noqa: E402
from mocks import is_allowed  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
OUT = Path(__file__).parent
ESTIMATE_URL = BASE + '/api/air-data/capture/estimate'
results = []


def check(name, ok, detail=''):
    results.append((bool(ok), name, detail))


aborted = None
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--explicitly-allowed-ports=5050,5060,5061,5070,8001"])
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        ctx.add_init_script("try{localStorage.setItem('atlas.flightTab','overview');localStorage.removeItem('atlas.air-operations.query.v3');localStorage.setItem('atlas.theme','claro');}catch(e){}")
        page = ctx.new_page()
        errors, air_jobs, pay = [], [], {}
        page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: '/api/jobs/air-capture' in r.url and air_jobs.append(r.post_data))
        page.on('response', lambda r: ('capture/estimate' in r.url or 'booking-options' in r.url) and pay.update({r.url.split('?')[0]: r.status}))
        mock_side_effects(page)
        page.goto(f'{BASE}/#flights')
        page.wait_for_selector('.fl-label', timeout=20000)

        check('3 pestañas con role=tab', page.locator('[data-flight-tab][role="tab"]').count() == 3)
        check('7 KPIs', page.locator('.kpi-strip--fl .kpi-strip__cell').count() == 7)
        check('marcadores envueltos en .map-pin', page.locator('.maplibregl-marker').count() == page.locator('.maplibregl-marker > .map-pin').count())
        check('capa de arcos en el mapa', page.evaluate("() => !!document.querySelector('#flMap canvas')"))
        first = page.locator('#flRouteSelect').input_value()

        # seleccionar ruta desde la etiqueta del mapa (nº de etiquetas según datos)
        n_labels = page.locator('.fl-label').count()
        check('hay etiquetas de ruta en el mapa', n_labels >= 1, str(n_labels))
        label = page.locator('.fl-label').nth(min(3, n_labels - 1))
        code = label.get_attribute('data-fl-label')
        label.dispatch_event('click')
        check('pulsar etiqueta selecciona la ruta', page.locator('#flRouteSelect').input_value() == code, code)
        check('etiqueta seleccionada resaltada', 'is-focus' in (page.locator(f'.fl-label[data-fl-label="{code}"]').first.get_attribute('class') or ''))
        check('fila del mapa de calor resaltada', page.locator(f'.fl-heat__route.is-focus[data-fl-route="{code}"]').count() >= 1, code)

        # select de ruta y fila del mapa de calor
        page.select_option('#flRouteSelect', first)
        check('select cambia la ruta', page.locator('.fl-route__head h2').inner_text().startswith(first))
        n_heat = page.locator('.fl-heat__route').count()
        check('hay filas en el mapa de calor', n_heat >= 1, str(n_heat))
        page.locator('.fl-heat__route').nth(min(2, n_heat - 1)).click()
        check('fila del calor selecciona ruta', page.locator('.fl-heat__route.is-focus').count() >= 1)

        # modo del grosor
        page.locator('[data-fl-mode="price"]').click()
        check('modo Precio activo', page.locator('[data-fl-mode="price"]').get_attribute('aria-pressed') == 'true')
        check('leyenda de grosor cambia', 'barata' in page.locator('#flMapLegend').inner_text())

        # señales
        n_sig = page.locator('.fl-signal').count()
        check('hay señales de precio', n_sig >= 1, str(n_sig))
        sig = page.locator('.fl-signal').first
        sig_code = sig.get_attribute('data-fl-route')
        sig.click()
        check('señal selecciona su ruta', page.locator('#flRouteSelect').input_value() == sig_code, sig_code)

        # desplegable de captura: pago bloqueado por mocks (G1-14, gasto 0)
        check('estimate fuera de la blanca de mocks', not is_allowed(ESTIMATE_URL, 'POST'))
        page.locator('[data-fl-plan]').click()
        expect(page.locator('#flPlan')).to_be_visible()
        page.wait_for_timeout(1500)
        est_txt = page.locator('#airCaptureEstimate').inner_text()
        check('estimate espera 403 bloqueado por mocks (sin gasto)',
              'bloqueado por mocks e2e' in est_txt and pay.get(ESTIMATE_URL) == 403,
              f"{est_txt[:60]!r} status={pay.get(ESTIMATE_URL)}")
        page.locator('#airCaptureBudget').fill('1')
        page.wait_for_timeout(800)
        check('con pago bloqueado: Iniciar desactivado', page.locator('[data-air-capture-start]').is_disabled())
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
        # aerolínea según datos vivos (antes «Ryanair» fija, ausente en la semilla actual)
        wanted = page.locator('#airOperationsTable tbody .fl-airline__cell .ellipsis').first.inner_text().strip()
        page.locator('#airOperationsSearch').fill(wanted)
        page.wait_for_timeout(900)
        airlines = set(page.locator('#airOperationsTable tbody .fl-airline__cell .ellipsis').all_inner_texts())
        check('búsqueda filtra por aerolínea', airlines == {wanted}, str(airlines))
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
        check('consulta guardada', stored and wanted in stored, (stored or '')[:120])

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
        # Los 403 de estimate/booking-options son bloqueos esperados (G1-14), no errores.
        other_errors = [e for e in errors if '403' not in e]
        check('sin errores de consola (salvo 403 de pago esperado)', not other_errors, '; '.join(other_errors[:3]))
        browser.close()
except Exception as exc:  # noqa: BLE001 - la QA no aborta: el fallo queda como check
    aborted = f'{type(exc).__name__}: {str(exc)[:200]}'

if aborted:
    results.append((False, 'sin abortos inesperados', aborted))
failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
