import asyncio
from datetime import date, timedelta
import sqlite3
from urllib.parse import parse_qs, urlsplit

import pytest
from pydantic import ValidationError

from backend.app.capture_profile import HotelCaptureProfile, effective_search_url, profile_from_url
from backend.app.models import MarketHotelRow, ScrapeSearchPayload, HotelRateDetailRow
from backend.app.database import Database
from backend.app.services import MarketService

URL = 'https://www.booking.com/searchresults.html?dest_id=1&nflt=ht_id=204;mealplan=1&age=5&selected_currency=USD'
START = date.today() + timedelta(days=7)

@pytest.fixture
def market(tmp_path):
    db = Database(tmp_path / 'test.sqlite')
    target = db.upsert_target('Test', URL)
    yield db, target
    db.conn.close()


def test_explicit_profile_preserves_destination_and_sets_effective_parameters():
    url = effective_search_url(URL, HotelCaptureProfile(checkIn=START))
    q = parse_qs(urlsplit(url).query)
    assert q['dest_id'] == ['1']
    assert q['selected_currency'] == ['EUR']
    assert q['checkout'] == [(START + timedelta(days=7)).isoformat()]
    assert q['group_adults'] == ['2'] and q['no_rooms'] == ['1']
    assert q['nflt'] == ['ht_id=204;mealplan=4']
    assert 'age' not in q


@pytest.mark.parametrize('url', ['https://booking.com.evil.test/search', 'https://notbooking.com/search', 'https://user:password@booking.com/search'])
def test_non_booking_and_embedded_credentials_rejected(url):
    with pytest.raises(ValueError):
        effective_search_url(url)


@pytest.mark.parametrize('overrides', [{'currency':'USD'}, {'children':1}, {'nights':0}, {'rooms':0}])
def test_unsupported_profile_is_rejected(overrides):
    with pytest.raises(ValidationError):
        HotelCaptureProfile(checkIn=START, **overrides)


def test_legacy_unknown_parameters_are_not_invented():
    result = profile_from_url('https://booking.com/searchresults.html')
    assert result['currency'] is None and result['adults'] is None
    assert result['origin'] == 'legacy_url'


def test_past_entry_rejected_before_capture():
    with pytest.raises(ValueError):
        effective_search_url(URL, HotelCaptureProfile(checkIn=date.today()-timedelta(days=1)))


@pytest.fixture
def service(market, monkeypatch):
    from backend.app import services
    calls = []
    async def scrape(url, limit):
        calls.append(url)
        q = parse_qs(urlsplit(url).query)
        return [MarketHotelRow(hotelKey='hotel-a', hotelName='Test', detailUrl='https://booking.com/hotel/es/a.html',
                price=700,pricePerNight=100,currency='EUR',position=1,checkIn=q['checkin'][0],checkOut=q['checkout'][0],
                nights=7,pax=2,roomType='Double',board='Todo incluido',freeCancellation=True)], 'hash', 1
    monkeypatch.setattr(services, 'scrape_search_graphql', scrape)
    return MarketService(market[0], None), calls


def test_effective_profile_persists_and_missing_coordinates_do_not_break_capture(market, service):
    svc,calls=service
    result=asyncio.run(svc.scrape_search(ScrapeSearchPayload(targetId=market[1].id,url=URL,profile=HotelCaptureProfile(checkIn=START))))
    saved=market[0].photo_detail(result.snapshot.id)['snapshot']
    assert saved['sourceUrl']==calls[0]
    assert saved['captureProfile']['currency']=='EUR'
    assert saved['captureProfile']['origin']=='explicit_profile'
    assert saved['captureProfile']['children']==0
    assert saved['captureProfile']['captureQuality']['status']=='complete'
    assert saved['captureProfile']['captureQuality']['coveragePct']==100.0
    assert saved['captureGroupId']
    assert saved['captureStatus'] == 'complete'
    assert saved['captureProfileHash']
    stored = market[0].conn.execute(
        'SELECT group_id, expected_slices, completed_slices, status FROM hotel_capture_runs WHERE id = (SELECT capture_run_id FROM market_snapshots WHERE id = ?)',
        (result.snapshot.id,),
    ).fetchone()
    assert stored['group_id'] == saved['captureGroupId']
    assert (stored['expected_slices'], stored['completed_slices'], stored['status']) == (1, 1, 'complete')
    assert len(market[0].snapshot_rows(result.snapshot.id))==1


def test_capture_quality_marks_provider_result_as_partial(market, monkeypatch):
    from backend.app import services

    async def scrape(url, limit):
        return [MarketHotelRow(
            hotelKey='hotel-a', hotelName='Test', detailUrl='https://booking.com/hotel/es/a.html',
            price=700, pricePerNight=100, currency='EUR', position=1,
            checkIn=START.isoformat(), checkOut=(START + timedelta(days=7)).isoformat(),
            nights=7, pax=2, roomType='Double', board='Todo incluido', freeCancellation=True,
        )], 'hash', 3

    monkeypatch.setattr(services, 'scrape_search_graphql', scrape)
    db, target = market
    result = asyncio.run(MarketService(db, None).scrape_search(
        ScrapeSearchPayload(targetId=target.id, url=URL, limit=3,
                            profile=HotelCaptureProfile(checkIn=START))))
    quality = result.snapshot.captureProfile['captureQuality']
    assert quality['status'] == 'partial'
    assert quality['expectedRows'] == 3
    assert quality['capturedRows'] == 1
    assert quality['coveragePct'] == 33.3


