from django.contrib import admin
from django import forms
from .models import Booking, Price, SupplementPrice, Capacity


# -----------------------------
# Admin pour les capacités
# -----------------------------
@admin.register(Capacity)
class CapacityAdmin(admin.ModelAdmin):
    list_display = (
        'booking_type',
        'max_places',
    )
    list_filter = ('booking_type',)
    search_fields = ('booking_type',)

    fieldsets = (
        ('Nombre d\'emplacements', {
            'fields': (
                'booking_type',
                'max_places',
            ),
            'description': "Nombre maximum d'emplacements disponibles pour chaque type de réservation."
        }),
    )

# -----------------------------
# Admin pour les suppléments
# -----------------------------
@admin.register(SupplementPrice)
class SupplementPriceAdmin(admin.ModelAdmin):
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

# -----------------------------
# Formulaire admin personnalisé pour Price
# -----------------------------
class PriceAdminForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get("booking_type")

        # Masquer les champs 1 personne si camping-car
        if booking_type == "camping_car":
            if cleaned_data.get("price_1_person_with_electricity") or cleaned_data.get("price_1_person_without_electricity"):
                raise forms.ValidationError(
                    "Pour les camping-cars, ne renseignez pas le champ '1 personne'."
                    "Le tarif est identique pour 1 ou 2 personnes : utilisez uniquement le champ 2 personnes."
                )
        return cleaned_data

# -----------------------------
# Admin pour les tarifs d'emplacements
# -----------------------------
@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
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

    # Organisation du formulaire
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

# -----------------------------
# Admin pour les réservations
# -----------------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'start_date',
        'end_date',
        'booking_subtype',
        'electricity',
        'deposit_paid',
        'created_at',
    )
    list_editable = ('deposit_paid',)
    list_filter = ('booking_subtype', 'electricity', 'deposit_paid', 'start_date', 'end_date')
    search_fields = ('last_name', 'first_name', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

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
            'fields': ('created_at', 'updated_at')
        }),
    )
