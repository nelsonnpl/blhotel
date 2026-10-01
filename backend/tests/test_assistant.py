from __future__ import annotations

import time

import httpx
import pytest

from backend.app.assistant import AssistantError, _post_chat_completion, ask_openrouter, assistant_data_gate, validate_assistant_response
from backend.app.copilot_contracts import EvidenceBundle
from backend.app.config import OpenRouterSettings, load_settings
from backend.app.models import AssistantChatPayload


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test-key", model="test/model", base_url="https://example.test/v1")


@pytest.mark.parametrize("status", [400, 401, 404])
def test_provider_non_retryable_errors_fail_without_extra_attempt(status: int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, text="provider error", request=request)

    telemetry = {"attempts": 0}
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AssistantError):
            _post_chat_completion(
                client,
                _settings(),
                {},
                {"model": "test/model", "messages": []},
                time.monotonic() + 5,
                telemetry,
            )

    assert calls == 1
    assert telemetry["attempts"] == 1
    assert telemetry["providerStatusCodes"] == [status]
    assert len(telemetry["attemptLatenciesMs"]) == 1
    assert telemetry["retryCount"] == 0


def test_provider_payload_requests_parameters_and_zero_retention(monkeypatch) -> None:
    captured = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, _url, *, headers, json, timeout):
            captured.update(json)
            request = httpx.Request("POST", "https://example.test")
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}, request=request)

    monkeypatch.setattr("backend.app.assistant.httpx.Client", FakeClient)
    ask_openrouter(_settings(), "hola", {})

    assert captured["provider"] == {
        "require_parameters": True,
        "data_collection": "deny",
        "zdr": True,
    }
    # Luna endpoints do not advertise ``temperature``.  Keeping the payload
    # within their supported contract is required when strict provider
    # routing is enabled.
    assert "temperature" not in captured


def test_allow_data_collection_does_not_enable_zdr_implicitly(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_DATA_COLLECTION", "allow")
    monkeypatch.delenv("OPENROUTER_ZDR", raising=False)

    settings = load_settings(require_decodo=False)

    assert settings.openrouter.data_collection == "allow"
    assert settings.openrouter.zdr is False


def test_explicit_zdr_override_is_preserved(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_DATA_COLLECTION", "allow")
    monkeypatch.setenv("OPENROUTER_ZDR", "true")

    settings = load_settings(require_decodo=False)

    assert settings.openrouter.data_collection == "allow"
    assert settings.openrouter.zdr is True


def test_data_gate_blocks_stale_or_unmatched_context() -> None:
    gate = assistant_data_gate(
        {
            "zonaActiva": {"id": 1, "name": "Gran Canaria"},
            "calidadAnalisis": {
                "estado": "caducado",
                "etiqueta": "Caducado",
                "comparabilidadPct": 42,
            },
        }
    )

    assert gate["blocked"] is True
    assert len(gate["warnings"]) == 2


def test_assistant_history_contract_is_eight_turns() -> None:
    turns = [{"role": "user", "content": str(index)} for index in range(9)]

    with pytest.raises(ValueError):
        AssistantChatPayload(message="test", history=turns)


def test_decision_gate_warns_on_unmatched_context_without_riu() -> None:
    gate = assistant_data_gate(
        {
            "zonaActiva": {"id": 1, "name": "Gran Canaria"},
            "calidadAnalisis": {
                "estado": "actualizado",
                "comparacion": {"estado": "unmatched"},
            },
        },
        mode="decision",
    )

    assert gate["blocked"] is True
    assert any("emparejada" in warning for warning in gate["warnings"])
    assert any("RIU" in warning for warning in gate["warnings"])


def test_data_gate_only_removes_recommendation_permission_in_decision_mode() -> None:
    context = {
        "zonaActiva": {"id": 1, "name": "Gran Canaria"},
        "riu": {"hoteles": [{"nombre": "RIU"}]},
        "calidadAnalisis": {"estado": "caducado", "etiqueta": "Caducado", "comparabilidadPct": 95},
    }

    quick = assistant_data_gate(context, mode="quick")
    decision = assistant_data_gate(context, mode="decision")

    assert quick["blocked"] is True
    assert quick["canRecommend"] is True
    assert decision["blocked"] is True
    assert decision["canRecommend"] is False
    assert decision["severity"] == "blocked"


def test_evidence_bundle_is_versioned_and_keeps_metric_provenance() -> None:
    bundle = EvidenceBundle.model_validate(
        {
            "records": [
                {
                    "evidenceId": "hotel-market-adrMedio",
                    "metric": "adrMedio",
                    "entityType": "market",
                    "targetId": 1,
                    "value": 268,
                    "unit": "EUR/noche",
                    "observedAt": "2026-08-23T14:41:00Z",
                    "snapshotId": 18,
                    "sourceTable": "market_snapshot_hotels",
                    "quality": "stale",
                    "comparability": "matched_partial",
                    "calculation": "media de pricePerNight de filas comparables",
                }
            ]
        }
    )

    assert bundle.schemaVersion == "revenue-evidence.v1"
    assert bundle.records[0].snapshotId == 18
    assert bundle.records[0].calculation.startswith("media")


def test_response_quality_accepts_required_revenue_blocks() -> None:
    quality = validate_assistant_response(
        "**Lectura**\n...\n**Evidencia**\n...\n**Acción siguiente**\n...\n**Límite de confianza**\n..."
    )

    assert quality["status"] == "ok"
    assert quality["missingBlocks"] == []
    assert quality["forbiddenArtifacts"] == []


def test_response_quality_flags_missing_blocks_and_forbidden_artifacts() -> None:
    quality = validate_assistant_response("**Lectura**\n```mermaid\ngraph TD\nA-->B\n```")

    assert quality["status"] == "warning"
    assert "Evidencia" in quality["missingBlocks"]
    assert "```mermaid" in quality["forbiddenArtifacts"]
