from django.db import models
from django.conf import settings
from datetime import timedelta
from django.core.exceptions import ValidationError
    

class SupplementPrice(models.Model):
    extra_adult_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    child_over_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    child_under_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    pet_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    extra_vehicle_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    extra_tent_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    visitor_price_without_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    visitor_price_with_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    deposit = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return "Suppléments"

class Price(models.Model):
    SEASON_CHOICES = [
        ('low', 'Basse Saison'),
        ('mid', 'Moyenne Saison'),
        ('high', 'Haute Saison'),
    ]

    TYPE_CHOICES = [
        ('tent', 'Tente / Voiture Tente'),
        ('caravan', 'Caravane / Fourgon / Van'),
        ('camping_car', 'Camping-car'),
        ('other', 'Emplacement ouvrier weekend')
    ]

    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, null=True, blank=True,
                              help_text="Laisser vide pour les tarifs ouvriers")
    is_worker = models.BooleanField(default=False)

    # --- Prix clients normaux de base, avec/sans électricité, 1 ou 2 pers ---
    price_1_person_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    price_2_persons_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    price_1_person_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    price_2_persons_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Nombre de personnes incluses dans le tarif de base
    included_people = models.PositiveIntegerField(editable=False) 
    
    # --- Prix ouvriers ---
    worker_week_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Prix par nuit en semaine, électricité incluse")
    weekend_price_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    weekend_price_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # --- Suppléments ---
    supplements = models.ForeignKey(SupplementPrice, on_delete=models.SET_NULL, related_name="prices", null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Automatise le nombre de personnes incluses :
        - Camping-car → toujours 2
        - Autres types → déduit des champs de prix renseignés
        - Fallback → 1
        """
        if self.booking_type == "camping_car":
            self.included_people = 2
        elif self.price_2_persons_with_electricity or self.price_2_persons_without_electricity:
            self.included_people = 2
        elif self.price_1_person_with_electricity or self.price_1_person_without_electricity:
            self.included_people = 1
        else:
            self.included_people = 1 # Fallback par défaut
        
        # Associe automatiquement un SupplementPrice s'il n'y en a pas
        if not self.supplements:
            self.supplements = SupplementPrice.objects.first()

        super().save(*args, **kwargs)

    def clean(self):
        """ Validation spécifique selon le type d'emplacement."""
        errors = {}

        # Camping-cars -> uniquement tarif 2 personnes
        if self.booking_type == "camping_car":
            if self.price_1_person_without_electricity or self.price_1_person_with_electricity:
                errors["booking_type"] = ValidationError(
                    "Pour les camping-cars, ne renseignez pas les champs '1 personne'."
                    "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement les champs '2 personnes'."
                )
        
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        label =  f"{self.get_booking_type_display()}"
        if self.is_worker:
            label += " (Ouvriers)"
        elif self.season:
            label += f" - {self.get_season_display()}"
        return label

class Capacity(models.Model):
    booking_type = models.CharField(max_length=20, choices=Price.TYPE_CHOICES, unique=True)
    max_places = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.get_booking_type_display()} - {self.max_places} emplacements"

class Booking(models.Model):
    TYPE_CHOICES = Price.TYPE_CHOICES

    ELECTRICITY_CHOICES = [
        ('yes', 'Avec électricité'),
        ('no', 'Sans électricité'),
    ]

    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    booking_subtype = models.CharField(max_length=20, null=True, blank=True)
    vehicle_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tent_width = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tent_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children_over_8 = models.PositiveIntegerField(default=0)
    children_under_8 = models.PositiveIntegerField(default=0)
    pets = models.PositiveIntegerField(default=0)
    electricity = models.CharField(max_length=3, choices=ELECTRICITY_CHOICES)
    cable_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    extra_vehicle = models.PositiveIntegerField(default=0)
    extra_tent = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Détermination de la saison
    def get_season(self):
        month, day = self.start_date.month, self.start_date.day
        # basse saison
        if (month >= 9 and day >= 27) or (month <= 4 and day <= 26):
            return 'low'
        # haute saison
        elif (month >= 7 and day >= 5) and (month <= 8 and day <= 30):
            return 'high'
        # moyenne saison
        else:
            return 'mid'

    # Calcul du prix total
    def calculate_total_price(self, supplement=None):
        nights = max((self.end_date - self.start_date).days, 1)

        # Mapping du sous-type vers les types principaux
        subtype_to_type_map = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        # On déduit le type de prix à utiliser
        booking_type_for_price = subtype_to_type_map.get(self.booking_subtype, self.booking_type)

        # Récupération du tarif classique
        season = self.get_season()
        try:
            price = Price.objects.get(
                booking_type=booking_type_for_price,
                is_worker=False,
                season=season
            )
        except Price.DoesNotExist:
            return 0

        # On récupère les suppléments
        if supplement is None:
            supplement = Price.objects.first().supplements if Price.objects.exists() else None

        # Gestion de l'électricité
        electricity_yes = self.electricity == 'yes'

        #Nombre de personnes incluses
        included_people = price.included_people if price else 1

        # Prix de base
        if booking_type_for_price == 'camping_car':
            base_price = price.price_2_persons_with_electricity if electricity_yes else price.price_2_persons_without_electricity
            included_people = 2
        else:
            included_people = 2 if self.adults >= 2 else 1
            if self.adults >= 2:
                base_price = price.price_2_persons_with_electricity if electricity_yes else price.price_2_persons_without_electricity
            else:
                base_price = price.price_1_person_with_electricity if electricity_yes else price.price_1_person_without_electricity

        total = (base_price or 0) * nights

        # Suppléments
        extra_adults = max(self.adults - included_people, 0)
        if supplement:
            total += extra_adults * (supplement.extra_adult_price or 0) * nights
            total += self.children_over_8 * (supplement.child_over_8_price or 0) * nights
            total += self.children_under_8 * (supplement.child_under_8_price or 0) * nights
            total += self.pets * (supplement.pet_price or 0) * nights
            total += self.extra_vehicle * (supplement.extra_vehicle_price or 0) * nights
            total += self.extra_tent * (supplement.extra_tent_price or 0) * nights

        return round(total, 2)

    def save(self, *args, **kwargs):
        """
        Automatise le nombre de personnes incluses selon le type d'hébergement
        et associe un SupplementPrice par défaut si nécessaire.
        """
        # Nombre de personnes incluses
        if self.booking_type == 'camping_car':
            self.included_people = 2
        elif self.booking_type in ['tent', 'caravan']:
            self.included_people = 1 
        else:
            self.included_people = 1 
        
        # Associe automatiquement un SupplementPrice s'il n'y en a pas
        if not hasattr(self, 'supplements') or self.supplements is None:
            self.supplements = SupplementPrice.objects.first()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_booking_type_display()} ({self.start_date} to {self.end_date})"