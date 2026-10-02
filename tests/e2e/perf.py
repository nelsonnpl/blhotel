"""perf.py — Playwright + CDP con 4x CPU y Fast 3G por vista.

Mide FCP, LCP, tareas largas, bytes por recurso y tiempos de API por vista.
Mediana de 5 ejecuciones. Salida JSON + MD.
Uso: .venv/bin/python tests/e2e/perf.py [--base URL] [--out DIR] [--runs 5]
"""
import argparse
import json
import statistics
from pathlib import Path

from playwright.sync_api import sync_playwright

from mocks import install_mocks

VIEWS = ["dashboard", "hotels", "reputation", "flights", "copilot", "workspace", "captures"]


def measure(page, base, view):
    sizes, apis, longtasks = {}, [], []

    def on_resp(r):
        try:
            h = r.headers
            n = int(h.get("content-length", 0) or 0)
        except ValueError:
            n = 0
        sizes[r.url.split("?")[0][-60:]] = n
        if "/api/" in r.url:
            apis.append({"url": r.url.split("?")[0][-80:], "ms": r.request.timing.get("responseEnd", 0)})

    page.on("response", on_resp)
    page.goto(f"{base}#{view}")
    page.wait_for_timeout(4000)
    perf = page.evaluate("""() => {
      const out = {fcp: 0, lcp: 0};
      for (const e of performance.getEntriesByName('first-contentful-paint')) out.fcp = e.startTime;
      const l = performance.getEntriesByType('largest-contentful-paint');
      if (l.length) out.lcp = l[l.length - 1].startTime;
      return out;
    }""")
    return {"fcp": round(perf["fcp"]), "lcp": round(perf["lcp"]),
            "bytes": sum(sizes.values()), "recursos": len(sizes), "apis": apis[:12]}


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, table = {}, ["| Vista | FCP | LCP | Bytes | Recursos |", "| --- | --- | --- | --- | --- |"]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for view in args.views:
            samples = []
            for _ in range(args.runs):
                ctx = browser.new_context()
                page = ctx.new_page()
                # 4x CPU + Fast 3G vía CDP
                client = page.context.new_cdp_session(page)
                client.send("Emulation.setCPUThrottlingRate", {"rate": 4})
                client.send("Network.emulateNetworkConditions", {
                    "offline": False, "downloadThroughput": 204800,
                    "uploadThroughput": 102400, "latency": 562.5})
                install_mocks(page)
                samples.append(measure(page, args.base, view))
                ctx.close()
            med = {k: int(statistics.median(s[k] for s in samples)) for k in ("fcp", "lcp", "bytes", "recursos")}
            med["apis"] = samples[0]["apis"]
            rows[view] = med
            table.append(f"| {view} | {med['fcp']} | {med['lcp']} | {med['bytes']} | {med['recursos']} |")
        browser.close()
    (out / "perf.json").write_text(json.dumps(rows, indent=1))
    (out / "perf.md").write_text("# perf · 4x CPU + Fast 3G (mediana de %d)\n\n%s\n" % (args.runs, "\n".join(table)))
    print("\n".join(table))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5060/")
    ap.add_argument("--out", default="artifacts/visual-qa/pulido/perf")
    ap.add_argument("--views", nargs="+", default=VIEWS)
    ap.add_argument("--runs", type=int, default=5)
    run(ap.parse_args())
