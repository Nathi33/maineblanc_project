import pytest
from django.utils import timezone
from bookings.forms import BookingFormClassic, BookingDetailsForm
from datetime import timedelta
from unittest.mock import patch

# -----------------------------
# Tests for BookingFormClassic
# -----------------------------
@patch("bookings.models.Booking.check_capacity", return_value=None)
class TestBookingFormClassic:

    def test_valid_data_tent(self, mock_check_capacity):
        """Valid data for tent type with electricity should pass"""
        today = timezone.localdate()
        form_data = {
            "booking_type": "tent",
            "start_date": today + timedelta(days=1),
            "end_date": today + timedelta(days=3),
            "adults": 2,
            "children_over_8": 1,
            "children_under_8": 0,
            "pets": 0,
            "electricity": "yes",
            "cable_length": 10,
            "tent_width": 3,
            "tent_length": 4,
            "vehicle_length": None,
        }
        form = BookingFormClassic(data=form_data)
        assert form.is_valid(), form.errors

    def test_missing_required_field(self, mock_check_capacity):
        """Missing conditional field (cable_length) should raise error"""
        today = timezone.localdate()
        form_data = {
            "booking_type": "tent",
            "start_date": today + timedelta(days=1),
            "end_date": today + timedelta(days=3),
            "adults": 2,
            "children_over_8": 1,
            "children_under_8": 0,
            "pets": 0,
            "electricity": "yes",  
            "tent_width": 3,
            "tent_length": 4,
        }
        form = BookingFormClassic(data=form_data)
        assert not form.is_valid()
        assert "cable_length" in form.errors

    def test_past_start_date(self, mock_check_capacity):
        """Start date in the past should raise error"""
        today = timezone.localdate()
        form_data = {
            "booking_type": "tent",
            "start_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "end_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "adults": 2,
            "children_over_8": 0,
            "children_under_8": 0,
            "pets": 0,
            "electricity": "no",
            "tent_width": 2,
            "tent_length": 3,
        }
        form = BookingFormClassic(data=form_data)
        assert not form.is_valid()
        errors = form.non_field_errors()
        assert "La date d'arrivée ne peut pas être antérieure à aujourd'hui." in errors

    def test_invalid_type_field(self, mock_check_capacity):
        """Invalid booking type should raise error"""
        today = timezone.localdate()
        form_data = {
            "booking_type": "",  # required
            "start_date": today + timedelta(days=1),
            "end_date": today + timedelta(days=3),
            "adults": 2,
            "children_over_8": 0,
            "children_under_8": 0,
            "pets": 0,
            "electricity": "no",
        }
        form = BookingFormClassic(data=form_data)
        assert not form.is_valid()
        assert "booking_type" in form.errors

# -----------------------------
# Tests for BookingDetailsForm
# -----------------------------
@pytest.mark.django_db
class TestBookingDetailsForm:

    def test_valid_data(self):
        """All valid fields should pass and normalize email/strip spaces"""
        form_data = {
            "first_name": " John ",
            "last_name": " Doe ",
            "address": " 123 Rue Test ",
            "postal_code": " 33000 ",
            "city": " Bordeaux ",
            "phone": "+33 6 01 02 03 04 ",
            "email": " JOHN@EXAMPLE.COM ",
        }
        form = BookingDetailsForm(data=form_data)
        assert form.is_valid(), form.errors
        cleaned = form.clean()
        assert cleaned["first_name"] == "John"
        assert cleaned["last_name"] == "Doe"
        assert cleaned["email"] == "john@example.com"
        assert cleaned["phone"] == "+33 6 01 02 03 04"

    def test_invalid_phone(self):
        """Phone with invalid characters should raise error"""
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "address": "123 Test St",
            "postal_code": "33000",
            "city": "Bordeaux",
            "phone": "abc123",
            "email": "john@example.com",
        }
        form = BookingDetailsForm(data=form_data)
        assert not form.is_valid()
        assert "phone" in form.errors

    def test_missing_required_fields(self):
        """Required fields missing should raise errors"""
        form_data = {
            "first_name": "",
            "last_name": "",
            "address": "",
            "postal_code": "",
            "city": "",
            "phone": "",
            "email": "",
        }
        form = BookingDetailsForm(data=form_data)
        assert not form.is_valid()
        for field in form_data.keys():
            assert field in form.errors
