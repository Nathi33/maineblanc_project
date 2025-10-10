from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator, EmailValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils import formats
from parler.models import TranslatableModel, TranslatedFields
import datetime
import deepl
    

class SupplementPrice(models.Model):
    """
    Stores additional pricing options for reservations.

    Fields:
        - extra_adult_price: price per extra adult
        - child_over_8_price: price per child over 8 years
        - child_under_8_price: price per child under 8 years
        - pet_price: price per pet
        - extra_vehicle_price: price per additional vehicle
        - extra_tent_price: price per additional tent
        - visitor_price_without_swimming_pool: visitor price without pool
        - visitor_price_with_swimming_pool: visitor price with pool

    Security:
        - Only stores numeric data
        - No user input processed directly
    """
    extra_adult_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], verbose_name="Prix/Adulte supplémentaire")
    child_over_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], verbose_name="Prix/Enfant +8 ans")
    child_under_8_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], verbose_name="Prix/Enfant -8 ans")
    pet_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], verbose_name="Prix/Animal de compagnie")
    extra_vehicle_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix/Véhicule supplémentaire")
    extra_tent_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix/Tente supplémentaire")
    visitor_price_without_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix/Visiteur sans piscine")
    visitor_price_with_swimming_pool = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix/Visiteur avec piscine")

    class Meta:
        verbose_name = "Prix des Suppléments"
        verbose_name_plural = "Prix des Suppléments"

    def __str__(self):
        """Return a human-readable string for the admin interface."""
        return "Prix des Suppléments"

class Price(models.Model):
    """
    Stores the base pricing for different types of accommodations and seasons.

    Fields:
        - booking_type: main type (tent, caravan, camping_car)
        - season: low/mid/high
        - is_worker: boolean flag for worker rates
        - price_1_person_with_electricity, price_2_persons_with_electricity
        - price_1_person_without_electricity, price_2_persons_without_electricity
        - supplements: related SupplementPrice

    Methods:
        - save(): auto-assigns included_people and supplements
        - clean(): validates camping-car pricing rules
    Security:
        - Only numeric and enum fields
        - Validation ensures business rules are respected
    """
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

    # --- Price for clients ---
    price_1_person_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix 1 personne avec électricité")
    price_2_persons_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix 2 personnes avec électricité")
    price_1_person_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix 1 personne sans électricité")
    price_2_persons_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix 2 personnes sans électricité")

    included_people = models.PositiveIntegerField(editable=False) 
    
    # --- Worker prices ---
    worker_week_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix ouvrier semaine", help_text="Prix par nuit en semaine, électricité incluse")
    weekend_price_without_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix ouvrier week-end sans électricité")
    weekend_price_with_electricity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Prix ouvrier week-end avec électricité")

    supplements = models.ForeignKey(SupplementPrice, on_delete=models.SET_NULL, related_name="prices", null=True, blank=True)

    class Meta:
        verbose_name = "Tarif"
        verbose_name_plural = "Tarifs"

    def save(self, *args, **kwargs):
        """
        Automatically assigns included_people based on booking_type and
        ensures a SupplementPrice is associated if missing.
        """
        if self.booking_type == "camping_car":
            self.included_people = 2
        elif self.price_2_persons_with_electricity or self.price_2_persons_without_electricity:
            self.included_people = 2
        elif self.price_1_person_with_electricity or self.price_1_person_without_electricity:
            self.included_people = 1
        else:
            self.included_people = 1 
        
        if not self.supplements:
            supplement = SupplementPrice.objects.first()
            if not supplement:
                supplement = SupplementPrice.objects.create()
            self.supplements = supplement

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validate business rules before saving.
        For camping_car, ensures that '1 person' price fields are empty.
        Raises ValidationError on violation.
        """
        errors = {}

        if self.booking_type == "camping_car":
            if self.price_1_person_without_electricity or self.price_1_person_with_electricity:
                errors["booking_type"] = ValidationError(
                    "Pour les camping-cars, ne renseignez pas les champs '1 personne'."
                    "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement les champs '2 personnes'."
                )
        
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Return a human-readable label including season or worker info."""
        label =  f"{self.get_booking_type_display()}"
        if self.is_worker:
            label += " (Ouvriers)"
        elif self.season:
            label += f" - {self.get_season_display()}"
        return label
    
