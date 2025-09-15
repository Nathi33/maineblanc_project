from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """
    Configuration for the 'reservations' app, which handles booking requests and forms.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
