from datetime import datetime, date, time
from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def format_time_by_locale(value):
    """
    Format a time according to the currently active language.

    Supported formats by language:
        - fr : 24-hour format with 'h', e.g., "14h30"
        - en : 12-hour format with AM/PM, e.g., "2:30 p.m."
        - es, de, nl : Standard 24-hour format, e.g., "14:30"

    Args:
        value (datetime.time | datetime.datetime): 
            The time to format.

    Returns:
        str: Formatted time string based on the active locale,
             or an empty string if value is None or invalid.
    """
    if not isinstance(value, (datetime, date, time)):
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
    Format a date according to the currently active language.

    Supported formats by language:
        - fr : "day/month" -> 25/09
        - en : "month/day" -> 09/25
        - es : "day/month" -> 25/09
        - de : "day.month" -> 25.09
        - nl : "day-month" -> 25-09
        - default : "month-day" -> 09-25

    Args:
        value (datetime.date | datetime.datetime): 
            The date to format.

    Returns:
        str: Formatted date string based on the active locale,
             or an empty string if value is None or invalid.
    """
    if not isinstance(value, (datetime, date)):
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
        return value.strftime("%m-%d")