"""Batería e2e de capturas Atlas (pulido).

Derivada de `artifacts/visual-qa/redesign-final/shoot.py` (no versionado),
adaptada con `--base`, `--out`, `--sizes` (añade 1280, 1024 y 768),
`--reduced-motion` y `--density`. Los mocks viven en `mocks.py`
(deny-by-default salvo GET y lista blanca; sin gasto real).

Uso:
  .venv/bin/python tests/e2e/shoot.py [--base URL] [--out DIR]
      [--views v1 v2 ...] [--sizes 1920x1080,...] [--themes claro,oscuro]
      [--densities compacta,equilibrada,espaciosa] [--reduced-motion] [--viewport]
Vistas: dashboard hotels hotels-bi reputation flights flights-routes flights-ops copilot workspace captures
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from mocks import install_mocks

# compat: los qa_*.py importan mock_side_effects de shoot
mock_side_effects = install_mocks

# vista → (vista de la app, claves de localStorage, selector de pintado)
VIEWS = {
    'dashboard': ('dashboard', {}, '.dash-grid'),
    'hotels': ('hotels', {'atlas.hotelTab': 'sheet'}, '.hsheet'),
    'hotels-bi': ('hotels', {'atlas.hotelTab': 'bi'}, '.bi'),
    'reputation': ('reputation', {}, '.rep'),
    'flights': ('flights', {'atlas.flightTab': 'overview'}, '.fl'),
    'flights-routes': ('flights', {'atlas.flightTab': 'routes'}, '.fl'),
    'flights-ops': ('flights', {'atlas.flightTab': 'operations'}, '.fl'),
    'copilot': ('copilot', {}, '.copilot'),
    'workspace': ('workspace', {}, '.workspace'),
    'captures': ('captures', {}, '.page'),
}

CHECK_JS = """() => {
  const doc = document.documentElement;
  const overflow = doc.scrollWidth - doc.clientWidth;
  const clipped = [];
  const all = document.querySelectorAll('.view.is-visible *, .topbar *, .sidebar *');
  for (const el of all) {
    if (!el.childNodes.length || el.children.length) continue;
    const text = (el.textContent || '').trim();
    if (!text || el.closest('.sr-only')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const hidden = ['hidden', 'clip'].includes(cs.overflowX) || ['hidden', 'clip'].includes(cs.overflow);
    if (hidden && el.scrollWidth > el.clientWidth + 1 && cs.textOverflow !== 'ellipsis') {
      clipped.push(text.slice(0, 60) + ' [' + (el.className || el.tagName) + ']');
    }
  }
  return { overflow, clipped: clipped.slice(0, 15) };
}"""


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sizes = [tuple(int(x) for x in s.split('x')) for s in args.sizes.split(',')]
    themes = args.themes.split(',')
    densities = args.density.split(',')
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name in args.views:
            view, storage, ready = VIEWS[name]
            for width, height in sizes:
                for theme in themes:
                    for density in densities:
                        problems = []
                        ctx_kwargs = {'viewport': {'width': width, 'height': height},
                                      'device_scale_factor': 1}
                        if args.reduced_motion:
                            ctx_kwargs['reduced_motion'] = 'reduce'
                        ctx = browser.new_context(**ctx_kwargs)
                        init = {'atlas.theme': theme, 'atlas.sidebar': 'expandida',
                                'atlas.density': density, **storage}
                        ctx.add_init_script('try{' + ''.join(
                            f"localStorage.setItem({json.dumps(k)},{json.dumps(v)});"
                            for k, v in init.items()) + '}catch(e){}')
                        page = ctx.new_page()
                        install_mocks(page)
                        page.on('console', lambda m, pr=problems: m.type == 'error' and pr.append(f'console: {m.text[:200]}'))
                        page.on('requestfailed', lambda r, pr=problems: pr.append(f'requestfailed: {r.url[:120]} {r.failure}'))
                        page.on('response', lambda r, pr=problems: r.status >= 400 and pr.append(f'http {r.status}: {r.url[:120]}'))
                        page.goto(f'{args.base}/#{view}')
                        try:
                            page.wait_for_selector(ready, timeout=20000)
                        except Exception as error:  # noqa: BLE001 - se informa y se sigue
                            problems.append(f'no apareció {ready}: {error}'.splitlines()[0])
                        page.wait_for_timeout(args.settle)
                        check = page.evaluate(CHECK_JS)
                        path = out / f'{name}-{width}-{theme}-{density}.png'
                        page.screenshot(path=str(path), full_page=not args.viewport)
                        if check['overflow'] > 0:
                            problems.append(f"desborde horizontal de {check['overflow']} px")
                        problems += [f'recortado: {c}' for c in check['clipped']]
                        report.append((path.name, problems))
                        ctx.close()
        browser.close()
    for name, problems in report:
        print(('OK  ' if not problems else 'MAL ') + name)
        for line in problems:
            print('     ' + line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:5050')
    parser.add_argument('--out', default='artifacts/visual-qa/pulido/regresion')
    parser.add_argument('--views', nargs='+', default=list(VIEWS))
    parser.add_argument('--sizes', default='1920x1080,1440x900,1366x768,1280x800,1024x768,768x1024')
    parser.add_argument('--themes', default='claro,oscuro')
    parser.add_argument('--density', default='equilibrada')
    parser.add_argument('--reduced-motion', action='store_true')
    parser.add_argument('--viewport', action='store_true')
    parser.add_argument('--settle', type=int, default=2500)
    run(parser.parse_args())
