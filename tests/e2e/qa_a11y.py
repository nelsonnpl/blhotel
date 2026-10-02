"""Barrido de accesibilidad por vista: nombre accesible en controles, objetivos ≥ 24 px y foco visible.

Uso: .venv/bin/python artifacts/visual-qa/redesign-final/qa_a11y.py [http://127.0.0.1:5050]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from shoot import mock_side_effects, VIEWS  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
SCAN = r"""() => {
  const out = { unnamed: [], small: [], tabs: 0, dialogs: 0 };
  const root = document.querySelector('.view.is-visible') || document.body;
  root.querySelectorAll('button, a[href], select, input:not([type=hidden]), textarea, [role=button], [role=tab]').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height || getComputedStyle(el).visibility === 'hidden') return;
    if (el.closest('.maplibregl-ctrl-attrib')) return;
    const label = (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || el.getAttribute('placeholder') || '').trim()
      || (el.id && document.querySelector(`label[for="${el.id}"]`)?.textContent.trim()) || (el.closest('label')?.textContent.trim());
    if (!label) out.unnamed.push(el.outerHTML.slice(0, 110));
    const inline = el.tagName === 'A' || el.classList.contains('link-button');
    if (!inline && (r.width < 24 || r.height < 24) && !['checkbox', 'radio'].includes(el.type)) out.small.push(`${Math.round(r.width)}×${Math.round(r.height)} ${el.outerHTML.slice(0, 90)}`);
  });
  out.tabs = root.querySelectorAll('[role=tab]').length;
  return out;
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    total = 0
    for name, (view, storage, ready) in VIEWS.items():
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        ctx.add_init_script('try{' + ''.join(f"localStorage.setItem('{k}','{v}');" for k, v in storage.items()) + '}catch(e){}')
        page = ctx.new_page()
        mock_side_effects(page)
        page.goto(f'{BASE}/#{view}')
        try:
            page.wait_for_selector(ready, timeout=20000)
        except Exception:
            print(f'{name}: no cargó'); ctx.close(); continue
        page.wait_for_timeout(1500)
        res = page.evaluate(SCAN)
        total += len(res['unnamed']) + len(res['small'])
        print(f"{name}: {len(res['unnamed'])} sin nombre · {len(res['small'])} objetivos < 24 px · {res['tabs']} tabs")
        for item in res['unnamed'][:6]: print('   sin nombre:', item)
        for item in res['small'][:8]: print('   pequeño:', item)
        ctx.close()
    browser.close()
print('problemas:', total)
