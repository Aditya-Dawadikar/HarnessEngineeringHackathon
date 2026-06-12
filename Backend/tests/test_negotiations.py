from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_start_negotiation_returns_transaction_id():
    response = client.post("/negotiations/start")

    assert response.status_code == 200
    body = response.json()
    assert "transaction_id" in body
    assert body["transaction_id"]


def test_get_negotiation_returns_final_state_after_background_run():
    start_response = client.post("/negotiations/start")
    transaction_id = start_response.json()["transaction_id"]

    response = client.get(f"/negotiations/{transaction_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["transaction_id"] == transaction_id
    assert body["status"] == "FULFILLED"
    assert body["turn"] > 0
    assert body["messages"][0]["sender"] == "BuyerAgent"
    assert body["invoice"]["payment_status"] == "succeeded"


def test_get_negotiation_returns_404_for_unknown_transaction_id():
    response = client.get("/negotiations/does-not-exist")

    assert response.status_code == 404
