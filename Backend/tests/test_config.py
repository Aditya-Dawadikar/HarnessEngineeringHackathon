from app.config import BUYER_CONFIG, VENDOR_CONFIG


def test_vendor_config_has_required_fields():
    for field in ("Product_ID", "Stock_Quantity", "Floor_Price", "Ceiling_Price"):
        assert field in VENDOR_CONFIG


def test_buyer_config_has_required_fields():
    for field in (
        "Target_Product_ID",
        "Desired_Quantity",
        "Buyer_Floor_Price",
        "Buyer_Ceiling_Price",
    ):
        assert field in BUYER_CONFIG


def test_buyer_targets_vendor_product():
    assert BUYER_CONFIG["Target_Product_ID"] == VENDOR_CONFIG["Product_ID"]


def test_vendor_floor_price_is_not_above_ceiling_price():
    assert VENDOR_CONFIG["Floor_Price"] <= VENDOR_CONFIG["Ceiling_Price"]
