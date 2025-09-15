from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """
    Configuration for the 'bookings' app, which manages pricing and reservations.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    verbose_name = "Prix et Réservations"
