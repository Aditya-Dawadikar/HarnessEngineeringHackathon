"""Hardcoded domain configuration for the negotiation POC.

See INSTRUCTIONS.md Section 2 for the Vendor/Buyer entity definitions.
"""

VENDOR_CONFIG = {
    "Product_ID": "PROD-1001",
    "Stock_Quantity": 500,
    "Floor_Price": 8.00,
    "Ceiling_Price": 12.00,
}

BUYER_CONFIG = {
    "Target_Product_ID": "PROD-1001",
    "Desired_Quantity": 200,
    "Buyer_Floor_Price": 7.00,
    "Buyer_Ceiling_Price": 10.00,
}
