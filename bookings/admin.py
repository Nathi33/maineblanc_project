from django.contrib import admin
from django import forms
from .models import Booking, Price, SupplementPrice, Capacity, MobileHome, SeasonInfo, SupplementMobileHome, OtherPrice
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin
from django.conf import settings
import deepl


@admin.register(Capacity)
class CapacityAdmin(admin.ModelAdmin):
    """Admin for the Capacity model: displays booking types and maximum capacity."""
    list_display = (
        'booking_type',
        'max_places',
        'number_locations',
        'number_mobile_homes',
    )
    list_filter = ('booking_type',)
    search_fields = ('booking_type',)

    fieldsets = (
        ('Nombre d\'emplacements par type', {
            'fields': (
                'booking_type',
                'max_places',
            ),
            'description': "Nombre maximum d'emplacements disponibles pour chaque type de réservation."
        }),
        ("Capacités totales du camping", {
            'fields': (
                'number_locations',
                'number_mobile_homes',
            )
        }),
    )


@admin.register(SupplementPrice)
class SupplementPriceAdmin(admin.ModelAdmin):
    """Admin for the SupplementPrice model: display and manage extra pricing."""
    list_display = (
        'extra_adult_price',
        'child_over_8_price',
        'child_under_8_price',
        'pet_price',
        'extra_vehicle_price',
        'extra_tent_price',
        'visitor_price_without_swimming_pool',
        'visitor_price_with_swimming_pool',
    )
    search_fields = ()
    
    fieldsets = (
        ('Suppléments', {
            'fields': (
                'extra_adult_price',
                'child_over_8_price',
                'child_under_8_price',
                'pet_price',
                'extra_vehicle_price',
                'extra_tent_price',
                'visitor_price_without_swimming_pool',
                'visitor_price_with_swimming_pool',
            ),
            'description': "Tarifs des suppléments quelque soit la saison et le type d'hébergement."
        }),
    )

class PriceAdminForm(forms.ModelForm):
    """Custom form for PriceAdmin to add validation logic."""
    class Meta:
        model = Price
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get("booking_type")

        if booking_type == "camping_car":
            if cleaned_data.get("price_1_person_with_electricity") or cleaned_data.get("price_1_person_without_electricity"):
                raise forms.ValidationError(
                    "Pour les camping-cars, ne renseignez pas le champ '1 personne'."
                    "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement le champ 2 personnes."
                )
        return cleaned_data


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    """
    Admin interface for Price model.

    - Uses custom form PriceAdminForm to validate fields
    - Displays pricing info for different booking types, seasons, and workers
    - Organizes form fields into sections with descriptions
    - List view shows both 1-person and 2-person prices, weekend and worker prices
    """
    form = PriceAdminForm
    list_display = (
        'booking_type', 
        'season', 
        'is_worker', 
        'price_1_person_with_electricity',
        'price_2_persons_with_electricity',
        'price_1_person_without_electricity',
        'price_2_persons_without_electricity',
        'worker_week_price',
        'weekend_price_without_electricity',
        'weekend_price_with_electricity',
    )
    list_filter = ('booking_type', 'season', 'is_worker')
    search_fields = ('booking_type', 'season')
    ordering = ('booking_type', 'season', 'is_worker')
    exclude = ('included_people',)

    fieldsets = (
        ('Tarifs classiques', {
            'fields': (
                'booking_type',
                'season',
                'price_1_person_with_electricity',
                'price_2_persons_with_electricity',
                'price_1_person_without_electricity',
                'price_2_persons_without_electricity',
            ),
            'description': (
                "Pour les tentes, caravanes et fourgons, saisir les tarifs 1 et 2 personnes.<br>"
                "Pour les camping-cars, le tarif est identique pour 1 ou 2 personnes."
                "Merci de renseigner uniquement la ligne <strong>2 personnes</strong> et laisser l'autre vide."
            )
        }),
        ('Tarifs ouvriers semaine', {
            'fields': (
                'is_worker',
                'worker_week_price',
            ),
            'description': "Prix spéciaux pour les ouvriers, électricité incluse."
        }),
        ('Tarifs ouvriers weekend', {
            'fields': (
                'weekend_price_without_electricity',
                'weekend_price_with_electricity',
            ),
            'description': "Tarifs réduits le week-end quelque soit le type d'hébergement."
        }),
    ) 


