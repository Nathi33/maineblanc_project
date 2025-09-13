import locale
from django import template
from django.utils.translation import get_language

register = template.Library()

@register.filter
def format_time_by_locale(value):
    """
    Affiche les heures au format correct selon la langue active.
    """
    if not value:
        return ""

    current_lang = get_language()

    if current_lang == 'fr':
        return value.strftime("%Hh%M")
    elif current_lang == 'en':
        formatted_time = value.strftime("%I:%M %p")
        return formatted_time.lower().replace('am', 'a.m.').replace('pm', 'p.m.')
    elif current_lang in ['es', 'de', 'nl']:
        return value.strftime("%H:%M")
    else:
        return value.strftime("%H:%M")  
    
@register.filter
def format_date_by_locale(value):
    """
    Affiche les dates au format correct selon la langue active.
    """
    if not value:
        return ""

    current_lang = get_language()

    if current_lang == 'fr':
        return value.strftime("%d/%m")
    elif current_lang == 'en':
        return value.strftime("%m/%d")
    elif current_lang == 'es':
        return value.strftime("%d/%m")
    elif current_lang == 'de':
        return value.strftime("%d.%m")
    elif current_lang == 'nl':
        return value.strftime("%d-%m")
    else:
        return value.strftime("%m-%d")  # Format par défaut