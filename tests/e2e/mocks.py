"""Lista blanca de escritura para tests e2e. Deniega por defecto todo lo que
no sea GET en /api/** salvo esta lista (los mocks responden canned).

Hoy los mocks NO cubren (pago): .../analyses, hotel-detail-capture,
air-data/capture, booking-options ni assistant/jobs → quedan BLOQUEADOS
hasta que la oleada 1 corrija la fuga (PA-97) y la contabilidad (PA-80).
"""
import json
import re

# (método, regex) permitidos con respuesta canned (sin gasto real)
ALLOW = [
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


def canned(url: str):
    path = url.split("?", 1)[0]
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
        if is_allowed(req.url, req.method):
            body = canned(req.url) if req.method.upper() != "GET" else None
            if body is not None:
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(body))
            else:
                route.continue_()
        else:
            route.fulfill(status=403, content_type="application/json",
                          body=json.dumps({"error": "bloqueado por mocks e2e"}))
    page.route("**/api/**", handler)
