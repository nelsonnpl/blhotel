from backend.app.copilot_gateway import route_request
from backend.app.copilot_gateway import select_model
from backend.app.copilot_gateway import MAX_EXPERT_CONTEXT_CHARS, project_context_for_experts
import json
from backend.app.config import OpenRouterSettings


def _models() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test", model="legacy", base_url="https://example.test")


def test_simple_hotel_question_uses_one_expert() -> None:
    plan = route_request("¿Cuál es el ADR medio del mercado?")

    assert plan["strategy"] == "single_expert"
    assert plan["experts"] == ["hotel_revenue"]
    assert plan["aggregation"] == "direct"


def test_air_question_routes_to_air_and_quality_experts() -> None:
    plan = route_request("Compara vuelos y conectividad por mercado emisor", "analysis")

    assert plan["strategy"] == "expert_panel"
    assert plan["experts"] == ["air_access", "data_quality"]
    assert plan["aggregation"] == "single_call_synthesis"


def test_decision_question_always_includes_quality_expert() -> None:
    plan = route_request("¿Puedo subir el precio?", "decision")

    assert plan["complexity"] == "complex"
    assert plan["experts"] == ["hotel_revenue", "market_checker", "data_quality"]
    assert plan["aggregation"] == "multi_call_synthesis"


def test_simple_questions_use_luna_and_air_analysis_uses_glm_flash() -> None:
    settings = _models()

    simple = select_model(route_request("¿Cuál es el ADR medio?"), settings)
    air = select_model(route_request("Compara vuelos por mercado emisor", "analysis"), settings)

    assert simple["model"] == "openai/gpt-5.6-luna"
    assert air["model"] == "z-ai/glm-5.3-flash"


def test_complex_question_never_uses_fast_model_in_quick_mode() -> None:
    settings = _models()
    selected = select_model(route_request("¿Puedo subir el precio?", "quick"), settings)
    assert selected["model"] == "deepseek/deepseek-v4-pro-0813"


def test_attachments_route_to_multimodal_gemini_without_user_model_choice() -> None:
    settings = _models()
    selected = select_model(
        route_request("Resume este informe"),
        settings,
        capabilities={"hasAttachments": True, "needsVision": True},
    )

    assert selected["model"] == "google/gemini-3.8-flash"
    assert "archivos" in selected["selectionReason"]


def test_retired_model_override_is_replaced_by_the_role_default() -> None:
    settings = OpenRouterSettings(
        api_key="test",
        model="openai/gpt-6-astra",
        base_url="https://example.test",
        fast_model="openai/gpt-5.6-sol",
        hotel_model="openai/gpt-5.6-terra",
        critic_model="anthropic/claude-sonnet-5",
        synthesis_model="openai/gpt-6-astra",
    )

    selected = select_model(route_request("¿Cuál es el ADR medio?"), settings)

    assert selected["model"] == "openai/gpt-5.6-luna"
    assert "económico" in selected["selectionReason"]


def test_auto_route_marks_recommendation_from_conversation_intent() -> None:
    plan = route_request("Con estos datos, ¿me recomiendas subir la tarifa?", "auto")

    assert plan["requestedMode"] == "auto"
    assert plan["requiresRecommendation"] is True
    assert plan["complexity"] == "complex"


def test_follow_up_uses_prior_user_turns_for_routing_without_model_text() -> None:
    plan = route_request(
        "¿y la anterior?",
        "auto",
        history=[
            {"role": "user", "content": "Compara la tarifa aérea con la hotelera"},
            {"role": "assistant", "content": "Te recomiendo subir un 5%"},
        ],
    )

    assert plan["experts"] == ["hotel_revenue", "air_access", "data_quality"]
    assert plan["complexity"] == "complex"


def test_air_projection_excludes_hotel_payload_and_keeps_traceability() -> None:
    context = {
        "zonaActiva": {"id": 1},
        "mercado": {"adrMedio": 250},
        "riu": {"hoteles": [{"nombre": "RIU"}]},
        "senalesAereas": {
            "resumen": {"rutas": 9},
            "rutas": [{"mercado": f"Mercado {index}", "precioMin": index} for index in range(9)],
        },
        "evidencia": {
            "schemaVersion": "revenue-evidence.v1",
            "records": [
                {"evidenceId": "air", "entityType": "route", "metric": "precio", "value": 50},
                {"evidenceId": "hotel", "entityType": "hotel", "metric": "adr", "value": 200},
            ],
        },
    }

    projected = project_context_for_experts(context, ["air_access", "data_quality"])

    assert "mercado" not in projected
    assert "riu" not in projected
    assert projected["senalesAereas"]["rutasRecortadas"] == 1
    assert [record["evidenceId"] for record in projected["evidencia"]["records"]] == ["air"]


def test_expert_projection_has_global_context_budget_and_keeps_quality_evidence() -> None:
    context = {
        "zonaActiva": {"id": 1},
        "calidadAnalisis": {"estado": "vigente"},
        "dataGate": {"allowed": True},
        "mercado": {"series": [{"label": "x" * 1500} for _ in range(80)]},
        "evidencia": {
            "schemaVersion": "revenue-evidence.v1",
            "records": [{"evidenceId": "keep", "entityType": "market", "metric": "adr", "value": 200}],
        },
    }

    projected = project_context_for_experts(context, ["hotel_revenue", "data_quality"])

    assert len(json.dumps(projected, ensure_ascii=False, separators=(",", ":"))) <= MAX_EXPERT_CONTEXT_CHARS
    assert projected["calidadAnalisis"]["estado"] == "vigente"
    assert projected["evidencia"]["records"][0]["evidenceId"] == "keep"


def test_project_context_preserves_redacted_attachments() -> None:
    projected = project_context_for_experts(
        {
            "zonaActiva": {"id": 1},
            "adjuntos": [{"id": 7, "filename": "ventas.csv", "mediaType": "text/csv", "text": "hotel,adr\nDemo,245"}],
        },
        ["hotel_revenue"],
    )

    assert projected["adjuntos"] == [{
        "id": 7,
        "filename": "ventas.csv",
        "mediaType": "text/csv",
        "extractionStatus": None,
        "text": "hotel,adr\nDemo,245",
    }]
