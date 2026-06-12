from app.config import BUYER_CONFIG, VENDOR_CONFIG
from app.graph import (
    MAX_TURNS,
    build_graph,
    build_initial_state,
    guardrail_validator,
    parse_offer,
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

    assert final_state["status"] in ("AGREEMENT", "TERMINATED")
    assert final_state["turn"] <= MAX_TURNS
    assert final_state["messages"][0]["sender"] == "BuyerAgent"


def test_negotiation_graph_converges_to_agreement_within_bounds():
    graph = build_graph()
    initial_state = build_initial_state("txn-1", VENDOR_CONFIG, BUYER_CONFIG)

    final_state = graph.invoke(initial_state)

    assert final_state["status"] == "AGREEMENT"
    assert VENDOR_CONFIG["Floor_Price"] <= final_state["current_price"] <= BUYER_CONFIG["Buyer_Ceiling_Price"]
