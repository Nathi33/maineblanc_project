from django.db import models
from parler.models import TranslatableModel, TranslatedFields
from django.utils.translation import gettext_lazy as _
import datetime

class CampingInfo(TranslatableModel):
    translations = TranslatedFields(
        # Horaires accueil
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

        # Arrivées
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

        # Départs
        departure_end = models.TimeField(
            default=datetime.time(12, 0), 
            verbose_name="Départs au plus tard"
        ),

        # Portail
        portal_start = models.TimeField(
            default=datetime.time(22, 0), 
            verbose_name="Fermeture portail"
        ),
        portal_end = models.TimeField(
            default=datetime.time(6, 0), 
            verbose_name="Ouverture portail"
        ),
    )

    def __str__(self):
        return "Informations diverses sur les modalités du camping"

    class Meta:
        verbose_name = "Modalités du camping"
        verbose_name_plural = "Modalités du camping"

class SwimmingPoolInfo(TranslatableModel):
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

    def __str__(self):
        return "Informations diverses sur la piscine"

    class Meta:
        verbose_name = "Piscine"
        verbose_name_plural = "Piscine"

class FoodInfo(TranslatableModel):
    translations = TranslatedFields(
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
        pizza_food_days = models.CharField(
            max_length=100, 
            default="jeudi", 
            verbose_name="Jours présence Pizza"
        ),
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
        bar_hours_start = models.TimeField(
            default=datetime.time(18, 0),
            verbose_name="Horaires ouverture bar"
        ),
        bar_hours_end = models.TimeField(
            default=datetime.time(21, 0),
            verbose_name="Horaires fermeture bar"
        ),
    )

    def __str__(self):
        return "Informations diverses sur la restauration"

    class Meta:
        verbose_name = "Restauration"
        verbose_name_plural = "Restauration"

class LaundryInfo(TranslatableModel):
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

    def __str__(self):
        return "Informations diverses sur la laverie"

    class Meta:
        verbose_name = "Laverie"
        verbose_name_plural = "Laverie"