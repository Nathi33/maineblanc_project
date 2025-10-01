from django.utils.translation import gettext as _, get_language
from parler.utils.context import switch_language
from django.shortcuts import render
from django.http import HttpResponse
from bookings.models import Price, SupplementPrice, SeasonInfo, Capacity, MobileHome, SupplementMobileHome, OtherPrice
from .models import CampingInfo, SwimmingPoolInfo, FoodInfo, LaundryInfo


def home_view(request):
    """
    Render the homepage.

    Template:
        core/home.html

    Context:
        languages (list of tuples): list of supported languages and their flag filenames.

    Security:
        - No user input processed; safe from XSS or injection.
    """
    return render(request, 'core/home.html')


def about_view(request):
    """
    Render the about page.

    Security:
        - No user input processed.
    """
    return render(request, 'core/about.html')


def infos_view(request):
    """
    Render the information page with pricing, supplements, seasons, mobile homes,
    camping info, capacity, and other prices.

    Features:
        - Groups normal and worker prices
        - Handles supplements and visitor prices
        - Dynamically sets mobile home descriptions based on current language

    Security:
        - Only retrieves data from the database
        - No user input is processed
        - Safe against XSS and injection
    """
    # --- Retrieve all standard and worker prices ---
    prices = Price.objects.all()

    grouped_prices = {}
    normal_prices = prices.filter(is_worker=False)
    
    for price in normal_prices:
        key = price.booking_type
        if key not in grouped_prices:
            grouped_prices[key] = []
        grouped_prices[key].append(price)

    worker_prices = prices.filter(is_worker=True)

    # --- Supplements prices ---
    supplements_obj = SupplementPrice.objects.first()
    supplements = []
    visitor_prices = []

    if supplements_obj:
        # Map field names to user-friendly labels with translations
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
        
        # Visitor price with/without swimming pool
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

    # --- Camping general information ---
    camping_info = CampingInfo.objects.first()
    other_prices = OtherPrice.objects.first()
    season_info = SeasonInfo.objects.first()
    capacity_info = Capacity.objects.first()

    # --- Language-specific handling ---
    lang = get_language()

    if camping_info:
        with switch_language(camping_info, lang):
            pass
    

    # --- Mobile homes pricing and translated descriptions ---
    mobilhomes = MobileHome.objects.all()
    for home in mobilhomes:
        # Dynamically choose name and description based on language
        home.name_display = getattr(home, f"name_{lang}", home.name)
        home.description_display = getattr(home, f"description_{lang}", home.description_text)

    mobilhome_supplements = SupplementMobileHome.objects.first()

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
    """
    Render the Services page including swimming pool, food, and laundry info.

    Security:
        - Only reads database objects
        - No user input processed
    """

    swimming_info = SwimmingPoolInfo.objects.first()
    food_info = FoodInfo.objects.first()
    laundry_info = LaundryInfo.objects.first()  

    return render(request, 'core/services.html', {
        "swimming_info": swimming_info,
        "food_info": food_info,
        "laundry_info": laundry_info
    })


def accommodations_view(request):
    """
    Render the Accommodations page.

    Security:
        - No user input processed
    """
    return render(request, 'core/accommodations.html')


def activities_view(request):
    """
    Render the Activities page.

    Security:
        - No user input processed
    """
    return render(request, 'core/activities.html')


def legal_view(request):
    """
    Render the Legal page.

    Security:
        - Static content, safe
    """
    return render(request, 'core/legal.html')


def privacy_view(request):
    """
    Render the Privacy Policy page.

    Security:
        - Static content, safe
    """
    return render(request, 'core/privacy-policy.html')


def not_found_view(request, exception=None):
    """
    Render the 404 Not Found page.

    Security:
        - Static content
        - Exception handling passed safely
    """
    return render(request, 'core/not_found.html', status=404)


def robots_txt(request):
    """
    Serve the robots.txt file for search engines.

    Returns:
        Plain text response with crawling rules for bots.
    """
    content = """
User-agent: *
Disallow: /admin/
Disallow: /accounts/
Disallow: /private/
Disallow: /media/private/
Allow: /static/
Allow: /media/
Sitemap: https://www.camping-le-maine-blanc.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")