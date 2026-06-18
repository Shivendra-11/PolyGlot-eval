"""pytest suite for I4 FastAPI service."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_convert_valid():
    r = client.post("/convert", json={"amount": 100, "from": "USD", "to": "EUR"})
    assert r.status_code == 200
    data = r.json()
    assert data["converted"] > 0
    assert data["rate"] > 0


def test_convert_unknown_currency():
    r = client.post("/convert", json={"amount": 10, "from": "USD", "to": "XYZ"})
    assert r.status_code == 422


def test_convert_negative_amount():
    r = client.post("/convert", json={"amount": -1, "from": "USD", "to": "EUR"})
    assert r.status_code == 422
