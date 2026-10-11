"""Rendimiento de cambios de vista y del calendario BI (WebKit y Chromium).

Solo lectura: aborta cualquier petición que no sea GET a /api/** (salvo
analytics/query, que es de lectura). Pensado para una instancia aislada:
  SQLITE_PATH=artifacts/perf/db/trabajo.sqlite FLASK_PORT=5062 .venv/bin/python run.py

Uso:
  .venv/bin/python tests/e2e/perf_switch.py [--base URL] [--engine webkit|chromium]
      [--out artifacts/perf/<nombre>] [--assert]
Escenarios: switch (Hoteles/Vuelos/Dashboard), scroll, date-click, hover.
Los objetivos de --assert son los del plan de rendimiento (WebKit, 2x).
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

INIT = """(() => {
  window.__frames = [];
  const loop = (t) => { window.__frames.push(t); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
})();"""

SWITCH = """async ([view, settleMs]) => {
  const ready = () => {
    const v = document.querySelector(`#view-${view}`);
    if (!v || !v.classList.contains('is-visible')) return false;
    if (view === 'hotels') { const k = v.querySelector('#biKpis'); return !!(k && k.children.length) || !!v.querySelector('#hotelSheetBody tr'); }
    if (view === 'flights') { const p = v.querySelector('#flPanel'); return !!(p && p.children.length); }
    if (view === 'dashboard') return !!v.querySelector('.dash-grid');
    return !!(v.querySelector('.page') && !v.querySelector('.sk-page'));
  };
  const mapKey = { hotels: 'biMap', flights: 'flightMap', dashboard: 'dashboardMap' }[view];
  const n0 = window.__frames.length;
  const t0 = performance.now();
  document.querySelector(`.nav__item[data-view="${view}"]`).click();
  const deadline = t0 + 15000;
  await new Promise((r) => { const c = () => (ready() || performance.now() > deadline) ? r() : setTimeout(c, 4); c(); });
  const tContent = performance.now() - t0;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const tPaint = performance.now() - t0;
  let tMap = null;
  while (mapKey && performance.now() < t0 + 15000) {
    const m = State[mapKey];
    if (m && m.loaded && m.loaded() && m.areTilesLoaded && m.areTilesLoaded()) { tMap = performance.now() - t0; break; }
    await new Promise((r) => setTimeout(r, 16));
  }
  await new Promise((r) => setTimeout(r, settleMs));
  const f = window.__frames.slice(n0);
  const gaps = [f.length ? f[0] - t0 : 0];
  for (let i = 1; i < f.length; i++) gaps.push(f[i] - f[i - 1]);
  return { view, content: Math.round(tContent), paint: Math.round(tPaint), map: tMap == null ? null : Math.round(tMap),
    maxGap: Math.round(Math.max(...gaps)), jank50: gaps.filter((g) => g > 50).length };
}"""

STATS = """() => { const f = window.__frames; const g = []; for (let i = 1; i < f.length; i++) g.push(f[i] - f[i - 1]);
  return { maxGap: Math.round(Math.max(0, ...g)), jank50: g.filter((x) => x > 50).length, frames: f.length }; }"""

CLICK = """async () => {
  const n0 = window.__frames.length; const t0 = performance.now();
  const cells = document.querySelectorAll('#biCalGrid .bi-cal__med[role="button"]');
  const el = cells[(Math.floor(Math.random() * 5) + 3) % cells.length]; el.click();
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const paint = performance.now() - t0;
  await new Promise((r) => setTimeout(r, 400));
  const f = window.__frames.slice(n0); let mx = 0; for (let i = 1; i < f.length; i++) mx = Math.max(mx, f[i] - f[i - 1]);
  return { clickToPaint: Math.round(paint), maxGap: Math.round(mx) };
}"""


def reset_frames(page):
    page.evaluate("() => { window.__frames = []; }")


def scenario_switch(page):
    page.wait_for_selector("#view-dashboard .dash-grid", timeout=30000)
    page.wait_for_timeout(2000)
    seq = ["hotels", "flights", "hotels", "flights", "hotels", "flights", "dashboard", "hotels", "flights"]
    return [page.evaluate(SWITCH, [v, 2200]) for v in seq]


def goto_bi(page, base):
    page.goto(base + "#hotels?tab=bi", wait_until="load")
    page.wait_for_selector("#biKpis > *", timeout=30000)
    page.wait_for_timeout(2500)


def scenario_scroll(page, base):
    goto_bi(page, base)
    page.mouse.move(700, 500)
    out = []
    for _ in range(2):
        reset_frames(page)
        for _ in range(30):
            page.mouse.wheel(0, 120); page.wait_for_timeout(16)
        for _ in range(30):
            page.mouse.wheel(0, -120); page.wait_for_timeout(16)
        page.wait_for_timeout(400)
        out.append(page.evaluate(STATS))
    return out


def scenario_date_click(page, base):
    goto_bi(page, base)
    page.evaluate("() => document.querySelector('#biCal').scrollIntoView({block:'start'})")
    page.wait_for_timeout(800)
    return [page.evaluate(CLICK) for _ in range(3)]


def scenario_hover(page, base):
    goto_bi(page, base)
    page.evaluate("() => document.querySelector('#biCalGrid').scrollIntoView({block:'center'})")
    page.wait_for_timeout(1200)
    x0, y0, w, h = page.evaluate("() => { const r = document.querySelector('#biCalGrid').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
    page.mouse.move(x0 + 5, y0 + h * 0.5)
    reset_frames(page)
    for i in range(60):
        page.mouse.move(x0 + 5 + (w - 10) * i / 59, y0 + h * (0.3 + 0.4 * ((i % 10) / 9)), steps=2)
        page.wait_for_timeout(16)
    page.wait_for_timeout(300)
    return page.evaluate(STATS)


def run(base, engine, width, height):
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)

        def guard(route):
            if route.request.method != "GET" and "/api/analytics/query" not in route.request.url:
                return route.abort()
            return route.continue_()

        ctx.route("**/api/**", guard)
        ctx.add_init_script(INIT)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(base + "#dashboard", wait_until="load")
        res = {"switch": scenario_switch(page)}
        res["scroll"] = scenario_scroll(page, base)
        res["date_click"] = scenario_date_click(page, base)
        res["hover"] = scenario_hover(page, base)
        res["errors"] = errors
        browser.close()
    return res


def check(res):
    """Objetivos del plan (WebKit, 1440x900 a 2x)."""
    sw = res["switch"]
    first_hotels = sw[0]
    seen, back = set(), []
    for r in sw:
        if r["view"] in seen and r["view"] in ("hotels", "flights"):
            back.append(r)
        seen.add(r["view"])
    rules = [
        ("primera visita a Hoteles: frame más largo ≤ 140 ms", first_hotels["maxGap"] <= 140),
        ("volver: contenido visible ≤ 16 ms", all(r["content"] <= 16 for r in back)),
        ("volver: frame más largo ≤ 80 ms", all(r["maxGap"] <= 80 for r in back)),
        ("scroll BI: 0 frames > 50 ms", all(s["jank50"] == 0 for s in res["scroll"])),
        ("clic en fecha ≤ 130 ms", all(c["clickToPaint"] <= 130 for c in res["date_click"])),
        ("ratón sobre calendario ≤ 50 ms", res["hover"]["maxGap"] <= 50),
        ("sin errores de página", not res["errors"]),
    ]
    return rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5062/")
    ap.add_argument("--engine", default="webkit", choices=["webkit", "chromium"])
    ap.add_argument("--out", default="artifacts/perf/ultimo")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--assert", dest="do_assert", action="store_true")
    a = ap.parse_args()
    res = run(a.base, a.engine, a.width, a.height)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.engine}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    lines = [f"# perf_switch · {a.engine} · {a.width}x{a.height} @2x", "", "| vista | contenido ms | pintado ms | mapa ms | frame máx ms | frames>50 |", "|---|---|---|---|---|---|"]
    for r in res["switch"]:
        lines.append(f"| {r['view']} | {r['content']} | {r['paint']} | {r['map']} | {r['maxGap']} | {r['jank50']} |")
    lines += ["", f"scroll: {res['scroll']}", f"clic fecha: {res['date_click']}", f"hover: {res['hover']}", f"errores: {res['errors']}", ""]
    rules = check(res)
    lines += ["## Objetivos"] + [f"- {'OK' if ok else 'FALLA'} · {name}" for name, ok in rules]
    (out / f"{a.engine}.md").write_text("\n".join(lines))
    print("\n".join(lines))
    if a.do_assert and not all(ok for _, ok in rules):
        sys.exit(1)


if __name__ == "__main__":
    main()