def test_capture_diagnostics_are_persisted_without_breaking_tuple_contract(market, monkeypatch):
    from backend.app import services
    from backend.app.graphql_scraper import ScrapeSearchResult

    async def scrape(url, limit):
        row = MarketHotelRow(
            hotelKey='hotel-a', hotelName='Test', detailUrl='https://booking.com/hotel/es/a.html',
            price=700, pricePerNight=100, currency='EUR', position=1,
            checkIn=START.isoformat(), checkOut=(START + timedelta(days=7)).isoformat(),
            nights=7, pax=2, roomType='Double', board='Todo incluido', freeCancellation=True,
        )
        return ScrapeSearchResult([row], 'hash', 3, {
            'pagesRequested': 3, 'pagesReceived': 2, 'pagesFailed': 1,
            'failedPages': [{'offset': 25, 'reason': 'HTTP 429'}],
            'hotelsBeforeDedupe': 2, 'hotelsAfterDedupe': 1,
            'terminationReason': 'partial_page_failures', 'blockDetected': True,
        })

    monkeypatch.setattr(services, 'scrape_search_graphql', scrape)
    db, target = market
    result = asyncio.run(MarketService(db, None).scrape_search(
        ScrapeSearchPayload(targetId=target.id, url=URL, limit=3,
                            profile=HotelCaptureProfile(checkIn=START))))
    profile = result.snapshot.captureProfile
    assert profile['captureDiagnostics']['pagesFailed'] == 1
    assert profile['captureQuality']['pagesReceived'] == 2
    assert profile['captureQuality']['blockDetected'] is True


def test_weekly_job_creates_distinct_photos_with_shared_group(market,service,monkeypatch):
    from backend.app import flask_app
    svc,calls=service
    monkeypatch.setattr(flask_app,'market_service',lambda **kwargs:svc)
    payload=ScrapeSearchPayload(targetId=market[1].id,url=URL,profile=HotelCaptureProfile(checkIn=START),arrivalWeeks=3)
    result=flask_app._run_hotel_capture_job(payload.model_dump(mode='json'),lambda *_:None)
    assert len(result['snapshots'])==3
    assert [parse_qs(urlsplit(url).query)['checkin'][0] for url in calls]==[(START+timedelta(days=7*i)).isoformat() for i in range(3)]
    assert len({p['captureProfile']['captureGroupId'] for p in result['snapshots']})==1
    run = market[0].conn.execute(
        'SELECT group_id, expected_slices, completed_slices, status FROM hotel_capture_runs WHERE group_id = ?',
        (result['captureGroupId'],),
    ).fetchone()
    assert run is not None
    assert (run['expected_slices'], run['completed_slices'], run['status']) == (3, 3, 'complete')
    assert market[0].conn.execute(
        'SELECT COUNT(DISTINCT capture_run_id) FROM market_snapshots WHERE capture_group_id = ?',
        (result['captureGroupId'],),
    ).fetchone()[0] == 1


def test_old_detail_is_explicitly_independent(market,service):
    svc,_=service;db,target=market
    photo=asyncio.run(svc.scrape_search(ScrapeSearchPayload(targetId=target.id,url=URL,profile=HotelCaptureProfile(checkIn=START)))).snapshot
    db.insert_rate_detail_rows(target.id,[HotelRateDetailRow(targetId=target.id,hotelKey='hotel-a',priceFinal=700,currency='EUR')])
    result=db.rate_detail_evidence(target.id,'hotel-a',photo.id)
    assert result['provenance']['scope']=='independent_latest_detail'
    assert result['rows'][0]['snapshotId'] is None


def test_linked_detail_is_retrieved_by_photo(market,service):
    svc,_=service;db,target=market
    photo=asyncio.run(svc.scrape_search(ScrapeSearchPayload(targetId=target.id,url=URL,profile=HotelCaptureProfile(checkIn=START)))).snapshot
    db.insert_rate_detail_rows(target.id,[HotelRateDetailRow(targetId=target.id,hotelKey='hotel-a',priceFinal=700,currency='EUR',snapshotId=photo.id)])
    result=db.rate_detail_evidence(target.id,'hotel-a',photo.id)
    assert result['provenance']['scope']=='linked_snapshot'
    assert result['rows'][0]['snapshotId']==photo.id


