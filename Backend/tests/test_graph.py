from app.config import BUYER_CONFIG, VENDOR_CONFIG
from app.graph import (
    MAX_TURNS,
    build_graph,
    build_initial_state,
    buyer_agent,
    generate_invoice,
    guardrail_validator,
    parse_offer,
    payment_authorization,
    payment_request,
    route_after_guardrail,
)


def _state_with_messages(messages, **overrides):
    state = build_initial_state("txn-1", VENDOR_CONFIG, BUYER_CONFIG)
    state["messages"] = messages
    state.update(overrides)
    return state


def _message(sender, price, quantity, action):
    return {
        "sender": sender,
        "text": f"[OFFER price={price:.2f} quantity={quantity} action={action}]",
        "extracted_price": price,
        "extracted_quantity": quantity,
        "timestamp": "2026-01-01T00:00:00+00:00",
    }


def test_parse_offer_extracts_price_quantity_and_action():
    text = "Sounds good. [OFFER price=9.50 quantity=200 action=COUNTER]"

    price, quantity, action = parse_offer(text)

    assert price == 9.50
    assert quantity == 200
    assert action == "COUNTER"


def test_parse_offer_returns_none_when_no_tag_present():
    assert parse_offer("no structured offer here") == (None, None, None)


def test_guardrail_terminates_when_vendor_price_below_floor():
    state = _state_with_messages(
        [_message("VendorAgent", VENDOR_CONFIG["Floor_Price"] - 1, 200, "COUNTER")]
    )

    update = guardrail_validator(state)

    assert update["status"] == "TERMINATED"


def test_guardrail_terminates_when_buyer_accepts_above_ceiling():
    state = _state_with_messages(
        [_message("BuyerAgent", BUYER_CONFIG["Buyer_Ceiling_Price"] + 1, 200, "ACCEPT")]
    )

    update = guardrail_validator(state)

    assert update["status"] == "TERMINATED"


def test_guardrail_terminates_when_turn_limit_exceeded():
    state = _state_with_messages(
        [_message("BuyerAgent", 9.00, 200, "COUNTER")], turn=MAX_TURNS
    )

    update = guardrail_validator(state)

    assert update["status"] == "TERMINATED"


def test_guardrail_marks_agreement_on_accept_within_bounds():
    agreed_price = (VENDOR_CONFIG["Floor_Price"] + BUYER_CONFIG["Buyer_Ceiling_Price"]) / 2
    state = _state_with_messages(
        [_message("VendorAgent", agreed_price, 200, "ACCEPT")]
    )

    update = guardrail_validator(state)

    assert update["status"] == "AGREEMENT"
    assert update["current_price"] == agreed_price
    assert update["current_quantity"] == 200


def test_route_after_guardrail_alternates_turns():
    negotiating_buyer_last = _state_with_messages(
        [_message("BuyerAgent", 8.00, 200, "COUNTER")], status="NEGOTIATING"
    )
    negotiating_vendor_last = _state_with_messages(
        [_message("VendorAgent", 8.00, 200, "COUNTER")], status="NEGOTIATING"
    )

    assert route_after_guardrail(negotiating_buyer_last) == "vendor_agent"
    assert route_after_guardrail(negotiating_vendor_last) == "buyer_agent"


def test_route_after_guardrail_handles_terminal_statuses():
    agreement_state = _state_with_messages([], status="AGREEMENT")
    terminated_state = _state_with_messages([], status="TERMINATED")

    assert route_after_guardrail(agreement_state) == "agreement"
    assert route_after_guardrail(terminated_state) == "terminated"


def test_negotiation_graph_reaches_a_terminal_status_within_turn_limit():
    graph = build_graph()
    initial_state = build_initial_state("txn-1", VENDOR_CONFIG, BUYER_CONFIG)

    final_state = graph.invoke(initial_state)

    assert final_state["status"] in ("FULFILLED", "TERMINATED")
    assert final_state["turn"] <= MAX_TURNS
    assert final_state["messages"][0]["sender"] == "BuyerAgent"


def test_negotiation_graph_converges_to_fulfilled_with_invoice():
    graph = build_graph()
    initial_state = build_initial_state("txn-1", VENDOR_CONFIG, BUYER_CONFIG)

    final_state = graph.invoke(initial_state)

    assert final_state["status"] == "FULFILLED"
    assert VENDOR_CONFIG["Floor_Price"] <= final_state["current_price"] <= BUYER_CONFIG["Buyer_Ceiling_Price"]

    invoice = final_state["invoice"]
    assert invoice["transaction_id"] == "txn-1"
    assert invoice["product_id"] == VENDOR_CONFIG["Product_ID"]
    assert invoice["unit_price"] == final_state["current_price"]
    assert invoice["quantity"] == final_state["current_quantity"]
    assert invoice["total_amount"] == round(final_state["current_price"] * final_state["current_quantity"], 2)
    assert invoice["payment_status"] == "succeeded"


def test_buyer_agent_logs_message_via_telemetry(monkeypatch):
    logged = []
    monkeypatch.setattr(
        "app.graph.telemetry.log_message", lambda **kwargs: logged.append(kwargs)
    )

    initial_state = build_initial_state("txn-1", VENDOR_CONFIG, BUYER_CONFIG)
    buyer_agent(initial_state)

    assert len(logged) == 1
    assert logged[0]["transaction_id"] == "txn-1"
    assert logged[0]["sender_type"] == "BuyerAgent"


def test_guardrail_validator_logs_system_message_via_telemetry(monkeypatch):
    logged = []
    monkeypatch.setattr(
        "app.graph.telemetry.log_message", lambda **kwargs: logged.append(kwargs)
    )

    state = _state_with_messages([_message("BuyerAgent", 8.00, 200, "COUNTER")])
    guardrail_validator(state)

    assert len(logged) == 1
    assert logged[0]["sender_type"] == "System"


def test_payment_request_sets_payment_pending_and_records_invoice_fields():
    state = _state_with_messages([], status="AGREEMENT", current_price=9.0, current_quantity=200)

    update = payment_request(state)

    assert update["status"] == "PAYMENT_PENDING"
    assert update["invoice"]["agreed_unit_price"] == 9.0
    assert update["invoice"]["quantity"] == 200
    assert update["invoice"]["total_amount"] == 1800.0
    assert update["invoice"]["payment_status"] == "requires_confirmation"


def test_payment_authorization_sets_fulfilled_and_succeeded_status():
    state = _state_with_messages(
        [],
        status="PAYMENT_PENDING",
        current_price=9.0,
        current_quantity=200,
        invoice={"total_amount": 1800.0},
    )

    update = payment_authorization(state)

    assert update["status"] == "FULFILLED"
    assert update["invoice"]["authorized_amount"] == 1800.0
    assert update["invoice"]["payment_status"] == "succeeded"


def test_generate_invoice_builds_invoice_from_agreed_terms():
    state = _state_with_messages(
        [], status="FULFILLED", current_price=9.0, current_quantity=200, invoice={}
    )

    update = generate_invoice(state)

    invoice = update["invoice"]
    assert invoice["transaction_id"] == "txn-1"
    assert invoice["product_id"] == VENDOR_CONFIG["Product_ID"]
    assert invoice["unit_price"] == 9.0
    assert invoice["quantity"] == 200
    assert invoice["total_amount"] == 1800.0
