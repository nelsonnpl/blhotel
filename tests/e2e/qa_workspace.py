"""QA funcional del Espacio de trabajo (§7).

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_workspace.py [http://127.0.0.1:5050]
El guardado (POST/PUT /api/workspaces) se intercepta: el tablero real del usuario no cambia.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
OUT = Path(__file__).parent
results, saves = [], []


def check(name, ok, detail=''):
    results.append((bool(ok), name, detail))


def workspaces(route):
    if route.request.method in ('POST', 'PUT'):
        body = json.loads(route.request.post_data or '{}')
        saves.append(body)
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'workspace': {**body, 'id': 999999, 'version': 1}}))
    else:
        route.continue_()


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--explicitly-allowed-ports=5050,5060,5061,5070,8001"])
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('atlas.theme','claro');}catch(e){}")
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    mock_side_effects(page)
    page.route('**/api/workspaces', workspaces)
    page.route('**/api/workspaces/*', workspaces)
    page.goto(f'{BASE}/#workspace')
    page.wait_for_selector('.board .wblock')

    check('catálogo compacto de bloques', 220 <= page.locator('.workspace__aside').bounding_box()['width'] <= 240)
    check('5 bloques disponibles con etiquetas legibles', page.locator('.block-add').count() == 5 and page.locator('.block-add .badge').first.bounding_box()['height'] >= 24)
    check('KPIs a todo el ancho', 'wide' in (page.locator('.wblock', has=page.locator('.badge', has_text='KPI')).first.get_attribute('class') or ''))
    check('sin desbordes en la cabecera', page.evaluate("() => { const m = document.querySelector('.workspace__main'); return m.scrollWidth <= m.clientWidth + 1; }"))
    check('estado «Guardado»', 'Guardado' in page.locator('.saved-chip').inner_text())

    # enlace A
    hotel = page.locator('[data-workspace-hotel]').first
    name = hotel.get_attribute('data-workspace-hotel-name')
    hotel.click()
    page.wait_for_selector('.ws-link')
    check('chip «Enlace A · hotel»', name in page.locator('.ws-link').inner_text())
    check('fila enlazada resaltada', page.locator('.ws-table tr.is-selected').count() == 1)
    check('la gráfica ADR muestra el hotel', page.locator('.workspace-selection-note').count() >= 1 and name in page.locator('.workspace-selection-note').first.inner_text())
    page.locator('[data-workspace-unlink]').click()
    page.wait_for_function("() => !document.querySelector('.ws-link')")
    check('× quita el enlace', page.locator('.ws-table tr.is-selected').count() == 0)

    # título y guardado
    page.locator('#workspaceName').fill('Pulso QA')
    check('«Cambios sin guardar»', 'Cambios sin guardar' in page.locator('.saved-chip').inner_text())
    check('Guardar activado', page.locator('#workspaceSave').is_enabled())

    # orden
    first_title = page.locator('.wblock__head strong').nth(0).inner_text()
    page.locator('[data-workspace-move][data-workspace-direction="1"]').first.click()
    page.wait_for_timeout(500)
    check('↓ reordena', page.locator('.wblock__head strong').nth(1).inner_text() == first_title)

    # tablero vacío
    while page.locator('[data-workspace-remove]').count():
        page.locator('[data-workspace-remove]').first.click()
        page.wait_for_timeout(250)
    check('«Tablero vacío»', page.locator('.ws-empty').is_visible() and 'Tablero vacío' in page.locator('.ws-empty').inner_text())
    page.locator('[data-workspace-reset]').click()
    page.wait_for_selector('.board .wblock')
    check('«Restaurar tablero base»', page.locator('.board .wblock').count() >= 3)
    page.locator('[data-workspace-add="data-quality"]').click()
    page.wait_for_timeout(500)
    check('añadir bloque desde la paleta', page.locator('.ws-qa').count() == 4)
    page.locator('#workspaceSave').click()
    page.wait_for_timeout(800)
    check('Guardar envía el tablero (interceptado)', saves and saves[-1]['name'] == 'Pulso QA', str(saves[-1:])[:200])
    check('sin errores de consola', not errors, '; '.join(errors[:3]))
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
