from app import payments


def test_create_payment_request_returns_payment_intent_id():
    result = payments.create_payment_request(
        transaction_id="txn-1",
        buyer_agent_id="BuyerAgent",
        product_id="PROD-1001",
        agreed_unit_price=9.00,
        quantity=200,
        total_amount=1800.00,
    )

    assert result["payment_intent_id"].startswith("pi_mock_")
    assert result["payment_status"] == "requires_confirmation"


def test_authorize_payment_returns_succeeded_status():
    result = payments.authorize_payment(
        transaction_id="txn-1",
        payment_method_token="tok_mock_visa",
        authorized_amount=1800.00,
    )

    assert result["payment_intent_id"].startswith("pi_mock_")
    assert result["payment_status"] == "succeeded"
