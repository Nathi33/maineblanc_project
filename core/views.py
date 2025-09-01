import json
import os
from django.conf import settings
from django.utils.translation import gettext as _
from django.shortcuts import render
from bookings.models import Price, SupplementPrice


def home_view(request):
    return render(request, 'core/home.html')

def about_view(request):
    return render(request, 'core/about.html')

def infos_view(request):
    # Récupérer tous les prix
    prices = Price.objects.all()

    # Organisation par type d'hébergement pour les clients "normaux"
    grouped_prices = {}
    normal_prices = prices.filter(is_worker=False)
    
    for price in normal_prices:
        key = price.booking_type
        if key not in grouped_prices:
            grouped_prices[key] = []
        grouped_prices[key].append(price)

    # Récupérer les prix ouvriers
    worker_prices = prices.filter(is_worker=True)

    # Récupérer les suppléments
    supplements_obj = SupplementPrice.objects.first()
    supplements = []
    visitor_prices = []

    if supplements_obj:
        # Mapping des champs traduisibles
        mapping = {
            "extra_adult_price": _("Adulte supplémentaire"),
            "child_over_8_price": _("Enfant +8 ans"),
            "child_under_8_price": _("Enfant -8 ans"),
            "pet_price": _("Animal"),
            "extra_vehicle_price": _("Véhicule supplémentaire"),
            "extra_tent_price": _("Tente supplémentaire"),
        }

        for field, label in mapping.items():
            value = getattr(supplements_obj, field, None)
            if value and value > 0:
                supplements.append({
                    "label": label,
                    "price": value
                })
        
        # Cas particulier pour les visiteurs
        if supplements_obj.visitor_price_without_swimming_pool:
            visitor_prices.append({
                "label": _("(sans piscine)"),
                "price": supplements_obj.visitor_price_without_swimming_pool
            })
        if supplements_obj.visitor_price_with_swimming_pool:
            visitor_prices.append({
                "label": _("(avec piscine)"),
                "price": supplements_obj.visitor_price_with_swimming_pool
            })

    return render(request, 'core/infos.html', {
        "grouped_prices": grouped_prices,
        "worker_prices": worker_prices,
        "supplements": supplements,
        "visitor_prices": visitor_prices
    })

def services_view(request):
    return render(request, 'core/services.html')

def accommodations_view(request):
    return render(request, 'core/accommodations.html')

def activities_view(request):
    return render(request, 'core/activities.html')

def legal_view(request):
    return render(request, 'core/legal.html')

def privacy_view(request):
    return render(request, 'core/privacy-policy.html')

