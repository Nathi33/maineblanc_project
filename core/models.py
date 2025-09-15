import logging
from django.db import models
from parler.models import TranslatableModel, TranslatedFields
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import deepl
import datetime

logger = logging.getLogger(__name__)

class CampingInfo(TranslatableModel):
    """
    Stores general camping rules and schedules.

    Fields include reception hours, arrival and departure times, and gate opening hours.

    Security:
        - No direct user input, so XSS or SQL injection risk is minimal.
    """
    translations = TranslatedFields(
        # Reception hours
        welcome_start = models.TimeField(
            default=datetime.time(9, 0), 
            verbose_name="Horaire d'accueil du matin"
        ),
        welcome_end = models.TimeField(
            default=datetime.time(12, 0), 
            verbose_name="Horaire d'accueil du midi"
        ),
        welcome_afternoon_start = models.TimeField(
            default=datetime.time(14, 0), 
            verbose_name="Horaire d'accueil début après-midi"
        ),
        welcome_afternoon_end = models.TimeField(
            default=datetime.time(19, 0), 
            verbose_name="Horaire d'accueil fin après-midi"
        ),

        # Arrivals
        arrivals_start_high = models.TimeField(
            default=datetime.time(14, 0), 
            verbose_name="Début arrivées haute saison"
        ),
        arrivals_end_high = models.TimeField(
            default=datetime.time(21, 0), 
            verbose_name="Fin arrivées haute saison"
        ),
        arrivals_end_low = models.TimeField(
            default=datetime.time(19, 0), 
            verbose_name="Fin arrivées basse saison"
        ),

        # Departures
        departure_end = models.TimeField(
            default=datetime.time(12, 0), 
            verbose_name="Départs au plus tard"
        ),

        # Gate opening/closing
        portal_start = models.TimeField(
            default=datetime.time(22, 0), 
            verbose_name="Fermeture portail"
        ),
        portal_end = models.TimeField(
            default=datetime.time(6, 0), 
            verbose_name="Ouverture portail"
        ),
    )

    class Meta:
        verbose_name = "Modalités du camping"
        verbose_name_plural = "Modalités du camping"

    def __str__(self):
        return "Informations diverses sur les modalités du camping"


class SwimmingPoolInfo(TranslatableModel):
    """
    Stores swimming pool schedule information.

    Security:
        - No user input processed.
    """
    translations = TranslatedFields(
        pool_opening_start = models.TimeField(
            default=datetime.time(10, 0), 
            verbose_name="Ouverture piscine"
        ),
        pool_opening_end = models.TimeField(
            default=datetime.time(21, 0), 
            verbose_name="Fermeture piscine"
        ),
    )

    class Meta:
        verbose_name = "Piscine"
        verbose_name_plural = "Piscine"

    def __str__(self):
        return "Informations diverses sur la piscine"
    

class FoodInfo(TranslatableModel):
    """
    Stores information about food services such as food trucks, pizza days,
    bread reservations, and bar opening hours.

    Translations:
        - Automatically translates burger and pizza days using DeepL API.
        - Logs translation errors without interrupting save process.

    Security:
        - No user input is directly processed here, reducing XSS risk.
        - DeepL API errors are caught and logged.
    """
    translations = TranslatedFields(
        # Food truck (Burger)
        burger_food_days = models.CharField(
            max_length=100, 
            default="jeudi", 
            verbose_name="Jours absence Food Truck Burger"
        ),
        burger_food_hours_start = models.TimeField(
            default=datetime.time(18, 30), 
            verbose_name="Horaires début Food Truck Burger"
        ),
        burger_food_hours_end = models.TimeField(
            default=datetime.time(20, 30), 
            verbose_name="Horaires fin Food Truck Burger"
        ),

        # Pizza
        pizza_food_days = models.CharField(
            max_length=100, 
            default="jeudi", 
            verbose_name="Jours présence Pizza"
        ),

        # Bread reservations and distribution
        bread_hours_reservations = models.TimeField(
            default=datetime.time(19, 0),
            verbose_name="Horaires réservations pain et viennoiseries"
        ),
        bread_hours_start = models.TimeField(
            default=datetime.time(8, 15),
            verbose_name="Horaires début distribution pain et viennoiseries"
        ),
        bread_hours_end = models.TimeField(
            default=datetime.time(9, 30),
            verbose_name="Horaires fin distribution pain et viennoiseries"
        ),

        # Bar
        bar_hours_start = models.TimeField(
            default=datetime.time(18, 0),
            verbose_name="Horaires ouverture bar"
        ),
        bar_hours_end = models.TimeField(
            default=datetime.time(21, 0),
            verbose_name="Horaires fermeture bar"
        ),
    )

    class Meta:
        verbose_name = "Restauration"
        verbose_name_plural = "Restauration"

    def __str__(self):
        return "Informations diverses sur la restauration"

    def save(self, *args, **kwargs):
        """
        Overrides save to automatically translate certain fields into multiple languages
        using DeepL API. Errors are logged but do not interrupt saving.

        Security:
            - Only controlled default values are translated; no user input is processed.
        """
        super().save(*args, **kwargs)

        # Check if DEEPL_API_KEY is set in settings
        if not getattr(settings, "DEEPL_API_KEY", None):
            return

        translator = deepl.Translator(settings.DEEPL_API_KEY)
        target_languages = ["en", "es", "de", "nl"]

        for lang in target_languages:
            try:
                # Create or retrieve translation object for the target language
                translation, _ = self.translations.get_or_create(language_code=lang)

                # Translate Burger days
                translation.burger_food_days = translator.translate_text(
                    self.burger_food_days,
                    target_lang=lang.upper() if lang != "en" else "EN-GB"
                ).text

                # Translate Pizza days
                translation.pizza_food_days = translator.translate_text(
                    self.pizza_food_days,
                    target_lang=lang.upper() if lang != "en" else "EN-GB"
                ).text

                translation.save()
            
            except deepl.DeepLException as e:
                logger.error(f"Erreur de traduction DeepL pour la langue {lang}: {e}")
                continue
    

class LaundryInfo(TranslatableModel):
    """
    Stores information about laundry services and pricing.

    Security:
        - Only fixed numeric values; no user input.
    """
    translations = TranslatedFields(
        washing_machine_price = models.DecimalField(
            max_digits=2, 
            decimal_places=0, 
            default=4.00,
            verbose_name="Prix machine à laver"
        ),
        dryer_price = models.DecimalField(
            max_digits=2, 
            decimal_places=0, 
            default=2.00,
            verbose_name="Prix sèche-linge"
        ),
    )

    class Meta:
        verbose_name = "Laverie"
        verbose_name_plural = "Laverie"

    def __str__(self):
        return "Informations diverses sur la laverie"

    