def test_mixed_currency_is_not_aggregated(market):
    db,target=market
    photo=db.create_snapshot(target.id,URL,10,2,2,'hash')
    for key,currency in [('a','EUR'),('b','USD')]:
        db.upsert_location(key,URL,28,-15,None)
        db.insert_market_hotel(photo.id,MarketHotelRow(hotelKey=key,hotelName=key,detailUrl=URL,price=700,pricePerNight=100,nights=7,currency=currency,position=1),'ready')
    assert db.dashboard_metrics(target.id)['currencyPolicy']['status']=='blocked'
    assert db.dashboard_metrics(target.id)['market']['avgPricePerNight'] is None
    assert db.revenue_opportunities(target.id)==[]
    assert db.photo_history(target.id)[0]['avgPricePerNight'] is None
    assert db.photo_detail(photo.id)['summary']['avgPricePerNight'] is None
    assert db.market_heatmap(target.id)['points']==[]


def test_migration_is_additive_and_idempotent(market):
    db,target=market
    photo=db.create_snapshot(target.id,URL,10,0,0,'hash')
    db.init();db.init()
    assert db.latest_snapshot(target.id).id==photo.id
    assert db.conn.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    assert db.conn.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_capture_metadata_migration_upgrades_legacy_schema(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE search_targets (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE market_snapshots (
          id INTEGER PRIMARY KEY, target_id INTEGER NOT NULL, source_url TEXT NOT NULL,
          requested_limit INTEGER NOT NULL, available_results INTEGER NOT NULL,
          captured_rows INTEGER NOT NULL, scraped_at TEXT NOT NULL, raw_hash TEXT NOT NULL
        );
        CREATE TABLE hotel_capture_runs (id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL);
        """
    )
    conn.commit()
    conn.close()

    db = Database(path)
    snapshot_columns = {row['name'] for row in db.conn.execute('PRAGMA table_info(market_snapshots)')}
    run_columns = {row['name'] for row in db.conn.execute('PRAGMA table_info(hotel_capture_runs)')}
    assert {'capture_group_id', 'capture_status', 'capture_profile_hash'} <= snapshot_columns
    assert {'group_id', 'target_id', 'profile_json', 'status', 'expected_slices', 'completed_slices'} <= run_columns
    assert db.conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    db.conn.close()


def test_detail_capture_batch_chunks_all_hotels_and_is_idempotent(market, monkeypatch):
    from backend.app import flask_app

    db, target = market
    hotels = [
        {"hotelKey": f"/hotel/es/hotel-{index}", "hotelName": f"Hotel {index}",
         "detailUrl": f"https://booking.com/hotel/es/hotel-{index}.html"}
        for index in range(16)
    ]
    payload = {
        "batchId": "detail-batch-1", "targetId": target.id, "snapshotId": None,
        "hotels": hotels, "checkIn": START.isoformat(),
        "checkOut": (START + timedelta(days=7)).isoformat(),
        "adults": 2, "children": 0, "rooms": 1,
    }
    db.create_hotel_detail_tasks(payload["batchId"], payload, hotels)
    calls = []

    async def fake_scrape(target_id, selected, **kwargs):
        calls.append(len(selected))
        return [HotelRateDetailRow(
            targetId=target_id, hotelKey=item["hotelKey"], hotelName=item["hotelName"],
            priceFinal=700, currency="EUR", checkIn=kwargs["checkin"],
            checkOut=kwargs["checkout"], adults=kwargs["adults"], children=kwargs["children"],
            rooms=kwargs["rooms"], snapshotId=kwargs.get("snapshot_id"),
        ) for item in selected]

    monkeypatch.setattr(flask_app, "db", db)
    monkeypatch.setattr(flask_app, "scrape_rate_details", fake_scrape)
    first = flask_app._run_hotel_detail_capture_job(payload, lambda *_: None)
    assert first["status"] == "complete"
    assert first["hotelsRequested"] == 16
    assert calls == [15, 1]
    assert db.conn.execute("SELECT COUNT(*) FROM hotel_rate_details").fetchone()[0] == 16
    assert all(task["status"] == "succeeded" for task in db.list_hotel_detail_tasks("detail-batch-1"))

    second = flask_app._run_hotel_detail_capture_job(payload, lambda *_: None)
    assert second["status"] == "complete"
    assert calls == [15, 1]
    assert db.conn.execute("SELECT COUNT(*) FROM hotel_rate_details").fetchone()[0] == 16


def test_failed_row_rolls_back_the_entire_photo(market,service,monkeypatch):
    svc,_=service;db,target=market
    original=db.insert_market_hotel
    def fail_after_write(*args,**kwargs):
        original(*args,**kwargs)
        raise RuntimeError('simulated failure')
    monkeypatch.setattr(db,'insert_market_hotel',fail_after_write)
    with pytest.raises(RuntimeError):
        asyncio.run(svc.scrape_search(ScrapeSearchPayload(targetId=target.id,url=URL,profile=HotelCaptureProfile(checkIn=START))))
    for table in ('market_snapshots','market_snapshot_hotels','hotel_capture_runs','hotel_price_observations'):
        assert db.conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0
