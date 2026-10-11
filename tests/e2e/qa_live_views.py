"""QA funcional de las vistas vivas (reutilización al navegar y cuándo NO reutilizar).

Uso: .venv/bin/python tests/e2e/qa_live_views.py [http://127.0.0.1:5062] [chromium|webkit]
"""
import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5062').rstrip('/') + '/'
ENGINE = sys.argv[2] if len(sys.argv) > 2 else 'chromium'
ok = fail = 0


def check(name, cond, extra=''):
    global ok, fail
    print(('OK  ' if cond else 'FALLA ') + name + (f' · {extra}' if extra and not cond else ''))
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)


def nav(page, view):
    page.click(f'.nav__item[data-view="{view}"]')
    page.wait_for_timeout(250)


def tag(page, view):
    page.evaluate("(v) => { document.querySelector(`#view-${v} .page`).__tag = 'x'; }", view)


def tagged(page, view):
    return page.evaluate("(v) => { const e = document.querySelector(`#view-${v} .page`); return !!(e && e.__tag === 'x'); }", view)


with sync_playwright() as p:
    b = getattr(p, ENGINE).launch(headless=True)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)
    ctx.route('**/api/**', lambda r: r.abort() if r.request.method != 'GET' else r.continue_())
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)[:160]))
    page.goto(BASE + '#hotels?tab=bi')
    page.wait_for_selector('#biKpis > *', timeout=30000)
    page.wait_for_timeout(1500)
    tag(page, 'hotels')
    nav(page, 'flights'); page.wait_for_selector('#flPanel > *', timeout=30000); page.wait_for_timeout(1500)
    tag(page, 'flights')
    nav(page, 'hotels')
    check('Hoteles se reutiliza al volver', tagged(page, 'hotels'))
    check('el panel de análisis sigue pintado (KPIs)', page.evaluate("() => document.querySelector('#biKpis').children.length > 0"))
    nav(page, 'flights')
    check('Vuelos se reutiliza al volver', tagged(page, 'flights'))
    check('el mapa de Vuelos sigue vivo y con tamaño', page.evaluate("() => { const m = State.flightMap; const c = document.querySelector('#flMap'); return !!m && c.clientWidth > 100 && c.clientHeight > 100; }"))
    nav(page, 'hotels')
    check('el mapa BI sigue vivo y con tamaño', page.evaluate("() => { const m = State.biMap; const c = document.querySelector('#biMap'); return !!m && c.clientWidth > 100 && c.clientHeight > 100; }"))
    # 1) tema
    page.click('#themeBtn'); page.wait_for_timeout(300)
    nav(page, 'flights'); page.wait_for_selector('#flPanel > *'); page.wait_for_timeout(800)
    check('cambiar de tema vuelve a pintar Vuelos', not tagged(page, 'flights'))
    page.click('#themeBtn'); page.wait_for_timeout(300)
    # 2) ancho de ventana
    nav(page, 'hotels'); page.wait_for_timeout(600); tag(page, 'hotels')
    nav(page, 'flights'); page.set_viewport_size({'width': 1100, 'height': 900}); page.wait_for_timeout(300)
    nav(page, 'hotels'); page.wait_for_timeout(600)
    check('cambiar el ancho vuelve a pintar Hoteles', not tagged(page, 'hotels'))
    page.set_viewport_size({'width': 1440, 'height': 900})
    # 3) mercado
    targets = page.evaluate('() => State.targets.map((t) => t.id)')
    if len(targets) > 1:
        other = [t for t in targets if t != page.evaluate('() => State.targetId')][0]
        nav(page, 'hotels'); page.wait_for_timeout(600); tag(page, 'hotels')
        nav(page, 'flights')
        page.evaluate('(id) => selectMarket(id)', other); page.wait_for_timeout(600)
        nav(page, 'hotels'); page.wait_for_timeout(1200)
        check('cambiar de mercado vuelve a pintar Hoteles', not tagged(page, 'hotels'))
        check('Hoteles muestra el mercado nuevo', page.evaluate('(id) => State.targetId === id && document.querySelector("#view-hotels h1") !== null', other))
        page.evaluate('(id) => selectMarket(id)', targets[0]); page.wait_for_timeout(600)
    # 4) abrir hotel desde el ticker/buscador: no reutiliza y aplica la búsqueda
    nav(page, 'flights'); page.wait_for_timeout(300)
    page.evaluate("() => openHotelInHotels('Riu')"); page.wait_for_selector('#hotelSearch', timeout=15000); page.wait_for_timeout(500)
    check('abrir un hotel aplica la búsqueda en la hoja', page.evaluate("() => document.querySelector('#hotelSearch').value === 'Riu'"))
    # 5) escritura correcta invalida
    nav(page, 'flights'); page.wait_for_timeout(300)
    rev0 = page.evaluate('() => State.dataRev')
    page.evaluate("() => api('/api/analytics/query', { method: 'POST', body: JSON.stringify({}) }).catch(() => {})")
    page.wait_for_timeout(300)
    check('una petición no GET que falla no invalida', page.evaluate('() => State.dataRev') == rev0)
    page.evaluate('() => { State.dataRev += 1; }')
    tag(page, 'flights'); nav(page, 'hotels'); nav(page, 'flights'); page.wait_for_selector('#flPanel > *'); page.wait_for_timeout(600)
    check('subir dataRev fuerza el repintado', not tagged(page, 'flights'))
    # 6) atrás/adelante
    nav(page, 'hotels'); nav(page, 'flights'); nav(page, 'dashboard')
    page.go_back(); page.wait_for_timeout(500)
    check('Atrás vuelve a Vuelos', page.evaluate("() => State.view") == 'flights')
    check('Vuelos visible tras Atrás', page.evaluate("() => document.querySelector('#view-flights').classList.contains('is-visible') && document.querySelector('#flPanel').children.length > 0"))
    page.go_forward(); page.wait_for_timeout(500)
    check('Adelante vuelve al Dashboard', page.evaluate("() => State.view") == 'dashboard')
    check('Dashboard con mapa y contenido', page.evaluate("() => !!document.querySelector('#view-dashboard .dash-grid') && !!State.dashboardMap"))
    check('sin errores de página', not errors, str(errors[:2]))
    b.close()
print(f'{ok}/{ok + fail} comprobaciones correctas')
sys.exit(1 if fail else 0)
