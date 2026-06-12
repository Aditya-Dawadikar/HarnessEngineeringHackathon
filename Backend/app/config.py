"""Hardcoded domain configuration for the negotiation POC.

See INSTRUCTIONS.md Section 2 for the Vendor/Buyer entity definitions.
"""

VENDOR_CONFIG = {
    # graph keys (unchanged — graph.py reads these)
    "Product_ID": "PROD-1001",
    "Stock_Quantity": 500,
    "Floor_Price": 8.00,
    "Ceiling_Price": 12.00,
    # display keys (for GET /config → UI context panel)
    "agent_id": "VendorAgent",
    "company": "Acme Supplies Co.",
    "product_name": "Industrial Widget",
    "product_description": "Heavy-duty steel widget, grade A",
    "product_unit": "pcs",
}

BUYER_CONFIG = {
    # graph keys (unchanged — graph.py reads these)
    "Target_Product_ID": "PROD-1001",
    "Desired_Quantity": 200,
    "Buyer_Floor_Price": 7.00,
    "Buyer_Ceiling_Price": 10.00,
    # display keys (for GET /config → UI context panel)
    "agent_id": "BuyerAgent",
    "company": "BuildCorp Ltd.",
    "product_name": "Industrial Widget",
    "product_unit": "pcs",
}
