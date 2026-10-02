"""QA funcional del Copilot (§6).

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_copilot.py [http://127.0.0.1:5050]
/api/assistant/chat se simula con una respuesta estructurada: nunca se llama al modelo.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
OUT = Path(__file__).parent
results = []
REPLY = ('## Lectura\nLa mediana del set es **268,48 €/noche** con **38 hoteles comparables**.\n\n'
         '## Evidencia\n- Métrica `hotel-market-adrMediano`.\n- Comparabilidad `matched_partial`.\n\n'
         '## Acción siguiente\nUsa 268,48 € como referencia y solicita una nueva captura.\n\n'
         '## Límite de confianza\nConfianza **media-baja** por la antigüedad de los datos.')
sent = []


def check(name, ok, detail=''):
    results.append((bool(ok), name, detail))


def chat(route):
    sent.append(json.loads(route.request.post_data or '{}'))
    route.fulfill(status=200, content_type='application/json', body=json.dumps({
        'reply': REPLY, 'sessionId': None,
        'dataMeta': {'model': 'qa', 'toolNames': ['hotel_market_summary'], 'references': [{'evidenceId': 'qa-1', 'snapshotId': 18}], 'responseQuality': {'status': 'ok'}},
    }))


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--explicitly-allowed-ports=5050,5060,5061,5070,8001"])
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('atlas.theme','claro');}catch(e){}")
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    page.on('pageerror', lambda e: errors.append(str(e)))
    mock_side_effects(page)
    page.route('**/api/assistant/chat', chat)
    page.goto(f'{BASE}/#copilot')
    page.wait_for_selector('#chatInput')
    page.wait_for_timeout(1200)

    aside = page.locator('.copilot__aside').bounding_box()
    check('barra de conversaciones de 280 px', abs(aside['width'] - 280) < 2, str(aside['width']))
    check('«+» de 32 px', page.locator('#newSession').bounding_box()['width'] == 32)
    check('descargo al pie', 'No sustituye pickup' in page.locator('.note-box').inner_text())
    check('chip de antigüedad', page.locator('#copilotAge:not([hidden])').count() == 1, page.locator('.copilot__scope').inner_text())
    check('select de modelo con 3 opciones', page.locator('#copilotMode option').count() == 3)
    check('sugerencias visibles', page.locator('#chatSuggestions button').count() >= 3 and page.locator('#chatSuggestions').is_visible())
    check('envío de 38 px', page.locator('#chatSend').bounding_box()['width'] == 38)

    # nueva conversación + Shift+Enter + Enter
    page.locator('#newSession').click()
    page.select_option('#copilotMode', 'quick')
    box = page.locator('#chatInput')
    box.click()
    box.type('¿Cuál es la mediana')
    page.keyboard.press('Shift+Enter')
    box.type('del set?')
    check('Mayús+Enter hace salto de línea', '\n' in box.input_value())
    page.evaluate("""() => { window.__busy = ''; new MutationObserver(() => { const s = document.querySelector('.msg-card--busy .msg-card__status'); if (s && document.querySelector('.msg-bot__avatar.is-busy')) window.__busy = s.textContent; }).observe(document.querySelector('#thread'), { childList: true, subtree: true }); }""")
    page.keyboard.press('Enter')
    expect(page.locator('.msg-card__head').last).to_be_visible(timeout=10000)
    busy = page.evaluate('() => window.__busy')
    check('estado «respondiendo»: avatar que late y «consultando foto #»', 'consultando' in busy, busy)
    check('burbuja de usuario en --ac', page.eval_on_selector('.msg-user', "el => getComputedStyle(el).backgroundColor") == page.evaluate("() => { const d = document.createElement('i'); d.style.color = 'var(--ac)'; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }"))
    expect(page.locator('.msg-card__head').last).to_be_visible(timeout=10000)
    card = page.locator('.msg-card').last
    check('modo enviado = quick', sent and sent[-1].get('mode') == 'quick', str(sent[-1:]))
    check('título y chip de confianza', 'MEDIA-BAJA' in card.locator('.msg-card__conf').inner_text().upper())
    check('negritas en las cifras', card.locator('.msg-card__text strong').count() >= 2)
    check('bloque SIGUIENTE', card.locator('.msg-card__next').count() == 1)
    check('límite de confianza', card.locator('.msg-card__limit').count() == 1)
    summary = card.locator('.copilot-trace summary').inner_text().upper()
    check('pie «Trazabilidad · Booking · foto #18»', 'BOOKING' in summary and '#18' in summary, summary)
    card.locator('.copilot-trace summary').click()
    check('trazabilidad despliega la evidencia', card.locator('.copilot-trace__evidence').is_visible())
    page.screenshot(path=str(OUT / 'copilot-respuesta-1440.png'))

    # sugerencia
    page.locator('#chatSuggestions button').first.click()
    page.wait_for_timeout(1000)
    check('una sugerencia envía su pregunta', len(sent) == 2)

    # Preguntar al Copilot desde Vuelos
    page.locator('.nav__item[data-view="flights"]').click()
    page.wait_for_selector('[data-fl-ask]', timeout=20000)
    q = page.locator('[data-fl-ask]').get_attribute('data-fl-ask')
    page.locator('[data-fl-ask]').click()
    page.wait_for_selector('.msg-user', timeout=10000)
    check('«Preguntar al Copilot» abre conversación nueva y envía', page.locator('.msg-user').first.inner_text() == q and sent[-1]['message'] == q and sent[-1].get('sessionId') is None)
    page.wait_for_timeout(1000)
    check('sin errores de consola', not errors, '; '.join(errors[:3]))
    browser.close()

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(('OK  ' if ok else 'MAL ') + name + (f' · {detail}' if detail and not ok else ''))
print(f'{len(results) - len(failed)}/{len(results)} comprobaciones correctas')
sys.exit(1 if failed else 0)