class OtherPrice(TranslatableModel):
    """
    Stores miscellaneous pricing info such as tourist tax.

    Fields:
        - current_year: current calendar year
        - tourist_tax_date: date when tourist tax applies
        - price_tourist_tax: price per night/person

    Security:
        - Read-only for user input
        - Only numeric and date fields
    """
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
            max_digits=5, decimal_places=2, default=0.29, validators=[MinValueValidator(0)],
            verbose_name="Prix taxe de séjour par nuit/personne"
        ),
    )

    def __str__(self):
        """Return a human-readable label including other pricing info."""
        return "Tarifs divers"

    class Meta:
        verbose_name = "Tarifs et infos divers"
        verbose_name_plural = "Tarifs et infos divers"

class Capacity(models.Model):
    """
    Stores maximum capacity for each booking type.

    Fields:
        - booking_type: type of accommodation
        - max_places: maximum allowed placements
        - number_locations: total locations
        - number_mobile_homes: number of mobile homes

    Security:
        - Only numeric data
        - Used for internal validation (check_capacity)
    """
    booking_type = models.CharField(max_length=20, choices=Price.TYPE_CHOICES, unique=True, verbose_name="Type d'emplacement")
    max_places = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Nombre maximum d'emplacements")
    number_locations = models.PositiveIntegerField(
        default=66, 
        validators=[MinValueValidator(0)],
        verbose_name="Nombre d'emplacements"
    )
    number_mobile_homes = models.PositiveIntegerField(
        default=5, 
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de mobil-homes"
    )

    class Meta:
        verbose_name = "Capacité d'emplacements"
        verbose_name_plural = "Capacités d'emplacements"

    def __str__(self):
        """Return a human-readable label including capacity info."""
        return f"{self.get_booking_type_display()} - {self.max_places} emplacements"

