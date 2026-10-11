"""Regresión Atlas UI: filtros, CSV, foco, calendario y estados controlados.

.venv/bin/python tests/e2e/qa_atlas_ui.py http://127.0.0.1:5063 artifacts/visual-qa/atlas-ui
Sin servicios de captura o IA: todas las escrituras se interceptan.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from mocks import install_mocks

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5063'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else 'artifacts/visual-qa/atlas-ui/states')
OUT.mkdir(parents=True, exist_ok=True)
checks = []

def check(name, condition):
    assert condition, name
    checks.append(name)
    print('OK ', name, flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={'width': 1366, 'height': 768}, reduced_motion='reduce')
    context.add_init_script("localStorage.setItem('atlas.hotelTab','sheet');localStorage.setItem('atlas.theme','claro');")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    install_mocks(page)
    page.goto(BASE+'/#hotels')
    page.wait_for_selector('#hotelTable .hrow')
    page.locator('#hotelSearch').fill('Seaside')
    expect(page.locator('#hotelTable .hrow').first).to_contain_text('Seaside')
    page.locator('#hotelGroup').select_option('chain')
    check('búsqueda y agrupación combinadas', page.locator('.hgroup').count() > 0)
    page.locator('[data-sheet-sort="adr"]').click()
    with page.expect_download() as download:
        page.locator('#exportHotels').click()
    csv = Path(download.value.path()).read_text(encoding='utf-8-sig')
    check('CSV conserva el resultado filtrado', 'Seaside' in csv and 'Abora' not in csv)
    page.locator('[data-sheet-toggle]').first.press('Enter')
    expect(page.locator('.hdetail')).to_be_visible()
    check('detalle abierto con teclado', True)
    page.locator('.nav__item[data-view="flights"]').click()
    page.wait_for_selector('#flPanel')
    page.locator('.nav__item[data-view="hotels"]').click()
    expect(page.locator('#hotelSearch')).to_have_value('Seaside')
    check('contexto de tabla conservado al navegar', True)
    page.locator('#hotelSearch').fill('zzz-ningún-hotel-qa')
    expect(page.locator('.hsheet__empty')).to_be_visible()
    page.screenshot(path=str(OUT/'hotels-empty.png'))
    page.locator('#hotelSearchClear').click()
    page.locator('#hotelTab-bi').click()
    page.wait_for_selector('#biCalGrid')
    meds = page.locator('.bi-cal__med[role="button"]')
    check('fechas del calendario con objetivo mínimo de 24 px', all((m.bounding_box()['width'] >= 24 and m.bounding_box()['height'] >= 24) for m in meds.all()))
    meds.first.press('End')
    check('Fin conserva foco dentro del calendario', page.evaluate("document.activeElement.matches('.bi-cal__med[role=button]')"))
    page.locator('#captureTop').click()
    expect(page.locator('#captureDialog')).to_be_visible()
    expect(page.locator('#captureConfirm')).to_be_focused()
    page.keyboard.press('Tab')
    expect(page.locator('#captureCancel')).to_be_focused()
    page.keyboard.press('Shift+Tab')
    expect(page.locator('#captureConfirm')).to_be_focused()
    page.screenshot(path=str(OUT/'capture-dialog.png'))
    page.keyboard.press('Escape')
    expect(page.locator('#captureDialog')).to_be_hidden()
    expect(page.locator('#captureTop')).to_be_focused()
    check('diálogo atrapa Tab, cierra con Escape y devuelve foco', True)
    page.locator('.nav__item[data-view="captures"]').click()
    page.wait_for_selector('#capCheckIn')
    page.locator('#capCheckIn').fill('2027-01-18')
    page.locator('#launchCapture').click()
    expect(page.locator('#captureLog')).to_contain_text('qa-mock', timeout=10000)
    page.screenshot(path=str(OUT/'capture-running.png'))
    check('trabajo y registro con respuesta controlada', True)
    check('sin errores de JavaScript', not errors)
    context.close()
    # Initial load and a nonretryable API error are independent controlled states.
    for name, fail in [('loading',False),('error',True)]:
        ctx = browser.new_context(viewport={'width':1366,'height':768}, reduced_motion='reduce')
        ctx.add_init_script("localStorage.setItem('atlas.hotelTab','sheet');")
        pg = ctx.new_page();install_mocks(pg)
        pending = []
        if fail:
            pg.route('**/api/snapshots/latest*',lambda r:r.fulfill(status=400,content_type='application/json',body=json.dumps({'error':'QA: respuesta controlada'})))
        else:
            # Keep the snapshot pending until the skeleton has been inspected.
            pg.route('**/api/snapshots/latest*',lambda r:pending.append(r))
        pg.goto(BASE+'/#hotels',wait_until='domcontentloaded')
        target='.inline-error' if fail else '.sk-page'
        pg.wait_for_selector(target)
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(OUT/f'hotels-{name}.png'), timeout=10000)
        for route in pending: route.abort()
        check('estado controlado '+name,True)
        ctx.close()
    for theme in ['claro', 'oscuro']:
        ctx = browser.new_context(viewport={'width':1366,'height':768})
        ctx.add_init_script("localStorage.setItem('atlas.theme', '" + theme + "');")
        pg=ctx.new_page();install_mocks(pg);pg.goto(BASE+'/#captures')
        pg.wait_for_selector('#launchCapture')
        ratios=pg.evaluate("""() => {
            const rgb = color => color.match(/[\d.]+/g).slice(0,3).map(Number).map(v => {v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
            const luminance = color => rgb(color).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
            const contrast = (fg,bg) => {const a=luminance(fg),b=luminance(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);};
            const btn=getComputedStyle(document.querySelector('#launchCapture'));
            const text=getComputedStyle(document.querySelector('.page h1'));
            const body=getComputedStyle(document.body);
            return {primary:contrast(btn.color,btn.backgroundColor),heading:contrast(text.color,body.backgroundColor)};
        }""")
        check('contraste de texto y botón principal en '+theme, all(ratio>=4.5 for ratio in ratios.values()))
        ctx.close()
    browser.close()
(OUT/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
