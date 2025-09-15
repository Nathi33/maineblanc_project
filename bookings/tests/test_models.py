import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from parler.utils.context import switch_language
from bookings.models import SupplementPrice, Price, Booking, Capacity, MobileHome, SupplementMobileHome, SeasonInfo
import datetime

@pytest.mark.django_db
def test_supplementprice_creation():
    """Test creation of SupplementPrice object and its string representation."""
    s = SupplementPrice.objects.create(
        extra_adult_price=4,
        child_over_8_price=5,
        child_under_8_price=3,
        pet_price=2
    )

    assert s.extra_adult_price == Decimal('4')
    assert s.child_over_8_price == Decimal('5')
    assert s.child_under_8_price == Decimal('3')
    assert s.pet_price == Decimal('2')

    assert str(s) == "Prix des Suppléments"

@pytest.mark.django_db
def test_price_save_and_clean():
    """Test saving a Price object, automatic field population, and validation rules."""
    supp = SupplementPrice.objects.create()
    price = Price.objects.create(
        booking_type='tent',
        season='low',
        price_1_person_with_electricity=10,
        price_2_persons_with_electricity=15
    )
    price.full_clean()
    assert price.included_people == 2
    assert price.supplements is not None
    assert "Tente / Voiture Tente" in str(price)

    # Check validation error for invalid camping_car configuration
    price_cc = Price(
        booking_type='camping_car',
        price_1_person_with_electricity=10
    )
    with pytest.raises(ValidationError):
        price_cc.clean()

@pytest.mark.django_db
def test_booking_save_total_and_deposit():
    """Test booking save, total price calculation, and deposit computation."""
    supp = SupplementPrice.objects.create(extra_adult_price=10)
    price = Price.objects.create(
        booking_type='tent',
        season='low',
        price_1_person_with_electricity=20,
        price_2_persons_with_electricity=30,
        supplements=supp
    )
    booking = Booking.objects.create(
        last_name='Dupont',
        first_name='Jean',
        address='Test',
        postal_code='33000',
        city='Bordeaux',
        phone='0600000000',
        email='test@example.com',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timezone.timedelta(days=2),
        booking_type='tent',
        booking_subtype='tent',
        electricity='yes',
        adults=2
    )
    booking.save()
    total = booking.calculate_total_price()
    deposit = booking.calculate_deposit()
    assert total >= 0
    assert deposit == round(total * Decimal('0.15'), 2)
    assert booking.included_people in [1, 2]
    assert str(booking) == f"{booking.get_booking_type_display()} ({booking.start_date} to {booking.end_date})"

@pytest.mark.django_db
def test_booking_capacity_validation():
    """Test that capacity validation prevents overbooking."""
    cap = Capacity.objects.create(booking_type='tent', max_places=1)
    b1 = Booking.objects.create(
        last_name='A', first_name='A', address='A', postal_code='33000', city='Bordeaux',
        phone='0600000000', email='a@a.com',
        start_date=timezone.now().date(), 
        end_date=timezone.now().date() + datetime.timedelta(days=1),
        booking_type='tent', electricity='yes'
    )
    b1.save()
    b2 = Booking(
        last_name='B', first_name='B', address='B', postal_code='33000', city='Bordeaux',
        phone='0600000000', email='b@b.com',
        start_date=b1.start_date, 
        end_date=b1.end_date,
        booking_type='tent', electricity='yes'
    )
    with pytest.raises(ValidationError):
        b2.check_capacity()

@pytest.mark.django_db
def test_capacity_str():
    """Test the string representation of Capacity."""
    cap = Capacity.objects.create(booking_type='tent', max_places=5)
    assert "5 emplacements" in str(cap)

@pytest.mark.django_db
def test_mobilehome_creation():
    """Test MobileHome object creation and string representation."""
    mh = MobileHome.objects.create(
        name="Mobilhome Test",
        description_text="Description FR"
    )
    assert mh.name == "Mobilhome Test"
    assert str(mh) == "Mobilhome Test"

@pytest.mark.django_db
def test_supplementmobilehome_creation():
    """Test SupplementMobileHome object creation and string representation."""
    smh = SupplementMobileHome.objects.create(
        mobile_home_deposit=400,
        cleaning_deposit=80,
        bed_linen_rental=20
    )
    assert str(smh) == "Suppléments mobil-home"
    assert smh.mobile_home_deposit == Decimal('400')

@pytest.mark.django_db
def test_seasoninfo_creation():
    """Test SeasonInfo object creation and translation handling (French)."""
    season = SeasonInfo.objects.create()
    with switch_language(season, 'fr'):
        season.low_season_start = datetime.date(2024, 9, 27)
        season.save()
        assert season.low_season_start == datetime.date(2024, 9, 27)