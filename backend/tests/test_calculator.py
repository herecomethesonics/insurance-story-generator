from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.calculator import calculate, depreciation_rate, months_between
from app.main import app
from app.models import ClaimRequest


def make_req(event_type="screen_damage", event_date="2025-07-01", sum_insured=100_000,
             deductible=3_000, condition="good", severity=0.5):
    return ClaimRequest.model_validate({
        "phone": {"brand": "Apple", "model": "iPhone 15", "purchase_price": 100_000,
                  "purchase_date": "2025-01-01", "condition": condition},
        "policy": {"sum_insured": sum_insured, "deductible": deductible},
        "event": {"type": event_type, "date": event_date, "severity": severity},
    })


def test_months_between():
    assert months_between(date(2025, 1, 1), date(2025, 7, 1)) == 6
    assert months_between(date(2025, 1, 31), date(2025, 2, 28)) == 0


def test_depreciation_is_capped():
    assert depreciation_rate(6) == pytest.approx(0.12)
    assert depreciation_rate(24) == pytest.approx(0.36)
    assert depreciation_rate(100) == pytest.approx(0.70)


def test_screen_damage_is_repair():
    # стоимость: 100000 * 0.88 * 0.9 = 79200; ремонт 25000
    r = calculate(make_req())
    assert r.device_value == pytest.approx(79_200)
    assert r.loss_amount == pytest.approx(25_000)
    assert not r.total_loss
    assert r.payout == pytest.approx(22_000)


def test_theft_pays_device_value():
    r = calculate(make_req("theft"))
    assert r.total_loss
    assert r.payout == pytest.approx(76_200)


def test_expensive_repair_becomes_total_loss():
    # 24 мес.: стоимость 57600, ремонт после залития 60000 > 0.8 * 57600
    r = calculate(make_req("water_damage", event_date="2027-01-01"))
    assert r.total_loss
    assert r.loss_amount == pytest.approx(57_600)


def test_sum_insured_limits_payout():
    r = calculate(make_req("theft", sum_insured=50_000, deductible=0))
    assert r.payout == pytest.approx(50_000)


def test_deductible_above_loss_gives_zero():
    r = calculate(make_req("other_damage", severity=0.01, deductible=5_000))
    assert r.payout == 0


def test_event_before_purchase_rejected():
    with pytest.raises(ValueError):
        calculate(make_req(event_date="2024-12-01"))


def test_page_served_without_logo():
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert 'logo.svg' not in page.text
    assert client.get("/static/logo.svg").status_code == 404


def test_api_estimate():
    client = TestClient(app)
    resp = client.post("/api/claims/estimate", json=make_req().model_dump(mode="json"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["compensation"]["payout"] == pytest.approx(22_000)
    assert "iPhone 15" in body["story"]
    assert ".." not in body["story"]
    assert body["story_source"] == "template"
    assert body["disclaimer"]
