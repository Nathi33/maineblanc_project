from django.db import models
from django.conf import settings
from datetime import timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils import formats
from parler.models import TranslatableModel, TranslatedFields
import datetime
import deepl
    

class SupplementPrice(models.Model):
    extra_adult_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Prix/Adulte supplémentaire")
    child_over_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Prix/Enfant +8 ans")
    child_under_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Prix/Enfant -8 ans")
    pet_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Prix/Animal de compagnie")
    extra_vehicle_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix/Véhicule supplémentaire")
    extra_tent_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix/Tente supplémentaire")
    visitor_price_without_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix/Visiteur sans piscine")
    visitor_price_with_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix/Visiteur avec piscine")

    class Meta:
        verbose_name = "Prix des Suppléments"
        verbose_name_plural = "Prix des Suppléments"

    def __str__(self):
        return "Prix des Suppléments"

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

    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'emplacement")
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, null=True, blank=True, verbose_name="Saison",
                              help_text="Laisser vide pour les tarifs ouvriers")
    is_worker = models.BooleanField(default=False, verbose_name="Tarif Ouvrier",)

    # --- Prix clients normaux de base, avec/sans électricité, 1 ou 2 pers ---
    price_1_person_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix 1 personne avec électricité")
    price_2_persons_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix 2 personnes avec électricité")

    price_1_person_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix 1 personne sans électricité")
    price_2_persons_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix 2 personnes sans électricité")

    # Nombre de personnes incluses dans le tarif de base
    included_people = models.PositiveIntegerField(editable=False) 
    
    # --- Prix ouvriers ---
    worker_week_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix ouvrier semaine", help_text="Prix par nuit en semaine, électricité incluse")
    weekend_price_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix ouvrier week-end sans électricité")
    weekend_price_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Prix ouvrier week-end avec électricité")

    # --- Suppléments ---
    supplements = models.ForeignKey(SupplementPrice, on_delete=models.SET_NULL, related_name="prices", null=True, blank=True)

    class Meta:
        verbose_name = "Tarif"
        verbose_name_plural = "Tarifs"

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
    
class OtherPrice(TranslatableModel):
    translations = TranslatedFields(
        current_year = models.PositiveIntegerField(
            default=datetime.datetime.now().year,
            verbose_name="Année"
        ),
        tourist_tax_date = models.DateField(
            default=datetime.date(2025, 1, 1), 
            verbose_name="Date taxe de séjour"
        ),
        price_tourist_tax = models.DecimalField( 
            max_digits=5, decimal_places=2, default=0.29, 
            verbose_name="Prix taxe de séjour par nuit/personne"
        ),
    )

    def __str__(self):
        return "Tarifs divers"

    class Meta:
        verbose_name = "Tarifs et infos divers"
        verbose_name_plural = "Tarifs et infos divers"

class Capacity(models.Model):
    booking_type = models.CharField(max_length=20, choices=Price.TYPE_CHOICES, unique=True, verbose_name="Type d'emplacement")
    max_places = models.PositiveIntegerField(default=1, verbose_name="Nombre maximum d'emplacements")
    number_locations = models.PositiveIntegerField(
        default=66, 
        verbose_name="Nombre d'emplacements"
    )
    number_mobile_homes = models.PositiveIntegerField(
        default=5, 
        verbose_name="Nombre de mobil-homes"
    )

    class Meta:
        verbose_name = "Capacité d'emplacements"
        verbose_name_plural = "Capacités d'emplacements"

    def __str__(self):
        return f"{self.get_booking_type_display()} - {self.max_places} emplacements"

