"""Lista blanca de escritura para tests e2e. Deniega por defecto todo lo que
no sea GET en /api/** salvo esta lista (los mocks responden canned).

Hoy los mocks NO cubren (pago): .../analyses, hotel-detail-capture,
air-data/capture, booking-options ni assistant/jobs → quedan BLOQUEADOS
hasta que la oleada 1 corrija la fuga (PA-97) y la contabilidad (PA-80).
"""
import json
import re

# (método, regex) permitidos con respuesta canned (sin gasto real).
# analytics/query es POST de SOLO LECTURA (métricas; sin gasto ni escrituras):
# se deja pasar al backend real con continue_().
ALLOW = [
    ("POST", r"/api/analytics/query$"),
    ("POST", r"/api/jobs/hotel-capture$"),
    ("POST", r"/api/jobs/air-capture$"),
    ("POST", r"/api/jobs/qa-"),
    ("POST", r"/api/hotel-reviews/captures$"),
    ("POST", r"/api/assistant/chat$"),
    ("POST", r"/api/assistant/jobs$"),
    ("POST", r"/api/assistant/sessions$"),
]
_ALLOW = [(m, re.compile(p)) for m, p in ALLOW]


def is_allowed(url: str, method: str) -> bool:
    """True si la petición puede continuar (GET o en lista blanca)."""
    path = url.split("?", 1)[0]
    if "/api/" not in path:
        return True
    if method.upper() == "GET":
        return True
    return any(m == method.upper() and rx.search(path) for m, rx in _ALLOW)


def canned(url: str, method: str = "POST"):
    path = url.split("?", 1)[0]
    if method.upper() == "GET" and "/api/jobs/qa-" not in path:
        return None
    if path.endswith("/api/jobs/hotel-capture"):
        return {"job": {"id": "qa-mock", "status": "queued", "progress": 0}}
    if path.endswith("/api/jobs/air-capture"):
        return {"job": {"id": "qa-air", "status": "queued"}}
    if "/api/jobs/qa-" in path:
        return {"job": {"id": "qa-mock", "status": "running", "progress": 40}}
    if path.endswith("/api/hotel-reviews/captures"):
        return {"job": {"id": "qa-rev", "status": "queued"}}
    if path.endswith("/api/assistant/chat"):
        return {"reply": "QA", "sessionId": None}
    if path.endswith("/api/assistant/jobs"):
        return {"job": {"id": "qa-chat", "status": "queued"}}
    if path.endswith("/api/assistant/sessions"):
        return {"session": {"id": 999999, "title": "QA", "messages": []}}
    return None


def install_mocks(page):
    """Instala mocks deny-by-default en una página Playwright."""
    def handler(route):
        req = route.request
        body = canned(req.url, req.method)
        if body is not None:
            # Ruta mock conocida: se responde siempre (cubre el sondeo GET
            # de jobs, p. ej. /api/jobs/qa-rev, que si llega al backend da 404).
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps(body))
        elif is_allowed(req.url, req.method):
            route.continue_()
        else:
            route.fulfill(status=403, content_type="application/json",
                          body=json.dumps({"error": "bloqueado por mocks e2e"}))
    page.route("**/api/**", handler)
