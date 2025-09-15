import pytest
from django.urls import reverse
from django.core import mail
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
from bookings.models import Booking, SupplementPrice
from datetime import date
from decimal import Decimal

pytestmark = pytest.mark.django_db

# ------------------------------
# Fixtures
# ------------------------------
@pytest.fixture
def valid_booking_data():
    """Returns a dictionary of valid booking data for form submission tests."""
    return {
        "booking_subtype": "tent",
        "start_date": "2025-09-15",
        "end_date": "2025-09-17",
        "adults": 2,
        "children": 1,
        "children_over_8": 1,
        "children_under_8": 0,
        "pets": 0,
        "electricity": "yes"
    }


@pytest.fixture
def client_details_data():
    """Returns a dictionary of valid client personal details for form submission tests."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "address": "123 rue du Test",
        "postal_code": "33000",
        "city": "Bordeaux",
        "email": "john@example.com",
        "phone": "0601020304"
    }


@pytest.fixture
def supplements():
    """Creates and returns a SupplementPrice object for price calculation tests."""
    return SupplementPrice.objects.create(
        extra_adult_price=10,
        child_over_8_price=5,
        child_under_8_price=3,
        pet_price=2,
        extra_vehicle_price=5,
        extra_tent_price=4,
        visitor_price_without_swimming_pool=6,
        visitor_price_with_swimming_pool=8
    )


# ------------------------------
# Helpers
# ------------------------------
def set_booking_session(client, booking_data):
    """Stores booking data in client session for views that rely on session data."""
    session = client.session
    session["booking_data"] = booking_data
    session.save()


# ------------------------------
# 1. booking_form
# ------------------------------
@patch("bookings.models.Booking.check_capacity", return_value=None)
def test_booking_form_valid(mock_check_capacity, client):
    """Submitting a valid booking form should redirect to booking_summary and call check_capacity."""
    valid_booking_data = {
        "booking_type": "tent",
        "booking_subtype": "tent",
        "start_date": "2025-09-20",
        "end_date": "2025-09-25",
        "adults": 2,
        "children": 1,
        "children_over_8": 1,
        "children_under_8": 0,
        "pets": 0,
        "electricity": "yes",
        "cable_length": 10,
        "vehicle_length": 4,
        "tent_length": 3,
        "tent_width": 2,
    }

    url = reverse("booking_form")
    response = client.post(url, data=valid_booking_data)

    if response.status_code != 302:
        print("Form errors:", response.context['form'].errors)

    assert response.status_code == 302
    assert response.url == reverse("booking_summary")
    mock_check_capacity.assert_called()


# ------------------------------
# 2. booking_summary
# ------------------------------
@patch("bookings.models.Booking.calculate_total_price", return_value=Decimal("100.00"))
@patch("bookings.models.Booking.calculate_deposit", return_value=Decimal("30.00"))
def test_booking_summary_displays_correct_prices(mock_deposit, mock_total, client, valid_booking_data):
    """Booking summary view should correctly display total, deposit, and remaining balance."""
    set_booking_session(client, valid_booking_data)
    url = reverse("booking_summary")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["total_price"] == Decimal("100.00")
    assert response.context["deposit"] == Decimal("30.00")
    assert response.context["remaining_balance"] == Decimal("70.00")


# ------------------------------
# 3. booking_details
# ------------------------------
@patch("stripe.checkout.Session.create")
@patch("bookings.models.Booking.calculate_deposit", return_value=Decimal("50.00"))
def test_booking_details_creates_stripe_session(mock_deposit, mock_stripe, client, valid_booking_data, client_details_data, supplements):
    """Booking details view should create a Stripe session for deposit payment and redirect to Stripe."""
    set_booking_session(client, valid_booking_data)

    mock_stripe.return_value = MagicMock(url="https://stripe.com/checkout-session")
    url = reverse("booking_details")
    response = client.post(url, data=client_details_data)

    assert response.status_code == 302
    assert response.url == "https://stripe.com/checkout-session"

    assert mock_stripe.called
    assert mock_stripe.call_args.kwargs["mode"] == "payment"
    assert mock_stripe.call_args.kwargs["line_items"][0]["price_data"]["unit_amount"] > 0


# ------------------------------
# 4. booking_confirm
# ------------------------------
@patch("django.core.mail.EmailMessage.send")
def test_booking_confirm_saves_booking_and_sends_emails(mock_send, client, valid_booking_data, client_details_data):
    """Booking confirmation should save the booking, mark deposit as paid, send emails, and clear session."""
    booking_session_data = {**valid_booking_data, **client_details_data}
    set_booking_session(client, booking_session_data)

    url = reverse("booking_confirm")
    response = client.get(url, follow=True)

    booking = Booking.objects.get(email="john@example.com")
    assert booking.deposit_paid is True
    assert booking.start_date == date(2025, 9, 15)

    assert mock_send.call_count == 2

    assert "booking_data" not in client.session

    messages_list = list(get_messages(response.wsgi_request))
    assert any("Votre réservation a été confirmée" in str(m) for m in messages_list)
