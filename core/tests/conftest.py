import pytest
from django.utils import translation
from core.models import CampingInfo, SwimmingPoolInfo, FoodInfo, LaundryInfo
from core.views import MobileHome
import datetime

@pytest.fixture
def campinginfo_fr(db):
    """Creates a CampingInfo object with French translation for testing."""
    with translation.override('fr'):
        obj = CampingInfo.objects.create(
            welcome_start=datetime.time(9, 0),
            welcome_end=datetime.time(12, 0),
            welcome_afternoon_start=datetime.time(14, 0),
            welcome_afternoon_end=datetime.time(19, 0),
            arrivals_start_high=datetime.time(14, 0),
            arrivals_end_high=datetime.time(21, 0),
            arrivals_end_low=datetime.time(19, 0),
            departure_end=datetime.time(12, 0),
            portal_start=datetime.time(22, 0),
            portal_end=datetime.time(6, 0)
        )
    return obj

@pytest.fixture
def swimmingpoolinfo_fr(db):
    """Creates a SwimmingPoolInfo object with French translation."""
    with translation.override('fr'):
        obj = SwimmingPoolInfo.objects.create(
            pool_opening_start=datetime.time(10, 0),
            pool_opening_end=datetime.time(21, 0)
        )
    return obj

@pytest.fixture
def foodinfo_fr(db):
    """Creates a FoodInfo object with French translation and food hours."""
    with translation.override('fr'):
        obj = FoodInfo.objects.create(
            burger_food_days="jeudi",
            burger_food_hours_start=datetime.time(18, 30),
            burger_food_hours_end=datetime.time(20, 30),
            pizza_food_days="jeudi",
            bread_hours_reservations=datetime.time(19, 0),
            bread_hours_start=datetime.time(8, 15),
            bread_hours_end=datetime.time(9, 30),
            bar_hours_start=datetime.time(18, 0),
            bar_hours_end=datetime.time(21, 0)
        )
    return obj

@pytest.fixture
def laundryinfo_fr(db):
    """Creates a LaundryInfo object with prices for testing."""
    with translation.override('fr'):
        obj = LaundryInfo.objects.create(
            washing_machine_price=4,
            dryer_price=2
        )
    return obj

@pytest.fixture
def mobilehome_fr(db):
    """Creates a MobileHome object with multilingual fields for testing."""
    with translation.override('fr'):
        obj = MobileHome.objects.create(
            name="Home 1",
            description_text="Description en français",
            description_en="English description",
            description_es="Descripción en español",
            description_de="Deutsche Beschreibung",
            description_nl="Nederlandse beschrijving",
            name_en="Home 1 EN",
            name_es="Home 1 ES",
            name_de="Home 1 DE",
            name_nl="Home 1 NL",
        )
    return obj