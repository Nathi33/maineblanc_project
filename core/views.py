import json
import os
from django.conf import settings
from django.utils.translation import get_language
from django.shortcuts import render

def home_view(request):
    return render(request, 'core/home.html')

def about_view(request):
    return render(request, 'core/about.html')

def accommodations_view(request):
    return render(request, 'core/accommodations.html')

def services_view(request):
    lang_code = get_language()[:2]  # ex: 'fr', 'en', 'es', 'de'
    translations = load_translation(lang_code)
    return render(request, 'core/services.html', {'t': translations})

def activities_view(request):
    return render(request, 'core/activities.html')

def pricing_view(request):
    return render(request, 'core/pricing.html')

def contact_view(request):
    return render(request, 'core/contact.html')

def bookings_view(request):
    return render(request, 'core/bookings.html')

def legal_view(request):
    return render(request, 'core/legal.html')

def load_translation(lang_code):
    lang_file = os.path.join(settings.BASE_DIR, 'static', 'lang', 'services', f'{lang_code}.json')
    try:
        with open(lang_file, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # fallback to French
        with open(os.path.join(settings.BASE_DIR, 'static', 'lang', 'services', 'fr.json'), encoding='utf-8') as f:
            return json.load(f)
