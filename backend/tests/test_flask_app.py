from backend.app.flask_app import app


def test_health_stack_is_flask() -> None:
    client = app.test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["stack"] == "python-flask"


def test_invalid_query_returns_clear_400() -> None:
    client = app.test_client()
    response = client.get("/api/dashboard/metrics?targetId=abc")

    assert response.status_code == 400
    assert "targetId debe ser numerico" in response.get_json()["error"]


def test_unknown_route_returns_json_404() -> None:
    client = app.test_client()
    response = client.get("/api/no-existe")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_photo_detail_not_found_returns_json_404() -> None:
    client = app.test_client()
    response = client.get("/api/photos/999999")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_heatmap_requires_numeric_target_id() -> None:
    client = app.test_client()
    response = client.get("/api/hotels/heatmap?targetId=nope")

    assert response.status_code == 400
    assert "targetId debe ser numerico" in response.get_json()["error"]