class Booking(models.Model):
    # Types principaux
    TYPE_CHOICES = Price.TYPE_CHOICES

    # Sous-types
    SUBTYPE_CHOICES = [
        ('tent', _('Tente')),
        ('car_tent', _('Voiture Tente')),
        ('caravan', _('Caravane')),
        ('fourgon', _('Fourgon')),
        ('van', _('Van')),
        ('camping_car', _('Camping-car')),
    ]

    ELECTRICITY_CHOICES = [
        ('yes', _('Avec électricité')),
        ('no', _('Sans électricité')),
    ]

    # Informations client
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    address = models.CharField(max_length=255, verbose_name="Adresse")
    postal_code = models.CharField(max_length=10, verbose_name="Code postal")
    city = models.CharField(max_length=100, verbose_name="Ville")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField()

    # Informations réservation
    start_date = models.DateField(verbose_name="Date d'arrivée")
    end_date = models.DateField(verbose_name="Date de départ")
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'emplacement")
    booking_subtype = models.CharField(max_length=20, choices=SUBTYPE_CHOICES, null=True, blank=True, verbose_name="Sous-type d'emplacement")
    electricity = models.CharField(max_length=3, choices=ELECTRICITY_CHOICES, verbose_name="Électricité")
    deposit_paid = models.BooleanField(default=False, verbose_name="Acompte payé")

    # Champs spécifiques
    tent_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Longueur de la tente")
    tent_width = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Largeur de la tente")
    vehicle_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Longueur du véhicule")
    cable_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Longueur du câble")

    # Nombre de personnes
    adults = models.PositiveIntegerField(default=1, verbose_name="Adultes")
    children_over_8 = models.PositiveIntegerField(default=0, verbose_name="Enfants +8 ans")
    children_under_8 = models.PositiveIntegerField(default=0, verbose_name="Enfants -8 ans")
    pets = models.PositiveIntegerField(default=0, verbose_name="Animaux de compagnie")

    # Véhicule et tente supplémentaire
    extra_vehicle = models.PositiveIntegerField(default=0, verbose_name="Véhicule supplémentaire")
    extra_tent = models.PositiveIntegerField(default=0, verbose_name="Tente supplémentaire")

    # Suivi interne
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    # Map des sous-types vers type principal
    MAIN_TYPE_MAP = {
        'tent': 'tent',
        'car_tent': 'tent',
        'caravan': 'caravan',
        'fourgon': 'caravan',
        'van': 'caravan',
        'camping_car': 'camping_car',
    }

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-created_at']

    def created_at_display(self):
        if not self.created_at:
            return ""
        local_dt = timezone.localtime(self.created_at)
        return formats.date_format(local_dt, format='d F Y à H:i', use_l10n=True)
    created_at_display.short_description = "Créé le"

    def updated_at_display(self):
        if not self.updated_at:
            return ""
        local_dt = timezone.localtime(self.updated_at)
        return formats.date_format(local_dt, format='d F Y à H:i', use_l10n=True)
    updated_at_display.short_description = "Mis à jour le"

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
    

    def calculate_deposit(self):
        """ Calcule l'acompte non remboursable de 15% """
        total_price = self.calculate_total_price()
        return round(total_price * Decimal('0.15'), 2)


    def save(self, *args, **kwargs):
        """
        Automatise : 
        - Le type principal à partir du sous-type
        - Le nombre de personnes incluses selon le type
        - L'association d'un SupplementPrice s'il n'y en a pas
        """
        # Définition automatique du type principal
        MAIN_TYPE_MAP = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        if self.booking_subtype:
            self.booking_type = MAIN_TYPE_MAP.get(self.booking_subtype, self.booking_subtype)
        
        # Nombre de personnes incluses
        if self.booking_type == 'camping_car':
            self.included_people = 2
        else:
            self.included_people = 1 
        
        # Associe automatiquement un SupplementPrice s'il n'y en a pas
        if not hasattr(self, 'supplements') or self.supplements is None:
            self.supplements = SupplementPrice.objects.first()

        super().save(*args, **kwargs)

    def check_capacity(self):
        """
        Vérifie si le type d'emplacement est disponible pour les dates choisies.
        Utilisable avant création de la réservation.
        """

        # Mapping des sous-types vers les types principaux
        MAIN_TYPE_MAP = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        # Détermination du type principal
        main_type = MAIN_TYPE_MAP.get(self.booking_type, self.booking_type)

        try:
            capacity = Capacity.objects.get(booking_type=main_type).max_places
        except Capacity.DoesNotExist:
            raise ValidationError(_("La capacité pour %(type)s n'est pas définie.") % {'type': main_type})
    
        # Comptabilise le nombre de réservations existantes qui se  chevauchent
        overlapping = Booking.objects.filter(
            booking_type__in=[key for key, value in MAIN_TYPE_MAP.items() if value == main_type],
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(pk=self.pk)  # Exclut la réservation actuelle en cas de modification

        # Vérifie si la nouvelle réservation dépasse la capacité
        if overlapping.count() >= capacity:
            raise ValidationError(
                _("Plus de places disponibles pour ces dates. "
                "Veuillez choisir d'autres dates ou contacter le camping.")
            )

    def clean(self):
        """
        Validation complète de l'objet avant sauvegarde.
        Vérifie la capacité et d'autres contraintes métier.
        """
        super().clean()

        # Vérification de la capacité
        self.check_capacity()

        # Vérifications spécifiques selon le type d'emplacement
        errors = {}

        # Camping-car -> uniquement tarif 2 personnes
        if hasattr(self, 'price_1_person_with_electricity') or hasattr(self, 'price_1_person_without_electricity'):
            if getattr(self, 'booking_type', '') == "camping_car":
                if getattr(self, 'price_1_person_with_electricity', None) or getattr(self, 'price_1_person_without_electricity', None):
                    errors["booking_type"] = ValidationError(
                        _("Pour les camping-cars, ne renseignez pas les champs '1 personne'."
                        "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement les champs '2 personnes'.")
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_booking_type_display()} ({self.start_date} to {self.end_date})"
    
class MobileHome(models.Model):
    # Nom traduit automatiquement
    name = models.CharField(max_length=100, verbose_name= "Nom du mobil-home")
    name_en = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (EN)")
    name_es = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (ES)")
    name_de = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (DE)")
    name_nl = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (NL)")

    # Description traduite automatiquement
    description_text = models.TextField(blank=True, verbose_name= "Description FR")   
    description_en = models.TextField(blank=True, verbose_name= "Description EN")
    description_es = models.TextField(blank=True, verbose_name= "Description ES")
    description_de = models.TextField(blank=True, verbose_name= "Description DE")
    description_nl = models.TextField(blank=True, verbose_name= "Description NL")

    # Prix à la nuitée
    night_price = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/nuitée (basse et moyenne saison)")
    night_price_mid = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True,
        verbose_name= "Prix/nuitée (moyenne saison)"
    )

    # Prix par semaine selon la saison
    week_low = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine (basse saison)")
    week_mid = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine (moyenne saison)")
    week_high = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine (haute saison)")

    # Prix spécial ouvriers (même tarif pour toutes les saisons)
    is_worker_home = models.BooleanField(default=False, verbose_name= "Réservé aux ouvriers")
    worker_price_1p = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine 1 personne (ouvrier)")
    worker_price_2p = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine 2 personnes (ouvrier)")
    worker_price_3p = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, verbose_name= "Prix/semaine 3 personnes (ouvrier)")

    class Meta:
        verbose_name = "Mobil-home"
        verbose_name_plural = "Mobil-homes"

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Traduction automatique du nom et de la description en plusieurs langues via DeepL API.
        """
        if settings.DEEPL_API_KEY and self.description_text:
            translator = deepl.Translator(settings.DEEPL_API_KEY)
            # Traduction du nom
            if self.name:
                if not self.name_en or 'update_fields' in kwargs:
                    self.name_en = translator.translate_text(self.name, target_lang="EN-GB").text
                if not self.name_es or 'update_fields' in kwargs:
                    self.name_es = translator.translate_text(self.name, target_lang="ES").text
                if not self.name_de or 'update_fields' in kwargs:
                    self.name_de = translator.translate_text(self.name, target_lang="DE").text
                if not self.name_nl or 'update_fields' in kwargs:
                    self.name_nl = translator.translate_text(self.name, target_lang="NL").text

        # Traduction de la description
        if self.description_text:
            if not self.description_en or 'update_fields' in kwargs:
                result = translator.translate_text(self.description_text, target_lang="EN-GB")
                self.description_en = result.text
            if not self.description_es or 'update_fields' in kwargs:
                result = translator.translate_text(self.description_text, target_lang="ES")
                self.description_es = result.text
            if not self.description_es or 'update_fields' in kwargs:
                result = translator.translate_text(self.description_text, target_lang="ES")
                self.description_es = result.text
            if not self.description_de or 'update_fields' in kwargs:
                result = translator.translate_text(self.description_text, target_lang="DE")
                self.description_de = result.text
            if not self.description_nl or 'update_fields' in kwargs:
                result = translator.translate_text(self.description_text, target_lang="NL")
                self.description_nl = result.text

        super().save(*args, **kwargs)
    
class SupplementMobileHome(TranslatableModel):
    translations = TranslatedFields(
        mobile_home_deposit = models.DecimalField(
            max_digits=4,
            decimal_places=0, 
            default=350,
            verbose_name="Montant caution mobil-home"
        ),
        cleaning_deposit = models.DecimalField(
            max_digits=4, 
            decimal_places=0, 
            default=70,
            verbose_name="Montant caution ménage"
        ),
        bed_linen_rental = models.DecimalField(
            max_digits=4, 
            decimal_places=0, 
            default=15,
            verbose_name="Prix location linge de lit"
        ),
    )

    def __str__(self):
        return "Suppléments mobil-home"

    class Meta:
        verbose_name = "Suppléments mobil-home"
        verbose_name_plural = "Suppléments mobil-home"

    
class SeasonInfo(TranslatableModel):
    translations = TranslatedFields(
        low_season_start = models.DateField( 
            default=datetime.date(2024, 9, 27), 
            verbose_name="Début basse saison"
        ),
        low_season_end = models.DateField(
            default=datetime.date(2024, 4, 26), 
            verbose_name="Fin basse saison"
        ),
        mid_season_start_1 = models.DateField(
            default=datetime.date(2024, 4, 27), 
            verbose_name="Début moyenne saison 1"
        ),
        mid_season_end_1 = models.DateField(
            default=datetime.date(2024, 7, 5), 
            verbose_name="Fin moyenne saison 1"
        ),
        mid_season_start_2 = models.DateField( 
            default=datetime.date(2024, 8, 30), 
            verbose_name="Début moyenne saison 2"
        ),
        mid_season_end_2 = models.DateField(
            default=datetime.date(2024, 9, 26), 
            verbose_name="Fin moyenne saison 2"
        ),
        high_season_start = models.DateField(
            default=datetime.date(2024, 7, 6), 
            verbose_name="Début haute saison"
        ),
        high_season_end = models.DateField(
            default=datetime.date(2024, 8, 29), 
            verbose_name="Fin haute saison"
        ),
    )

    def __str__(self):
        return "Dates des saisons"

    class Meta:
        verbose_name = "Dates des saisons"
        verbose_name_plural = "Dates des saisons"