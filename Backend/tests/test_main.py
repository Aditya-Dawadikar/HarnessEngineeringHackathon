from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_config_returns_vendor_and_buyer():
    response = client.get("/config")

    assert response.status_code == 200
    body = response.json()

    vendor = body["vendor"]
    assert vendor["agent_id"] == "VendorAgent"
    assert vendor["company"]
    assert vendor["product"]["id"]
    assert vendor["product"]["name"]
    assert vendor["product"]["description"]
    assert vendor["product"]["unit"]
    assert isinstance(vendor["stock_quantity"], int)
    assert isinstance(vendor["floor_price"], float)
    assert isinstance(vendor["ceiling_price"], float)

    buyer = body["buyer"]
    assert buyer["agent_id"] == "BuyerAgent"
    assert buyer["company"]
    assert buyer["product"]["id"]
    assert buyer["product"]["name"]
    assert buyer["product"]["unit"]
    assert isinstance(buyer["desired_quantity"], int)
    assert isinstance(buyer["floor_price"], float)
    assert isinstance(buyer["ceiling_price"], float)
