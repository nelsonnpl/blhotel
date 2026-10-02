"""G1 · QA exploratorio — bloqueos estrictos y matriz API (sin gasto).

Adapta qa_flights a mocks estrictos: los endpoints de pago/captura quedan
BLOQUEADOS por diseno (mocks.py deny-by-default) y la QA debe esperar 403
con {"error": "bloqueado por mocks e2e"}, no abortar.

Uso: .venv/bin/python tests/e2e/qa_g1_bloqueos.py [http://127.0.0.1:5060]
Solo GET + mocks.is_allowed (sin POST reales, sin gasto).
"""
import sys
import urllib.request
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mocks import is_allowed, canned  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5060"
results = []


def check(name, ok, detail=""):
    results.append((bool(ok), name, detail))


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, json.loads(r.read().decode())


# 1. Mocks estrictos: pago bloqueado, lectura permitida.
check("GET lectura permitido", is_allowed(BASE + "/api/dashboard/metrics?targetId=1", "GET"))
check("POST analytics/query permitido (solo lectura)",
      is_allowed(BASE + "/api/analytics/query", "POST"))
check("POST air-data/capture bloqueado",
      not is_allowed(BASE + "/api/air-data/capture", "POST"))
check("POST air-data/capture/estimate bloqueado (causa aborto qa_flights)",
      not is_allowed(BASE + "/api/air-data/capture/estimate", "POST"))
check("POST booking-options bloqueado",
      not is_allowed(BASE + "/api/air-data/booking-options", "POST"))
check("POST hotel-detail-capture bloqueado",
      not is_allowed(BASE + "/api/jobs/hotel-detail-capture", "POST"))
check("canned cubre qa-mock", canned(BASE + "/api/jobs/qa-rev") is not None)

# 2. Matriz API viva: 2 mercados x vistas principales (solo GET).
for tid in (1, 2):
    try:
        s, m = get(f"/api/dashboard/metrics?targetId={tid}")
        check(f"mercado {tid} metrics 200 con competitiveSet",
              s == 200 and isinstance(m.get("competitiveSet"), list),
              f"n={len(m.get('competitiveSet', []))}")
    except Exception as e:  # noqa: BLE001
        check(f"mercado {tid} metrics 200", False, str(e)[:120])
try:
    s, snap = get("/api/snapshots/latest?targetId=1")
    check("snapshot latest 200", s == 200 and "latest" in snap)
except Exception as e:  # noqa: BLE001
    check("snapshot latest 200", False, str(e)[:120])
try:
    s, air = get("/api/air-data?direction=arrival")
    check("air-data 200 global (no por mercado)", s == 200 and "airports" in air)
except Exception as e:  # noqa: BLE001
    check("air-data 200", False, str(e)[:120])

# 3. PA-74 base vacia: endpoint sin targetId responde 400, no 500.
try:
    urllib.request.urlopen(BASE + "/api/dashboard/metrics", timeout=10)
    check("metrics sin targetId 400", False, "devolvio 200")
except Exception as e:  # noqa: BLE001
    check("metrics sin targetId 400 (no 500)", "400" in str(e), str(e)[:120])

failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(("OK  " if ok else "MAL ") + name + (f" · {detail}" if detail and not ok else ""))
print(f"{len(results) - len(failed)}/{len(results)} comprobaciones correctas")
sys.exit(1 if failed else 0)
