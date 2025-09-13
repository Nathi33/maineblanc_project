from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import CampingInfo, SwimmingPoolInfo, FoodInfo, LaundryInfo
from django.utils.translation import gettext_lazy as _


@admin.register(CampingInfo)
class CampingInfoAdmin(TranslatableAdmin):
    list_display = [
        'welcome_start', 
        'welcome_end', 
        'welcome_afternoon_start', 
        'welcome_afternoon_end',
        'arrivals_start_high',
        'arrivals_end_high',
        'arrivals_end_low',
        'departure_end',
        'portal_start',
        'portal_end',
    ]

    fieldsets = (
        (_("Accueil"), {
            'fields': (
                'welcome_start', 
                'welcome_end', 
                'welcome_afternoon_start', 
                'welcome_afternoon_end',
            )
        }),
        (_("Arrivées"), {
            'fields': (
                'arrivals_start_high', 
                'arrivals_end_high', 
                'arrivals_end_low',
            )
        }),
        (_("Départs"), {
            'fields': (
                'departure_end',
            )
        }),
        (_("Portail de sécurité"), {
            'fields': (
                'portal_start', 
                'portal_end',
            )
        }),
    )

@admin.register(SwimmingPoolInfo)
class SwimmingPoolInfoAdmin(TranslatableAdmin):
    list_display = [
        'pool_opening_start',
        'pool_opening_end',
    ]

    fieldsets = (
        (_("Piscine"), {
            'fields': (
                'pool_opening_start',
                'pool_opening_end',
            )
        }),
    )

@admin.register(FoodInfo)
class FoodInfoAdmin(TranslatableAdmin):
    list_display = [
        'burger_food_days',
        'burger_food_hours_start',
        'burger_food_hours_end',
        'pizza_food_days',
        'bread_hours_reservations',
        'bread_hours_start',
        'bread_hours_end',
        'bar_hours_start',
        'bar_hours_end',
    ]
    fieldsets = (
        (_("Restauration"), {
            'fields': (
                'burger_food_days',
                'burger_food_hours_start',
                'burger_food_hours_end',
                'pizza_food_days',
                'bread_hours_reservations',
                'bread_hours_start',
                'bread_hours_end',
                'bar_hours_start',
                'bar_hours_end',
            )
        }),
    )

@admin.register(LaundryInfo)
class LaundryInfoAdmin(TranslatableAdmin):
    list_display = [
        'washing_machine_price',
        'dryer_price',
    ]
    fieldsets = (
        (_("Laverie"), {
            'fields': (
                'washing_machine_price',
                'dryer_price',
            )
        }),
    )