from dataclasses import replace

from backend.app import flask_app
from backend.app.models import MarketHotelRow, MarketSnapshot
from backend.app.weather import make_weather_record

app = flask_app.app


def test_health_stack_is_flask() -> None:
    client = app.test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["stack"] == "python-flask"
    assert "database" not in response.get_json()
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_invalid_query_returns_clear_400() -> None:
    client = app.test_client()
    response = client.get("/api/dashboard/metrics?targetId=abc")

    assert response.status_code == 400
    assert "targetId debe ser numerico" in response.get_json()["error"]


def test_istac_sync_rejects_unbounded_territory_scope() -> None:
    response = app.test_client().post(
        "/api/external/sync/istac",
        json={"datasetId": "C00065A_000038", "version": "1.43", "territoryCodes": ["ALL"]},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "datasetId o version de ISTAC no permitidos"


def test_workspace_copilot_context_is_calculated_from_ids_not_client_metrics(monkeypatch) -> None:
    class FakeDatabase:
        snapshot = MarketSnapshot(
            id=18, targetId=1, sourceUrl="https://example.test/market", requestedLimit=10,
            availableResults=2, capturedRows=2, scrapedAt="2026-08-23T14:41:00+00:00",
        )
        rows = [
            MarketHotelRow(hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a", price=700, pricePerNight=100, currency="EUR", checkIn="2026-10-06", nights=7, position=1),
            MarketHotelRow(hotelKey="hotel-b", hotelName="Hotel B", detailUrl="https://example.test/b", price=1400, pricePerNight=200, currency="EUR", checkIn="2026-10-06", nights=7, position=2),
        ]

        def snapshot_by_id(self, target_id, snapshot_id):
            return self.snapshot if (target_id, snapshot_id) == (1, 18) else None

        def capture_group_snapshot_ids(self, target_id, snapshot_id):
            return {"id": "capture-1", "kind": "capture_group", "snapshotIds": [18]}

        def snapshot_rows(self, snapshot_id):
            return self.rows if snapshot_id == 18 else []

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    context = flask_app.workspace_assistant_context(1, flask_app.AssistantWorkspaceContext(snapshotId=18, checkIn="2026-10-06"))

    assert context["population"] == {"totalRows": 2, "comparableRows": 2, "comparablePct": 100.0}
    assert context["metrics"]["adrMedian"] == 150.0
    assert context["topHotels"][0] == {"hotel": "Hotel B", "adrMean": 200.0}


def test_unknown_route_returns_json_404() -> None:
    client = app.test_client()
    response = client.get("/api/no-existe")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_attachment_redaction_preserves_iso_dates() -> None:
    redacted = flask_app._redact_attachment_text(
        "hotel,fecha,telefono\nDemo,2026-10-06,600 123 456"
    )

    assert "2026-10-06" in redacted
    assert "[teléfono oculto]" in redacted


def test_main_ui_exposes_accessible_data_navigation() -> None:
    client = app.test_client()
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'role="tabpanel" aria-labelledby="hotelTableTab"' in html
    assert 'role="tabpanel" aria-labelledby="airTableTab"' in html
    assert 'aria-label="Métrica del mapa"' in html
    assert '<caption class="sr-only">Histórico de tarifas hoteleras por captura</caption>' in html


def test_main_ui_shell_exposes_palette_capture_dialog_and_no_inline_scripts() -> None:
    import re

    client = app.test_client()
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # Selector de mercado, tema, barra contraíble y avisos del shell.
    for hook in ('id="marketBtn"', 'id="marketMenu"', 'id="themeBtn"', 'id="collapseBtn"', 'id="dataAge"', 'id="toasts"'):
        assert hook in html
    assert 'aria-live="polite"' in html
    # Paleta ⌘K y confirmación de captura son diálogos modales accesibles.
    assert re.search(r'id="palette"[\s\S]*?role="dialog" aria-modal="true"', html)
    assert re.search(r'id="captureDialog"[\s\S]*?role="dialog" aria-modal="true" aria-labelledby="captureDialogTitle"', html)
    # La CSP prohíbe scripts inline: todo <script> debe cargarse por src.
    assert not re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html)
    assert "onclick=" not in html


def test_csp_allows_carto_gl_styles_and_tiles_for_the_maps() -> None:
    # Los mapas usan los estilos vectoriales de CARTO (positron / dark-matter):
    # el style.json vive en el dominio raíz y las teselas, sprites y fuentes en subdominios.
    csp = app.test_client().get("/").headers["Content-Security-Policy"]
    connect = next(part for part in csp.split(";") if part.strip().startswith("connect-src"))
    assert "https://basemaps.cartocdn.com" in connect.split()
    assert "https://*.basemaps.cartocdn.com" in connect.split()
    assert "worker-src 'self' blob:" in csp


def test_weather_market_example_groups_coordinates_and_links_snapshot(monkeypatch) -> None:
    class FakeOpenMeteo:
        def __init__(self, *args, **kwargs):
            pass

        async def forecast_daily(self, **kwargs):
            return [make_weather_record(
                provider="open-meteo", dataset="forecast.daily", kind="forecast",
                location_key=kwargs["location_key"], valid_at="2026-09-10T00:00:00+00:00",
                retrieved_at=kwargs["retrieved_at"], capture_at=kwargs["capture_at"],
                values={"temperature_2m_max": 25.0}, units={"temperature_2m_max": "°C"},
                local_date="2026-09-10",
            )]

    class FakeDatabase:
        def __init__(self):
            self.snapshot = MarketSnapshot(
                id=77,
                targetId=7,
                sourceUrl="https://example.test/market",
                requestedLimit=50,
                availableResults=2,
                capturedRows=2,
                scrapedAt="2026-09-07T12:00:00+00:00",
            )
            self.rows = [
                MarketHotelRow(
                    hotelKey="/hotel/a", hotelName="Hotel A", detailUrl="https://example.test/a",
                    position=1, latitude=27.75, longitude=-15.58,
                ),
                MarketHotelRow(
                    hotelKey="/hotel/b", hotelName="Hotel B", detailUrl="https://example.test/b",
                    position=2, latitude=27.751, longitude=-15.581,
                ),
            ]

        def latest_snapshot(self, target_id):
            return self.snapshot if target_id == self.snapshot.targetId else None

        def snapshot_rows(self, snapshot_id):
            return self.rows if snapshot_id == self.snapshot.id else []

        def cached_weather_snapshot(self, *args, **kwargs):
            return None

        def persist_weather_records(self, records, **kwargs):
            return {"snapshotId": 101, "knownAtCaptureDays": 0, "days": len(records), "rows": len(records)}

    monkeypatch.setattr(flask_app, "OpenMeteoClient", FakeOpenMeteo)
    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    response = app.test_client().get("/api/weather/market-example?targetId=7&startDate=2026-09-10&endDate=2026-09-10")
    assert response.status_code == 200
    body = response.get_json()
    assert body["geographicGroups"] == body["weatherRequests"]
    assert body["assignments"]
    assert body["assignments"][0]["marketSnapshotId"] == body["marketSnapshotId"]


def test_weather_price_association_exposes_non_causal_contract(monkeypatch) -> None:
    class FakeDatabase:
        def weather_price_association(self, target_id, limit_snapshots):
            return {
                "schemaVersion": "weather-price-association.v1",
                "targetId": target_id,
                "status": "insufficient_sample",
                "observations": [],
                "pairs": [],
                "samplePairs": 0,
                "temperatureAdrCorrelation": None,
                "limitations": ["No representa demanda real."],
            }

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    response = app.test_client().get("/api/analytics/weather-price-association?targetId=7&snapshots=6")
    assert response.status_code == 200
    body = response.get_json()
    assert body["schemaVersion"] == "weather-price-association.v1"
    assert body["status"] == "insufficient_sample"
    assert body["temperatureAdrCorrelation"] is None


def test_detail_capture_job_queues_one_task_per_hotel(monkeypatch, tmp_path) -> None:
    from backend.app.database import Database

    isolated = Database(tmp_path / "detail-job.sqlite")
    target = isolated.upsert_target("Test", "https://booking.com/searchresults.html")

    class FakeWorker:
        def start(self):
            return None

        def enqueue(self, kind, payload, max_attempts=1):
            assert kind == "hotel_detail_capture"
            assert payload["batchId"]
            assert max_attempts == 1
            return {"id": "job-detail-1", "status": "queued"}

    monkeypatch.setattr(flask_app, "db", isolated)
    monkeypatch.setattr(flask_app, "active_job_worker", lambda: FakeWorker())
    response = app.test_client().post(
        "/api/jobs/hotel-detail-capture",
        json={
            "targetId": target.id,
            "hotels": [{"hotelKey": "/hotel/es/a", "hotelName": "Hotel A", "detailUrl": "https://booking.com/hotel/es/a.html"}],
            "checkIn": "2026-10-01", "checkOut": "2026-10-08", "adults": 2, "children": 0, "rooms": 1,
        },
    )
    assert response.status_code == 202
    body = response.get_json()
    assert body["tasks"] == 1
    assert isolated.conn.execute("SELECT COUNT(*) FROM hotel_detail_capture_tasks").fetchone()[0] == 1
    isolated.conn.close()


def test_air_payload_can_split_summary_from_paged_options() -> None:
    client = app.test_client()
    summary = client.get("/api/air-data?includeFlights=0")
    assert summary.status_code == 200
    assert "flights" not in summary.get_json()
    assert summary.get_json()["summary"]["total_routes"] > 0

    options = client.get("/api/air-data/options?page=1&pageSize=2")
    body = options.get_json()
    assert options.status_code == 200
    assert len(body["rows"]) == 2
    assert body["total"] >= 2
    assert body["page"] == 1
    assert body["pageSize"] == 2


def test_air_option_rows_sort_by_origin_and_date_and_filter_by_segment() -> None:
    from backend.app.flask_app import _filter_air_option_rows, _sort_air_option_rows

    rows = [
        {"origin": "MAN", "market_segment": "Británico", "outbound_date": "2026-10-08", "departure_time": "09:00", "price": 90},
        {"origin": "AMS", "market_segment": "Neerlandés", "outbound_date": "2026-10-06", "departure_time": "14:55", "price": 180},
        {"origin": "LGW", "market_segment": "Británico", "outbound_date": "2026-10-06", "departure_time": "07:10", "price": 120},
        {"origin": None, "market_segment": None, "outbound_date": None, "price": 50},
    ]
    assert [r["origin"] for r in _sort_air_option_rows(rows, "origin-asc")] == ["AMS", "LGW", "MAN", None]
    assert [r["origin"] for r in _sort_air_option_rows(rows, "origin-desc")] == ["MAN", "LGW", "AMS", None]
    assert [r["origin"] for r in _sort_air_option_rows(rows, "date-asc")] == ["LGW", "AMS", "MAN", None]
    assert [r["origin"] for r in _sort_air_option_rows(rows, "date-desc")] == ["MAN", "AMS", "LGW", None]
    british = _filter_air_option_rows(rows, {"segment": "Británico"})
    assert [r["origin"] for r in british] == ["MAN", "LGW"]


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


def test_dashboard_comparison_exposes_strict_product_coverage() -> None:
    client = app.test_client()
    response = client.get("/api/dashboard/metrics?targetId=1")

    assert response.status_code == 200
    body = response.get_json()
    comparison = body["comparison"]
    assert comparison["criteria"]
    assert 0 <= comparison["matchedCoveragePct"] <= 100
    assert comparison["matchedRows"] <= comparison["currentComparableRows"]
    assert body["movement"]["isComparable"] is (comparison["status"] == "matched")


def test_analytics_catalog_and_query_share_versioned_semantics(monkeypatch) -> None:
    class FakeDatabase:
        def dashboard_metrics(self, target_id, snapshot_id=None):
            assert target_id == 1
            assert snapshot_id == 11
            return {
                "latestSnapshot": {"id": 11, "scrapedAt": "2026-09-08T09:00:00+00:00"},
                "market": {"avgPricePerNight": 210.0, "medianPricePerNight": 200.0, "minPricePerNight": 100.0, "maxPricePerNight": 300.0},
                "rateShoppingIndex": {"totalCompetitors": 5},
                "movement": {"avgPricePerNightChangePct": 4.2},
                "comparison": {"matchedCoveragePct": 80.0, "matchedRows": 4, "status": "matched", "limits": "condiciones no verificadas"},
                "dataQuality": {"totalRows": 5, "pricedRows": 5, "comparableRows": 5, "comparablePct": 100.0},
            }

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    flask_app.clear_cache()
    client = app.test_client()
    catalog = client.get("/api/analytics/catalog")
    assert catalog.status_code == 200
    catalog_body = catalog.get_json()
    assert catalog_body["schemaVersion"] == "revenue-semantics.v1"
    assert {item["id"] for item in catalog_body["metrics"]} >= {"adr_mean", "adr_median", "hotel_count"}

    response = client.post(
        "/api/analytics/query",
        json={"targetId": 1, "snapshotId": 11, "metrics": ["adr_mean", "comparison_coverage_pct"]},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["schemaVersion"] == "analytics-query.v1"
    assert body["semanticVersion"] == catalog_body["schemaVersion"]
    assert body["scope"] == "snapshot"
    assert len(body["values"]) == 2
    assert body["provenance"]["snapshotId"]
    assert "formula" in body["values"][0]


def test_analytics_query_rejects_unknown_metric_and_filter() -> None:
    client = app.test_client()
    unknown_metric = client.post(
        "/api/analytics/query", json={"targetId": 1, "metrics": ["revpar"]}
    )
    assert unknown_metric.status_code == 400
    assert "Métricas no soportadas" in unknown_metric.get_json()["details"][0]["msg"]

    unknown_filter = client.post(
        "/api/analytics/query",
        json={"targetId": 1, "metrics": ["adr_mean"], "filters": {"roomType": "Double"}},
    )
    assert unknown_filter.status_code == 400
    assert "Filtros no soportados" in unknown_filter.get_json()["details"][0]["msg"]


def test_analytics_query_returns_hotel_breakdown_for_selected_photo(monkeypatch) -> None:
    class FakeDatabase:
        def dashboard_metrics(self, target_id, snapshot_id=None):
            return {
                "latestSnapshot": {"id": 11, "scrapedAt": "2026-09-08T09:00:00+00:00"},
                "market": {"avgPricePerNight": 150.0, "medianPricePerNight": 150.0, "minPricePerNight": 100.0, "maxPricePerNight": 200.0},
                "rateShoppingIndex": {"totalCompetitors": 2},
                "movement": {"avgPricePerNightChangePct": None},
                "comparison": {"matchedCoveragePct": 0, "matchedRows": 0, "status": "unmatched", "limits": None},
                "dataQuality": {"totalRows": 2, "pricedRows": 2, "comparableRows": 2, "comparablePct": 100.0},
            }

        def snapshot_rows(self, snapshot_id):
            return [
                MarketHotelRow(
                    hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a",
                    price=700, pricePerNight=100, currency="EUR", checkIn="2026-10-01",
                    checkOut="2026-10-08", nights=7, position=1,
                ),
                MarketHotelRow(
                    hotelKey="hotel-b", hotelName="Hotel B", detailUrl="https://example.test/b",
                    price=1400, pricePerNight=200, currency="EUR", checkIn="2026-10-08",
                    checkOut="2026-10-15", nights=7, position=2,
                ),
            ]

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/analytics/query",
        json={"targetId": 1, "snapshotId": 11, "dimensions": ["hotel"], "metrics": ["adr_mean", "hotel_count"], "limit": 1},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["breakdown"]) == 1
    assert body["pagination"] == {"limit": 1, "offset": 0, "total": 2, "returned": 1}
    assert body["breakdown"][0]["values"][0]["value"] in {100.0, 200.0}
    assert body["breakdown"][0]["labels"]["hotel"] in {"Hotel A", "Hotel B"}
    assert body["breakdown"][0]["population"]["distinctCheckIns"] == 1
    assert body["breakdown"][0]["population"]["checkIns"] in [["2026-10-01"], ["2026-10-08"]]


def test_analytics_query_applies_observation_filters_and_pagination(monkeypatch) -> None:
    class FakeDatabase:
        def dashboard_metrics(self, target_id, snapshot_id=None):
            return {
                "latestSnapshot": {"id": 11, "scrapedAt": "2026-09-08T09:00:00+00:00"},
                "market": {"avgPricePerNight": 150.0, "medianPricePerNight": 150.0, "minPricePerNight": 100.0, "maxPricePerNight": 200.0},
                "rateShoppingIndex": {"totalCompetitors": 2},
                "movement": {"avgPricePerNightChangePct": None},
                "comparison": {"matchedCoveragePct": 0, "matchedRows": 0, "status": "unmatched", "limits": None},
                "dataQuality": {"totalRows": 2, "pricedRows": 2, "comparableRows": 2, "comparablePct": 100.0},
            }

        def snapshot_rows(self, snapshot_id):
            return [
                MarketHotelRow(hotelKey="hotel-a", hotelName="Hotel A", detailUrl="https://example.test/a", price=700, pricePerNight=100, currency="EUR", checkIn="2026-10-01", nights=7, position=1),
                MarketHotelRow(hotelKey="hotel-b", hotelName="Hotel B", detailUrl="https://example.test/b", price=1400, pricePerNight=200, currency="EUR", checkIn="2026-10-08", nights=7, position=2),
            ]

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/analytics/query",
        json={"targetId": 1, "snapshotId": 11, "filters": {"hotelKey": "hotel-b"}, "metrics": ["adr_mean"]},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["values"][0]["value"] == 200.0
    assert body["population"]["totalRows"] == 1
    assert body["coverage"]["status"] == "not_applicable"


def test_hotel_history_keeps_hotel_key_for_product_matching(monkeypatch) -> None:
    hotel_key = "/hotel/es/aparthotel-green-field.html"

    class FakeDatabase:
        def get_target(self, target_id):
            return {"id": target_id}

        def can_access_target(self, owner_key, target_id):
            return target_id == 1

        def hotel_price_history(self, key, *, target_id, limit):
            assert (key, target_id, limit) == (hotel_key, 1, 2)
            return [{"hotelKey": key, "snapshotId": 18}]

    monkeypatch.setattr(flask_app, "db", FakeDatabase())
    response = app.test_client().get(
        f"/api/hotels/price-history?targetId=1&limit=2&hotelKey={hotel_key}"
    )

    assert response.status_code == 200
    assert response.get_json()["history"] == [{"hotelKey": hotel_key, "snapshotId": 18}]


def test_capture_history_exposes_extraction_groups() -> None:
    client = app.test_client()
    response = client.get("/api/captures/history?targetId=1&limit=40")

    assert response.status_code == 200
    captures = response.get_json()["captures"]
    if captures:
        capture = captures[0]
        assert capture["anchorSnapshotId"] in capture["snapshotIds"]
        assert capture["kind"] in {"capture_group", "legacy_inferred_capture_group"}
        assert capture["capturedRows"] >= capture["comparableRows"]


def test_workspace_create_and_optimistic_update() -> None:
    client = app.test_client()
    created = client.post(
        "/api/workspaces",
        json={"name": "Pulso semanal", "targetIds": [], "globalFilters": {}, "layers": []},
    )
    assert created.status_code == 201
    workspace = created.get_json()["workspace"]
    assert workspace["version"] == 1

    updated = client.put(
        f"/api/workspaces/{workspace['id']}",
        json={
            "name": "Pulso semanal",
            "targetIds": [],
            "globalFilters": {"linkGroup": "A"},
            "layers": [{"id": "layer-1", "type": "hotel-table"}],
            "expectedVersion": 1,
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["workspace"]["version"] == 2

    revisions = client.get(f"/api/workspaces/{workspace['id']}/revisions")
    assert revisions.status_code == 200
    history = revisions.get_json()["revisions"]
    assert [item["workspaceVersion"] for item in history] == [2, 1]
    assert history[0]["layers"] == [{"id": "layer-1", "type": "hotel-table"}]
    assert history[1]["name"] == "Pulso semanal"

    conflict = client.put(
        f"/api/workspaces/{workspace['id']}",
        json={"name": "Viejo", "targetIds": [], "globalFilters": {}, "layers": [], "expectedVersion": 1},
    )
    assert conflict.status_code == 409


def test_user_owned_workspaces_and_copilot_sessions_are_isolated() -> None:
    owner_a = app.test_client()
    owner_b = app.test_client()
    with owner_a.session_transaction() as browser_session:
        browser_session["ownerKey"] = "analyst-a"
    with owner_b.session_transaction() as browser_session:
        browser_session["ownerKey"] = "analyst-b"

    created = owner_a.post(
        "/api/workspaces",
        json={"name": "Solo A", "targetIds": [], "globalFilters": {}, "layers": []},
    )
    assert created.status_code == 201
    workspace_id = created.get_json()["workspace"]["id"]
    assert owner_a.get("/api/workspaces").get_json()["workspaces"][0]["ownerKey"] == "analyst-a"
    assert owner_b.get("/api/workspaces").get_json()["workspaces"] == []
    assert owner_b.put(
        f"/api/workspaces/{workspace_id}",
        json={"name": "No", "targetIds": [], "globalFilters": {}, "layers": []},
    ).status_code == 409

    session = owner_a.post("/api/assistant/sessions", json={"title": "Consulta A"}).get_json()["session"]
    assert owner_b.get(f"/api/assistant/sessions/{session['id']}").status_code == 404


def test_market_access_grant_blocks_analytics_and_workspace_scope() -> None:
    target = flask_app.db.upsert_target("Mercado privado", "https://booking.com/searchresults.html?private=1")
    flask_app.db.ensure_identity("analyst-a", "Analyst A", "analyst")
    flask_app.db.ensure_identity("analyst-b", "Analyst B", "analyst")
    flask_app.db.grant_market_access("analyst-a", target.id, "viewer")
    owner_a = app.test_client()
    owner_b = app.test_client()
    with owner_a.session_transaction() as browser_session:
        browser_session["ownerKey"] = "analyst-a"
    with owner_b.session_transaction() as browser_session:
        browser_session["ownerKey"] = "analyst-b"

    assert owner_a.get(f"/api/dashboard/metrics?targetId={target.id}").status_code == 200
    assert owner_b.get(f"/api/dashboard/metrics?targetId={target.id}").status_code == 403
    blocked_workspace = owner_b.post(
        "/api/workspaces",
        json={"name": "No acceso", "targetIds": [target.id], "globalFilters": {}, "layers": []},
    )
    assert blocked_workspace.status_code == 403


def test_authenticated_session_exposes_configured_owner(monkeypatch) -> None:
    production = replace(
        flask_app.settings,
        environment="production",
        auth_password="test-only-password",
        auth_user="revenue-manager",
        session_secret="test-only-session-secret",
    )
    monkeypatch.setattr(flask_app, "settings", production)
    client = app.test_client()
    assert client.get("/api/auth/session").get_json() == {"authenticated": False, "authRequired": True}
    login = client.post("/api/auth/session", json={"password": "test-only-password"})
    assert login.status_code == 200
    assert login.get_json()["ownerKey"] == "revenue-manager"
    assert client.get("/api/auth/session").get_json()["ownerKey"] == "revenue-manager"


def test_production_session_protects_operational_api(monkeypatch) -> None:
    production = replace(
        flask_app.settings,
        environment="production",
        auth_password="test-only-password",
        session_secret="test-only-session-secret",
    )
    monkeypatch.setattr(flask_app, "settings", production)
    client = app.test_client()

    status = client.get("/api/auth/session")
    assert status.status_code == 200
    assert status.get_json() == {"authenticated": False, "authRequired": True}
    assert client.get("/api/targets").status_code == 401
    assert client.post("/api/auth/session", json={"password": ""}).status_code == 401
    assert client.post("/api/auth/session", json={"password": "wrong"}).status_code == 401
    assert client.post("/api/auth/session", json={"password": "test-only-password"}).status_code == 200
    assert client.get("/api/targets").status_code == 200
    assert client.delete("/api/auth/session").get_json() == {"authenticated": False, "authRequired": True}
    assert client.get("/api/targets").status_code == 401


def test_assistant_endpoint_returns_provenance_and_data_gate(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        openrouter=replace(flask_app.settings.openrouter, api_key="test-key"),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(flask_app, "load_settings", lambda **_kwargs: runtime)

    def fake_assistant(*_args, telemetry=None, **_kwargs):
        telemetry.update({"requestId": "test-request", "model": "test/model", "latencyMs": 12, "attempts": 1, "toolRounds": 0, "usage": {"total_tokens": 42}})
        return "Respuesta de prueba"

    monkeypatch.setattr(flask_app, "ask_openrouter", fake_assistant)
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/assistant/chat",
        json={"message": "Resume el mercado", "targetId": 2},
    )

    assert response.status_code == 200
    meta = response.get_json()["dataMeta"]
    assert meta["requestId"] == "test-request"
    assert meta["model"] == "test/model"
    assert meta["usage"]["total_tokens"] == 42
    assert "dataGate" in meta
    assert meta["routing"]["schemaVersion"] == "revenue-routing.v1"
    assert meta["routing"]["experts"]

    client = app.test_client()
    manual = client.post("/api/assistant/sessions", json={"title": "Nueva consulta", "mode": "quick"})
    manual_id = manual.get_json()["session"]["id"]
    titled = client.post(
        "/api/assistant/chat",
        json={"message": "Compara el ADR de los hoteles RIU", "sessionId": manual_id},
    )
    assert titled.status_code == 200
    assert titled.get_json()["session"]["title"] == "Compara el ADR de los hoteles RIU"


def test_assistant_rate_limit_returns_retry_hint(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        copilot_requests_per_minute=1,
        openrouter=replace(flask_app.settings.openrouter, api_key=""),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(flask_app, "load_settings", lambda **_kwargs: runtime)
    flask_app._assistant_rate_windows.clear()
    client = app.test_client()

    first = client.post("/api/assistant/chat", json={"message": "Resume el mercado", "targetId": 2})
    second = client.post("/api/assistant/chat", json={"message": "Resume el mercado", "targetId": 2})

    assert first.status_code == 503
    assert second.status_code == 429
    assert second.headers["Retry-After"].isdigit()
    assert second.get_json()["retryAfterSeconds"] >= 1
    flask_app._assistant_rate_windows.clear()


def test_latest_evaluation_endpoint_is_available() -> None:
    response = app.test_client().get("/api/assistant/evaluations/latest")

    assert response.status_code == 200
    assert "evaluation" in response.get_json()


def test_assistant_decision_does_not_call_provider_when_data_gate_blocks(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        openrouter=replace(flask_app.settings.openrouter, api_key="test-key"),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(
        flask_app,
        "build_revenue_context",
        lambda *_args, **_kwargs: {
            "zonaActiva": {"id": 2, "name": "Gran Canaria"},
            "calidadAnalisis": {"estado": "caducado", "etiqueta": "Caducado", "comparabilidadPct": 94},
            "riu": {"hoteles": [{"nombre": "RIU"}]},
        },
    )

    def provider_must_not_run(*_args, **_kwargs):
        raise AssertionError("El proveedor no debe llamarse con el data gate bloqueado")

    monkeypatch.setattr(flask_app, "ask_openrouter", provider_must_not_run)
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/assistant/chat",
        json={"message": "¿Puedo subir precio?", "targetId": 2, "mode": "decision"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["model"] is None
    assert payload["dataMeta"]["dataGate"]["canRecommend"] is False
    assert payload["dataMeta"]["dataGate"]["severity"] == "blocked"
    assert "control de calidad" in payload["reply"]


def test_assistant_decision_uses_moa_after_data_gate(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        openrouter=replace(flask_app.settings.openrouter, api_key="test-key"),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(
        flask_app,
        "assistant_data_gate",
        lambda *_args, **_kwargs: {"blocked": False, "canRecommend": True, "warnings": [], "severity": "ok"},
    )

    def fake_moa(*_args, telemetry=None, **_kwargs):
        telemetry.update(
            {
                "requestId": "moa-request",
                "model": "openai/gpt-5.6-sol",
                "latencyMs": 25,
                "attempts": 3,
                "toolRounds": 0,
                "usage": {"total_tokens": 100},
                "moa": {"enabled": True, "executed": True, "expertCalls": 2},
            }
        )
        return "Respuesta MoA"

    def provider_must_not_run(*_args, **_kwargs):
        raise AssertionError("La decisión compleja debe usar el orquestador MoA")

    monkeypatch.setattr(flask_app, "run_moa", fake_moa)
    monkeypatch.setattr(flask_app, "ask_openrouter", provider_must_not_run)
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/assistant/chat",
        json={"message": "¿Puedo subir precio?", "targetId": 2, "mode": "decision"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["reply"] == "Respuesta MoA"
    assert payload["model"] == "openai/gpt-5.6-sol"
    assert payload["dataMeta"]["moa"]["expertCalls"] == 2


def test_assistant_decision_can_disable_moa_without_changing_endpoint(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        openrouter=replace(flask_app.settings.openrouter, api_key="test-key", moa_enabled=False),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(flask_app, "load_settings", lambda **_kwargs: runtime)
    monkeypatch.setattr(
        flask_app,
        "assistant_data_gate",
        lambda *_args, **_kwargs: {"blocked": False, "canRecommend": True, "warnings": [], "severity": "ok"},
    )

    def moa_must_not_run(*_args, **_kwargs):
        raise AssertionError("El MoA está desactivado en esta prueba")

    def fake_assistant(*_args, telemetry=None, **_kwargs):
        telemetry.update({"model": "openai/gpt-5.6-sol", "latencyMs": 5, "attempts": 1})
        return "Respuesta directa"

    monkeypatch.setattr(flask_app, "run_moa", moa_must_not_run)
    monkeypatch.setattr(flask_app, "ask_openrouter", fake_assistant)
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/assistant/chat",
        json={"message": "¿Puedo subir precio?", "targetId": 2, "mode": "decision"},
    )

    assert response.status_code == 200
    assert response.get_json()["dataMeta"]["moa"]["reason"] == "disabled_by_configuration"


def test_air_analysis_falls_back_when_glm_primary_fails(monkeypatch) -> None:
    runtime = replace(
        flask_app.settings,
        openrouter=replace(
            flask_app.settings.openrouter,
            api_key="test-key",
            air_model="glm-test",
            air_fallback_model="luna-test",
        ),
    )
    monkeypatch.setattr(flask_app, "settings", runtime)
    monkeypatch.setattr(flask_app, "load_settings", lambda **_kwargs: runtime)
    calls = []

    def fake_assistant(settings, *_args, telemetry=None, **_kwargs):
        calls.append(settings.model)
        if settings.model == "glm-test":
            raise flask_app.AssistantError("GLM no respondió")
        telemetry.update({"model": settings.model, "latencyMs": 7, "attempts": 2})
        return "**Lectura**\nOK\n**Evidencia**\nOK\n**Acción siguiente**\nOK\n**Límite de confianza**\nOK"

    monkeypatch.setattr(flask_app, "ask_openrouter", fake_assistant)
    flask_app.clear_cache()
    response = app.test_client().post(
        "/api/assistant/chat",
        json={"message": "Analiza la conectividad aérea por mercado emisor", "targetId": 2, "mode": "analysis"},
    )

    assert response.status_code == 200
    assert calls == ["glm-test", "luna-test"]
    payload = response.get_json()
    assert payload["model"] == "luna-test"
    assert payload["dataMeta"]["airFallback"]["from"] == "glm-test"


def test_assistant_session_can_be_created_read_pinned_and_archived() -> None:
    client = app.test_client()
    created = client.post(
        "/api/assistant/sessions",
        json={"title": "Revisión semanal", "mode": "analysis"},
    )
    assert created.status_code == 201
    session_id = created.get_json()["session"]["id"]

    detail = client.get(f"/api/assistant/sessions/{session_id}")
    assert detail.status_code == 200
    assert detail.get_json()["session"]["mode"] == "analysis"
    assert detail.get_json()["messages"] == []

    pinned = client.patch(
        f"/api/assistant/sessions/{session_id}",
        json={"pinned": True, "expectedVersion": detail.get_json()["session"]["version"]},
    )
    assert pinned.status_code == 200
    assert pinned.get_json()["session"]["pinned"] is True

    archived = client.patch(
        f"/api/assistant/sessions/{session_id}",
        json={"status": "archived"},
    )
    assert archived.status_code == 200
    assert archived.get_json()["session"]["status"] == "archived"
    assert not any(item["id"] == session_id for item in client.get("/api/assistant/sessions").get_json()["sessions"])
