from __future__ import annotations

from datetime import datetime, timezone
from contextlib import nullcontext
import importlib
import json
import os
import re
import sys
import time
from typing import Callable
from typing import Any

from .parser import parse_reviews_html
from .schema import GoogleReviewsResult


class JevUnavailable(RuntimeError):
    """Raised when the optional Jev sidecar is not installed or configured."""


class JevNavigationError(RuntimeError):
    """Raised when Jev cannot reach a verifiable review state."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blocked_page(browser: Any) -> bool:
    text = browser.evaluate("document.body ? document.body.innerText : ''") or ""
    lowered = str(text).casefold()
    return any(marker in lowered for marker in (
        "captcha",
        "verify you are human",
        "unusual traffic",
        "robot check",
        "inicia sesión",
        "sign in to continue",
    ))


def _wait_for_listing(agent: Any, hotel_name: str | None, timeout: float = 15) -> None:
    """Wait for Google's async listing before Jev makes its first choice.

    Jev Ultrafast observes the document once in ``Agent.__init__``. Google
    Maps can report ``readyState=complete`` while its app shell still has no
    visible text or controls, which otherwise makes Jev choose BLOCKED.
    """

    tokens = re.findall(r"\w+", (hotel_name or "").casefold())
    if tokens and tokens[0] == "servatur":
        tokens = tokens[1:]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        page = agent.state["page"]
        text = str(page.get("text") or "")
        url = str(page.get("url") or "")
        if "consent.google.com" in url or (
            len(text) >= 100
            and page.get("actions")
            and (not tokens or all(token in text.casefold() for token in tokens))
        ):
            return
        time.sleep(0.25)
        agent.state["page"] = agent.browser.observe(screenshot=agent.screenshots)
    raise JevNavigationError("Google no terminó de cargar la ficha del hotel en 15 segundos.")


def _element_rect(browser: Any, selector: str) -> dict[str, float] | None:
    expression = """(() => {
        const element = document.querySelector(%s);
        if (!element) return null;
        const r = element.getBoundingClientRect();
        return {x:r.x, y:r.y, width:r.width, height:r.height,
                viewportWidth:innerWidth, viewportHeight:innerHeight};
    })()""" % json.dumps(selector)
    return browser.evaluate(expression)


def _click_visible_control(browser: Any, selector: str) -> bool:
    """Click an observed DOM control through normal browser input."""

    for _ in range(5):
        rect = _element_rect(browser, selector)
        if not rect:
            return False
        x = rect["x"] + rect["width"] / 2
        y = rect["y"] + rect["height"] / 2
        viewport_height = rect["viewportHeight"]
        if rect["width"] > 0 and rect["height"] > 0 and 0 <= x < rect["viewportWidth"] and 0 <= y < viewport_height:
            browser.call("Input.dispatchMouseEvent", type="mouseMoved", x=rect["viewportWidth"] - 4,
                         y=viewport_height - 4)
            time.sleep(0.12)
            for event in ("mousePressed", "mouseReleased"):
                browser.call("Input.dispatchMouseEvent", type=event, x=x, y=y, button="left", clickCount=1)
            time.sleep(0.2)
            return True
        if rect["width"] <= 0 or rect["height"] <= 0:
            return False
        delta = max(-2000, min(2000, int(y - viewport_height / 2)))
        browser.call("Input.dispatchMouseEvent", type="mouseWheel", x=rect["viewportWidth"] / 2,
                     y=viewport_height * 0.75, deltaX=0, deltaY=delta)
        time.sleep(0.2)
    return False


def _text_control_rect(browser: Any, selector: str, label: str) -> dict[str, float] | None:
    expression = """(() => {
        const el = Array.from(document.querySelectorAll(%s))
          .find(item => item.textContent.trim() === %s);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x:r.x, y:r.y, width:r.width, height:r.height,
                viewportWidth:innerWidth, viewportHeight:innerHeight};
    })()""" % (json.dumps(selector), json.dumps(label))
    return browser.evaluate(expression)


def _click_text_control(browser: Any, selector: str, label: str) -> bool:
    for _ in range(6):
        rect = _text_control_rect(browser, selector, label)
        if not rect or rect["width"] <= 0 or rect["height"] <= 0:
            return False
        x = rect["x"] + rect["width"] / 2
        y = rect["y"] + rect["height"] / 2
        if 0 <= x < rect["viewportWidth"] and 0 <= y < rect["viewportHeight"]:
            browser.call("Input.dispatchMouseEvent", type="mouseMoved", x=rect["viewportWidth"] - 4,
                         y=rect["viewportHeight"] - 4)
            time.sleep(0.12)
            for event in ("mousePressed", "mouseReleased"):
                browser.call("Input.dispatchMouseEvent", type=event, x=x, y=y, button="left", clickCount=1)
            time.sleep(0.25)
            return True
        dy = max(-2000, min(2000, int(y - rect["viewportHeight"] / 2)))
        browser.call("Input.dispatchMouseEvent", type="mouseWheel", x=rect["viewportWidth"] / 2,
                     y=rect["viewportHeight"] * 0.75, deltaX=0, deltaY=dy)
        time.sleep(0.2)
    return False


def _selected_topic(browser: Any, label: str) -> bool:
    return bool(browser.evaluate(
        "Array.from(document.querySelectorAll('.ZDdmlb button'))"
        ".some(el => el.textContent.trim() === %s && el.getAttribute('aria-pressed') === 'true')"
        % json.dumps(label)
    ))


def _choose_travel_option(browser: Any, listbox_label: str, option_label: str) -> bool:
    listbox = f'[role="listbox"][aria-label="{listbox_label}"]'
    option = f'{listbox} [role="option"][aria-label="{option_label}"]'
    selected = browser.evaluate(
        "document.querySelector(%s)?.querySelector('[aria-selected=true]')?.getAttribute('aria-label')" % json.dumps(listbox)
    )
    if selected == option_label:
        return True
    if not _click_visible_control(browser, listbox):
        return False
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        rect = _element_rect(browser, option)
        if rect and rect["width"] > 0 and rect["height"] > 0:
            break
        time.sleep(0.1)
    clicked = _click_visible_control(browser, option)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        selected = browser.evaluate(
            "document.querySelector(%s)?.querySelector('[aria-selected=true]')?.getAttribute('aria-label')" % json.dumps(listbox)
        )
        if selected == option_label:
            return True
        if not clicked:
            break
        time.sleep(0.1)
    return False


def _travel_card_signature(browser: Any) -> list[str]:
    return browser.evaluate(
        "Array.from(document.querySelectorAll('.Svr5cf.bKhjM')).slice(0, 3)"
        ".map(card => card.querySelector('a.DHIhE')?.textContent || card.textContent.slice(0, 80))"
    ) or []


def _wait_for_travel_cards(browser: Any, previous: list[str], timeout: float = 1.5) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _travel_card_signature(browser) != previous:
            time.sleep(0.2)
            return
        time.sleep(0.15)


def _expand_travel_topics(browser: Any) -> list[str]:
    more = '[aria-label*="filtros de reseñas más"]'
    if _element_rect(browser, more):
        _click_visible_control(browser, more)
        time.sleep(0.3)
    labels = browser.evaluate(
        "Array.from(document.querySelectorAll('.ZDdmlb button'))"
        ".map(el => el.textContent.trim())"
        ".filter(text => /^.+ \\(\\d+\\)$/.test(text))"
    ) or []
    return list(dict.fromkeys(labels))


def _collect_travel_reviews(browser: Any, *, source_url: str, hotel_name: str | None,
                            captured_at: str, navigation_steps: int, max_reviews: int | None,
                            checkpoint: Callable[[GoogleReviewsResult], None] | None = None) -> GoogleReviewsResult:
    before_filter = _travel_card_signature(browser)
    google_filter = _choose_travel_option(browser, "Revisar opciones de fuentes", "Google")
    if google_filter:
        _wait_for_travel_cards(browser, before_filter)
    collected: dict[str, Any] = {}
    result: GoogleReviewsResult | None = None
    sort_modes = ("Más recientes", "Puntuación más alta", "Puntuación más baja", "Más útiles")
    verified_sorts: list[str] = []
    topic_labels = _expand_travel_topics(browser)
    # The "Todas" chip provides baseline coverage; topic chips expose more
    # Google-authored reviews that do not appear in the initial unfiltered set.
    topics = ["Todas", *topic_labels]
    active_sort: str | None = None
    completed_contexts: list[dict[str, str]] = []
    unavailable_contexts: list[dict[str, str]] = []
    stopped_early = False
    blocked = False
    for topic_index, topic in enumerate(topics, start=1):
        before_topic = _travel_card_signature(browser)
        already_selected = _selected_topic(browser, topic)
        if not already_selected:
            if not _click_text_control(browser, ".ZDdmlb button", topic):
                unavailable_contexts.extend({"topic": topic, "sort": sort_label} for sort_label in sort_modes)
                continue
            _wait_for_travel_cards(browser, before_topic)
            if not _selected_topic(browser, topic):
                unavailable_contexts.extend({"topic": topic, "sort": sort_label} for sort_label in sort_modes)
                continue
        for sort_label in sort_modes:
            if _blocked_page(browser):
                blocked = True
                break
            selected_before = browser.evaluate(
                "document.querySelector(%s)?.querySelector('[aria-selected=true]')?.getAttribute('aria-label')"
                % json.dumps('[role="listbox"][aria-label="Revisar opciones de orden"]')
            )
            if selected_before != sort_label:
                before_sort = _travel_card_signature(browser)
                if _choose_travel_option(browser, "Revisar opciones de orden", sort_label):
                    verified_sorts.append(sort_label)
                    _wait_for_travel_cards(browser, before_sort)
                    active_sort = sort_label
                else:
                    unavailable_contexts.append({"topic": topic, "sort": sort_label})
                    continue
            elif active_sort is None:
                active_sort = sort_label
                verified_sorts.append(sort_label)
            html = browser.evaluate("document.documentElement.outerHTML") or ""
            result = parse_reviews_html(
                html,
                source_url=source_url,
                final_url=browser.evaluate("location.href"),
                captured_at=captured_at,
                fallback_hotel_name=hotel_name,
                navigation_steps=navigation_steps,
            )
            if result.status == "blocked":
                blocked = True
                break
            for review in result.reviews:
                key = review.reviewId or "|".join((review.authorName or "", str(review.rating or ""),
                                                     review.text or "", review.publishedAt or "",
                                                     review.relativePublishedAt or ""))
                contexts = list(collected.get(key, review).discoveryContexts or [])
                context = {"topic": topic, "sort": sort_label, "source": "google_hotels"}
                if context not in contexts:
                    contexts.append(context)
                review.discoveryContexts = contexts
                collected[key] = review
            completed_contexts.append({"topic": topic, "sort": sort_label})
            if checkpoint:
                result.reviews = list(collected.values())[:max_reviews] if max_reviews else list(collected.values())
                result.status = "partial"
                result.coverage = {"strategy": "google_hotels_topics_and_sorts_v1",
                                   "completedContexts": completed_contexts,
                                   "configuredContextCount": len(topics) * len(sort_modes),
                                   "historicalCompletenessVerified": False}
                checkpoint(result)
            if sort_label == sort_modes[-1]:
                print(f"{hotel_name or 'Hotel'}: tema {topic_index}/{len(topics)}, "
                      f"{len(collected)} reseñas únicas", file=sys.stderr, flush=True)
            if max_reviews and len(collected) >= max_reviews:
                stopped_early = len(collected) >= max_reviews
                break
        if (max_reviews and len(collected) >= max_reviews) or blocked:
            break

    if result is None:
        result = parse_reviews_html(
            browser.evaluate("document.documentElement.outerHTML") or "",
            source_url=source_url, final_url=browser.evaluate("location.href"),
            captured_at=captured_at, fallback_hotel_name=hotel_name,
            navigation_steps=navigation_steps,
        )
    result.reviews = list(collected.values())[:max_reviews] if max_reviews else list(collected.values())
    if blocked:
        result.status = "partial" if result.reviews else "blocked"
        result.message = "Google interrumpió la vista; se conservaron las reseñas visibles." if result.reviews else "Google bloqueó la vista de reseñas."
    elif max_reviews and len(collected) >= max_reviews:
        result.status = "partial"
        result.message = "Se alcanzó el límite solicitado antes de recorrer todas las vistas configuradas."
    elif result.reviews and google_filter and not unavailable_contexts and len(completed_contexts) == len(topics) * len(sort_modes):
        result.status = "exhausted"
        result.message = "Se recorrieron las combinaciones públicas de temas y orden; Google no acredita que sean todas las reseñas históricas."
    elif result.reviews:
        result.status = "partial"
        result.message = "No se pudieron verificar todos los filtros y ordenaciones públicos; la cobertura es parcial."
    result.coverage = {
        "strategy": "google_hotels_topics_and_sorts_v1",
        "attemptedTopics": topics,
        "attemptedSorts": list(sort_modes),
        "verifiedSorts": list(dict.fromkeys(verified_sorts)),
        "completedContexts": completed_contexts,
        "unavailableContexts": unavailable_contexts,
        "configuredContextCount": len(topics) * len(sort_modes),
        "completedContextCount": len(completed_contexts),
        "limitReached": stopped_early,
        "googleSourceFilterVerified": google_filter,
        "blocked": blocked,
        "historicalCompletenessVerified": False,
    }
    if result.reviews:
        result.message = result.message or None
    return result


def _collect_maps_reviews(browser: Any, *, source_url: str, hotel_name: str | None,
                          captured_at: str, navigation_steps: int, max_reviews: int | None,
                          checkpoint: Callable[[GoogleReviewsResult], None] | None = None) -> GoogleReviewsResult:
    """Scroll only the public Maps review pane, expanding visible review text."""
    import time

    collected: dict[str, Any] = {}
    stagnant = 0
    loops = 0
    blocked_after_reviews = False
    blocked_before_reviews = False
    last_result: GoogleReviewsResult | None = None
    while (not max_reviews or len(collected) < max_reviews) and stagnant < 4 and loops < 400:
        if _blocked_page(browser):
            blocked_after_reviews = bool(collected)
            blocked_before_reviews = not collected
            break
        loops += 1
        # Expand only visible review cards through their own public controls.
        browser.evaluate("""(() => {
          const labels = new Set(['more', 'read more', 'más', 'ver más', 'leer más']);
          for (const card of document.querySelectorAll('[data-review-id]')) {
            for (const button of card.querySelectorAll('button,[role=button]')) {
              const label = `${button.getAttribute('aria-label') || ''} ${button.innerText || ''}`.trim().toLowerCase();
              if (labels.has(label) || [...labels].some(item => label.endsWith(` ${item}`))) button.click();
            }
          }
        })()""")
        html = browser.evaluate("document.documentElement.outerHTML") or ""
        last_result = parse_reviews_html(
            html, source_url=source_url, final_url=browser.evaluate("location.href"),
            captured_at=captured_at, fallback_hotel_name=hotel_name,
            navigation_steps=navigation_steps + loops,
        )
        prior_count = len(collected)
        for review in last_result.reviews:
            key = review.reviewId or "|".join((review.authorName or "", str(review.rating or ""),
                                                 review.text or "", review.publishedAt or "",
                                                 review.relativePublishedAt or ""))
            if key not in collected:
                review.discoveryContexts = [{"surface": "google_maps_reviews_pane", "scroll": loops}]
                collected[key] = review
            else:
                contexts = collected[key].discoveryContexts
                context = {"surface": "google_maps_reviews_pane", "scroll": loops}
                if context not in contexts:
                    contexts.append(context)
        if len(collected) == prior_count:
            stagnant += 1
        else:
            stagnant = 0
        blocked_after_reviews = bool(collected) and _blocked_page(browser)
        if checkpoint and last_result:
            last_result.reviews = list(collected.values())[:max_reviews] if max_reviews else list(collected.values())
            last_result.status = "partial" if blocked_after_reviews or (max_reviews and len(collected) >= max_reviews) else "ok"
            last_result.coverage = {"strategy": "google_maps_public_review_pane_scroll_v1",
                                    "scrollIterations": loops, "stagnantIterations": stagnant,
                                    "historicalCompletenessVerified": False}
            checkpoint(last_result)
        if (max_reviews and len(collected) >= max_reviews) or blocked_after_reviews:
            break
        # Discover the scrollable ancestor that actually contains review cards;
        # do not scroll the whole page or query undocumented network endpoints.
        scrolled = browser.evaluate("""(() => {
          const cards = [...document.querySelectorAll('[data-review-id]')];
          const card = cards.at(-1);
          if (!card) return false;
          let node = card;
          while (node && node !== document.body) {
            if (node.scrollHeight > node.clientHeight + 40 && node.clientHeight > 80) {
              const before = node.scrollTop;
              node.scrollTop = Math.min(node.scrollHeight, before + Math.max(240, node.clientHeight * 0.8));
              return node.scrollTop > before;
            }
            node = node.parentElement;
          }
          return false;
        })()""")
        if not scrolled:
            stagnant += 1
        time.sleep(0.45)
    if last_result is None:
        last_result = parse_reviews_html("", source_url=source_url, captured_at=captured_at,
                                         fallback_hotel_name=hotel_name, navigation_steps=navigation_steps)
    last_result.reviews = list(collected.values())[:max_reviews] if max_reviews else list(collected.values())
    published_count = last_result.reviewCount
    visible_count = len(collected)
    limited_public_view = False
    try:
        limited_public_view = bool(browser.evaluate("""(() => {
          const text = (document.body?.innerText || '').toLowerCase();
          return text.includes('vista limitada de google maps') ||
                 text.includes('limited view of google maps');
        })()"""))
    except Exception:
        pass
    if blocked_before_reviews:
        last_result.status = "blocked"
        last_result.message = "Google bloqueó el panel de reseñas."
    elif blocked_after_reviews or (max_reviews and len(collected) >= max_reviews):
        last_result.status = "partial"
        last_result.message = "La captura se detuvo en un límite de acceso o en el máximo solicitado."
    elif limited_public_view or (published_count is not None and published_count > visible_count):
        last_result.status = "partial"
        if limited_public_view and visible_count == 0:
            last_result.message = "Google Maps mostró una vista pública limitada y no cargó tarjetas de reseñas; el total publicado no se considera extraído."
        else:
            last_result.message = "El recorrido visible terminó, pero Google muestra más reseñas publicadas que tarjetas recuperadas; el historial queda incompleto."
    elif loops >= 400 and last_result.reviews:
        last_result.status = "partial"
        last_result.message = "Se alcanzó el límite técnico de 400 desplazamientos; la cobertura puede continuar en otra captura."
    elif last_result.reviews:
        last_result.status = "exhausted"
        last_result.message = "El panel dejó de cargar nuevas tarjetas; no se puede verificar el historial completo."
    last_result.coverage = {
        "strategy": "google_maps_public_review_pane_scroll_v1",
        "scrollIterations": loops,
        "stagnantIterations": stagnant,
        "limitReached": bool(max_reviews and len(collected) >= max_reviews),
        "traversalCapReached": loops >= 400 and stagnant < 4,
        "blockedAfterPartialResults": blocked_after_reviews,
        "blockedBeforeResults": blocked_before_reviews,
        "limitedPublicView": limited_public_view,
        "publishedReviewCount": published_count,
        "observedReviewCount": visible_count,
        "publishedCountExceedsObserved": bool(published_count is not None and published_count > visible_count),
        "historicalCompletenessVerified": False,
    }
    return last_result


def collect_with_jev(
    url: str,
    *,
    hotel_name: str | None = None,
    record_dir: str | None = None,
    max_reviews: int | None = 20,
    budget_usd: float | None = None,
    estimated_decision_cost_usd: float | None = None,
    max_decisions: int | None = None,
    checkpoint: Callable[[GoogleReviewsResult], None] | None = None,
    typesafe_api_key: str | None = None,
    openrouter_api_key: str | None = None,
) -> GoogleReviewsResult:
    """Navigate with Jev, then parse the final visible DOM deterministically.

    Jev owns bounded navigation decisions. It never supplies selectors or
    review values to the parser. This keeps the output testable and makes a
    future Atlas ingestion adapter independent from the model provider.

    I1-13: `typesafe_api_key`/`openrouter_api_key` llegan por argumento o por
    env del hijo (`TYPESAFE_API_KEY`/`OPENROUTER_API_KEY`); nunca se muta
    `os.environ` global aquí (el padre solo inyecta el env del hijo).
    """

    if max_reviews is not None and not 1 <= max_reviews <= 10000:
        raise ValueError("max_reviews debe ser None (hasta agotar recorrido) o estar entre 1 y 10000.")

    try:
        from jev_ultrafast import Agent
    except ImportError as exc:  # pragma: no cover - optional live dependency
        raise JevUnavailable(
            "Instala el sidecar Jev Ultrafast según side_projects/atlas_google_reviews_jev/README.md"
        ) from exc

    provider = (os.environ.get("ATLAS_JEV_PROVIDER", "typesafe") or "typesafe").casefold()
    resolved_typesafe_key = (typesafe_api_key or os.environ.get("TYPESAFE_API_KEY") or "").strip()
    resolved_openrouter_key = (openrouter_api_key or os.environ.get("OPENROUTER_API_KEY") or "").strip()
    jev_usage: dict[str, Any] = {"decisions": 0, "reportedCostUsd": 0.0, "estimatedCostUsd": 0.0,
                                 "costBasis": "unavailable"}
    if provider == "openrouter":
        try:
            from .openrouter_jev import route_jev_through_openrouter

            model_module = importlib.import_module("jev_ultrafast.model")
            provider_context = route_jev_through_openrouter(
                model_module, budget_usd=budget_usd,
                estimated_decision_cost_usd=estimated_decision_cost_usd,
                max_decisions=max_decisions,
                usage=jev_usage,
                openrouter_api_key=resolved_openrouter_key or None,
            )
        except (ImportError, RuntimeError) as exc:
            raise JevUnavailable(str(exc)) from exc
    elif provider == "typesafe":
        provider_context = nullcontext()
        if not resolved_typesafe_key:
            raise JevUnavailable("Configura TYPESAFE_API_KEY o usa ATLAS_JEV_PROVIDER=openrouter.")
    else:
        raise JevUnavailable("ATLAS_JEV_PROVIDER debe ser 'typesafe' u 'openrouter'.")

    target_hotel = hotel_name or "el hotel que aparece en el enlace"
    if "/travel/hotels/entity/" in url and "/reviews" in url:
        goal = (
            f"Confirm that the Google Hotels reviews page belongs to {target_hotel} "
            "and displays individual review cards. If Google shows a cookie choice, "
            "select 'Reject all' or 'Rechazar todo' to decline optional cookies. "
            "Choose DONE when individual review cards are visible. Choose BLOCKED "
            "for CAPTCHA, login, or an unverifiable page. Do not post, book, or submit forms."
        )
    else:
        goal = (
            f"Find the Google Maps listing for {target_hotel} and open its Reviews tab. "
            "If Google shows a cookie choice, select 'Reject all' or 'Rechazar todo' "
            "to decline optional cookies and continue. If a control shows more "
            "reviews, open it until individual review cards are visible. Choose "
            "DONE only when review cards are visibly present. Choose BLOCKED for "
            "CAPTCHA, login, or an unverifiable page. Do not post, book, or submit forms."
        )
    started = time.monotonic()
    last_state: dict[str, Any] | None = None
    try:
        with provider_context:
            with Agent(url, goal, record_dir=record_dir) as agent:
                _wait_for_listing(agent, hotel_name)
                for state in agent.run():
                    last_state = state
                    if time.monotonic() - started > 90:
                        raise JevNavigationError("Se alcanzó el límite de 90 segundos del sidecar Jev.")
                if not last_state:
                    raise JevNavigationError("Jev no devolvió ningún estado de navegación.")
                browser = agent.browser
                if last_state.get("status") == "blocked" or _blocked_page(browser):
                    interface_language = browser.evaluate("document.documentElement.lang || navigator.language")
                    result = GoogleReviewsResult(
                        status="blocked",
                        sourceUrl=url,
                        finalUrl=browser.evaluate("location.href"),
                        hotelName=hotel_name,
                        capturedAt=_now(),
                        navigationSteps=len(last_state.get("history") or []),
                        message="Jev detuvo la navegación porque la página estaba bloqueada o no era verificable.",
                    )
                    result.coverage = {"strategy": "jev_public_ui_navigation", "historicalCompletenessVerified": False,
                                       "interfaceLanguage": interface_language or None,
                                       "finalUrl": result.finalUrl,
                                       "navigationSteps": result.navigationSteps,
                                       "durationSeconds": round(time.monotonic() - started, 2)}
                    result.modelDecisions = jev_usage["decisions"]
                    result.estimatedCostUsd = round(jev_usage["reportedCostUsd"] + jev_usage["estimatedCostUsd"], 8)
                    result.costBasis = jev_usage["costBasis"]
                    return result
                html = browser.evaluate("document.documentElement.outerHTML") or ""
                final_url = browser.evaluate("location.href")
                captured_at = _now()
                if "/travel/hotels/entity/" in final_url and "/reviews" in final_url:
                    result = _collect_travel_reviews(
                        browser,
                        source_url=url,
                        hotel_name=hotel_name,
                        captured_at=captured_at,
                        navigation_steps=len(last_state.get("history") or []),
                        max_reviews=max_reviews,
                        checkpoint=checkpoint,
                    )
                elif "/maps/" in final_url:
                    result = _collect_maps_reviews(
                        browser, source_url=url, hotel_name=hotel_name,
                        captured_at=captured_at, navigation_steps=len(last_state.get("history") or []),
                        max_reviews=max_reviews,
                        checkpoint=checkpoint,
                    )
                else:
                    result = parse_reviews_html(
                        html, source_url=url, final_url=final_url, captured_at=captured_at,
                        fallback_hotel_name=hotel_name,
                        navigation_steps=len(last_state.get("history") or []),
                    )
                result.modelDecisions = jev_usage["decisions"]
                result.estimatedCostUsd = round(jev_usage["reportedCostUsd"] + jev_usage["estimatedCostUsd"], 8)
                result.costBasis = jev_usage["costBasis"]
                result.coverage = dict(result.coverage or {})
                result.coverage.update({
                    "interfaceLanguage": browser.evaluate("document.documentElement.lang || navigator.language") or None,
                    "finalUrl": final_url,
                    "navigationSteps": len(last_state.get("history") or []),
                    "durationSeconds": round(time.monotonic() - started, 2),
                    "modelDecisions": jev_usage["decisions"],
                    "estimatedCostUsd": result.estimatedCostUsd,
                    "costBasis": result.costBasis,
                })
                return result
    except JevNavigationError:
        raise
    except Exception as exc:
        from .openrouter_jev import JevBudgetExceeded
        if isinstance(exc, JevBudgetExceeded):
            return GoogleReviewsResult(
                status="budget_exhausted", sourceUrl=url, hotelName=hotel_name,
                capturedAt=_now(), message=str(exc),
                modelDecisions=jev_usage["decisions"],
                estimatedCostUsd=round(jev_usage["reportedCostUsd"] + jev_usage["estimatedCostUsd"], 8),
                costBasis=jev_usage["costBasis"],
                coverage={"strategy": "jev_public_ui_navigation", "historicalCompletenessVerified": False,
                          "modelDecisions": jev_usage["decisions"],
                          "durationSeconds": round(time.monotonic() - started, 2),
                          "budgetExceededByProviderCost": bool(jev_usage.get("budgetExceededByProviderCost"))},
            )
        raise JevNavigationError(f"Falló la navegación Jev: {exc}") from exc
