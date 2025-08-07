import json
import os
from django.conf import settings
from django.utils.translation import get_language
from django.shortcuts import render

def load_translation(folder, lang_code):
    """
    Charge un fichier JSON de traduction dans le dossier `folder`.
    Retombe sur 'fr.json' si la langue demandée n'existe pas.
    """
    lang_file = os.path.join(settings.BASE_DIR, 'static', 'lang', folder, f'{lang_code}.json')
    fallback_file = os.path.join(settings.BASE_DIR, 'static', 'lang', folder, 'fr.json')
    try:
        with open(lang_file, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        with open(fallback_file, encoding='utf-8') as f:
            return json.load(f)

# --- Vues simples sans traductions dynamiques
def home_view(request):
    return render(request, 'core/home.html')

def about_view(request):
    return render(request, 'core/about.html')

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

# --- Vues avec traduction JSON
def services_view(request):
    lang_code = get_language()
    translations = load_translation('services', lang_code)
    return render(request, 'core/services.html', {'t': translations})

def accommodations_view(request):
    lang_code = get_language()
    translations = load_translation('accommodations', lang_code)
    return render(request, 'core/accommodations.html', {'t': translations})
