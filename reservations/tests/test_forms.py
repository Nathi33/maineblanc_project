import pytest
from reservations.forms import ReservationRequestForm
from django.utils import timezone

# ==============================
# Fixtures
# ==============================

@pytest.fixture
def valid_form_data():
    """Valid data for the booking form"""
    today = timezone.localdate()
    start = today + timezone.timedelta(days=1)
    end = start + timezone.timedelta(days=5)
    return {
        'name': 'Dupont',
        'first_name': 'Jean',
        'address': '10 rue de la Paix',
        'postal_code': '33000',
        'city': 'Bordeaux',
        'phone': '0600000000',
        'email': 'test@example.com',
        'start_date': start,
        'end_date': end,
        'accommodation_type': 'tent',
        'adults': 2,
        'children_over_8': 1,
        'children_under_8': 0,
        'pets': 0,
        'electricity': 'no',
        'tent_length': 5,
        'tent_width': 3,
        'vehicle_length': None,
        'cable_length': None,
        'message': 'Bonjour'
    }

# ==============================
# Tests
# ==============================

def test_form_valid(valid_form_data):
    """Form with all valid data should be valid."""
    form = ReservationRequestForm(data=valid_form_data)
    assert form.is_valid() 

def test_form_missing_required_field(valid_form_data):
    """Form missing 'name' field should be invalid and report error."""
    valid_form_data.pop('name')  
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()
    assert 'name' in form.errors

def test_form_dates_invalid(valid_form_data):
    """Start date in the past or end date not after start should be invalid."""
    valid_form_data['start_date'] = timezone.localdate() - timezone.timedelta(days=1)
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()
    assert "La date d'arrivée ne peut pas être antérieure à aujourd'hui." in form.non_field_errors()

    valid_form_data['start_date'] = timezone.localdate() + timezone.timedelta(days=2)
    valid_form_data['end_date'] = valid_form_data['start_date']
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()
    assert "La date de départ doit être postérieure à la date d'arrivée." in form.non_field_errors()

def test_form_tent_requires_dimensions(valid_form_data):
    """Tent accommodation requires both length and width to be filled."""
    valid_form_data['tent_length'] = None
    valid_form_data['tent_width'] = None
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()  
    assert "La longueur et la largeur de la tente sont obligatoires" in str(form.errors)

def test_form_vehicle_requires_length(valid_form_data):
    """Vehicle-type accommodation requires vehicle_length to be filled."""
    valid_form_data['accommodation_type'] = 'van'
    valid_form_data['vehicle_length'] = None
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()
    assert "La longueur du véhicule est obligatoire" in str(form.errors)

def test_form_cable_requires_if_electricity_yes(valid_form_data):
    """If electricity is 'yes', cable_length must be filled."""
    valid_form_data['accommodation_type'] = 'camping_car'
    valid_form_data['electricity'] = 'yes'
    valid_form_data['cable_length'] = ''
    form = ReservationRequestForm(data=valid_form_data)
    assert not form.is_valid()
    assert "La longueur du câble électrique est obligatoire si l'électricité est demandée." in form.non_field_errors()
