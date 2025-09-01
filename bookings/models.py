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
        ('caravan', 'Caravane / Fourgon'),
        ('camping_car', 'Camping-car'),
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
        # Automatise le nombre de personnes incluses selon le type d'hébergement.
        if self.booking_type == "camping_car":
            self.included_people = 2
        else:
            self.included_people = 1
        
        # Associe automatiquement un SupplementPrice s'il n'y en a pas
        if not self.supplements:
            self.supplements = SupplementPrice.objects.first()

        super().save(*args, **kwargs)

    def clean(self):
        """ Validation spécifique selon le type d'emplacement."""
        if self.booking_type == "camping_car":
            if self.price_1_person_without_electricity or self.price_1_person_with_electricity:
                raise ValidationError(
                    "Pour les camping-cars, ne enseignez pas les champs '1 personne'."
                    "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement la colonne 2 personnes."
                )

    def __str__(self):
        label =  f"{self.get_booking_type_display()}"
        if self.is_worker:
            label += " (Ouvriers)"
        elif self.season:
            label += f" - {self.get_season_display()}"
        return label


class Booking(models.Model):
    TYPE_CHOICES = Price.TYPE_CHOICES

    ELECTRICITY_CHOICES = [
        ('yes', 'Avec électricité'),
        ('no', 'Sans électricité'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_worker = models.BooleanField(default=False, help_text="Tarif spécial ouvrier")
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
    def calculate_total_price(self):
        nights = max((self.end_date - self.start_date).days, 1)

        # --- TARIF OUVRIERS ---
        if self.is_worker:
            try:
                price = Price.objects.get(booking_type=self.booking_type, is_worker=True)
            except Price.DoesNotExist:
                return 0
            
            total = 0

            for d in self._get_date_range():
                if d.weekday() >= 5:  # Week-end
                    if self.electricity == 'yes':
                        total += price.weekend_price_with_electricity or 0
                    else:
                        total += price.weekend_price_without_electricity or 0
                else:  # Semaine
                    total += price.worker_week_price or 0  # L'électricité est incluse
            return round(total, 2)
        
        # --- TARIF CLIENT NORMAL ---
        season = self.get_season()
        try:
            price = Price.objects.get(
                booking_type=self.booking_type, 
                is_worker=False,
                season=season
            )
        except Price.DoesNotExist:
            return 0

        # On récupère les suppléments
        supplement = SupplementPrice.objects.first()

        # Tarif de base avec ou sans électricité
        if self.electricity == 'yes':
            total = price.price_with_electricity * nights
        else:
            total = price.price_without_electricity * nights

        # Nombre de personnes incluses dans le prix de base 
        included = price.included_people
        if self.adults > included:
            total += (self.adults - included) * (supplement.extra_adult_price if supplement else 0) * nights
        total += self.children_over_8 * (supplement.child_over_8_price if supplement else 0) * nights
        total += self.children_under_8 * (supplement.child_under_8_price if supplement else 0) * nights
        total += self.pets * (supplement.pet_price if supplement else 0) * nights

        # Autres suppléments
        total += self.extra_vehicle * (supplement.extra_vehicle_price if supplement else 0) * nights
        total += self.extra_tent * (supplement.extra_tent_price if supplement else 0) * nights

        return round(total, 2)

    def _get_date_range(self):
        return [self.start_date + timedelta(days=i) for i in range((self.end_date - self.start_date).days + 1)]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_booking_type_display()} ({self.start_date} to {self.end_date})"