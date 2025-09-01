from django.contrib import admin
from .models import Booking, Price, SupplementPrice


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
# Admin pour les tarifs d'emplacements
# -----------------------------
@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
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
        ('Tarifs ouvriers', {
            'fields': (
                'is_worker',
                'worker_week_price',
                'weekend_price_without_electricity',
                'weekend_price_with_electricity',
            ),
            'description': "Prix spéciaux pour les ouvriers, avec des tarifs réduits le week-end."
        }),
    ) 
