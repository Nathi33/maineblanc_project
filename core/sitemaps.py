from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class MultilingualStaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    pages = [
        'home',
        'about',
        'infos',
        'services',
        'accommodations',
        'activities',
        'reservation_request',
        'legal',
        'privacy-policy',
    ]

    languages = ['fr', 'en', 'es', 'de', 'nl']

    def items(self):
        """
        Returns a list of tuples (language, name_url)
        Example: [('fr', 'home'), ('en', 'home'), ...]
        """
        return [(lang, page) for lang in self.languages for page in self.pages]

    def location(self, item):
        """
        Constructs the final URL with the language code
        """
        lang, page = item
        return f"/{lang}{reverse(page)}"
    
    def alternates(self, item):
        """
        Adds <xhtml:link> tags to indicate translated versions
        """
        _, page = item
        return {
            lang: f"/{lang}{reverse(page)}"
            for lang in self.languages
        }