@admin.register(OtherPrice)
class OtherPriceAdmin(TranslatableAdmin):
    """Admin for the OtherPrice model: manage current year and tourist tax."""
    list_display = (
        'current_year',
        'tourist_tax_date',
        'price_tourist_tax',
    )

    fieldsets = (
        ("Année en cours", {
            'fields': (
                'current_year',
            )
        }),
        ("Taxe de séjour", {
            'fields': (
                'tourist_tax_date',
                'price_tourist_tax',
            )
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for Booking model.

    - Displays client info, booking details, capacities, and extra options
    - Allows editing of deposit status directly from list view
    - Provides filters by type, electricity, deposit, and dates
    - Readonly fields: created_at_display, updated_at_display
    """
    list_display = (
        'last_name',
        'first_name',
        'start_date',
        'end_date',
        'booking_type',
        'booking_subtype',
        'electricity',
        'deposit_paid',
        'created_at_display',
        'updated_at_display',
    )
    list_editable = ('deposit_paid',)
    list_filter = ('booking_type', 'booking_subtype', 'electricity', 'deposit_paid', 'start_date', 'end_date')
    search_fields = ('last_name', 'first_name', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at_display', 'updated_at_display')

    fieldsets = (
        ('Informations client', {
            'fields': (
                'last_name',
                'first_name',
                'address',
                'postal_code',
                'city',
                'phone',
                'email',
            )
        }),
        ('Détails de la réservation', {
            'fields': (
                'start_date',
                'end_date',
                'booking_type',
                'booking_subtype',
                'electricity',
                'deposit_paid',
            )
        }),
        ('Capacités et options', {
            'fields': (
                'adults',
                'children_over_8',
                'children_under_8',
                'pets',
                'extra_vehicle',
                'extra_tent',
            )
        }),
        ('Détails supplémentaires', {
            'fields': (
                'tent_length',
                'tent_width',
                'vehicle_length',
                'cable_length'
            ),
            'description': "Ces champs apparaissent uniquement pour certains types d'hébergements."
        }),
        ('Dates de création et de mise à jour', {
            'fields': ('created_at_display', 'updated_at_display')
        }),
    )


@admin.register(MobileHome)
class MobileHomeAdmin(admin.ModelAdmin):
    """Admin for the MobileHome model: display pricing, information, and options."""
    list_display = (
        'name',
        'night_price',
        'night_price_mid',
        'week_low',
        'week_mid',
        'week_high',
        'is_worker_home',
    )
    search_fields = ('name',)
    list_filter = ('is_worker_home',)

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'name',
                'description_text'
            )
        }),
        ('Prix à la nuitée', {
            'fields': (
                'night_price',
                'night_price_mid'
            ),
            'description': "Prix à la nuitée uniquement en basse et moyenne saison (si le prix moyenne saison diffère, utilisez night_price_mid)."
        }),
        ('Prix par semaine', {
            'fields': (
                'week_low',
                'week_mid',
                'week_high'
            ),
        }),
        ('Prix ouvriers', {
            'fields': (
                'is_worker_home',
                'worker_price_1p',
                'worker_price_2p',
                'worker_price_3p',
            ),
            'description': "Uniquement pour le mobil-home ouvrier. Les prix sont fixes selon le nombre de personnes."
        }),
    )


@admin.register(SupplementMobileHome)
class SupplementMobileHomeAdmin(TranslatableAdmin):
    """Admin for the SupplementMobileHome model: manage deposits and linen rental."""
    list_display = (
        'mobile_home_deposit',
        'cleaning_deposit',
        'bed_linen_rental',
    )
    
    fieldsets = (
        ("Cautions et location de linge", {
            'fields': (
                'mobile_home_deposit',
                'cleaning_deposit',
                'bed_linen_rental',
            )
        }),
    )


@admin.register(SeasonInfo)
class SeasonInfoAdmin(TranslatableAdmin):
    """Admin for the SeasonInfo model: manage low, mid, and high season dates."""
    list_display = [
        'low_season_start',
        'low_season_end',
        'mid_season_start_1',
        'mid_season_end_1',
        'mid_season_start_2',
        'mid_season_end_2',
        'high_season_start',
        'high_season_end',
    ]


    fieldsets = (
        ("Saisons", {
            'fields': (
                'low_season_start',
                'low_season_end',
                'mid_season_start_1',
                'mid_season_end_1',
                'mid_season_start_2',
                'mid_season_end_2',
                'high_season_start',
                'high_season_end',
            )
        }),
    )