class Booking(models.Model):
    """
    Stores client booking information.

    Fields:
        - Personal info: last_name, first_name, address, postal_code, city, phone, email
        - Reservation info: start_date, end_date, booking_type, booking_subtype, electricity
        - Counts: adults, children_over_8, children_under_8, pets
        - Extras: extra_vehicle, extra_tent, deposit_paid
        - Timestamps: created_at, updated_at

    Methods:
        - get_season(): determines season based on start_date
        - calculate_total_price(): calculates total cost including supplements
        - calculate_deposit(): calculates 15% deposit
        - save(): auto-assigns main type, included_people, supplements
        - check_capacity(): checks if capacity is available
        - clean(): validates business rules and capacity

    Security:
        - Input validation via clean() ensures business rules are respected
        - Numeric and enum fields only; safe from injection
        - check_capacity prevents overbooking
        - All calculations server-side
    """
    TYPE_CHOICES = Price.TYPE_CHOICES

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

    # Client info
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    address = models.CharField(max_length=255, verbose_name="Adresse")
    postal_code = models.CharField(max_length=10, verbose_name="Code postal")
    city = models.CharField(max_length=100, verbose_name="Ville")
    phone = models.CharField(
        max_length=20, 
        validators=[RegexValidator(r'^[0-9 +()-]*$')],
        verbose_name="Téléphone"
        )
    email = models.EmailField(
        max_length=255, 
        validators=[EmailValidator()],
        verbose_name="Email"
    )

    # Booking details
    start_date = models.DateField(verbose_name="Date d'arrivée")
    end_date = models.DateField(verbose_name="Date de départ")
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type d'emplacement")
    booking_subtype = models.CharField(max_length=20, choices=SUBTYPE_CHOICES, null=True, blank=True, verbose_name="Sous-type d'emplacement")
    electricity = models.CharField(max_length=3, choices=ELECTRICITY_CHOICES, verbose_name="Électricité")
    deposit_paid = models.BooleanField(default=False, verbose_name="Acompte payé")

    # Optional details
    tent_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Longueur de la tente")
    tent_width = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Largeur de la tente")
    vehicle_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Longueur du véhicule")
    cable_length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="Longueur du câble")

    adults = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Adultes")
    children_over_8 = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Enfants +8 ans")
    children_under_8 = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Enfants -8 ans")
    pets = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Animaux de compagnie")

    extra_vehicle = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Véhicule supplémentaire")
    extra_tent = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Tente supplémentaire")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

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
        """Format creation date for admin display."""
        if not self.created_at:
            return ""
        local_dt = timezone.localtime(self.created_at)
        return formats.date_format(local_dt, format='d F Y à H:i', use_l10n=True)
    created_at_display.short_description = "Créé le"

    def updated_at_display(self):
        """Format updated date for admin display."""
        if not self.updated_at:
            return ""
        local_dt = timezone.localtime(self.updated_at)
        return formats.date_format(local_dt, format='d F Y à H:i', use_l10n=True)
    updated_at_display.short_description = "Mis à jour le"

    def get_season(self):
        """Determine season based on start_date."""
        month, day = self.start_date.month, self.start_date.day
        if (month >= 9 and day >= 27) or (month <= 4 and day <= 26):
            return 'low'
        elif (month >= 7 and day >= 5) and (month <= 8 and day <= 30):
            return 'high'
        else:
            return 'mid'

    def calculate_total_price(self, supplement=None):
        """
        Calculate total price including extras and supplements.
        Ensures nights >= 1 and applies correct base price depending on booking_type and electricity.
        """
        nights = max((self.end_date - self.start_date).days, 1)

        subtype_to_type_map = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        booking_type_for_price = subtype_to_type_map.get(self.booking_subtype, self.booking_type)
        season = self.get_season()
        try:
            price = Price.objects.get(
                booking_type=booking_type_for_price,
                is_worker=False,
                season=season
            )
        except Price.DoesNotExist:
            return 0

        if supplement is None:
            supplement = Price.objects.first().supplements if Price.objects.exists() else None
        electricity_yes = self.electricity == 'yes'

        included_people = price.included_people if price else 1

        # Base price
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

        # Add extras
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
        """Calculate 15% deposit of total price, rounded to 2 decimals."""
        total_price = self.calculate_total_price()
        return round(total_price * Decimal('0.15'), 2)


    def save(self, *args, **kwargs):
        """
        Automatically sets booking_type from booking_subtype, included_people,
        and assigns a SupplementPrice if missing.
        """

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
        if self.booking_type == 'camping_car':
            self.included_people = 2
        else:
            self.included_people = 1 
        
        if not hasattr(self, 'supplements') or self.supplements is None:
            self.supplements = SupplementPrice.objects.first()

        super().save(*args, **kwargs)

    def check_capacity(self):
        """
        Checks availability for given dates and booking type.
        Raises ValidationError if capacity exceeded.
        """
        MAIN_TYPE_MAP = {
            'tent': 'tent',
            'car_tent': 'tent',
            'caravan': 'caravan',
            'fourgon': 'caravan',
            'van': 'caravan',
            'camping_car': 'camping_car',
        }

        if self.start_date is None or self.end_date is None:
            raise ValidationError(_("Les dates de réservations sont requises pour vérifier la disponibilité."))
        
        main_type = MAIN_TYPE_MAP.get(self.booking_type, self.booking_type)

        try:
            capacity = Capacity.objects.get(booking_type=main_type).max_places
        except Capacity.DoesNotExist:
            raise ValidationError(_("La capacité pour %(type)s n'est pas définie.") % {'type': main_type})
    
        overlapping = Booking.objects.filter(
            booking_type__in=[key for key, value in MAIN_TYPE_MAP.items() if value == main_type],
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(pk=self.pk)  

        if overlapping.count() >= capacity:
            raise ValidationError(
                _("Plus de places disponibles pour ces dates. "
                "Veuillez choisir d'autres dates ou contacter le camping.")
            )

    def clean(self):
        """
        Validates business rules:
        - Capacity availability
        - Camping_car pricing rules
        Raises ValidationError on violation.
        """
        super().clean()

        self.check_capacity()

        if self.booking_type == "camping_car":
            pass

    def __str__(self):
        """Return a human-readable representation of the booking with dates."""
        return f"{self.get_booking_type_display()} ({self.start_date} to {self.end_date})"
    
class MobileHome(models.Model):
    """
    Stores mobile home info and translations.

    Fields:
        - name, description_text: French version
        - name_en/es/de/nl, description_en/es/de/nl: translated versions
        - night_price, week_low/mid/high: nightly and weekly prices
        - is_worker_home: reserved for workers
        - worker_price_1p/2p/3p: weekly prices for workers

    Methods:
        - save(): automatically translates name and description via DeepL API

    Security:
        - Only numeric/text fields
        - DeepL translations handled server-side
        - No user input directly sent to API
    """
    # Name in multiple languages
    name = models.CharField(max_length=100, verbose_name= "Nom du mobil-home")
    name_en = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (EN)")
    name_es = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (ES)")
    name_de = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (DE)")
    name_nl = models.CharField(max_length=100, blank=True, verbose_name= "Nom du mobil-home (NL)")

    # Descriptions in multiple languages
    description_text = models.TextField(blank=True, verbose_name= "Description FR")   
    description_en = models.TextField(blank=True, verbose_name= "Description EN")
    description_es = models.TextField(blank=True, verbose_name= "Description ES")
    description_de = models.TextField(blank=True, verbose_name= "Description DE")
    description_nl = models.TextField(blank=True, verbose_name= "Description NL")

    # Nightly and weekly pricing
    night_price = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True,
        validators=[MinValueValidator(0)], 
        verbose_name= "Prix/nuitée (basse et moyenne saison)"
        )
    night_price_mid = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name= "Prix/nuitée (moyenne saison)"
    )
    week_low = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)], 
        verbose_name= "Prix/semaine (basse saison)"
        )
    week_mid = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)], 
        verbose_name= "Prix/semaine (moyenne saison)"
    )
    week_high = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)], 
        verbose_name= "Prix/semaine (haute saison)"
    )

    # Worker special pricing
    is_worker_home = models.BooleanField(default=False, verbose_name= "Réservé aux ouvriers")
    worker_price_1p = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name= "Prix/semaine 1 personne (ouvrier)")
    worker_price_2p = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name= "Prix/semaine 2 personnes (ouvrier)")
    worker_price_3p = models.DecimalField(
        max_digits=6, decimal_places=0, null=True, blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name= "Prix/semaine 3 personnes (ouvrier)")

    class Meta:
        verbose_name = "Mobil-home"
        verbose_name_plural = "Mobil-homes"

    def __str__(self):
        """Return the mobile home name for display."""
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Automatically translate name and description to multiple languages using DeepL.
        Only executed if DEEPL_API_KEY is set and description_text is provided.
        """
        if settings.DEEPL_API_KEY and self.description_text:
            try:
                translator = deepl.Translator(settings.DEEPL_API_KEY)

                # Traduction noms
                for lang, field in [('EN-GB','name_en'), ('ES','name_es'), ('DE','name_de'), ('NL','name_nl')]:
                    if not getattr(self, field, None):
                        setattr(self, field, translator.translate_text(self.name, target_lang=lang).text)

                # Traduction descriptions
                for lang, field in [('EN-GB','description_en'), ('ES','description_es'), ('DE','description_de'), ('NL','description_nl')]:
                    if not getattr(self, field, None):
                        setattr(self, field, translator.translate_text(self.description_text, target_lang=lang).text)

            except Exception as e:
                # logger.warning(f"DeepL translation failed: {e}")
                pass

        super().save(*args, **kwargs)
    
class SupplementMobileHome(TranslatableModel):
    """
    Stores extra charges for mobile homes.

    Fields:
        - mobile_home_deposit: security deposit
        - cleaning_deposit: cleaning deposit
        - bed_linen_rental: optional linen rental

    Security:
        - Numeric fields only
        - Used for internal calculations, no user input processed
    """
    translations = TranslatedFields(
        mobile_home_deposit = models.DecimalField(
            max_digits=4,
            decimal_places=0, 
            default=350,
            validators=[MinValueValidator(0)],
            verbose_name="Montant caution mobil-home"
        ),
        cleaning_deposit = models.DecimalField(
            max_digits=4, 
            decimal_places=0, 
            default=70,
            validators=[MinValueValidator(0)],
            verbose_name="Montant caution ménage"
        ),
        bed_linen_rental = models.DecimalField(
            max_digits=4, 
            decimal_places=0, 
            default=15,
            validators=[MinValueValidator(0)],
            verbose_name="Prix location linge de lit"
        ),
    )

    def __str__(self):
        """Return a human-readable label for admin."""
        return "Suppléments mobil-home"

    class Meta:
        verbose_name = "Suppléments mobil-home"
        verbose_name_plural = "Suppléments mobil-home"

    
class SeasonInfo(TranslatableModel):
    """
    Stores season start and end dates.

    Fields:
        - low_season_start/end
        - mid_season_start_1/end_1, mid_season_start_2/end_2
        - high_season_start/end

    Security:
        - Date fields only
        - Used internally for price and availability calculations
    """

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
        """Return human-readable season info."""
        return "Dates des saisons"

    class Meta:
        verbose_name = "Dates des saisons"
        verbose_name_plural = "Dates des saisons"