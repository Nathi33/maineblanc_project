import pytest

def test_campinginfo_fixture(campinginfo_fr):
    """Verify that the CampingInfo fixture is correctly created and times are set."""
    assert campinginfo_fr.pk is not None
    assert campinginfo_fr.welcome_start.hour == 9
    assert campinginfo_fr.portal_end.hour == 6

def test_swimmingpoolinfo_fixture(swimmingpoolinfo_fr):
    """Verify that the SwimmingPoolInfo fixture is correctly created and opening times are correct."""
    assert swimmingpoolinfo_fr.pk is not None
    assert swimmingpoolinfo_fr.pool_opening_start.hour == 10
    assert swimmingpoolinfo_fr.pool_opening_end.hour == 21

def test_foodinfo_fixture(foodinfo_fr):
    """Verify that the FoodInfo fixture is correctly created and food hours are set."""
    assert foodinfo_fr.pk is not None
    assert foodinfo_fr.burger_food_days == "jeudi"
    assert foodinfo_fr.bar_hours_end.hour == 21

def test_laundryinfo_fixture(laundryinfo_fr):
    """Verify that the LaundryInfo fixture is correctly created and prices are correct."""
    assert laundryinfo_fr.pk is not None
    assert laundryinfo_fr.washing_machine_price == 4
    assert laundryinfo_fr.dryer_price == 2