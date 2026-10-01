from backend.app.config import OpenRouterSettings
from backend.app.copilot_evaluation import EVALUATION_CASES, run_data_gate_evaluation, run_evaluation, run_routing_evaluation
from backend.app.database import Database


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(api_key="test", model="legacy", base_url="https://example.test")


def test_routing_evaluation_passes_all_revenue_cases() -> None:
    results = run_routing_evaluation(_settings())

    assert len(results) == len(EVALUATION_CASES)
    assert all(item["passed"] for item in results)


def test_data_gate_evaluation_rejects_stale_and_unmatched_decisions() -> None:
    results = {item["id"]: item for item in run_data_gate_evaluation()}

    assert results["fresh_matched_context"]["canRecommend"] is True
    assert results["stale_context"]["canRecommend"] is False
    assert results["unmatched_context"]["canRecommend"] is False


def test_full_evaluation_is_provider_free_and_passes() -> None:
    summary = run_evaluation(_settings())

    assert summary["passed"] is True
    assert len(summary["routing"]) == len(EVALUATION_CASES)


def test_evaluation_record_keeps_only_technical_summary(tmp_path) -> None:
    database = Database(tmp_path / "copilot-evaluation.sqlite")
    result = run_evaluation(_settings())

    record = database.record_copilot_evaluation(result, source="offline_contract", provider_live=False)
    latest = database.latest_copilot_evaluation()

    assert record["passed"] is True
    assert latest is not None
    assert latest["source"] == "offline_contract"
    assert latest["providerLive"] is False
    assert latest["caseCount"] == len(EVALUATION_CASES) + 3
