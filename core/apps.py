from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration for the 'core' app, which manages general campsite information.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "Informations diverses"


