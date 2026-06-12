"""Stripe payment integration.

[PLACEHOLDER] Stripe API keys, mode (test/live), and preferred flow
(PaymentIntents vs. Checkout vs. Invoices API) are not yet known -- see
INSTRUCTIONS.md Section 5. Ask the user for these before implementing
the real client.

Until then, both functions are mocks that always succeed so the
payment_request / payment_authorization / generate_invoice graph nodes
(BE-4) can be developed and tested.
"""

import uuid


def create_payment_request(
    *,
    transaction_id: str,
    buyer_agent_id: str,
    product_id: str,
    agreed_unit_price: float,
    quantity: int,
    total_amount: float,
) -> dict:
    return {
        "payment_intent_id": f"pi_mock_{uuid.uuid4().hex[:24]}",
        "payment_status": "requires_confirmation",
    }


def authorize_payment(
    *,
    transaction_id: str,
    payment_method_token: str,
    authorized_amount: float,
) -> dict:
    return {
        "payment_intent_id": f"pi_mock_{uuid.uuid4().hex[:24]}",
        "payment_status": "succeeded",
    }
