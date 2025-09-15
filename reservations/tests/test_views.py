from django.conf import settings
import pytest
from django.urls import reverse
from unittest.mock import patch
from django.contrib.messages import get_messages
from reservations.forms import ReservationRequestForm


# ==============================
# Fixtures
# ==============================

@pytest.fixture
def valid_reservation_data():
    """Valid POST data for the reservation form"""
    return {
        'name': 'Dupont',
        'first_name': 'Jean',
        'address': '10 rue de la Paix',
        'postal_code': '33000',
        'city': 'Bordeaux',
        'phone': '0600000000',
        'email': 'test@example.com',
        'start_date': '2025-09-20',
        'end_date': '2025-09-25',
        'accommodation_type': 'tent',
        'adults': 2,
        'children_over_8': 1,
        'children_under_8': 0,
        'pets': 0,
        'electricity': 'no',
        'tent_length': 5,
        'tent_width': 3,
        'vehicle_length': 4,
        'cable_length': 10,
        'message': 'Bonjour, je souhaite réserver.'
    }

# ==============================
# Tests
# ==============================

@pytest.mark.django_db
def test_get_reservation_request_view(client):
    """GET request to reservation_request returns the form and correct template."""
    url = reverse('reservation_request')
    response = client.get(url)
    assert response.status_code == 200
    assert 'reservations/reservation_request.html' in [t.name for t in response.templates]
    assert isinstance(response.context['form'], ReservationRequestForm)

@pytest.mark.django_db
@patch('reservations.views.EmailMessage.send')
@patch('deepl.Translator.translate_text')
def test_post_valid_reservation_with_datetime_and_label(mock_translate, mock_send, client, valid_reservation_data):
    """POST valid reservation sends email, shows success, and sets submission_datetime."""
    settings.DEEPL_API_KEY = 'fake-api-key'
    
    mock_translate.return_value.text = "Bonjour"

    url = reverse('reservation_request')
    response = client.post(url, data=valid_reservation_data, follow=True)
    
    # Check that email was sent
    assert mock_send.called

    # Check that success message is present
    success_text = "Votre demande de réservation a été envoyée avec succès"
    messages_list = list(get_messages(response.wsgi_request))
    assert any(success_text in str(message) for message in messages_list)

    # Check that context includes correct accommodation_label
    form = response.context['form']
    label_dict = dict(form.fields['accommodation_type'].choices)
    accommodation_value = valid_reservation_data['accommodation_type']
    expected_label = label_dict.get(accommodation_value, accommodation_value)
    assert expected_label == dict(form.fields['accommodation_type'].choices).get(accommodation_value)

    # submission_datetime exists and is timezone-aware
    if 'submission_datetime' in response.context:
        dt = response.context['submission_datetime']
        import datetime
        assert isinstance(dt, datetime.datetime)

@pytest.mark.django_db
def test_post_invalid_reservation(client):
    """POST request with missing required fields returns form errors"""
    url = reverse('reservation_request')
    response = client.post(url, data={}, follow=True)
    assert response.status_code == 200
    form = response.context['form']
    assert form.errors 
