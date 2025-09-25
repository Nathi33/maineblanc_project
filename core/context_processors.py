from datetime import datetime

def global_static_version(request):
    """
    Adds STATIC_VERSION to the global context to handle cache-busting.
    """
    return {'STATIC_VERSION': datetime.now().strftime('%Y%m%d%H%M%S')}


def available_languages(request):
    """
    Provides the list of languages ​​and flags for the drop-down menu.
    """
    return {
        'languages': [
            ("fr", "flag-french.png"),
            ("en", "flag-UK.png"),
            ("es", "flag-spain.png"),
            ("de", "flag-deutsch.png"),
            ("nl", "flag-nederlands.png"),
        ]
    }