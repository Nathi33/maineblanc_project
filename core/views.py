from django.conf import settings
from django.utils.translation import gettext as _
from django.shortcuts import render
from bookings.models import Price, SupplementPrice, SeasonInfo, Capacity, MobileHome, SupplementMobileHome, OtherPrice
from .models import CampingInfo, SwimmingPoolInfo, FoodInfo, LaundryInfo
from django.utils import translation


def home_view(request):
    return render(request, 'core/home.html')

def about_view(request):
    return render(request, 'core/about.html')

def infos_view(request):
    # --- Tarifs classiques et ouvriers ---
    prices = Price.objects.all()

    grouped_prices = {}
    normal_prices = prices.filter(is_worker=False)
    
    for price in normal_prices:
        key = price.booking_type
        if key not in grouped_prices:
            grouped_prices[key] = []
        grouped_prices[key].append(price)

    worker_prices = prices.filter(is_worker=True)

    # --- Suppléments ---
    supplements_obj = SupplementPrice.objects.first()
    supplements = []
    visitor_prices = []

    if supplements_obj:
        mapping = {
            "extra_adult_price": _("Adulte supplémentaire"),
            "child_over_8_price": _("Enfant +8 ans"),
            "child_under_8_price": _("Enfant -8 ans"),
            "pet_price": _("Animal"),
            "extra_vehicle_price": _("Véhicule supplémentaire"),
            "extra_tent_price": _("Tente supplémentaire"),
            "deposit": _("Caution - Prêt de matériel (adaptateur, fer à repasser, sèche-cheveux...)"),
        }

        for field, label in mapping.items():
            value = getattr(supplements_obj, field, None)
            if value and value > 0:
                supplements.append({
                    "label": label,
                    "price": value
                })
        
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

    # --- Modalités du camping ---
    camping_info = CampingInfo.objects.first()

    # --- Année et tarifs divers ---
    other_prices = OtherPrice.objects.first()

    # --- Dates des saisons ---
    season_info = SeasonInfo.objects.first()

    # --- Tarifs Mobil-homes ---
    mobilhomes = MobileHome.objects.all()

    # --- Supplements Mobil-homes ---
    mobilhome_supplements = SupplementMobileHome.objects.first()

    # --- Capacité du camping ---
    capacity_info = Capacity.objects.first()

    return render(request, 'core/infos.html', {
        "grouped_prices": grouped_prices,
        "worker_prices": worker_prices,
        "supplements": supplements,
        "visitor_prices": visitor_prices,
        "mobilhomes": mobilhomes,
        "mobilhome_supplements": mobilhome_supplements,
        "camping_info": camping_info,
        "season_info": season_info,
        "capacity_info": capacity_info,
        "other_prices": other_prices,
    })

def services_view(request):
    swimming_info = SwimmingPoolInfo.objects.first()
    food_info = FoodInfo.objects.first()
    laundry_info = LaundryInfo.objects.first()  

    return render(request, 'core/services.html', {
        "swimming_info": swimming_info,
        "food_info": food_info,
        "laundry_info": laundry_info
    })

def accommodations_view(request):
    return render(request, 'core/accommodations.html')

def activities_view(request):
    return render(request, 'core/activities.html')

def legal_view(request):
    return render(request, 'core/legal.html')

def privacy_view(request):
    return render(request, 'core/privacy-policy.html')

def not_found_view(request, exception=None):
    return render(request, 'core/not_found.html', status=404)